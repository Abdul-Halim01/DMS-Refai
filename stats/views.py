# stats/views.py
import pandas as pd
import plotly.express as px
from django.shortcuts import render, redirect
from .forms import CsvUploadForm
from django.http import JsonResponse, FileResponse
from django.template.loader import render_to_string
import io
import json
from .insight_generator import generate_donor_insights
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.template import Library
from django import template
from .pdf_generator import generate_pdf_report
import os
import logging
import traceback
from .data_filter import DataFilter

register = Library()  # Registering template tags and filters
logger = logging.getLogger(__name__)

def home(request):
    """Display the CSV upload form."""
    form = CsvUploadForm()
    return render(request, 'stats/upload.html', {'form': form})

def generate_overview(df):
    """Generate overview statistics for the dataset."""
    return {
        'num_rows': df.shape[0],
        'num_columns': df.shape[1],
        'columns': list(df.columns),
        'missing_data': df.isnull().sum().to_dict(),
        'dtypes': df.dtypes.astype(str).to_dict()
    }

def generate_summary_statistics(df):
    """Generate summary statistics for numeric columns."""
    numeric_stats = df.describe().to_dict()
    categorical_stats = {
        col: {
            'unique_values': df[col].nunique(),
            'top_values': df[col].value_counts().head(5).to_dict()
        }
        for col in df.select_dtypes(include=['object', 'category']).columns
    }
    return {'numeric': numeric_stats, 'categorical': categorical_stats}

def generate_plot(df, column):
    """Generate a plot for a single column."""
    if pd.api.types.is_numeric_dtype(df[column]):
        fig = px.histogram(df, x=column, title=f"Distribution of {column}")
    else:
        value_counts = df[column].value_counts()
        fig = px.bar(x=value_counts.index, 
                    y=value_counts.values,
                    title=f"Distribution of {column}")
        fig.update_layout(xaxis_title=column, yaxis_title="Count")
    
    fig.update_layout(
        showlegend=True,
        template='plotly_white',
        margin=dict(l=40, r=40, t=40, b=40)
    )
    
    return fig.to_html(full_html=False)

def generate_all_plots(df):
    """Generate plots for all columns."""
    return {col: generate_plot(df, col) for col in df.columns}

def analyze_csv(request):
    if request.method == "POST":
        form = CsvUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Read CSV file
                csv_file = form.cleaned_data['csv_file']
                df = pd.read_csv(csv_file)
                
                # Store DataFrame in session
                request.session['csv_data'] = df.to_json(orient='split')
                request.session['filename'] = csv_file.name
                request.session.modified = True  # Mark session as modified
                
                # Generate analysis components
                overview = generate_overview(df)
                summary_stats = generate_summary_statistics(df)
                plots = generate_all_plots(df)
                insights = generate_donor_insights(df)
                
                # Convert insights to JSON-serializable format
                serializable_insights = []
                for insight in insights:
                    try:
                        insight_json = json.dumps(insight, default=str)
                        serializable_insight = json.loads(insight_json)
                        serializable_insights.append(serializable_insight)
                    except Exception as e:
                        logger.error(f"Error serializing insight: {str(e)}")
                        continue
                
                context = {
                    'form': form,
                    'overview': overview,
                    'summary_stats': summary_stats,
                    'plots': plots,
                    'insights': serializable_insights,
                }
                
                return render(request, 'stats/analysis.html', context)
            except Exception as e:
                logger.error(f"Error in analyze_csv: {str(e)}")
                messages.error(request, f"Error analyzing CSV file: {str(e)}")
                return render(request, 'stats/upload.html', {'form': form})
    else:
        form = CsvUploadForm()
    return render(request, 'stats/upload.html', {'form': form})

def get_unique_values(request):
    if request.method == "GET":
        try:
            column = request.GET.get('column')
            if not column:
                return JsonResponse({'error': 'No column specified'}, status=400)
            
            # Get data from session
            data_json = request.session.get('csv_data')
            if not data_json:
                return JsonResponse({'error': 'No data found in session'}, status=400)
            
            df = pd.read_json(io.StringIO(data_json), orient='split')
            
            if column not in df.columns:
                return JsonResponse({
                    'error': f'Column "{column}" not found'
                }, status=400)
            
            # Get unique values
            unique_values = df[column].astype(str).unique().tolist()
            
            return JsonResponse({'values': unique_values})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)


def filter_plot(request):
    if request.method == "GET":
        try:
            target = request.GET.get('target')
            mode = request.GET.get('mode')
            values = request.GET.getlist('values[]') or request.GET.getlist('values')
            filter_column = request.GET.get('filter_column')
            
            # Retrieve data from the session
            data_json = request.session.get('csv_data')
            if not data_json:
                return JsonResponse({'error': 'No data found in session'}, status=400)
            
            df = pd.read_json(io.StringIO(data_json), orient='split')
            
            if target not in df.columns:
                return JsonResponse({
                    'error': f'Column "{target}" not found'
                }, status=400)
            
            # Initialize DataFilter with your DataFrame
            data_filter = DataFilter(df)
            
            # Apply filters and track them
            if mode == 'self' and values:
                data_filter.apply_filter(target, values)
            elif mode == 'other' and filter_column and values:
                if filter_column not in df.columns:
                    return JsonResponse({
                        'error': f'Filter column "{filter_column}" not found'
                    }, status=400)
                data_filter.apply_filter(filter_column, values)
            
            # Get the filtered DataFrame
            df_filtered = data_filter.get_filtered_data()
            
            # Store the filtered data and applied filters in the session
            request.session['filtered_data'] = df_filtered.to_json(orient='split')
            request.session['applied_filters'] = data_filter.filter_tracker.get_filters()
            
            # Generate plot
            if pd.api.types.is_numeric_dtype(df[target]):
                fig = px.histogram(df_filtered, x=target, title=f"Distribution of {target}")
            else:
                value_counts = df_filtered[target].value_counts()
                fig = px.bar(x=value_counts.index, y=value_counts.values, title=f"Distribution of {target}")
            
            plot_html = fig.to_html(full_html=False)
            return JsonResponse({'plot_html': plot_html})
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def apply_global_filters(request):
    if request.method == "POST":
        try:
            filters = json.loads(request.POST.get('filters', '[]'))
            logic = request.POST.get('logic', 'AND').upper()
            
            csv_json = request.session.get('csv_data')
            if not csv_json:
                return JsonResponse({'error': 'No data found in session'}, status=400)
            
            df = pd.read_json(io.StringIO(csv_json), orient='split')
            
            # Apply global filters
            query_parts = []
            for filt in filters:
                column = filt.get('column')
                values = filt.get('values', [])
                if column and values:
                    quoted_vals = ", ".join(["'{}'".format(v) for v in values])
                    query_parts.append("`{}` in ({})".format(column, quoted_vals))
            
            if query_parts:
                query_str = (" " + logic + " ").join(query_parts)
                try:
                    filtered_df = df.query(query_str)
                except Exception as e:
                    return JsonResponse({'error': 'Query error: ' + str(e)}, status=400)
            else:
                filtered_df = df

            # Store the filtered DataFrame in the session
            request.session['filtered_data'] = filtered_df.to_json(orient='split')
            
            # Generate plots using the filtered data
            plots = {}
            for col in filtered_df.columns:
                if pd.api.types.is_numeric_dtype(filtered_df[col]):
                    fig = px.histogram(filtered_df, x=col, title=f"Distribution of {col}")
                else:
                    counts = filtered_df[col].value_counts().reset_index()
                    counts.columns = [col, 'count']
                    fig = px.bar(counts, x=col, y='count', title=f"Distribution of {col}")
                plots[col] = fig.to_html(full_html=False)
            
            return JsonResponse({'plots': plots})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_column_types(request):
    if request.method == "GET":
        target = request.GET.get('target')
        compare_column = request.GET.get('compare_column')
        
        data_json = request.session.get('filtered_data') or request.session.get('csv_data')
        if not data_json:
            return JsonResponse({'error': 'No data found'}, status=400)
        
        df = pd.read_json(io.StringIO(data_json), orient='split')
        
        column_types = {
            'target': 'numeric' if pd.api.types.is_numeric_dtype(df[target]) else 'categorical',
            'compare': 'numeric' if pd.api.types.is_numeric_dtype(df[compare_column]) else 'categorical'
        }
        
        return JsonResponse({'column_types': column_types})
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def compare_plot(request):
    if request.method == "GET":
        try:
            target = request.GET.get('target')
            compare_column = request.GET.get('compare_column')
            plot_type = request.GET.get('plot_type')
            agg_method = request.GET.get('agg_method', 'mean')
            color_column = request.GET.get('color_column')
            
            data_json = request.session.get('filtered_data') or request.session.get('csv_data')
            if not data_json:
                return JsonResponse({'error': 'No data found'}, status=400)
            
            df = pd.read_json(io.StringIO(data_json), orient='split')
            
            # Determine column types
            target_is_numeric = pd.api.types.is_numeric_dtype(df[target])
            compare_is_numeric = pd.api.types.is_numeric_dtype(df[compare_column])
            
            if plot_type == 'bar':
                if target_is_numeric:
                    if color_column:
                        # Group by both comparison column and color column
                        agg_df = df.groupby([compare_column, color_column])[target].agg(agg_method).reset_index()
                        fig = px.bar(agg_df, x=compare_column, y=target, color=color_column,
                                   barmode='group',
                                   title=f"{target} by {compare_column} grouped by {color_column} ({agg_method})")
                    else:
                        agg_df = df.groupby(compare_column)[target].agg(agg_method).reset_index()
                        fig = px.bar(agg_df, x=compare_column, y=target,
                                   title=f"{target} by {compare_column} ({agg_method})")
                else:
                    # For categorical target, count occurrences
                    counts = df.groupby([compare_column, target]).size().reset_index(name='count')
                    fig = px.bar(counts, x=compare_column, y='count', color=target,
                               barmode='group',
                               title=f"Count of {target} by {compare_column}")
            
            elif plot_type == 'strip':
                if color_column:
                    fig = px.strip(df, x=compare_column, y=target,
                                 color=color_column,
                                 title=f"{target} by {compare_column} (colored by {color_column})")
                else:
                    fig = px.strip(df, x=compare_column, y=target,
                                 title=f"{target} by {compare_column}")
            
            elif plot_type == 'box':
                if color_column:
                    fig = px.box(df, x=compare_column, y=target,
                               color=color_column,
                               title=f"{target} by {compare_column} (grouped by {color_column})")
                else:
                    fig = px.box(df, x=compare_column, y=target,
                               title=f"{target} by {compare_column}")
            
            elif plot_type == 'violin':
                if color_column:
                    fig = px.violin(df, x=compare_column, y=target,
                                  color=color_column,
                                  title=f"{target} by {compare_column} (grouped by {color_column})")
                else:
                    fig = px.violin(df, x=compare_column, y=target,
                                  title=f"{target} by {compare_column}")
            
            elif plot_type == 'heatmap':
                if color_column:
                    # Create a multi-level crosstab
                    contingency = pd.crosstab([df[target], df[color_column]], df[compare_column])
                    # Reshape for better visualization
                    contingency_flat = contingency.reset_index().melt(
                        id_vars=[target, color_column],
                        var_name=compare_column,
                        value_name='count'
                    )
                    fig = px.density_heatmap(
                        contingency_flat,
                        x=compare_column,
                        y=target,
                        facet_col=color_column,
                        z='count',
                        title=f"{target} vs {compare_column} by {color_column}"
                    )
                else:
                    contingency = pd.crosstab(df[target], df[compare_column])
                    fig = px.imshow(contingency,
                                  title=f"{target} vs {compare_column}")
            
            elif plot_type == 'grouped_bar':
                if color_column:
                    counts = pd.crosstab([df[target], df[color_column]], df[compare_column]).reset_index()
                    counts_melted = counts.melt(
                        id_vars=[target, color_column],
                        var_name=compare_column,
                        value_name='count'
                    )
                    fig = px.bar(counts_melted,
                               x=compare_column,
                               y='count',
                               color=target,
                               pattern_shape=color_column,
                               barmode='group',
                               title=f"{target} vs {compare_column} grouped by {color_column}")
                else:
                    counts = pd.crosstab(df[target], df[compare_column]).reset_index()
                    counts_melted = counts.melt(
                        id_vars=[target],
                        var_name=compare_column,
                        value_name='count'
                    )
                    fig = px.bar(counts_melted,
                               x=compare_column,
                               y='count',
                               color=target,
                               barmode='group',
                               title=f"{target} vs {compare_column}")
            
            elif plot_type == 'stacked_bar':
                if color_column:
                    counts = pd.crosstab([df[target], df[color_column]], df[compare_column]).reset_index()
                    counts_melted = counts.melt(
                        id_vars=[target, color_column],
                        var_name=compare_column,
                        value_name='count'
                    )
                    fig = px.bar(counts_melted,
                               x=compare_column,
                               y='count',
                               color=target,
                               pattern_shape=color_column,
                               barmode='stack',
                               title=f"{target} vs {compare_column} stacked by {color_column}")
                else:
                    counts = pd.crosstab(df[target], df[compare_column]).reset_index()
                    counts_melted = counts.melt(
                        id_vars=[target],
                        var_name=compare_column,
                        value_name='count'
                    )
                    fig = px.bar(counts_melted,
                               x=compare_column,
                               y='count',
                               color=target,
                               barmode='stack',
                               title=f"{target} vs {compare_column}")
            
            elif plot_type == 'scatter':
                if color_column:
                    fig = px.scatter(df, x=target, y=compare_column,
                                   color=color_column,
                                   title=f"{target} vs {compare_column} (colored by {color_column})")
                else:
                    fig = px.scatter(df, x=target, y=compare_column,
                                   title=f"{target} vs {compare_column}")
            
            # Update layout
            fig.update_layout(
                template='plotly_white',
                showlegend=True,
                margin=dict(l=40, r=40, t=40, b=40),
                xaxis_title=compare_column,
                yaxis_title=target if plot_type not in ['grouped_bar', 'stacked_bar'] else 'Count'
            )
            
            # Adjust figure height for faceted plots
            if color_column and plot_type == 'heatmap':
                fig.update_layout(height=400 * len(df[color_column].unique()))
            
            plot_html = fig.to_html(full_html=False)
            return JsonResponse({'plot_html': plot_html})
            
        except Exception as e:
            print(f"Error in compare_plot: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def reset_filters(request):
    if request.method == "POST":
        try:
            # Remove the filtered data from session
            if 'filtered_data' in request.session:
                del request.session['filtered_data']
            
            # Return original plots
            csv_json = request.session.get('csv_data')
            if not csv_json:
                return JsonResponse({'error': 'No data found in session'}, status=400)
            
            df = pd.read_json(io.StringIO(csv_json), orient='split')
            plots = {}
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    fig = px.histogram(df, x=col, title=f"Distribution of {col}")
                else:
                    counts = df[col].value_counts().reset_index()
                    counts.columns = [col, 'count']
                    fig = px.bar(counts, x=col, y='count', title=f"Distribution of {col}")
                plots[col] = fig.to_html(full_html=False)
            
            return JsonResponse({'plots': plots})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def upload_file(request):
    if request.method == 'POST':
        try:
            file = request.FILES['file']
            if file.name.endswith('.csv'):
                # Read the CSV file
                df = pd.read_csv(file)
                
                # Store the original data in session
                request.session['csv_data'] = df.to_json(orient='split')
                
                # Store column information
                request.session['columns'] = df.columns.tolist()
                
                # Generate initial plots
                plots = {}
                for col in df.columns:
                    if pd.api.types.is_numeric_dtype(df[col]):
                        fig = px.histogram(df, x=col, title=f"Distribution of {col}")
                    else:
                        value_counts = df[col].value_counts()
                        fig = px.bar(x=value_counts.index, 
                                   y=value_counts.values,
                                   title=f"Distribution of {col}")
                    plots[col] = fig.to_html(full_html=False)
                
                # Store the plots in session
                request.session['plots'] = plots
                
                return redirect('analysis')  # or your analysis page URL
            else:
                return JsonResponse({'error': 'Please upload a CSV file'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return render(request, 'upload.html')  # or your upload template

def analysis(request):  # or whatever your analysis view is named
    try:
        # Get data from session
        data_json = request.session.get('csv_data')
        if not data_json:
            return redirect('upload')  # or your upload page URL
        
        df = pd.read_json(io.StringIO(data_json), orient='split')
        
        # Generate plots
        plots = {}
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                fig = px.histogram(df, x=col, title=f"Distribution of {col}")
            else:
                value_counts = df[col].value_counts()
                fig = px.bar(x=value_counts.index, 
                           y=value_counts.values,
                           title=f"Distribution of {col}")
            plots[col] = fig.to_html(full_html=False)
        
        context = {
            'plots': plots,
            'overview': {
                'columns': df.columns.tolist()
            }
        }
        
        return render(request, 'stats/analysis.html', context)
        
    except Exception as e:
        print(f"Error in analysis view: {str(e)}")
        return redirect('upload')  # or handle error appropriately

@register.filter(is_safe=True)
def to_json(value):
    """Convert a value to JSON string"""
    return json.dumps(value, cls=DjangoJSONEncoder)


def generate_report(request):
    if request.method == 'POST':
        try:
            logger.debug("Starting generate_report function")
            
            # Get the current DataFrame from the session
            csv_data = request.session.get('csv_data')
            if not csv_data:
                logger.error("No CSV data found in session")
                return JsonResponse({
                    'error': 'No data available. Please upload a file first.'
                }, status=400)
            
            # Reconstruct DataFrame from session
            df = pd.read_json(io.StringIO(csv_data), orient='split')
            filename = request.session.get('filename', 'donations.csv')
            
            # Instead of using insights from the HTML, regenerate them
            # This ensures we have direct access to the Plotly figures
            insights = generate_donor_insights(df, include_figures=True)
            
            # Generate PDF report with direct figure access
            pdf_filename = generate_pdf_report(insights, filename,df)

            # Return the PDF file
            if os.path.exists(pdf_filename):
                pdf_file = open(pdf_filename, 'rb')
                response = FileResponse(
                    pdf_file, 
                    content_type='application/pdf',
                    as_attachment=True,
                    filename=os.path.basename(pdf_filename)
                )
                return response
            else:
                raise FileNotFoundError(f"PDF file not found at: {pdf_filename}")
                
        except Exception as e:
            logger.error(f"Error in report generation: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'error': f'Error generating PDF: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def analyze_file(request):
    if request.method == 'POST':
        try:
            file = request.FILES['file']
            
            # Read the file into a DataFrame
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file)
            else:
                return JsonResponse({'error': 'Unsupported file format'}, status=400)
            
            # Store DataFrame in session
            request.session['df_json'] = df.to_json()
            request.session['filename'] = file.name
            
            # Generate insights
            insights = generate_donor_insights(df)
            
            return JsonResponse({'insights': insights})
            
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return render(request, 'stats/upload.html')

    