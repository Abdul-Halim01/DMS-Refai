# analysis/deepseek_api.py
import re

import requests
import json
import os
from django.conf import settings
from openai import OpenAI
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
import io
from .insight_generator import generate_summary_statistics
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

#api_key="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",
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
)


@csrf_exempt
def get_dataset_insights(request):
    """API endpoint for generating dataset insights"""
    if request.method == 'POST':
        try:
            logger.info("Dataset insights request received")
            data = json.loads(request.body) if request.body else {}
            
            # Get the dataset data from session
            data_json = request.session.get('csv_data')
            
            if not data_json:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No dataset available. Please upload a dataset first.'
                }, status=400)
            
            # Load dataset from session
            df = pd.read_json(io.StringIO(data_json), orient='split')
            
            # Generate basic statistics
            try:
                # Calculate some additional statistics to enrich the insights
                numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
                categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
                
                # Basic stats dictionary
                summary_stats = {
                    'numeric': {},
                    'categorical': {}
                }
                
                # Calculate numeric stats
                for col in numeric_columns:
                    summary_stats['numeric'][col] = {
                        'mean': float(df[col].mean()) if not pd.isna(df[col].mean()) else 0,
                        'median': float(df[col].median()) if not pd.isna(df[col].median()) else 0,
                        'min': float(df[col].min()) if not pd.isna(df[col].min()) else 0,
                        'max': float(df[col].max()) if not pd.isna(df[col].max()) else 0,
                        'std': float(df[col].std()) if not pd.isna(df[col].std()) else 0,
                        'count': int(df[col].count()),
                        'null_count': int(df[col].isna().sum()),
                        'null_percentage': float(df[col].isna().mean() * 100)
                    }
                
                # Calculate categorical stats
                for col in categorical_columns:
                    value_counts = df[col].value_counts().head(5).to_dict()
                    summary_stats['categorical'][col] = {
                        'unique_values': int(df[col].nunique()),
                        'top_value': df[col].value_counts().index[0] if df[col].value_counts().any() else "",
                        'top_value_count': int(df[col].value_counts().iloc[0]) if df[col].value_counts().any() else 0,
                        'null_count': int(df[col].isna().sum()),
                        'null_percentage': float(df[col].isna().mean() * 100),
                        'value_counts': {str(k): int(v) for k, v in value_counts.items()}
                    }
                
            except Exception as e:
                logger.error(f"Error generating custom statistics: {str(e)}")
                summary_stats = {
                    'numeric': {},
                    'categorical': {}
                }
            
            # Find correlations between numeric columns
            correlations = {}
            try:
                if len(numeric_columns) > 1:
                    corr_matrix = df[numeric_columns].corr().round(2)
                    for i, col1 in enumerate(numeric_columns):
                        for col2 in numeric_columns[i+1:]:
                            corr_value = corr_matrix.loc[col1, col2]
                            if not pd.isna(corr_value) and abs(corr_value) > 0.5:  # Only strong correlations
                                correlations[f"{col1}-{col2}"] = float(corr_value)
            except Exception as e:
                logger.error(f"Error calculating correlations: {str(e)}")
            
            # Find potential outliers in numeric data
            outliers = {}
            try:
                for col in numeric_columns:
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    outlier_count = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
                    outlier_percentage = outlier_count / len(df) * 100
                    if outlier_percentage > 1:  # Only mention columns with significant outliers
                        outliers[col] = {
                            'count': int(outlier_count),
                            'percentage': float(outlier_percentage),
                            'lower_bound': float(lower_bound),
                            'upper_bound': float(upper_bound)
                        }
            except Exception as e:
                logger.error(f"Error calculating outliers: {str(e)}")
            
            # Prepare a data sample - first and last rows
            data_sample = {
                'head': df.head(5).to_dict('records'),
                'tail': df.tail(5).to_dict('records')
            }
            
            system_prompt = f"""You are Data Analyst, an advanced data analyst expert who provides SPECIFIC and ACTIONABLE insights.

Dataset Overview:
- Number of rows: {len(df)}
- Columns: {', '.join(df.columns.tolist())}

The dataset contains information about {', '.join(df.columns.tolist())}.

Data Sample (first 5 rows):
{json.dumps(data_sample['head'], indent=2)}

Data Sample (last 5 rows):
{json.dumps(data_sample['tail'], indent=2)}

Numeric Column Statistics: 
{json.dumps(summary_stats['numeric'], indent=2)}

Categorical Column Statistics:
{json.dumps(summary_stats['categorical'], indent=2)}

Strong Correlations:
{json.dumps(correlations, indent=2)}

Potential Outliers:
{json.dumps(outliers, indent=2)}

Analyze this dataset and provide the following:

1. DATA QUALITY INSIGHTS: Highlight missing values, outliers, data inconsistencies, etc.
2. DISTRIBUTION INSIGHTS: Analyze the distributions of key variables
3. CORRELATION INSIGHTS: Identify relationships between variables
4. TREND INSIGHTS: Identify any time-based patterns if date fields exist
5. BUSINESS INSIGHTS: Provide specific business recommendations based on the data

FORMAT REQUIREMENTS:
- Format your response as clean bullet points (• or -) with NO HEADERS or TITLES
- Each bullet point should be a SPECIFIC and ACTIONABLE insight (not general statements)
- Focus on DATA-DRIVEN insights with specific metrics and numbers
- Avoid vague statements like "analyze X" or "look into Y" - instead, provide specific findings
- Make insights concise (1-2 sentences maximum per bullet)
- Provide 6-9 total insights across all categories
- Answer in Arabic ONLY.
- No code blocks or technical syntax
- Simple bullet points when appropriate

EXAMPLE GOOD INSIGHT:
• 23% of donations come from Corporate donors, with an average amount of $5,280 - 3.2x higher than Individual donors
• Missing region data (18% of entries) correlates with older donations (pre-2020), suggesting a data collection process change

DO NOT use any headers or section dividers in your response. ONLY bullet points with specific insights.
Answer in Arabic.
"""
            
            completion = client.chat.completions.create(
                extra_body={},
                model="deepseek/deepseek-r1-zero:free",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    }
                ],
                stream=False
            )
            
            response = completion.choices[0].message.content
            
            # Store this insight in session for future reference
            request.session['ai_insights'] = response
            request.session.modified = True
            
            return JsonResponse({
                'status': 'success',
                'insights': response
            })
            
        except Exception as e:
            logger.error(f"Error generating dataset insights: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f"Error generating insights: {str(e)}"
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Only POST requests are allowed'
    }, status=405)


@csrf_exempt
def analysis_chat_api(request):
    """API endpoint for processing chat messages in the analysis page with simplified, user-friendly responses"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')

            # Use a separate conversation history for analysis page
            analysis_conversation = request.session.get('analysis_conversation', [])
            analysis_conversation.append({"role": "user", "content": user_message})

            # Get the dataset data from session
            data_json = request.session.get('csv_data')
            if not data_json:
                response_prefix = ""
                system_prompt = """أنت محلل بيانات مساعد ودود وبسيط.
                لا توجد بيانات متاحة للتحليل حاليًا.
                أخبر المستخدم بضرورة الذهاب إلى لوحة التحكم وتحميل البيانات أولاً.
                استخدم لغة بسيطة ومباشرة كأنك تتحدث إلى صديق.
                تجنب المصطلحات التقنية واشرح الأمور بطريقة سهلة الفهم.
                كن مرحًا وودودًا في إجاباتك.
                احرص على أن تكون ردودك قصيرة وواضحة.
                """
            else:
                df = pd.read_json(io.StringIO(data_json), orient='split')

                # Generate detailed statistics
                summary_stats = generate_summary_statistics(df)

                dataset_info = {
                    "column_names": df.columns.tolist(),
                    "row_count": len(df),
                    "numeric_stats": summary_stats.get('numeric', {}),
                    "categorical_stats": summary_stats.get('categorical', {})
                }

                system_prompt = f"""أنت محلل بيانات مساعد ودود وبسيط.
                
                لديك بيانات تحتوي على {dataset_info['row_count']} سجل وتتضمن البيانات التالية: {', '.join(dataset_info['column_names'])}.
                
                مهمتك هي:
                - مساعدة المستخدم على فهم البيانات بلغة بسيطة وواضحة
                - تجنب المصطلحات التقنية المعقدة والتفاصيل الإحصائية الثقيلة
                - التركيز على المعلومات المفيدة للمستخدم العادي
                - استخدام أمثلة من الحياة اليومية لتوضيح الأفكار
                - رد على الأسئلة بطريقة محادثة ودية وقصيرة
                
                عند وصف التحليلات:
                - قل "حوالي 75% من البيانات..." بدلاً من "الربيع الثالث (75%) للبيانات..."
                - قل "الأسعار تتراوح بين X وY" بدلاً من "نطاق القيم لعمود السعر هو X إلى Y"
                - قل "معظم العملاء يفضلون..." بدلاً من "التحليل يشير إلى ميل إحصائي نحو..."
                
                كن مباشرًا وودودًا وبسيطًا في تعبيرك، كأنك تتحدث مع صديق.
                أجب بلغة عربية سلسة وواضحة.
                """
                response_prefix = ""

            messages = [
                {"role": "system", "content": system_prompt},
                *analysis_conversation
            ]
            
            completion = client.chat.completions.create(
                extra_body={},
                messages=messages,
                model="deepseek/deepseek-r1-zero:free"
            )
            
            response = completion.choices[0].message.content
            full_response = response_prefix + response
            full_response = full_response.replace('\\boxed{', '').replace('}\n', '\n').strip('}')
            
            # Remove technical markers and improve readability
            full_response = full_response.replace('text ', '')  # Remove 'text' prefix
            
            # Remove numbered technical bullet points format if present
            import re
            full_response = re.sub(r'^\d+\.\s+\*\*[^:]+:\*\*\s+-', '•', full_response, flags=re.MULTILINE)
            full_response = re.sub(r'^\d+\.\s+\*\*[^:]+:\*\*', '•', full_response, flags=re.MULTILINE)
            
            # Clean up potential technical formatting
            full_response = full_response.replace('**', '')  # Remove bold markers
            full_response = re.sub(r'`([^`]+)`', r'\1', full_response)  # Remove code markers
            
            analysis_conversation.append({"role": "assistant", "content": full_response})

            # Store the conversation in the session
            request.session['analysis_conversation'] = analysis_conversation
            request.session.modified = True

            return JsonResponse({
                'status': 'success',
                'response': full_response,
                'hasData': bool(data_json)
            })
        except Exception as e:
            logger.error(f"Error in analysis_chat_api: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

    return JsonResponse({
        'status': 'error',
        'message': 'Only POST requests are allowed'
    }, status=405)

