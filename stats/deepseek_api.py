# analysis/deepseek_api.py

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
def chat_api(request):
    """API endpoint for processing chat messages"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')

            conversation_history = request.session.get('conversation_history', [])
            conversation_history.append({"role": "user", "content": user_message})

            data_json = request.session.get('csv_data')
            if not data_json:
                system_prompt = """You are Data Analyst, an AI data analyst assistant.
                Currently, no dataset has been uploaded. 
                Please inform users that they need to upload data first and guide them on how to do so.
                You can only analyze data after it has been uploaded.
                For now, you can only:
                1. Greet users
                2. Explain that data needs to be uploaded
                3. Guide them on how to upload data
                4. Answer general questions about data analysis capabilities
                Answer in Arabic.
                """
                response_prefix = "No dataset is currently loaded. "
            else:
                df = pd.read_json(io.StringIO(data_json), orient='split')

                # Generate detailed statistics
                summary_stats = generate_summary_statistics(df)

                dataset_info = {
                    "data_by_records": df.to_dict('records'),  # List of row dictionaries
                    "data_by_columns": df.to_dict('list'),     # Dictionary of column lists
                    "column_names": df.columns.tolist(),
                    "row_count": len(df),
                    "numeric_stats": summary_stats['numeric'],
                    "categorical_stats": summary_stats['categorical']
                }

                system_prompt = f""" You are called Data Analyst, a specialized data analyst.
                Your main task is to give insights that help users improve their
                performance based on the data given and answer any questions about the data.

                You are analyzing the following dataset:

                Dataset Overview:
                - Number of rows: {dataset_info['row_count']}
                - Columns: {', '.join(dataset_info['column_names'])}

                Complete Data (by records - each dictionary represents a row):
                {json.dumps(dataset_info['data_by_records'][:5], indent=2)}  # First 5 rows shown for brevity

                Complete Data (by columns - each key is a column name with all its values):
                {json.dumps(dataset_info['data_by_columns'], indent=2)}

                Numeric Statistics: 
                {json.dumps(dataset_info['numeric_stats'], indent=2)}

                Categorical Statistics:
                {json.dumps(dataset_info['categorical_stats'], indent=2)}

                You have two ways to access the data:
                1. By records (rows) - useful for analyzing individual entries
                2. By columns - useful for analyzing trends and patterns in specific fields

                Use this structured data to provide accurate and data-driven responses.
                Answer efficiently and concisely.
                Answer greetings with: would you like some help with your data?.

                For numeric analysis, use the column-oriented data.
                For individual record analysis, use the record-oriented data.
                Answer in Arabic.
                """
                response_prefix = ""

            completion = client.chat.completions.create(
                extra_body={},
                model="deepseek/deepseek-r1-zero:free",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    *conversation_history
                ],
                stream=False
            )

            response = completion.choices[0].message.content
            full_response = response_prefix + response
            full_response = full_response.replace('\\boxed{', '').replace('}\n', '\n').strip('}')
            conversation_history.append({"role": "assistant", "content": full_response})

            request.session['conversation_history'] = conversation_history

            return JsonResponse({
                'status': 'success',
                'response': full_response,
                'hasData': bool(data_json)
            })
        except Exception as e:
            print(f"Error in chat_api: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

    return JsonResponse({
        'status': 'error',
        'message': 'Only POST requests are allowed'
    }, status=405)


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
    """API endpoint for processing chat messages in the analysis page"""
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
                response_prefix = "No dataset is currently loaded for analysis. "
                system_prompt = """You are Data Analyst, an AI data analyst assistant.
                Currently, no dataset is available for analysis. 
                Please inform the user that they need to navigate to the dashboard and upload data first.
                Answer in Arabic.
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

                system_prompt = f"""You are Data Analyst, a specialized data analyst assistant.
                You are currently helping the user analyze a dataset in the analysis page.
                
                Dataset Overview:
                - Number of rows: {dataset_info['row_count']}
                - Columns: {', '.join(dataset_info['column_names'])}
                
                Your task is to help the user understand patterns in their data,
                explain statistical concepts, interpret visualizations, and answer
                any questions about the data analysis process.
                
                Be concise yet informative in your responses.
                If the user asks about specific data insights, refer to what you see 
                in the provided dataset information.
                Answer in Arabic.
                """
                response_prefix = ""

            completion = client.chat.completions.create(
                extra_body={},
                model="deepseek/deepseek-r1-zero:free",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    *analysis_conversation
                ],
                stream=False
            )

            response = completion.choices[0].message.content
            full_response = response_prefix + response
            full_response = full_response.replace('\\boxed{', '').replace('}\n', '\n').strip('}')
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