# stats/views.py
import pandas as pd
import plotly.express as px
from django.shortcuts import render, redirect
from .forms import CsvUploadForm
from django.http import JsonResponse, FileResponse, HttpResponse
from django.template.loader import render_to_string
import io
import json
from .insight_generator import generate_donor_insights
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.template import Library
from django import template
import os
import logging
import traceback
import plotly.io as pio
import plotly.graph_objects as go
from PIL import Image
import numpy as np
import time
import threading
import queue
from pathlib import Path
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from .data_tracking import DataTracker, ComparisonTracker
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views import View
from .models import CustomForm, AnalysisReport  
from form_builder.cursor_db import get_form, get_form_fields
from django.core.paginator import Paginator




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
    type=""
    fig=None
    if pd.api.types.is_numeric_dtype(df[column]):
        type = "numeric"
        fig = px.histogram(df, x=column, nbins=50,title=f"المخطط التكراري للعمود {column}")
    elif pd.api.types.is_datetime64_any_dtype(df[column]):
        type = "datetime"
        date_counts = df[column].value_counts()
        fig = px.line(x=date_counts.index, y=date_counts.values, title=f"التوزيع الزمني للعمود {column}")
        fig.update_layout(xaxis_title=column, yaxis_title="Count")

    else:
        type = "categorical"
        value_counts = df[column].value_counts().head(10)
        if len(value_counts) <= 7:
            fig = px.pie(names=value_counts.index,values=value_counts.values,title=f"المخطط الدائري للعمود {column}")
        else:
            fig = px.bar(x=value_counts.index, 
                        y=value_counts.values,
                        title=f"المخطط العمودي لأكثر 10 قيم في {column}")
        fig.update_layout(xaxis_title=column, yaxis_title="Count")

    print(f"{column} is {type}")
    fig.update_layout(
        showlegend=True,
        template='plotly_white',
        margin=dict(l=40, r=40, t=40, b=40)
    )

    html = fig.to_html(full_html=False, include_plotlyjs='cdn')

    print(f"{column} is finished")

    return html,type

def generate_all_plots(df):
    """Generate plots for all columns."""
    return {col: generate_plot(df, col) for col in df.columns}

def get_html_plots_folder(filename):
    """
    Create and return a folder path for storing HTML plots
    
    Parameters:
    -----------
    filename : str
        Original CSV filename
    
    Returns:
    --------
    Path
        Path object to the plots folder
    """
    # Remove extension from filename and sanitize
    base_name = os.path.splitext(os.path.basename(filename))[0]
    sanitized_name = ''.join(c if c.isalnum() or c in ['-', '_'] else '_' for c in base_name)
    
    # Create folder name with date
    today = datetime.now().strftime("%Y%m%d")
    folder_name = f"{sanitized_name}_{today}"
    
    # Base directory for plots
    base_dir = Path('pdf_generator') / 'html_plots' / folder_name
    
    # Ensure directory exists
    os.makedirs(base_dir, exist_ok=True)
    logger.debug(f"Created HTML plots folder: {base_dir}")
    
    return base_dir

def save_html_plot(fig, column_name, plot_type='distribution', index=None, filename=None):
    """
    Save a plot as HTML file with data embedded in a consistent format
    
    Parameters:
    -----------
    fig : plotly.graph_objects.Figure
        Plotly figure to save
    column_name : str
        Name of the column being plotted
    plot_type : str, optional
        Type of plot (e.g., 'distribution', 'correlation')
    index : int, optional
        Index number for the plot
    filename : str, optional
        Original CSV filename
        
    Returns:
    --------
    str or None
        Path to the saved HTML file, or None if saving failed
    """
    try:
        # Create folder path
        plots_folder = get_html_plots_folder(filename)
        
        # Sanitize column name for filename
        safe_col_name = ''.join(c if c.isalnum() or c in ['-', '_'] else '_' for c in column_name)
        
        # Create filename with index if provided
        if index is not None:
            html_filename = f"{safe_col_name}_{plot_type}_{index}.html"
        else:
            html_filename = f"{safe_col_name}_{plot_type}.html"
            
        html_path = plots_folder / html_filename
        
        # Add a div with the raw data in JSON format (helps with extraction)
        plot_data = fig.to_json()
        
        # Create custom HTML with embedded data for easier extraction
        custom_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        </head>
        <body>
            <div id="plot-div" style="width: 800px; height: 500px;"></div>
            
            <!-- Data storage for PDF extraction -->
            <div id="plot-data" style="display:none;">
                {plot_data}
            </div>
            
            <script>
                var plotData = JSON.parse(document.getElementById('plot-data').textContent);
                Plotly.newPlot('plot-div', plotData.data, plotData.layout);
            </script>
        </body>
        </html>
        """
        
        # Write to file
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(custom_html)
            
        return str(html_path)
        
    except Exception as e:
        logger.error(f"Error saving HTML plot: {str(e)}")
        logger.error(traceback.format_exc())
        return None

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
                    
                

                # Set a flag to indicate that images need to be generated
                request.session['images_pending'] = True
               
                context = {
                    'form': form,
                    'columns': df.columns.tolist(),
                    'numeric_columns': [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])],
                    'categorical_columns': [col for col in df.columns if not pd.api.types.is_numeric_dtype(df[col])],
                }
                
                

                return render(request, 'stats/analysis.html', context)
                
            except Exception as e:
                form.add_error(None, f"Error processing file: {str(e)}")
                logger.error(f"Error processing file: {str(e)}")
                logger.error(traceback.format_exc())
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
            unique_values = df[column].astype(str).unique().tolist()[:100]
            
            return JsonResponse({'values': unique_values})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)


# def filter_plot(request):
#     if request.method == "GET":
#         try:
#             target = request.GET.get('target')
#             mode = request.GET.get('mode')
#             values = request.GET.getlist('values[]') or request.GET.getlist('values')
#             filter_column = request.GET.get('filter_column')
            
#             # Retrieve data from the session
#             data_json = request.session.get('csv_data')
#             if not data_json:
#                 return JsonResponse({'error': 'No data found in session'}, status=400)
            
#             df = pd.read_json(io.StringIO(data_json), orient='split')
            
#             if target not in df.columns:
#                 return JsonResponse({
#                     'error': f'Column "{target}" not found'
#                 }, status=400)
            
#             # Initialize DataFilter with your DataFrame
#             data_filter = DataFilter(df)
            
#             # Apply filters and track them
#             if mode == 'self' and values:
#                 data_filter.apply_filter(target, values)
#             elif mode == 'other' and filter_column and values:
#                 if filter_column not in df.columns:
#                     return JsonResponse({
#                         'error': f'Filter column "{filter_column}" not found'
#                     }, status=400)
#                 data_filter.apply_filter(filter_column, values)
            
#             # Get the filtered DataFrame
#             df_filtered = data_filter.get_filtered_data()
            
#             # Store the filtered data and applied filters in the session
#             request.session['filtered_data'] = df_filtered.to_json(orient='split')
#             request.session['applied_filters'] = data_filter.filter_tracker.get_filters()
            
#             # Generate plot
#             if pd.api.types.is_numeric_dtype(df[target]):
#                 fig = px.histogram(df_filtered, x=target, title=f"Distribution of {target}")
#             else:
#                 value_counts = df_filtered[target].value_counts()
#                 fig = px.bar(x=value_counts.index, y=value_counts.values, title=f"Distribution of {target}")
            
#             plot_html = fig.to_html(full_html=False)
#             return JsonResponse({'plot_html': plot_html})
        
#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=400)
    
#     return JsonResponse({'error': 'Invalid request method'}, status=400)

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
                
                # Store filename for later use
                request.session['filename'] = file.name
                
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
                
                # Set flag to generate HTML plots for PDF
                request.session['images_pending'] = True
                
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
        
        # Get filename for client-side plot saving
        filename = request.session.get('filename', 'data.csv')
        
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
            plots[col] = fig.to_html(full_html=False, include_plotlyjs='cdn')
        
        context = {
            'plots': plots,
            'overview': {
                'columns': df.columns.tolist()
            },
            'filename': filename  # Add filename to context for client-side saving
        }
        
        return render(request, 'stats/analysis.html', context)
        
    except Exception as e:
        print(f"Error in analysis view: {str(e)}")
        return redirect('upload')  # or handle error appropriately

@register.filter(is_safe=True)
def to_json(value):
    """Convert a value to JSON string"""
    return json.dumps(value, cls=DjangoJSONEncoder)


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
            
            # Store DataFrame in session in multiple formats to ensure compatibility
            request.session['df_json'] = df.to_json()
            request.session['filename'] = file.name
            
            # Also save as csv_data format used by other functions
            request.session['csv_data'] = df.to_json(orient='split')
            
            logger.info(f"DataFrame stored in session with keys: df_json, csv_data. Shape: {df.shape}")
            
            # Generate insights
            insights = generate_donor_insights(df)
            
            return JsonResponse({'insights': insights})
            
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return render(request, 'stats/upload.html')


def get_html_plots(filename):
    """
    Get all saved HTML plots for a file
    
    Parameters:
    -----------
    filename : str
        Original CSV filename
        
    Returns:
    --------
    list
        List of paths to HTML plots
    """
    try:
        plots_folder = get_html_plots_folder(filename)
        html_files = list(plots_folder.glob("*.html"))
        
        # Sort by modification time (newest first)
        html_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        return [str(p) for p in html_files]
        
    except Exception as e:
        logger.error(f"Error getting saved HTML plots: {str(e)}")
        return []

# Add a new endpoint to save client-side plots
@csrf_exempt
def save_client_plot(request):
    """
    Save a plot rendered on the client side for later use in PDF generation
    """
    if request.method == 'POST':
        try:
            # Get plot data from the request
            plot_html = request.POST.get('html')
            plot_id = request.POST.get('plot_id')
            plot_title = request.POST.get('title')
            filename = request.session.get('filename', 'data.csv')
            
            if not plot_html:
                return JsonResponse({'error': 'No plot HTML provided'}, status=400)
            
            # Create folder for HTML plots
            plots_folder = get_html_plots_folder(filename)
            
            # Create a filename for the plot
            if plot_id:
                safe_id = ''.join(c if c.isalnum() or c in ['-', '_'] else '_' for c in plot_id)
                html_filename = f"{safe_id}.html"
            else:
                # Generate a unique filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                html_filename = f"plot_{timestamp}.html"
            
            html_path = plots_folder / html_filename
            
            # Save the HTML
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(plot_html)
            
            logger.info(f"Saved client-side plot to {html_path}")
            
            return JsonResponse({
                'success': True,
                'path': str(html_path)
            })
            
        except Exception as e:
            logger.error(f"Error saving client-side plot: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def get_selected_plots(request):
    """Get plots for selected columns."""
    if request.method == "GET":
        time_now = datetime.now()
        print(f"get_selected_plots function called at {time_now}")
        try:
            columns = request.GET.getlist('columns[]')
            if not columns:
                return JsonResponse({'error': 'No columns specified'}, status=400)
            
            # Get data from session
            data_json = request.session.get('csv_data')
            if not data_json:
                return JsonResponse({'error': 'No data found in session'}, status=400)
            
            df = pd.read_json(io.StringIO(data_json), orient='split')
            
            # Generate plots for selected columns
            plots = {}
            stats = {}
           
            for col in columns:
                if col in df.columns:
                    logger.debug(f"Generating plot for column: {col}")
                    
                    
                    # Convert to JSON for client-side rendering
                    
                    html ,type =generate_plot(df,col)
                    
                    # Store both the JSON and HTML versions
                    plots[col] = {
                        'html': html,
                        'type': type
                    }
                    
                    # Generate statistics
                    if pd.api.types.is_numeric_dtype(df[col]):
                        stats[col] = {
                            'mean': float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                            'median': float(df[col].median()) if not pd.isna(df[col].median()) else None,
                            'std': float(df[col].std()) if not pd.isna(df[col].std()) else None,
                            'min': float(df[col].min()) if not pd.isna(df[col].min()) else None,
                            'max': float(df[col].max()) if not pd.isna(df[col].max()) else None,
                            'missing': int(df[col].isna().sum()),
                            'type': 'numeric'
                        }
                    else:
                        value_counts = df[col].value_counts().head(5).to_dict()
                        # Convert keys to strings for JSON serialization
                        value_counts = {str(k): int(v) for k, v in value_counts.items()}
                        
                        stats[col] = {
                            'unique': int(df[col].nunique()),
                            'top_values': value_counts,
                            'missing': int(df[col].isna().sum()),
                            'type': 'categorical'
                        }
            
            print(f"plots are sending")
            time_after = datetime.now()
            print(f"plots are finished at {time_after.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"time taken: {time_after - time_now}")
            return JsonResponse({
                'plots': plots,
                'stats': stats
            })
            
        except Exception as e:
            logger.error(f"Error generating plots: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def generate_plot_for_column(df, column):
    """Generate appropriate plot based on column data type"""
    try:
        if pd.api.types.is_numeric_dtype(df[column]):
            # For numeric columns, create a histogram
            fig = px.histogram(
                df, 
                x=column,
                title=f"Distribution of {column}",
                height=500
            )
        else:
            # For categorical columns, create a bar chart
            value_counts = df[column].value_counts().head(30)
            fig = px.bar(
                x=value_counts.index, 
                y=value_counts.values,
                title=f"Distribution of {column}",
                labels={'x': column, 'y': 'Count'},
                height=500
            )
            
        # Optimize layout
        fig.update_layout(
            margin=dict(l=40, r=40, t=60, b=40),
            xaxis_title=column,
            yaxis_title="Count",
            template="plotly_white"
        )
        
        # IMPORTANT: Make sure to set full_html=False and include_plotlyjs='cdn'
        # to ensure proper rendering when added to the page dynamically
        return fig
        
    except Exception as e:
        logger.error(f"Error generating plot for {column}: {str(e)}")
        # Return a simple error plot
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error generating plot for {column}: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig

def get_column_values(request):
    """Get unique values for a column to populate filter dropdowns"""
    try:
        column = request.GET.get('column')
        if not column:
            return JsonResponse({'error': 'No column specified'}, status=400)
            
        # Get the DataFrame from session
        data_sources = [
            ('df_json', lambda x: pd.read_json(x)),
            ('csv_data', lambda x: pd.read_json(io.StringIO(x), orient='split')),
            ('dataframe', lambda x: pd.read_json(x))
        ]
        
        df = None
        for key, loader in data_sources:
            data = request.session.get(key)
            if data:
                try:
                    df = loader(data)
                    break
                except Exception as e:
                    logger.warning(f"Could not load DataFrame from {key}: {str(e)}")
        
        if df is None:
            return JsonResponse({'error': 'No data available'}, status=400)
            
        if column not in df.columns:
            return JsonResponse({'error': f'Column {column} not found in data'}, status=400)
            
        # Get unique values, limited to 100 to prevent overwhelming the UI
        unique_values = df[column].dropna().unique().tolist()
        if len(unique_values) > 100:
            unique_values = unique_values[:100]
            
        # Convert non-string values to strings for JSON
        unique_values = [str(val) for val in unique_values]
            
        return JsonResponse({'values': unique_values})
        
    except Exception as e:
        logger.error(f"Error getting column values: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def get_column_types(request):
    """Get column types to determine appropriate plot options"""
    try:
        target_column = request.GET.get('target')
        compare_column = request.GET.get('compare_column')
        
        if not target_column or not compare_column:
            return JsonResponse({'error': 'Missing required parameters'}, status=400)
            
        # Get the DataFrame from session
        data_sources = [
            ('df_json', lambda x: pd.read_json(x)),
            ('csv_data', lambda x: pd.read_json(io.StringIO(x), orient='split')),
            ('dataframe', lambda x: pd.read_json(x))
        ]
        
        df = None
        for key, loader in data_sources:
            data = request.session.get(key)
            if data:
                try:
                    df = loader(data)
                    break
                except Exception as e:
                    logger.warning(f"Could not load DataFrame from {key}: {str(e)}")
        
        if df is None:
            return JsonResponse({'error': 'No data available'}, status=400)
            
        # Check if columns exist
        if target_column not in df.columns or compare_column not in df.columns:
            return JsonResponse({'error': 'One or more columns not found in data'}, status=400)
            
        # Determine column types
        target_type = 'numeric' if pd.api.types.is_numeric_dtype(df[target_column]) else 'categorical'
        compare_type = 'numeric' if pd.api.types.is_numeric_dtype(df[compare_column]) else 'categorical'
            
        return JsonResponse({
            'column_types': {
                'target': target_type,
                'compare': compare_type
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting column types: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def filter_plot(request):
    """Filter a plot by column values"""
    try:
        filter_mode = request.GET.get('mode') # mode 
        target_column = request.GET.get('target') #column 
        condition = request.GET.get('condition') # condition
        filter_values = request.GET.getlist('filter_values[]') # values
        filter_column = request.GET.get('filter_column') #filter_column
        
        print(f"filter_mode: {filter_mode}")
        print(f"target_column: {target_column}")
        print(f"condition: {condition}")
        print(f"filter_values: {filter_values}")
        print(f"filter_column: {filter_column}")
        
        if not target_column or not filter_mode:
            return JsonResponse({'error': 'Missing required parameters'}, status=400)
            
        # Get the DataFrame from session
        data_sources = [
            ('df_json', lambda x: pd.read_json(x)),
            ('csv_data', lambda x: pd.read_json(io.StringIO(x), orient='split')),
            ('dataframe', lambda x: pd.read_json(x))
        ]
        
        df = None
        for key, loader in data_sources:
            data = request.session.get(key)
            if data:
                try:
                    df = loader(data)
                    break
                except Exception as e:
                    logger.warning(f"Could not load DataFrame from {key}: {str(e)}")
        
        if df is None:
            return JsonResponse({'error': 'No data available'}, status=400)
            
        # Filter dataframe based on mode
        data_tracker = DataTracker(df)
        html, row_count = data_tracker.add_filter(filter_mode, target_column, condition, filter_values, filter_column)
        print(f"row_count: {row_count}")
        return JsonResponse({
            'html': html,
            'row_count': row_count
        })
        
    except Exception as e:
        logger.error(f"Error filtering plot: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def compare_columns(request):
    """Create a comparison plot between two columns"""
    try:
        # Get parameters with fallbacks
        target_column = request.GET.get('target')
        compare_column = request.GET.get('compare_column')
        plot_type = request.GET.get('plot_type', 'auto')  # Make plot_type optional

        # Validate required parameters
        if not target_column or not compare_column:
            return JsonResponse({'error': 'Missing target or comparison column'}, status=400)

        # Get the DataFrame from session
        df = None
        data_sources = [
            ('df_json', lambda x: pd.read_json(x)),
            ('csv_data', lambda x: pd.read_json(io.StringIO(x), orient='split')),
            ('dataframe', lambda x: pd.read_json(x))
        ]
        
        for key, loader in data_sources:
            if data := request.session.get(key):
                try:
                    df = loader(data)
                    break
                except Exception as e:
                    logger.warning(f"Could not load DataFrame from {key}: {str(e)}")

        if df is None or df.empty:
            return JsonResponse({'error': 'No valid data available'}, status=400)

        # Validate columns exist in DataFrame
        missing_cols = [col for col in [target_column, compare_column] 
                       if col and col not in df.columns]
        if missing_cols:
            return JsonResponse({'error': f"Columns not found: {', '.join(missing_cols)}"}, status=400)

        # Generate comparison plot
        comparison_tracker = ComparisonTracker(df)
        html = comparison_tracker.get_comparison_plot(
            col1=target_column,
            col2=compare_column,
            plot_type=plot_type if plot_type != 'auto' else None,
        )
        
        return JsonResponse({'plot_html': html})

    except Exception as e:
        logger.error(f"Comparison error: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({'error': 'Failed to generate comparison. Please check column types.'}, status=500)
def transform_column(request):
    """Apply transformations to a column and return updated plot"""
    try:
        target_column = request.GET.get('column')
        transform_type = request.GET.get('transform')
        
        if not target_column or not transform_type:
            return JsonResponse({'error': 'Missing required parameters'}, status=400)
        
        logger.info(f"Applying transformation {transform_type} to column {target_column}")
        
        # Get the DataFrame from session
        data_sources = [
            ('df_json', lambda x: pd.read_json(x)),
            ('csv_data', lambda x: pd.read_json(io.StringIO(x), orient='split')),
            ('dataframe', lambda x: pd.read_json(x))
        ]
        
        df = None
        for key, loader in data_sources:
            data = request.session.get(key)
            if data:
                try:
                    df = loader(data)
                    break
                except Exception as e:
                    logger.warning(f"Could not load DataFrame from {key}: {str(e)}")
        
        if df is None:
            return JsonResponse({'error': 'No data available'}, status=400)
            
        # Check if column exists
        if target_column not in df.columns:
            return JsonResponse({'error': f'Column {target_column} not found in data'}, status=400)
            
        # Check if column is numeric
        if not pd.api.types.is_numeric_dtype(df[target_column]):
            return JsonResponse({'error': f'Column {target_column} is not numeric and cannot be transformed'}, status=400)
        
        # Make a copy to avoid modifying the original
        df_copy = df.copy()
        
        # Apply transformation
        if transform_type == 'log':
            # Handle zero and negative values
            min_value = df_copy[target_column].min()
            if min_value <= 0:
                offset = abs(min_value) + 1
                df_copy[target_column] = np.log(df_copy[target_column] + offset)
                transform_name = f"Log({target_column} + {offset})"
            else:
                df_copy[target_column] = np.log(df_copy[target_column])
                transform_name = f"Log({target_column})"
                
        elif transform_type == 'sqrt':
            # Handle negative values
            min_value = df_copy[target_column].min()
            if min_value < 0:
                offset = abs(min_value)
                df_copy[target_column] = np.sqrt(df_copy[target_column] + offset)
                transform_name = f"Sqrt({target_column} + {offset})"
            else:
                df_copy[target_column] = np.sqrt(df_copy[target_column])
                transform_name = f"Sqrt({target_column})"
                
        elif transform_type == 'standardize':
            mean = df_copy[target_column].mean()
            std = df_copy[target_column].std()
            if std > 0:
                df_copy[target_column] = (df_copy[target_column] - mean) / std
                transform_name = f"Standardized {target_column}"
            else:
                return JsonResponse({'error': 'Standard deviation is zero, cannot standardize'}, status=400)
                
        elif transform_type == 'minmax':
            min_val = df_copy[target_column].min()
            max_val = df_copy[target_column].max()
            if max_val > min_val:
                df_copy[target_column] = (df_copy[target_column] - min_val) / (max_val - min_val)
                transform_name = f"Min-Max Scaled {target_column}"
            else:
                return JsonResponse({'error': 'Max and min values are equal, cannot scale'}, status=400)
                
        elif transform_type == 'bin':
            bins = int(request.GET.get('bins', 5))
            df_copy[target_column] = pd.cut(df_copy[target_column], bins=bins, labels=False)
            transform_name = f"{target_column} (Binned to {bins} groups)"
            
        else:
            return JsonResponse({'error': f'Unknown transformation: {transform_type}'}, status=400)
        
        # Generate plot with the transformed data
        fig = None
        
        # Check if it's categorical after transformation
        if pd.api.types.is_categorical_dtype(df_copy[target_column]) or df_copy[target_column].nunique() < 15:
            # Create a categorical plot
            value_counts = df_copy[target_column].value_counts().reset_index()
            value_counts.columns = [target_column, 'count']
            
            fig = px.bar(
                value_counts, 
                x=target_column, 
                y='count',
                title=f"Distribution of {transform_name}",
                labels={target_column: transform_name, 'count': 'Count'}
            )
        else:
            # Create numeric distribution
            fig = px.histogram(
                df_copy, 
                x=target_column,
                title=f"Distribution of {transform_name}",
                labels={target_column: transform_name},
                marginal="box"  # Add box plot on the marginal
            )
        
        # Add explanatory text
        transformation_text = {
            'log': 'Logarithmic transformation can help with right-skewed data and make multiplicative relationships more linear.',
            'sqrt': 'Square root transformation can reduce right skew and stabilize variance.',
            'standardize': 'Standardization (z-score) centers data around 0 with standard deviation of 1.',
            'minmax': 'Min-Max scaling normalizes data to range from 0 to 1.',
            'bin': 'Binning groups continuous data into discrete categories.'
        }
        
        fig.add_annotation(
            x=0, y=-0.15,
            xref="paper", yref="paper",
            text=transformation_text.get(transform_type, ''),
            showarrow=False,
            font=dict(size=10, color="gray"),
            align="left"
        )
        
        # Generate plot HTML
        plot_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        
        # Calculate basic stats for the transformed column
        stats = {
            'mean': float(df_copy[target_column].mean()) if not pd.api.types.is_categorical_dtype(df_copy[target_column]) else None,
            'median': float(df_copy[target_column].median()) if not pd.api.types.is_categorical_dtype(df_copy[target_column]) else None,
            'std': float(df_copy[target_column].std()) if not pd.api.types.is_categorical_dtype(df_copy[target_column]) else None,
            'min': float(df_copy[target_column].min()) if not pd.api.types.is_categorical_dtype(df_copy[target_column]) else None,
            'max': float(df_copy[target_column].max()) if not pd.api.types.is_categorical_dtype(df_copy[target_column]) else None,
            'missing_count': int(df_copy[target_column].isna().sum()),
            'missing_percent': float(df_copy[target_column].isna().mean() * 100)
        }
        
        return JsonResponse({
            'plot_html': plot_html,
            'transform_name': transform_name,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error applying transformation: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)

def export_column_data(request):
    """Export column data as CSV"""
    try:
        column = request.GET.get('column')
        
        if not column:
            return JsonResponse({'error': 'No column specified'}, status=400)
        
        # Get the DataFrame from session
        data_sources = [
            ('df_json', lambda x: pd.read_json(x)),
            ('csv_data', lambda x: pd.read_json(io.StringIO(x), orient='split')),
            ('dataframe', lambda x: pd.read_json(x))
        ]
        
        df = None
        for key, loader in data_sources:
            data = request.session.get(key)
            if data:
                try:
                    df = loader(data)
                    break
                except Exception as e:
                    logger.warning(f"Could not load DataFrame from {key}: {str(e)}")
        
        if df is None:
            return JsonResponse({'error': 'No data available'}, status=400)
            
        if column not in df.columns:
            return JsonResponse({'error': f'Column {column} not found in data'}, status=400)
            
        # Extract the column and generate CSV
        df_export = df[[column]].copy()
        
        # Convert to CSV
        csv_buffer = io.StringIO()
        df_export.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        return JsonResponse({'csv_data': csv_data})
        
    except Exception as e:
        logger.error(f"Error exporting column data: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def get_correlation_matrix(request):
    """Generate a correlation matrix plot"""
    try:
        # Get the DataFrame from session
        data_sources = [
            ('df_json', lambda x: pd.read_json(x)),
            ('csv_data', lambda x: pd.read_json(io.StringIO(x), orient='split')),
            ('dataframe', lambda x: pd.read_json(x))
        ]
        
        df = None
        for key, loader in data_sources:
            data = request.session.get(key)
            if data:
                try:
                    df = loader(data)
                    break
                except Exception as e:
                    logger.warning(f"Could not load DataFrame from {key}: {str(e)}")
        
        if df is None:
            return JsonResponse({'error': 'No data available'}, status=400)
            
        # Select only numeric columns
        numeric_df = df.select_dtypes(include=['number'])
        
        if numeric_df.shape[1] < 2:
            return JsonResponse({'error': 'Need at least 2 numeric columns to create correlation matrix'}, status=400)
            
        # Compute correlation matrix
        corr_matrix = numeric_df.corr()
        
        # Create heatmap
        fig = px.imshow(
            corr_matrix,
            text_auto='.2f',
            color_continuous_scale=px.colors.diverging.RdBu_r,
            title="Correlation Matrix of Numeric Variables"
        )
        
        # Improve layout
        fig.update_layout(
            height=600,
            width=800,
            margin=dict(l=40, r=40, t=60, b=40),
        )
        
        # Generate plot HTML
        plot_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        
        # Get column pairs with high correlation
        high_corr_pairs = []
        for i, col1 in enumerate(corr_matrix.columns):
            for j, col2 in enumerate(corr_matrix.columns):
                if i < j:  # Only look at upper triangle
                    corr_value = corr_matrix.iloc[i, j]
                    if abs(corr_value) > 0.7:  # High correlation threshold
                        high_corr_pairs.append({
                            'col1': col1,
                            'col2': col2,
                            'corr': float(corr_value),
                            'type': 'positive' if corr_value > 0 else 'negative'
                        })
        
        return JsonResponse({
            'plot_html': plot_html,
            'high_correlations': high_corr_pairs
        })
        
    except Exception as e:
        logger.error(f"Error generating correlation matrix: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)



def clear_chat(request):
    """Clear the conversation history"""
    if request.method == 'POST':
        if 'conversation_history' in request.session:
            del request.session['conversation_history']
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({
        'status': 'error',
        'message': 'Only POST requests are allowed'
    }, status=405)

def get_column_type(request):
    """Get the type of a column"""
    column = request.GET.get('column')
    if not column:
        return JsonResponse({'error': 'No column specified'}, status=400)
    
    # Get the DataFrame from session
    data_sources = [
        ('df_json', lambda x: pd.read_json(x)),
        ('csv_data', lambda x: pd.read_json(io.StringIO(x), orient='split')),
        ('dataframe', lambda x: pd.read_json(x))
    ]

    df = None
    for key, loader in data_sources:
        data = request.session.get(key)
        if data:
            try:
                df = loader(data)
                break
            except Exception as e:
                logger.warning(f"Could not load DataFrame from {key}: {str(e)}")

    if df is None:
        return JsonResponse({'error': 'No data available'}, status=400)
    
    # Get the type of the column
    dtype = df[column].dtype

    # Map dtype to a more user-friendly type
    if pd.api.types.is_numeric_dtype(dtype):
            return JsonResponse({'type': 'numeric'})
    elif pd.api.types.is_datetime64_any_dtype(dtype):
            return JsonResponse({'type': 'datetime'})
    else:
            return JsonResponse({'type': 'categorical'})


# Example Django view
def get_column_types_compare(request):
    target_col = request.GET.get('target')
    compare_col = request.GET.get('compare_column')

    # Get the DataFrame from session
    data_sources = [
        ('df_json', lambda x: pd.read_json(x)),
        ('csv_data', lambda x: pd.read_json(io.StringIO(x), orient='split')),
        ('dataframe', lambda x: pd.read_json(x))
    ]

    df = None
    for key, loader in data_sources:
        data = request.session.get(key)
        if data:
            try:
                df = loader(data)
                break
            except Exception as e:
                logger.warning(f"Could not load DataFrame from {key}: {str(e)}")
    
    # Get column types using ComparisonTracker
    tracker = ComparisonTracker(df)
    col1_type = tracker.get_column_type(target_col)
    col2_type = tracker.get_column_type(compare_col)
    
    # Define allowed plot types
    plot_types = []
    if col1_type == 'numerical' and col2_type == 'numerical':
        plot_types = [
            {'value': 'scatter', 'label': 'Scatter Plot'},
            {'value': 'heatmap', 'label': 'Heatmap'},
            {'value': 'hexbin', 'label': 'Hexbin Plot'}
        ]
    elif (col1_type == 'numerical' and col2_type == 'categorical') or \
         (col1_type == 'categorical' and col2_type == 'numerical'):
        plot_types = [
            {'value': 'box', 'label': 'Box Plot'},
            {'value': 'violin', 'label': 'Violin Plot'},
            {'value': 'bar', 'label': 'Bar Chart'}
        ]
    elif col1_type == 'categorical' and col2_type == 'categorical':
        plot_types = [
            {'value': 'heatmap', 'label': 'Heatmap'},
            {'value': 'stacked_bar', 'label': 'Stacked Bar Chart'}
        ]
    elif 'datetime' in [col1_type, col2_type]:
        plot_types = [
            {'value': 'line', 'label': 'Time Series'},
            {'value': 'area', 'label': 'Area Chart'}
        ]
    
    return JsonResponse({
        'column_types': {'target': col1_type, 'compare': col2_type},
        'allowed_plots': plot_types
    })



@method_decorator(ensure_csrf_cookie, name='dispatch')
class AnalysisView(View):
    def get(self, request):
        # Get all available forms for analysis
        forms = CustomForm.objects.all()
        
        # Add record count to each form
        for form in forms:
            try:
                form_data = get_form(form.name)
                form.record_count = len(form_data)
            except:
                form.record_count = 0
        
        
        
        # Handle pagination
        paginator = Paginator(forms, 10)  # Show 10 forms per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        form = CsvUploadForm()
        context = {
            'forms': forms,
            'page_obj': page_obj,
            
        }
        return render(request, 'stats/dashboard.html', context)
    

    def post(self, request):
        try:
            # Check if it's a file upload or form data analysis
            if request.FILES.get('file'):
                return self._handle_file_upload(request)
            else:
                return self._handle_form_analysis(request)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    def _handle_file_upload(self, request):
        file = request.FILES['file']
        file_name = file.name
        
        # Check file extension
        if file_name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file_name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Unsupported file format. Please upload CSV or Excel file.'
            })
        
        # Generate basic analysis
        analysis_results = self._analyze_dataframe(df)
            
        return JsonResponse({
            'success': True,
            'analysis': analysis_results
        })
    
    def _handle_form_analysis(self, request):
        data = json.loads(request.body)
        form_id = data.get('form_id')
        
        if not form_id:
            return JsonResponse({
                'success': False,
                'error': 'Form ID is required'
            })
        
        try:
            form = CustomForm.objects.get(id=form_id)
            form_name = form.name
            form_data = get_form(form_name)
            form_fields = get_form_fields(form_name)
            
            # Convert form data to DataFrame
            records = []
            for record in form_data:
                record_dict = {
                    'id': record[0],
                    'created_at': record[1],
                }
                # Add the dynamic field values
                for i, field in enumerate(form_fields, start=2):
                    if i < len(record):
                        record_dict[field] = record[i]
                records.append(record_dict)
            
            df = pd.DataFrame(records)
            
            # Generate analysis
            analysis_results = self._analyze_dataframe(df)
            
            return JsonResponse({
                'success': True,
                'analysis': analysis_results
            })
            
        except CustomForm.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Form not found'
            })
    
    def _analyze_dataframe(self, df):
        """Generate basic statistical analysis from DataFrame"""
        analysis = {
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': list(df.columns),
            'summary': {},
            'correlations': {}
        }
        
        # Add summary statistics for numeric columns
        for column in df.columns:
            # Skip ID and date columns
            if column.lower() in ['id', 'created_at']:
                continue
                
            # Check if column is numeric
            if pd.api.types.is_numeric_dtype(df[column]):
                analysis['summary'][column] = {
                    'mean': float(df[column].mean()) if not pd.isna(df[column].mean()) else 0,
                    'median': float(df[column].median()) if not pd.isna(df[column].median()) else 0,
                    'min': float(df[column].min()) if not pd.isna(df[column].min()) else 0,
                    'max': float(df[column].max()) if not pd.isna(df[column].max()) else 0,
                    'std': float(df[column].std()) if not pd.isna(df[column].std()) else 0
                }
            else:
                # For categorical columns, count unique values
                value_counts = df[column].value_counts().to_dict()
                # Convert any non-serializable keys to strings
                clean_counts = {str(k): int(v) for k, v in value_counts.items()}
                analysis['summary'][column] = {
                    'unique_values': len(clean_counts),
                    'top_values': clean_counts
                }
        
        # Calculate correlations between numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr().to_dict()
            # Clean up correlation matrix for JSON serialization
            for col1, values in corr_matrix.items():
                analysis['correlations'][col1] = {str(col2): float(val) for col2, val in values.items()}
        
        return analysis
    

class SaveAnalysisView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            report_name = data.get('report_name')
            analysis_data = data.get('analysis_data')
            form_id = data.get('form_id')
            source_type = data.get('source_type', 'form')
            source_name = data.get('source_name', '')
            
            if not report_name:
                return JsonResponse({
                    'success': False,
                    'error': 'Report name is required'
                })
                
            # Create report
            report = AnalysisReport()
            report.name = report_name
            report.source_type = source_type
            report.source_name = source_name
            report.analysis_data = json.dumps(analysis_data)
            
            if form_id and source_type == 'form':
                try:
                    form = CustomForm.objects.get(id=form_id)
                    report.form = form
                    report.source_name = form.name
                except CustomForm.DoesNotExist:
                    pass
                
            report.save()
            
            return JsonResponse({
                'success': True,
                'report_id': report.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
        
class DeleteAnalysisView(View):
    def post(self, request, pk):
        try:
            report = AnalysisReport.objects.get(id=pk)
            report.delete()
            return JsonResponse({
                'success': True
            })
        except AnalysisReport.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Report not found'
            })


def analyze_form_view(request):
    if request.method == "POST":
        form_id = request.POST.get("form_id")
        if not form_id:
            return redirect("analysis")  # fallback

        try:
            form = CustomForm.objects.get(id=form_id)
            form_name = form.name
            form_data = get_form(form_name)
            form_fields = get_form_fields(form_name)

            # Convert to DataFrame
            records = []
            for record in form_data:
                record_dict = {}
                for i, field in enumerate(form_fields, start=2):
                    if i < len(record):
                        record_dict[field] = record[i]
                records.append(record_dict)

            df = pd.DataFrame(records)

            # Store in session like in analyze_csv
            request.session['csv_data'] = df.to_json(orient='split')
            request.session['filename'] = form_name
            request.session['images_pending'] = True
            request.session.modified = True

            context = {
                'form': CsvUploadForm(),
                'columns': df.columns.tolist(),
                'numeric_columns': [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])],
                'categorical_columns': [col for col in df.columns if not pd.api.types.is_numeric_dtype(df[col])],
            }

            return render(request, 'stats/analysis.html', context)

        except CustomForm.DoesNotExist:
            return redirect("analysis")
    else:
        return redirect("analysis")
