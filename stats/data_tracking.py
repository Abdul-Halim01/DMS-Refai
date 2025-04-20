import pandas as pd
import json
from django.http import JsonResponse
import plotly.express as px
from pandas.api.types import is_numeric_dtype, is_datetime64_any_dtype
class DataTracker:
    def __init__(self, df):
        self.original_df = df.copy()
        self.current_df = df.copy()
        self.columns = df.columns.tolist()
        self.filters = {}
        self.comparisons = {}   

    def get_type_column(self, column):
        if column in self.original_df.select_dtypes(include=['number']).columns:
            return 'numerical'
        elif column in self.original_df.select_dtypes(include=['datetime']).columns:
            return 'datetime'
        else:
            return 'categorical'

    def add_filter(self, mode, column, condition, values, filter_column=None):
        if column not in self.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")
        
        get_column_type = self.get_type_column(column)
        df = self.current_df

        if get_column_type == 'numerical':
            controller = NumericalController(df)
        elif get_column_type == 'categorical':
            controller = CategoricalController(df)
        elif get_column_type == 'datetime':
            controller = DateTimeController(df)

        if mode == 'self':
            dict_filter , html, row_count = controller.filter_by_value(column, mode, condition, values)
        elif mode == 'other':
            df_sec = self.current_df[[filter_column]]  # Changed to DataFrame
            filter_column_type = self.get_type_column(filter_column)
            dict_filter, html, row_count = controller.filter_by_other(column, filter_column, mode, condition, values,df_sec, filter_column_type)


        if row_count == 0:
            html = """
            <div style='
                text-align:center; 
                padding:30px; 
                font-size:18px; 
                color:#444; 
                border:1px dashed #ccc; 
                border-radius:10px;
                background-color:#f9f9f9;
                max-width:600px;
                margin:30px auto;
            '>
                <strong>لا يوجد بيانات مطابقة لمعايير الفلتر الخاصة بك.</strong><br><br>
                يرجى التحقق من التالي:
                <ul style='text-align:left; max-width:400px; margin:10px auto; font-size:16px;'>
                    <li>1-التحقق من قيم الفلتر (مثل المدى الأدنى/الأقصى أو الفئة المحددة).</li>
                    <li>2-التأكد من أن العمود الذي فلترته يحتوي على قيم متوقعة.</li>
                </ul>
            </div>
            """
        self.filters[column] = dict_filter
        return html, row_count
    
    def add_comparison(self, column1, column2, plot_type=None):
        """Add comparison plot to tracking"""
        if column1 not in self.columns or column2 not in self.columns:
            raise ValueError("One or both columns not found in DataFrame")
            
        # Generate comparison plot
        comparison = ComparisonTracker(self.current_df)
        html = comparison.get_comparison_plot(column1, column2, plot_type)
        
        # Store comparison and return HTML
        key = (column1, column2)
        dict_comparison = {
            'mode': 'comparison',
            'column1': column1,
            'column2': column2,
            'plot_type': plot_type
        }
        self.comparisons[key] = dict_comparison
        return html
        
        
        

class NumericalController:        
    def __init__(self, df):
        self.df = df

    def filter_by_value(self, column, mode, condition, values):
        if column not in self.df.columns:
            available_columns = self.df.columns.tolist()
            raise ValueError(f"العمود '{column}' غير موجود في DataFrame. الأعمدة المتاحة: {available_columns}")


        col_dtype = self.df[column].dtype

        try:
            if condition == '=':
                mask = self.df[column].isin([col_dtype.type(v) for v in values])
            elif condition == '!=':
                mask = ~self.df[column].isin([col_dtype.type(v) for v in values])
            elif condition == '>':
                mask = self.df[column] > col_dtype.type(values[0])
            elif condition == '<':
                mask = self.df[column] < col_dtype.type(values[0])
            elif condition == '>=':
                mask = self.df[column] >= col_dtype.type(values[0])
            elif condition == '<=':
                mask = self.df[column] <= col_dtype.type(values[0])
            elif condition == 'between':
                if not isinstance(values, (list, tuple)) or len(values) != 2:
                    raise ValueError("للفلتر 'between'، يجب أن تكون القيم قائمة أو توربل من عنصرين.")
                mask = self.df[column].between(col_dtype.type(values[0]), col_dtype.type(values[1]))
            else:
                raise ValueError(f"الشرط غير صالح: {condition}")
        except Exception as e:
            raise ValueError(f"خطأ أثناء تطبيق الشرط '{condition}' مع القيم {values}: {e}")


        filtered_df = self.df[mask]

        dict_filter = {
            'mode': mode,
            'column': column,
            'condition': condition,
            'values': values
        }

        fig = px.histogram(filtered_df, x=column, title=f"المخطط التكراري للعمود {column}", nbins=50)
        fig.update_layout(xaxis_title=column, yaxis_title="Count")
        fig.update_layout(
            showlegend=True,
            template='plotly_white',
            margin=dict(l=40, r=40, t=40, b=40)
        )

        html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        row_count = len(filtered_df)

        return dict_filter, html, row_count
    
    def filter_by_other(self, column,filter_column, mode, condition, values,df_sec, filter_column_type):

        if filter_column_type == 'numerical':
            mask = NumericalController.get_mask(df_sec,filter_column, condition, values)
        elif filter_column_type == 'categorical':
            mask = CategoricalController.get_mask(df_sec, filter_column, condition, values)
        elif filter_column_type == 'datetime':
            mask = DateTimeController.get_mask(df_sec, filter_column, condition, values)

        filtered_df = self.df[mask]

        dict_filter = {
            'mode': mode,
            'column': column,
            'filter_column': filter_column,
            'condition': condition,
            'values': values
        }

        fig = px.histogram(filtered_df, x=column, title=f"المخطط التكراري للعمود {column} بعمود مراد تصفيته {filter_column}", nbins=50)
        fig.update_layout(xaxis_title=column, yaxis_title="Count")
        fig.update_layout(
            showlegend=True,
            template='plotly_white',
            margin=dict(l=40, r=40, t=40, b=40)
        )

        html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        row_count = len(filtered_df)

        return dict_filter, html, row_count

    @staticmethod 
    def get_mask(df, column, condition, values):
        col_dtype = df[column].dtype
        if condition == '=':
            mask =df[column].isin([col_dtype.type(v) for v in values])
        elif condition == '!=':
            mask = ~df[column].isin([col_dtype.type(v) for v in values])
        elif condition == '>':
            mask = df[column] > col_dtype.type(values[0])
        elif condition == '<':
            mask = df[column] < col_dtype.type(values[0])
        elif condition == '>=':
            mask = df[column] >= col_dtype.type(values[0])
        elif condition == '<=':
            mask = df[column] <= col_dtype.type(values[0])
        elif condition == 'between':
            mask = df[column].between(col_dtype.type(values[0]), col_dtype.type(values[1]))
        else:
            raise ValueError(f"Invalid condition: {condition}")
        
        return mask



class CategoricalController:
    def __init__(self, df):
        self.df = df
    def filter_by_value(self,column,mode,condition,values):
        if column not in self.df.columns:
            available_columns = self.df.columns.tolist()
            raise ValueError(f"العمود '{column}' غير موجود في DataFrame. الأعمدة المتاحة: {available_columns}")

        if condition == '=':
            mask = self.df[column].isin(values)
        elif condition == '!=':
            mask = ~self.df[column].isin(values)

        filtered_df = self.df[mask]
        filtered_df = filtered_df.dropna(subset=[column])
        value_counts = filtered_df[column].value_counts().head(10)

        dict_filter = {
            'mode': mode,
            'column': column,
            'condition': condition,
            'values': values
        }

        if len(value_counts) <= 7:
            fig = px.pie(names=value_counts.index, values=value_counts.values, title=f"المخطط الدائري للعمود {column}")
            fig.update_traces(textinfo='percent+label', pull=[0.1] * len(value_counts))  # Exploding slices slightly
        else:
            fig = px.bar(x=value_counts.index, 
                        y=value_counts.values,
                        title=f"المخطط العمودي لأكثر 10 قيم في {column}")
            fig.update_traces(
                marker=dict(color='rgb(158,202,225)', line=dict(color='rgb(8,48,107)', width=1.5)),  # Custom color
                text=value_counts.values,  # Add text on bars (value counts)
                textposition='outside'  # Position the text outside the bars
            )

        fig.update_layout(
            title=f"التوزيع الدائري للعمود {column}",
            title_x=0.5,  # Center title
            title_font=dict(size=20),
            xaxis_title=column,
            yaxis_title="Count",
            xaxis_title_font=dict(size=15),
            yaxis_title_font=dict(size=15),
            font=dict(size=12),  # Adjust font size for axis labels and tick labels
            margin=dict(l=50, r=50, t=50, b=50),  # Add margins for better spacing
            plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
            showlegend=False  # Hide legend if not needed
        )


        html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        row_count = len(filtered_df)

        return dict_filter, html, row_count
    

    @staticmethod
    def get_mask(df, column, condition, values):
        if condition == '=':
            mask = df[column].isin(values)
        elif condition == '!=':
            mask = ~df[column].isin(values)
        return mask

    def filter_by_other(self, column, filter_column, mode, condition, values, df_sec, filter_column_type):
        
        if filter_column_type == 'numerical':
            mask = NumericalController.get_mask(df_sec, filter_column, condition, values)
        elif filter_column_type == 'categorical':
            mask = CategoricalController.get_mask(df_sec, filter_column, condition, values)
        elif filter_column_type == 'datetime':
            mask = DateTimeController.get_mask(df_sec,filter_column, condition, values)

        filtered_df = self.df[mask]
        
        dict_filter = {
            'mode': mode,
            'column': column,
            'filter_column': filter_column,
            'condition': condition,
            'values': values
        }

        value_counts = filtered_df[column].value_counts().head(10)
        if len(value_counts) <= 7:
            fig = px.pie(names=value_counts.index,values=value_counts.values,title=f"المخطط الدائري للعمود {column} بعمود مراد تصفيته {filter_column}")
        else:
            fig = px.bar(x=value_counts.index, 
                        y=value_counts.values,
                        title=f"المخطط العمودي لأكثر 10 قيم في {column} بعمود مراد تصفيته {filter_column}")
        fig.update_layout(xaxis_title=column, yaxis_title="Count")
        fig.update_layout(
            showlegend=True,
            template='plotly_white',
            margin=dict(l=40, r=40, t=40, b=40)
        )

        html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        row_count = len(filtered_df)

        return dict_filter, html, row_count


class DateTimeController:
    def __init__(self, df):
        self.df = df
    def filter_by_value(self,column,mode,condition,values):
        if condition == '=':
            mask = self.df.isin(values)
        elif condition == '!=':
            mask = ~self.df.isin(values)
        elif condition == '>':
            mask = self.df > values
        elif condition == '<':
            mask = self.df < values
        elif condition == '>=':
            mask = self.df >= values
        elif condition == '<=':
            mask = self.df <= values
        elif condition == 'between':
            mask = self.df.between(values[0], values[1])
        else:
            raise ValueError(f"Invalid condition: {condition}")

        filtered_df = self.df[mask]

        dict_filter = {
            'mode': mode,
            'column': column,
            'condition': condition,
            'values': values
        }


        date_counts = filtered_df.value_counts()
        fig = px.line(x=date_counts.index, y=date_counts.values, title=f"المخطط الزمني للعمود {column}")
        fig.update_layout(xaxis_title=column, yaxis_title="Count")
        fig.update_layout(
            showlegend=True,
            template='plotly_white',
            margin=dict(l=40, r=40, t=40, b=40)
        )

        html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        row_count = len(filtered_df)

        return dict_filter, html, row_count


    @staticmethod
    def get_mask(df, condition, values):
        if condition == '=':
            mask = df.isin(values)
        elif condition == '!=':
            mask = ~df.isin(values)
        elif condition == '>':
            mask = df > values
        elif condition == '<':
            mask = df < values
        elif condition == '>=':
            mask = df >= values
        elif condition == '<=':
            mask = df <= values
        elif condition == 'between':
            mask = df.between(values[0], values[1])
        else:
            raise ValueError(f"Invalid condition: {condition}")
        
        return mask
    

    def filter_by_other(self, column, filter_column, mode, condition, values,df_sec, filter_column_type):

        if filter_column_type == 'numerical':
            mask = NumericalController.get_mask(df_sec, condition, values)
        elif filter_column_type == 'categorical':
            mask = CategoricalController.get_mask(df_sec, condition, values)
        elif filter_column_type == 'datetime':
            mask = DateTimeController.get_mask(df_sec, condition, values)

        filtered_df = self.df[mask]
        
        dict_filter = {
            'mode': mode,
            'column': column,
            'filter_column': filter_column,
            'condition': condition,
            'values': values
        }

        fig = px.line(x=filtered_df.value_counts().index, y=filtered_df.value_counts().values, title=f"المخطط الزمني للعمود {column} بعمود مراد تصفيته {filter_column}")
        fig.update_layout(xaxis_title=column, yaxis_title="Count")
        fig.update_layout(
            showlegend=True,
            template='plotly_white',
            margin=dict(l=40, r=40, t=40, b=40)
        )

        html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        row_count = len(filtered_df)

        return dict_filter, html, row_count


class ComparisonTracker:
    def __init__(self, df, max_samples=100000, max_categories=50):
        """
        Initialize the ComparisonTracker with performance safeguards
        
        Parameters:
        - df: DataFrame to analyze
        - max_samples: Maximum number of rows to use for visualization
        - max_categories: Maximum number of categories to display in categorical plots
        """
        self.original_df = df
        self.max_samples = max_samples
        self.max_categories = max_categories
        # Create a sampling strategy based on dataset size
        self.df = self._create_safe_sample(df)
        self.color_theme = px.colors.qualitative.Plotly  # Custom color theme
        
    def _create_safe_sample(self, df):
        """Create a performance-safe sample of the dataframe"""
        if len(df) > self.max_samples:
            # Use stratified sampling if possible, otherwise random sampling
            sample_fraction = self.max_samples / len(df)
            return df.sample(frac=sample_fraction, random_state=42)
        return df.copy()
        
    def get_column_type(self, column):
        if is_numeric_dtype(self.df[column]):
            return 'numerical'
        elif is_datetime64_any_dtype(self.df[column]):
            return 'datetime'
        else:
            return 'categorical'
    
    def _get_top_n_categories(self, column, n=None):
        """Get the top N categories by frequency"""
        if n is None:
            n = self.max_categories
            
        # Get value counts and limit to top n
        value_counts = self.df[column].value_counts()
        top_n = value_counts.nlargest(n).index.tolist()
        
        return top_n
        
    def get_comparison_plot(self, col1, col2, plot_type=None):
        col1_type = self.get_column_type(col1)
        col2_type = self.get_column_type(col2)
        
        # Check for high cardinality issues before proceeding
        self._check_cardinality_warning(col1, col2)
        
        # Numerical vs Numerical
        if col1_type == 'numerical' and col2_type == 'numerical':
            return self._numerical_vs_numerical(col1, col2, plot_type)
            
        # Numerical vs Categorical
        elif (col1_type == 'numerical' and col2_type == 'categorical'):
            return self._numerical_vs_categorical(numerical_col=col1, categorical_col=col2, plot_type=plot_type)
            
        # Categorical vs Numerical (redirects to the same handler but with reversed roles)
        elif (col1_type == 'categorical' and col2_type == 'numerical'):
            return self._numerical_vs_categorical(numerical_col=col2, categorical_col=col1, plot_type=plot_type)
            
        # Categorical vs Categorical
        elif col1_type == 'categorical' and col2_type == 'categorical':
            return self._categorical_vs_categorical(col1, col2, plot_type)
            
        # Datetime vs Any
        elif col1_type == 'datetime' or col2_type == 'datetime':
            return self._datetime_comparison(col1, col2, plot_type)
            
        else:
            raise ValueError(f"Unsupported comparison: {col1_type} vs {col2_type}")
            
    def _check_cardinality_warning(self, col1, col2):
        """Check for potential memory issues with categorical comparisons"""
        col1_cardinality = self.df[col1].nunique() if self.get_column_type(col1) == 'categorical' else 0
        col2_cardinality = self.df[col2].nunique() if self.get_column_type(col2) == 'categorical' else 0
        
        # Log warning if potentially problematic
        if col1_cardinality * col2_cardinality > 10000:  
            import logging
            logging.warning(f"المقارنة بين عمودين ذوي عدد كبير من التصنيفات: {col1} ({col1_cardinality} تصنيف) vs {col2} ({col2_cardinality} تصنيف)")

    # --- Enhanced Plot Methods with Performance Optimizations ---
    def _numerical_vs_numerical(self, col1, col2, plot_type):
        # For extremely large datasets, use datashader or hexbin instead of scatter
        if len(self.df) > 10000 and (plot_type == 'scatter' or not plot_type):
            plot_type = 'hexbin'
            
        if plot_type == 'scatter':
            fig = px.scatter(
                self.df, x=col1, y=col2,
                title=f"{col1} vs {col2}: Scatter Plot Showing Correlation",
                color_discrete_sequence=[self.color_theme[0]]
            )
            fig.update_traces(
                hovertemplate=f"<b>{col1}</b>: %{{x}}<br><b>{col2}</b>: %{{y}}<extra></extra>"
            )
        elif plot_type == 'hexbin':
            # Memory-efficient alternative to scatter for large datasets
            fig = px.density_heatmap(
                self.df, x=col1, y=col2,
                title=f"{col1} vs {col2}: Hex Density Plot",
                color_continuous_scale=self.color_theme,
                nbinsx=50, nbinsy=50  # Limit bin count for performance
            )
            fig.update_traces(
                hovertemplate=f"<b>{col1}</b>: %{{x}}<br><b>{col2}</b>: %{{y}}<br>Count: %{{z}}<extra></extra>"
            )
        elif plot_type == 'heatmap':
            # Set reasonable bin limits for performance
            fig = px.density_heatmap(
                self.df, x=col1, y=col2,
                title=f"Density Distribution: {col1} vs {col2}",
                color_continuous_scale=self.color_theme,
                nbinsx=40, nbinsy=40  # Limit bin count for performance
            )
            fig.update_traces(
                hovertemplate=f"<b>{col1}</b>: %{{x}}<br><b>{col2}</b>: %{{y}}<br>Density: %{{z}}<extra></extra>"
            )

        fig.update_layout(
            xaxis_title=col1,
            yaxis_title=col2,
            template="plotly_white",
            margin=dict(l=40, r=40, t=60, b=40),
            font=dict(family="Arial", size=12),
            title_font=dict(size=16, color="#2c3e50")
        )
        return fig.to_html(full_html=False, include_plotlyjs='cdn')

    def _numerical_vs_categorical(self, numerical_col, categorical_col, plot_type):
        """
        Enhanced method to handle numerical vs categorical comparisons
        with optimizations for large datasets
        """
        # Get top N categories for large categorical columns
        unique_cats = self.df[categorical_col].nunique()
        if unique_cats > self.max_categories:
            top_cats = self._get_top_n_categories(categorical_col)
            filtered_df = self.df[self.df[categorical_col].isin(top_cats)]
            # Add "Other" category for remaining values
            if len(filtered_df) < len(self.df):
                other_df = self.df[~self.df[categorical_col].isin(top_cats)].copy()
                other_df[categorical_col] = 'Other'
                filtered_df = pd.concat([filtered_df, other_df])
        else:
            filtered_df = self.df
            
        if plot_type == 'box' or not plot_type:
            fig = px.box(
                filtered_df, 
                x=categorical_col, 
                y=numerical_col, 
                title=f"{numerical_col} التوزيع عبر تصنيفات {categorical_col} (أكثر {min(unique_cats, self.max_categories)} تصنيف)",
                color=categorical_col,
                color_discrete_sequence=self.color_theme
            )
            fig.update_traces(
                hovertemplate=f"<b>{categorical_col}</b>: %{{x}}<br>"
                            f"<b>Q1</b>: %{{q1}}<br><b>Median</b>: %{{median}}<br>"
                            f"<b>Q3</b>: %{{q3}}<extra></extra>"
            )
        elif plot_type == 'violin':
            fig = px.violin(
                filtered_df, 
                x=categorical_col, 
                y=numerical_col,
                title=f"{numerical_col} Density Distribution by {categorical_col} (Top {min(unique_cats, self.max_categories)})",
                color=categorical_col,
                color_discrete_sequence=self.color_theme,
                # Performance optimization for large datasets
                points=False if len(filtered_df) > 5000 else "all"
            )
            fig.update_traces(
                hovertemplate=f"<b>{categorical_col}</b>: %{{x}}<br>"
                            f"<b>Value</b>: %{{y}}<extra></extra>"
            )
        elif plot_type == 'bar':
            # Calculate aggregated statistics instead of using all data points
            agg_data = filtered_df.groupby(categorical_col)[numerical_col].agg(['mean', 'count']).reset_index()
            agg_data.columns = [categorical_col, 'mean', 'count']
            
            fig = px.bar(
                agg_data,
                x=categorical_col,
                y='mean',
                title=f"المتوسط {numerical_col} بتصنيف {categorical_col} (أكثر {min(unique_cats, self.max_categories)} تصنيف)",
                color=categorical_col,
                color_discrete_sequence=self.color_theme,
                # Use size or hover to show count/sample size
                hover_data=['count']
            )
            fig.update_traces(
                hovertemplate=f"<b>{categorical_col}</b>: %{{x}}<br>"
                            f"<b>Avg {numerical_col}</b>: %{{y:.2f}}<br>"
                            f"<b>Count</b>: %{{customdata[0]}}<extra></extra>"
            )
        elif plot_type == 'strip':
            # For large datasets, limit points or use sampling
            if len(filtered_df) > 5000:
                # Use a smaller sample for strip plots
                plot_df = filtered_df.groupby(categorical_col).apply(
                    lambda x: x.sample(min(1000, len(x)), random_state=42)
                ).reset_index(drop=True)
            else:
                plot_df = filtered_df
                
            fig = px.strip(
                plot_df,
                x=categorical_col,
                y=numerical_col,
                title=f"نقاط {numerical_col} بتصنيف {categorical_col} (أكثر {min(unique_cats, self.max_categories)} تصنيف)",
                color=categorical_col,
                color_discrete_sequence=self.color_theme
            )
            fig.update_traces(
                hovertemplate=f"<b>{categorical_col}</b>: %{{x}}<br>"
                            f"<b>{numerical_col}</b>: %{{y}}<extra></extra>"
            )

        fig.update_layout(
            xaxis_title=categorical_col,
            yaxis_title=numerical_col,
            template="plotly_white",
            margin=dict(l=60, r=40, t=60, b=40),
            showlegend=False
        )
        
        # Rotate x-axis labels if there are many categories
        if unique_cats > 5:
            fig.update_layout(xaxis=dict(tickangle=45))
            
        return fig.to_html(full_html=False, include_plotlyjs='cdn')

    def _categorical_vs_categorical(self, col1, col2, plot_type):
        """
        Memory-efficient categorical comparison that handles high cardinality
        """
        # Get cardinality of both columns
        col1_nunique = self.df[col1].nunique()
        col2_nunique = self.df[col2].nunique()
        
        # For high-cardinality columns, limit to top categories
        if col1_nunique > self.max_categories or col2_nunique > self.max_categories:
            top_cats1 = self._get_top_n_categories(col1)
            top_cats2 = self._get_top_n_categories(col2)
            
            # Filter dataframe to include only top categories (plus 'Other')
            df_filtered = self.df.copy()
            df_filtered.loc[~df_filtered[col1].isin(top_cats1), col1] = 'Other'
            df_filtered.loc[~df_filtered[col2].isin(top_cats2), col2] = 'Other'
        else:
            df_filtered = self.df
        
        # Instead of using crosstab on full data, calculate it more efficiently
        # Using value_counts is more memory efficient than crosstab
        if plot_type == 'heatmap' or not plot_type:
            # Compute counts efficiently
            grouped = df_filtered.groupby([col1, col2]).size().reset_index(name='count')
            
            # Pivot to create a matrix (much more efficient than pd.crosstab)
            pivot_table = grouped.pivot_table(
                index=col1, 
                columns=col2, 
                values='count', 
                fill_value=0
            )
            
            fig = px.imshow(
                pivot_table, 
                labels=dict(x=col2, y=col1, color="Count"),
                title=f"العلاقة بين {col1} و {col2}: المخطط الحراري للتكرار (أكثر {min(col1_nunique, col2_nunique)} تصنيف)",
                color_continuous_scale=self.color_theme
            )
            fig.update_traces(
                hovertemplate=f"<b>{col1}</b>: %{{y}}<br>"
                            f"<b>{col2}</b>: %{{x}}<br>"
                            f"Count: %{{z}}<extra></extra>"
            )
        elif plot_type == 'stacked_bar':
            # Use the grouped data for efficient bar chart
            grouped = df_filtered.groupby([col1, col2]).size().reset_index(name='count')
            
            fig = px.bar(
                grouped,
                x=col1,
                y='count',
                color=col2,
                title=f"العلاقة بين {col1} و {col2}: المخطط العمودي المجمع (أكثر {min(col1_nunique, col2_nunique)} تصنيف)", 
                color_discrete_sequence=self.color_theme
            )
            fig.update_traces(
                hovertemplate=f"<b>{col1}</b>: %{{x}}<br>"
                            f"<b>{col2}</b>: %{{customdata}}<br>"
                            f"Count: %{{y}}<extra></extra>",
                customdata=grouped[col2]
            )
        elif plot_type == 'mosaic':
            # More efficient alternative to create_annotated_heatmap
            # Calculate proportions directly
            grouped = df_filtered.groupby([col1, col2]).size().reset_index(name='count')
            total = grouped['count'].sum()
            grouped['proportion'] = grouped['count'] / total
            
            # Sort by count to focus on most important relationships
            grouped = grouped.sort_values('count', ascending=False)
            
            # Create a treemap (more scalable than mosaic plot)
            fig = px.treemap(
                grouped,
                path=[col1, col2],
                values='count',
                title=f"العلاقة بين {col1} و {col2}: المخطط الشجري (أكثر {min(col1_nunique, col2_nunique)} تصنيف)",
                color='count',
                color_continuous_scale=self.color_theme
            )
            fig.update_traces(
                hovertemplate=f"<b>{col1} → {col2}</b>: %{{label}}<br>"
                            f"Count: %{{value}}<br>"
                            f"Proportion: %{{percentRoot:.2%}}<extra></extra>"
            )

        # Add appropriate layout
        if plot_type != 'mosaic':
            fig.update_layout(
                xaxis_title=col2 if plot_type == 'heatmap' or not plot_type else col1,
                yaxis_title=col1 if plot_type == 'heatmap' or not plot_type else 'Count',
                template="plotly_white",
                margin=dict(l=80, r=40, t=60, b=40),
                coloraxis_colorbar=dict(title="Count") if plot_type == 'heatmap' or not plot_type else {}
            )
            
            # Rotate x-axis labels if there are many categories
            if (plot_type == 'heatmap' and col2_nunique > 5) or \
               (plot_type == 'stacked_bar' and col1_nunique > 5):
                fig.update_layout(xaxis=dict(tickangle=45))
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')


    def _datetime_comparison(self, col1, col2, plot_type):
        # Identify which column is datetime
        datetime_col = col1 if self.get_column_type(col1) == 'datetime' else col2
        other_col = col2 if datetime_col == col1 else col1
        other_col_type = self.get_column_type(other_col)
        
        # For datetime analysis, often useful to resample/bin data
        if other_col_type == 'numerical':
            # For numerical data, aggregate by time periods for better performance
            if plot_type == 'line' or not plot_type:
                # Resample data by appropriate time period based on data range
                date_range = (self.df[datetime_col].max() - self.df[datetime_col].min()).days
                
                if date_range > 365*5:  # More than 5 years
                    freq = 'Q'  # Quarterly
                elif date_range > 365:  # More than 1 year
                    freq = 'M'  # Monthly
                elif date_range > 30:  # More than a month
                    freq = 'W'  # Weekly
                else:
                    freq = 'D'  # Daily
                
                # Create time-based aggregation
                agg_df = self.df.set_index(datetime_col)[other_col].resample(freq).mean().reset_index()
                
                fig = px.line(
                    agg_df, 
                    x=datetime_col, 
                    y=other_col,
                    title=f"{other_col} الاتجاه عبر الزمن ({datetime_col}, {freq}-resampled)",
                    color_discrete_sequence=[self.color_theme[1]]
                )
                fig.update_traces(
                    hovertemplate=f"<b>Date</b>: %{{x|%b %d, %Y}}<br>"
                                f"<b>{other_col}</b>: %{{y}}<extra></extra>"
                )
            elif plot_type == 'scatter':
                # For large datasets, sample points
                plot_df = self.df
                if len(self.df) > 5000:
                    plot_df = self.df.sample(5000, random_state=42)
                    
                fig = px.scatter(
                    plot_df,
                    x=datetime_col,
                    y=other_col,
                    title=f"{other_col} القيم عبر الزمن ({datetime_col})",
                    color_discrete_sequence=[self.color_theme[2]]
                )
                fig.update_traces(
                    hovertemplate=f"<b>Date</b>: %{{x|%b %d, %Y}}<br>"
                                f"<b>{other_col}</b>: %{{y}}<extra></extra>"
                )
            elif plot_type == 'area':
                # Similar resampling as line plot
                date_range = (self.df[datetime_col].max() - self.df[datetime_col].min()).days
                
                if date_range > 365*5:
                    freq = 'Q'
                elif date_range > 365:
                    freq = 'M'
                elif date_range > 30:
                    freq = 'W'
                else:
                    freq = 'D'
                
                agg_df = self.df.set_index(datetime_col)[other_col].resample(freq).mean().reset_index()
                
                fig = px.area(
                    agg_df.sort_values(datetime_col),
                    x=datetime_col,
                    y=other_col,
                    title=f"{other_col} عبر الزمن ({datetime_col}, {freq}-resampled)",
                    color_discrete_sequence=[self.color_theme[3]]
                )
                fig.update_traces(
                    hovertemplate=f"<b>Date</b>: %{{x|%b %d, %Y}}<br>"
                                f"<b>{other_col}</b>: %{{y}}<extra></extra>"
                )
        else:  # Categorical other column
            # For categorical data with datetime, limit categories and bin by time
            if other_col_type == 'categorical' and self.df[other_col].nunique() > self.max_categories:
                top_cats = self._get_top_n_categories(other_col)
                plot_df = self.df.copy()
                plot_df.loc[~plot_df[other_col].isin(top_cats), other_col] = 'Other'
            else:
                plot_df = self.df
                
            if plot_type == 'histogram' or not plot_type:
                # Bin dates for better visualization
                date_range = (plot_df[datetime_col].max() - plot_df[datetime_col].min()).days
                nbins = min(30, max(10, date_range//30))  # Reasonable number of bins
                
                fig = px.histogram(
                    plot_df, 
                    x=datetime_col, 
                    color=other_col,
                    title=f"{other_col} التوزيع عبر الزمن ({datetime_col})",
                    color_discrete_sequence=self.color_theme,
                    nbins=nbins
                )
                fig.update_traces(
                    hovertemplate=f"<b>Date Range</b>: %{{x|%b %d, %Y}}<br>"
                                f"<b>Count</b>: %{{y}}<br>"
                                f"<b>{other_col}</b>: %{{customdata}}<extra></extra>",
                    customdata=plot_df[other_col]
                )
            elif plot_type == 'heatmap':
                # Select appropriate time period for aggregation
                date_range = (plot_df[datetime_col].max() - plot_df[datetime_col].min()).days
                
                if date_range > 365*5:
                    freq = 'Y'  # Yearly
                elif date_range > 365:
                    freq = 'Q'  # Quarterly
                elif date_range > 90:
                    freq = 'M'  # Monthly
                else:
                    freq = 'W'  # Weekly
                
                # Create efficient aggregation
                plot_df[f"{datetime_col}_period"] = plot_df[datetime_col].dt.to_period(freq)
                cat_counts = plot_df.groupby([f"{datetime_col}_period", other_col]).size().unstack(fill_value=0)
                
                # Convert period index to datetime for better visualization
                cat_counts.index = cat_counts.index.to_timestamp()
                
                fig = px.imshow(
                    cat_counts.T,  # Transpose for better visualization
                    labels=dict(x="الفتر الزمني", y=other_col, color="التكرار"),
                    title=f"{other_col} التكرار بالفتر الزمني {freq} ({datetime_col})",
                    color_continuous_scale=self.color_theme
                )
                
                # Format x-axis to show appropriate date format
                if freq == 'Y':
                    date_format = '%Y'
                elif freq in ['Q', 'M']:
                    date_format = '%b %Y'
                else:
                    date_format = '%b %d, %Y'
                    
                fig.update_xaxes(
                    tickformat=date_format,
                    tickvals=list(range(len(cat_counts.index))),
                    ticktext=[d.strftime(date_format) for d in cat_counts.index]
                )
                
        fig.update_layout(
            xaxis_title=datetime_col,
            yaxis_title=other_col if other_col_type == 'numerical' else "Count",
            template="plotly_white",
            hovermode="x unified",
            margin=dict(l=60, r=40, t=60, b=40)
        )
        return fig.to_html(full_html=False, include_plotlyjs='cdn')


