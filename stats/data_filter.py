# data_analysis.py
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
from typing import List, Dict, Any, Union, Optional, Tuple
import io
import base64
import json
from django.http import JsonResponse
class ColumnAnalyzer:
    """
    Analyzes column properties and determines appropriate operations based on data type.
    """
    
    @staticmethod
    def get_column_type(df: pd.DataFrame, column_name: str) -> str:
        """
        Determine the column type (numeric, categorical, datetime, boolean).
        
        Args:
            df: DataFrame containing the column
            column_name: Name of the column to analyze
            
        Returns:
            str: Column type ('numeric', 'categorical', 'datetime', 'boolean')
        """
        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' not found in DataFrame")
            
        col = df[column_name]
        
        if pd.api.types.is_numeric_dtype(col):
            # Check if it's really a categorical with numeric codes
            if col.nunique() < 10 and col.nunique() / len(col) < 0.05:
                return 'categorical'
            return 'numeric'
        elif pd.api.types.is_datetime64_dtype(col):
            return 'datetime'
        elif pd.api.types.is_bool_dtype(col):
            return 'boolean'
        else:
            return 'categorical'
    
    @staticmethod
    def get_column_stats(df: pd.DataFrame, column_name: str) -> Dict[str, Any]:
        """
        Get summary statistics for a column based on its type.
        
        Args:
            df: DataFrame containing the column
            column_name: Name of the column to analyze
            
        Returns:
            dict: Statistics for the column
        """
        col_type = ColumnAnalyzer.get_column_type(df, column_name)
        stats = {
            'type': col_type,
            'missing': df[column_name].isna().sum(),
            'missing_percent': round(df[column_name].isna().sum() / len(df) * 100, 2)
        }
        
        if col_type == 'numeric':
            stats.update({
                'min': float(df[column_name].min()) if not pd.isna(df[column_name].min()) else None,
                'max': float(df[column_name].max()) if not pd.isna(df[column_name].max()) else None,
                'mean': float(df[column_name].mean()) if not pd.isna(df[column_name].mean()) else None,
                'median': float(df[column_name].median()) if not pd.isna(df[column_name].median()) else None,
                'std': float(df[column_name].std()) if not pd.isna(df[column_name].std()) else None,
                'unique_count': int(df[column_name].nunique()),
            })
            
            # Check for outliers using IQR method
            Q1 = df[column_name].quantile(0.25)
            Q3 = df[column_name].quantile(0.75)
            IQR = Q3 - Q1
            outlier_mask = (df[column_name] < (Q1 - 1.5 * IQR)) | (df[column_name] > (Q3 + 1.5 * IQR))
            stats['outliers_count'] = int(outlier_mask.sum())
            stats['has_outliers'] = stats['outliers_count'] > 0
            
        elif col_type == 'categorical':
            value_counts = df[column_name].value_counts()
            stats.update({
                'unique_count': int(df[column_name].nunique()),
                'top_value': value_counts.index[0] if not value_counts.empty else None,
                'top_count': int(value_counts.iloc[0]) if not value_counts.empty else 0,
                'top_values': {str(k): int(v) for k, v in value_counts.head(5).items()},
            })
            
        elif col_type == 'datetime':
            stats.update({
                'min': df[column_name].min().strftime('%Y-%m-%d') if not pd.isna(df[column_name].min()) else None,
                'max': df[column_name].max().strftime('%Y-%m-%d') if not pd.isna(df[column_name].max()) else None,
                'range_days': (df[column_name].max() - df[column_name].min()).days 
                              if not pd.isna(df[column_name].min()) and not pd.isna(df[column_name].max()) else None
            })
            
        return stats


class FilterOperation:
    """Base class for filter operations"""
    
    def __init__(self, column_name: str):
        self.column_name = column_name
    
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply the filter to the dataframe"""
        raise NotImplementedError("Subclasses must implement this method")
    
    def describe(self) -> str:
        """Return a description of the filter"""
        raise NotImplementedError("Subclasses must implement this method")


class ValueFilter(FilterOperation):
    """Filter based on one or more values"""
    
    def __init__(self, column_name: str, values: List[Any], include: bool = True):
        super().__init__(column_name)
        self.values = values
        self.include = include  # True for 'in', False for 'not in'
    
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.column_name not in df.columns:
            raise ValueError(f"Column '{self.column_name}' not found in DataFrame")
        
        # Convert all values to strings for consistent comparison
        str_values = [str(v) for v in self.values]
        
        if self.include:
            return df[df[self.column_name].astype(str).isin(str_values)]
        else:
            return df[~df[self.column_name].astype(str).isin(str_values)]
    
    def describe(self) -> str:
        op = "in" if self.include else "not in"
        values_str = ", ".join([str(v) for v in self.values])
        return f"{self.column_name} {op} [{values_str}]"


class RangeFilter(FilterOperation):
    """Filter based on a range (for numeric or datetime)"""
    
    def __init__(self, column_name: str, min_value: Any = None, max_value: Any = None, 
                 include_min: bool = True, include_max: bool = True):
        super().__init__(column_name)
        self.min_value = min_value
        self.max_value = max_value
        self.include_min = include_min
        self.include_max = include_max
    
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.column_name not in df.columns:
            raise ValueError(f"Column '{self.column_name}' not found in DataFrame")
        
        filtered_df = df.copy()
        
        if self.min_value is not None:
            if self.include_min:
                filtered_df = filtered_df[filtered_df[self.column_name] >= self.min_value]
            else:
                filtered_df = filtered_df[filtered_df[self.column_name] > self.min_value]
        
        if self.max_value is not None:
            if self.include_max:
                filtered_df = filtered_df[filtered_df[self.column_name] <= self.max_value]
            else:
                filtered_df = filtered_df[filtered_df[self.column_name] < self.max_value]
        
        return filtered_df
    
    def describe(self) -> str:
        result = []
        
        if self.min_value is not None:
            op = ">=" if self.include_min else ">"
            result.append(f"{self.column_name} {op} {self.min_value}")
        
        if self.max_value is not None:
            op = "<=" if self.include_max else "<"
            result.append(f"{self.column_name} {op} {self.max_value}")
        
        return " AND ".join(result)


class ComparisonOperation:
    """Base class for column comparison operations"""
    
    def __init__(self, column1: str, column2: str, operation_type: str):
        self.column1 = column1
        self.column2 = column2
        self.operation_type = operation_type
    
    def generate_plot(self, df: pd.DataFrame) -> go.Figure:
        """Generate plot based on the comparison"""
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_comparison_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get data related to the comparison"""
        raise NotImplementedError("Subclasses must implement this method")
    
    def describe(self) -> str:
        """Return a description of the comparison"""
        return f"Comparing {self.column1} and {self.column2} using {self.operation_type}"


class NumericComparison(ComparisonOperation):
    """Compare two numeric columns"""
    
    def __init__(self, column1: str, column2: str, operation_type: str = 'scatter',
                 color_by: Optional[str] = None, size_by: Optional[str] = None):
        super().__init__(column1, column2, operation_type)
        self.color_by = color_by
        self.size_by = size_by
    
    def generate_plot(self, df: pd.DataFrame) -> go.Figure:
        if self.operation_type == 'scatter':
            # Use plotly express for scatter plot
            if self.color_by and self.color_by in df.columns:
                fig = px.scatter(df, x=self.column1, y=self.column2, color=self.color_by,
                                title=f'Scatter Plot: {self.column1} vs {self.column2}',
                                labels={self.column1: self.column1, self.column2: self.column2})
            else:
                fig = px.scatter(df, x=self.column1, y=self.column2,
                                title=f'Scatter Plot: {self.column1} vs {self.column2}',
                                labels={self.column1: self.column1, self.column2: self.column2})
            
        elif self.operation_type == 'heatmap':
            # Create heatmap using correlation
            # Calculate binned correlation
            x_bins = min(20, df[self.column1].nunique())
            y_bins = min(20, df[self.column2].nunique())
            
            heatmap_data, x_edges, y_edges = np.histogram2d(
                df[self.column1].dropna(), 
                df[self.column2].dropna(),
                bins=[x_bins, y_bins]
            )
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=heatmap_data.T,
                x=[(x_edges[i] + x_edges[i+1])/2 for i in range(len(x_edges)-1)],
                y=[(y_edges[i] + y_edges[i+1])/2 for i in range(len(y_edges)-1)],
                colorscale='Viridis'
            ))
            
            fig.update_layout(
                title=f'Heatmap: {self.column1} vs {self.column2}',
                xaxis_title=self.column1,
                yaxis_title=self.column2
            )
            
        elif self.operation_type == 'hexbin':
            # Create a scatter plot with hexbin aggregation
            fig = px.density_heatmap(
                df, x=self.column1, y=self.column2, 
                marginal_x="histogram", marginal_y="histogram",
                title=f"Hexbin Density: {self.column1} vs {self.column2}"
            )
            
        elif self.operation_type == 'box':
            # Create box plot comparison
            fig = go.Figure()
            
            fig.add_trace(go.Box(y=df[self.column1], name=self.column1))
            fig.add_trace(go.Box(y=df[self.column2], name=self.column2))
            
            fig.update_layout(
                title=f'Box Plot Comparison: {self.column1} vs {self.column2}',
                yaxis_title='Value'
            )
        else:
            # Default to scatter plot
            fig = px.scatter(df, x=self.column1, y=self.column2,
                           title=f'Scatter Plot: {self.column1} vs {self.column2}')
        
        # Enhance layout
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=40, r=40, t=50, b=40)
        )
        
        return fig
    
    def get_comparison_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Calculate correlation and other metrics
        correlation = df[[self.column1, self.column2]].corr().iloc[0, 1]
        
        # Calculate regression (if scipy is available)
        regression_data = None
        try:
            from scipy import stats
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                df[self.column1].dropna(), 
                df[self.column2].dropna()
            )
            regression_data = {
                'slope': round(slope, 4),
                'intercept': round(intercept, 4),
                'r_squared': round(r_value**2, 4),
                'p_value': round(p_value, 6),
                'std_err': round(std_err, 4)
            }
        except:
            pass
        
        return {
            'correlation': round(correlation, 3),
            'column1_mean': round(df[self.column1].mean(), 3),
            'column2_mean': round(df[self.column2].mean(), 3),
            'regression': regression_data,
            'sample_data': df[[self.column1, self.column2]].head(5).to_dict('records')
        }


class CategoricalNumericComparison(ComparisonOperation):
    """Compare categorical and numeric columns"""
    
    def __init__(self, categorical_column: str, numeric_column: str, 
                 operation_type: str = 'box', aggregation: str = 'mean',
                 color_by: Optional[str] = None):
        super().__init__(categorical_column, numeric_column, operation_type)
        self.aggregation = aggregation
        self.color_by = color_by
    
    def generate_plot(self, df: pd.DataFrame) -> go.Figure:
        if self.operation_type == 'box':
            fig = px.box(df, x=self.column1, y=self.column2, 
                        color=self.color_by if self.color_by else None,
                        title=f'Box Plot: {self.column2} by {self.column1}')
            
        elif self.operation_type == 'violin':
            fig = px.violin(df, x=self.column1, y=self.column2, 
                          color=self.color_by if self.color_by else None,
                          box=True, points="all",
                          title=f'Violin Plot: {self.column2} by {self.column1}')
            
        elif self.operation_type == 'bar':
            # Aggregate data
            if self.aggregation == 'mean':
                agg_data = df.groupby(self.column1)[self.column2].mean().reset_index()
                agg_name = 'Mean'
            elif self.aggregation == 'median':
                agg_data = df.groupby(self.column1)[self.column2].median().reset_index()
                agg_name = 'Median'
            elif self.aggregation == 'sum':
                agg_data = df.groupby(self.column1)[self.column2].sum().reset_index()
                agg_name = 'Sum'
            elif self.aggregation == 'count':
                agg_data = df.groupby(self.column1)[self.column2].count().reset_index()
                agg_name = 'Count'
            else:
                agg_data = df.groupby(self.column1)[self.column2].mean().reset_index()
                agg_name = 'Mean'
            
            fig = px.bar(agg_data, x=self.column1, y=self.column2,
                       color=self.color_by if self.color_by and self.color_by in agg_data.columns else None,
                       title=f'{agg_name} of {self.column2} by {self.column1}')
            
        else:
            # Default to box plot
            fig = px.box(df, x=self.column1, y=self.column2, 
                        title=f'Box Plot: {self.column2} by {self.column1}')
        
        # Enhance layout
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=40, r=40, t=50, b=40),
            xaxis_tickangle=-45
        )
        
        return fig
    
    def get_comparison_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Calculate group statistics
        if self.aggregation == 'mean':
            agg_data = df.groupby(self.column1)[self.column2].mean()
        elif self.aggregation == 'median':
            agg_data = df.groupby(self.column1)[self.column2].median()
        elif self.aggregation == 'sum':
            agg_data = df.groupby(self.column1)[self.column2].sum()
        elif self.aggregation == 'count':
            agg_data = df.groupby(self.column1)[self.column2].count()
        else:
            agg_data = df.groupby(self.column1)[self.column2].mean()
        
        # Convert to dictionary with string keys
        agg_dict = {str(k): float(v) for k, v in agg_data.items()}
        
        # Calculate ANOVA if applicable
        anova_result = None
        try:
            from scipy import stats
            groups = [df[df[self.column1] == val][self.column2].dropna() for val in df[self.column1].unique()]
            # Only calculate if we have at least 2 groups with data
            if len(groups) >= 2 and all(len(g) > 0 for g in groups):
                f_val, p_val = stats.f_oneway(*groups)
                anova_result = {'f_value': round(f_val, 3), 'p_value': round(p_val, 5)}
        except:
            pass
        
        return {
            'group_stats': agg_dict,
            'anova': anova_result,
            'overall_mean': round(df[self.column2].mean(), 3),
            'sample_data': df[[self.column1, self.column2]].head(5).to_dict('records')
        }


class CategoricalComparison(ComparisonOperation):
    """Compare two categorical columns"""
    
    def __init__(self, column1: str, column2: str, operation_type: str = 'heatmap'):
        super().__init__(column1, column2, operation_type)
    
    def generate_plot(self, df: pd.DataFrame) -> go.Figure:
        if self.operation_type == 'heatmap':
            # Create contingency table
            contingency = pd.crosstab(df[self.column1], df[self.column2], normalize='index')
            
            # Create heatmap
            fig = px.imshow(contingency, text_auto='.2%',
                          labels=dict(x=self.column2, y=self.column1, color="Proportion"),
                          title=f"Heatmap: {self.column1} vs {self.column2}")
            
        elif self.operation_type == 'bar':
            # Create bar plot with stacked bars
            contingency = pd.crosstab(df[self.column1], df[self.column2])
            contingency_melted = contingency.reset_index().melt(id_vars=[self.column1], 
                                                            value_name='Count', 
                                                            var_name=self.column2)
            
            fig = px.bar(contingency_melted, x=self.column1, y='Count', color=self.column2,
                       title=f'Stacked Bar Plot: {self.column1} vs {self.column2}')
            
        elif self.operation_type == 'treemap':
            # Create a treemap visualization
            contingency = pd.crosstab(df[self.column1], df[self.column2])
            contingency_melted = contingency.reset_index().melt(id_vars=[self.column1], 
                                                            value_name='Count', 
                                                            var_name=self.column2)
            
            fig = px.treemap(contingency_melted, path=[self.column1, self.column2], values='Count',
                           title=f'Treemap: {self.column1} vs {self.column2}')
            
        else:
            # Default to heatmap
            contingency = pd.crosstab(df[self.column1], df[self.column2])
            fig = px.imshow(contingency, text_auto=True,
                          labels=dict(x=self.column2, y=self.column1, color="Count"),
                          title=f"Heatmap: {self.column1} vs {self.column2}")
        
        # Enhance layout
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=40, r=40, t=50, b=40),
            xaxis_tickangle=-45
        )
        
        return fig
    
    def get_comparison_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Create contingency table
        contingency = pd.crosstab(df[self.column1], df[self.column2])
        
        # Calculate chi-squared test if applicable
        chi2_result = None
        try:
            from scipy import stats
            chi2, p, dof, expected = stats.chi2_contingency(contingency)
            chi2_result = {
                'chi2': round(chi2, 3), 
                'p_value': round(p, 5), 
                'degrees_of_freedom': dof
            }
        except:
            pass
        
        # Convert contingency table to serializable format
        contingency_dict = contingency.to_dict()
        # Further processing to make it fully serializable
        processed_contingency = {}
        for col, values in contingency_dict.items():
            processed_contingency[str(col)] = {str(k): int(v) for k, v in values.items()}
        
        return {
            'contingency_table': processed_contingency,
            'chi2_test': chi2_result,
            'column1_unique': int(df[self.column1].nunique()),
            'column2_unique': int(df[self.column2].nunique()),
            'sample_data': df[[self.column1, self.column2]].head(5).to_dict('records')
        }


class AnalysisTracker:
    """
    Tracks all filters and comparisons applied to a DataFrame.
    """
    
    def __init__(self, df: pd.DataFrame):
        self.original_df = df.copy()
        self.current_df = df.copy()
        self.filters: List[FilterOperation] = []
        self.comparisons: List[ComparisonOperation] = []
        self.analysis_history: List[Dict[str, Any]] = []
        
    def add_filter(self, filter_op: FilterOperation) -> None:
        """Add a filter operation"""
        self.filters.append(filter_op)
        self.current_df = filter_op.apply(self.current_df)
        self.analysis_history.append({
            'type': 'filter',
            'operation': filter_op.describe(),
            'timestamp': pd.Timestamp.now(),
            'rows_before': len(self.current_df),
            'rows_after': len(filter_op.apply(self.current_df))
        })
    
    def add_comparison(self, comparison_op: ComparisonOperation) -> None:
        """Add a comparison operation"""
        self.comparisons.append(comparison_op)
        self.analysis_history.append({
            'type': 'comparison',
            'operation': comparison_op.describe(),
            'timestamp': pd.Timestamp.now()
        })
    
    def remove_filter(self, index: int) -> None:
        """Remove a filter by index and reapply remaining filters"""
        if 0 <= index < len(self.filters):
            removed = self.filters.pop(index)
            self.analysis_history.append({
                'type': 'remove_filter',
                'operation': removed.describe(),
                'timestamp': pd.Timestamp.now()
            })
            # Reapply all filters
            self.current_df = self.original_df.copy()
            for f in self.filters:
                self.current_df = f.apply(self.current_df)
    
    def clear_filters(self) -> None:
        """Clear all filters"""
        self.filters = []
        self.current_df = self.original_df.copy()
        self.analysis_history.append({
            'type': 'clear_filters',
            'timestamp': pd.Timestamp.now()
        })
    
    def get_filtered_data(self) -> pd.DataFrame:
        """Get the current filtered DataFrame"""
        return self.current_df.copy()
    
    def get_filter_summary(self) -> str:
        """Get a summary of all applied filters"""
        if not self.filters:
            return "No filters applied"
        
        filter_descriptions = [f.describe() for f in self.filters]
        summary = "Applied filters:\n" + "\n".join([f"- {desc}" for desc in filter_descriptions])
        summary += f"\nOriginal rows: {len(self.original_df)}, Filtered rows: {len(self.current_df)}"
        return summary
    
    def compare_columns(self, column1: str, column2: str, operation_type: str = 'auto', 
                        **kwargs) -> Union[ComparisonOperation, None]:
        """
        Compare two columns and create an appropriate comparison operation.
        
        Args:
            column1: First column name
            column2: Second column name
            operation_type: Type of comparison ('auto' to determine based on column types)
            **kwargs: Additional parameters for the comparison
            
        Returns:
            ComparisonOperation: The created comparison operation
        """
        # Check if columns exist
        if column1 not in self.current_df.columns or column2 not in self.current_df.columns:
            raise ValueError(f"Columns must exist in the DataFrame")
        
        # Get column types
        col1_type = ColumnAnalyzer.get_column_type(self.current_df, column1)
        col2_type = ColumnAnalyzer.get_column_type(self.current_df, column2)
        
        # Select appropriate comparison based on column types
        if operation_type == 'auto':
            if col1_type == 'numeric' and col2_type == 'numeric':
                operation_type = 'scatter'
            elif (col1_type == 'categorical' and col2_type == 'numeric') or \
                 (col1_type == 'numeric' and col2_type == 'categorical'):
                operation_type = 'box'
            elif col1_type == 'categorical' and col2_type == 'categorical':
                operation_type = 'heatmap'
            else:
                # Default to scatter for other combinations
                operation_type = 'scatter'
        
        # Create appropriate comparison operation
        if col1_type == 'numeric' and col2_type == 'numeric':
            comparison = NumericComparison(column1, column2, operation_type, **kwargs)
        elif col1_type == 'categorical' and col2_type == 'numeric':
            comparison = CategoricalNumericComparison(column1, column2, operation_type, **kwargs)
        elif col1_type == 'numeric' and col2_type == 'categorical':
            comparison = CategoricalNumericComparison(column2, column1, operation_type, **kwargs)
        elif col1_type == 'categorical' and col2_type == 'categorical':
            comparison = CategoricalComparison(column1, column2, operation_type, **kwargs)
        else:
            # Default to NumericComparison for other combinations
            comparison = NumericComparison(column1, column2, operation_type, **kwargs)
        
        # Add the comparison to the tracker
        self.add_comparison(comparison)
        return comparison
    
    def generate_plot(self, comparison_index: int = -1) -> go.Figure:
        """
        Generate a plot for a specific comparison (default: most recent)
        
        Args:
            comparison_index: Index of the comparison, -1 for most recent
            
        Returns:
            go.Figure: Plotly figure with the plot
        """
        if not self.comparisons:
            fig = go.Figure()
            fig.add_annotation(text="No comparisons available", showarrow=False)
            return fig
        
        idx = comparison_index if comparison_index >= 0 else len(self.comparisons) + comparison_index
        if 0 <= idx < len(self.comparisons):
            return self.comparisons[idx].generate_plot(self.current_df)
        else:
            raise IndexError("Comparison index out of range")
    
    def get_plot_as_html(self, comparison_index: int = -1, full_html: bool = False, 
                        include_plotlyjs: bool = 'cdn') -> str:
        """
        Get a plot as HTML for embedding in web pages
        
        Args:
            comparison_index: Index of the comparison
            full_html: Whether to include full HTML (doctype, head, etc.)
            include_plotlyjs: How to include plotly.js ('cdn', True, False)
            
        Returns:
            str: HTML representation of the plot
        """
        fig = self.generate_plot(comparison_index)
        html = fig.to_html(full_html=full_html, include_plotlyjs=include_plotlyjs)
        return html
    
    def generate_report(self, include_plots: bool = True) -> Dict[str, Any]:
        """
        Generate a comprehensive report on the data analysis
        
        Args:
            include_plots: Whether to include plots in the report (as HTML)
            
        Returns:
            dict: Report data
        """
        report = {
            'summary': {
                'original_rows': len(self.original_df),
                'filtered_rows': len(self.current_df),
                'filters_applied': len(self.filters),
                'comparisons_made': len(self.comparisons),
                'columns_analyzed': list(self.current_df.columns),
            },
            'filters': [f.describe() for f in self.filters],
            'comparisons': [],
            'column_stats': {}
        }
        
        # Add comparison details and plots
        for i, comparison in enumerate(self.comparisons):
            comp_data = {
                'description': comparison.describe(),
                'data': comparison.get_comparison_data(self.current_df)
            }
            
            if include_plots:
                comp_data['plot_html'] = self.get_plot_as_html(i, full_html=False, include_plotlyjs=False)
            
            report['comparisons'].append(comp_data)
        
        # Add column statistics for key columns
        key_columns = set()
        for f in self.filters:
            key_columns.add(f.column_name)
        for c in self.comparisons:
            key_columns.add(c.column1)
            key_columns.add(c.column2)
        
        for col in key_columns:
            if col in self.current_df.columns:
                report['column_stats'][col] = ColumnAnalyzer.get_column_stats(self.current_df, col)
        
        return report
    
    def generate_filter_plot(self, column_name: str) -> go.Figure:
        """
        Generate a plot for a filtered column
        
        Args:
            column_name: Column to plot
            
        Returns:
            go.Figure: Plotly figure with the plot
        """
        df = self.get_filtered_data()
        
        # Check if column exists
        if column_name not in df.columns:
            fig = go.Figure()
            fig.add_annotation(text=f"Column '{column_name}' not found", showarrow=False)
            return fig
        
        # Determine the type of plot based on column type
        col_type = ColumnAnalyzer.get_column_type(df, column_name)
        
        if col_type == 'numeric':
            # Create histogram for numeric column
            fig = px.histogram(df, x=column_name, 
                             title=f'Distribution of {column_name}',
                             labels={column_name: column_name})
            
            # Add box plot below the histogram
            fig.add_trace(go.Box(
                y=[0],  # This doesn't matter and will be hidden
                x=df[column_name],
                name=column_name,
                boxpoints=False,
                orientation='h',
                yaxis='y2'
            ))
            
            # Update layout to position box plot below histogram
            fig.update_layout(
                yaxis2=dict(
                    overlaying='y',
                    side='bottom',
                    showticklabels=False,
                    range=[-0.5, 0.1]  # Adjust this to control box plot size
                )
            )
            
            fig.update_layout(
                showlegend=False,
                template="plotly_white",
                margin=dict(l=40, r=40, t=50, b=40),
                yaxis_title="Count"
            )
            
        elif col_type == 'categorical':
            # Create bar chart for categorical column
            value_counts = df[column_name].value_counts().reset_index()
            value_counts.columns = [column_name, 'count']
            
            fig = px.bar(value_counts, x=column_name, y='count',
                       title=f'Distribution of {column_name}',
                       labels={column_name: column_name, 'count': 'Count'})
            
            fig.update_layout(
                template="plotly_white",
                margin=dict(l=40, r=40, t=50, b=40),
                xaxis_tickangle=-45
            )
            
        elif col_type == 'datetime':
            # Create a histogram for datetime column
            fig = px.histogram(df, x=column_name, 
                             title=f'Distribution of {column_name}',
                             labels={column_name: column_name})
            
            fig.update_layout(
                template="plotly_white",
                margin=dict(l=40, r=40, t=50, b=40),
                yaxis_title="Count"
            )
            
        else:
            # Default to bar chart for other types
            value_counts = df[column_name].value_counts().reset_index()
            value_counts.columns = [column_name, 'count']
            
            fig = px.bar(value_counts, x=column_name, y='count',
                       title=f'Distribution of {column_name}')
            
            fig.update_layout(
                template="plotly_white",
                margin=dict(l=40, r=40, t=50, b=40),
                xaxis_tickangle=-45
            )
        
        return fig
    
    def get_filter_plot_as_html(self, column_name: str, full_html: bool = False, 
                               include_plotlyjs: bool = 'cdn') -> str:
        """
        Get a filter plot as HTML for embedding in web pages
        
        Args:
            column_name: Column to plot
            full_html: Whether to include full HTML
            include_plotlyjs: How to include plotly.js
            
        Returns:
            str: HTML representation of the plot
        """
        fig = self.generate_filter_plot(column_name)
        html = fig.to_html(full_html=full_html, include_plotlyjs=include_plotlyjs)
        return html
    
    def to_dict(self):
        """Convert the tracker to a serializable dictionary"""
        return {
            'original_df': self.original_df.to_json(orient='split'),
            'current_df': self.current_df.to_json(orient='split'),
            'filters': [{
                'type': f.__class__.__name__,
                'column_name': f.column_name,
                'values': getattr(f, 'values', None),
                'min_value': getattr(f, 'min_value', None),
                'max_value': getattr(f, 'max_value', None),
                'include': getattr(f, 'include', None)
            } for f in self.filters],
            'comparisons': [{
                'type': c.__class__.__name__,
                'column1': c.column1,
                'column2': c.column2,
                'operation_type': c.operation_type
            } for c in self.comparisons]
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a tracker from a serialized dictionary"""
        tracker = cls(pd.read_json(io.StringIO(data['original_df']), orient='split'))
        tracker.current_df = pd.read_json(io.StringIO(data['current_df']), orient='split')
        
        # Recreate filters
        for f_data in data['filters']:
            if f_data['type'] == 'ValueFilter':
                tracker.filters.append(ValueFilter(
                    f_data['column_name'], 
                    f_data['values'],
                    include=f_data['include']
                ))
            elif f_data['type'] == 'RangeFilter':
                tracker.filters.append(RangeFilter(
                    f_data['column_name'],
                    min_value=f_data['min_value'],
                    max_value=f_data['max_value']
                ))
        
        # Recreate comparisons
        for c_data in data['comparisons']:
            if c_data['type'] == 'NumericComparison':
                tracker.comparisons.append(NumericComparison(
                    c_data['column1'],
                    c_data['column2'],
                    operation_type=c_data['operation_type']
                ))
            # Add other comparison types as needed
            
        return tracker

def get_selected_plots(request):
    if request.method == "GET":
        try:
            columns = request.GET.getlist('columns[]')
            
            # Get tracker data from session
            tracker_data = request.session.get('analysis_tracker')
            if tracker_data:
                tracker = AnalysisTracker.from_dict(tracker_data)
            else:
                # Initialize new tracker if none exists
                data_json = request.session.get('csv_data')
                if not data_json:
                    return JsonResponse({'error': 'No data found'}, status=400)
                
                df = pd.read_json(io.StringIO(data_json), orient='split')
                tracker = AnalysisTracker(df)
            
            # Use the tracker's current_df which includes filters
            df = tracker.current_df
            
            # Generate plots and stats
            plots = {}
            stats = {}
            
            for col in columns:
                if col in df.columns:
                    fig = tracker.generate_filter_plot(col)
                    plot_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
                    
                    plots[col] = {
                        'html': plot_html,
                        'type': ColumnAnalyzer.get_column_type(df, col)
                    }
                    
                    # Generate statistics
                    stats[col] = ColumnAnalyzer.get_column_stats(df, col)
            
            # Store the updated tracker in session
            request.session['analysis_tracker'] = tracker.to_dict()
            
            return JsonResponse({
                'plots': plots,
                'stats': stats
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def filter_plot(request):
    if request.method == "GET":
        try:
            # Get tracker from session or create new one
            tracker_data = request.session.get('analysis_tracker')
            if tracker_data:
                tracker = AnalysisTracker.from_dict(tracker_data)
            else:
                data_json = request.session.get('csv_data')
                if not data_json:
                    return JsonResponse({'error': 'No data found'}, status=400)
                
                df = pd.read_json(io.StringIO(data_json), orient='split')
                tracker = AnalysisTracker(df)
            
            # Apply the new filter
            target = request.GET.get('target')
            mode = request.GET.get('mode')
            values = request.GET.getlist('values[]')
            
            if mode == 'self' and values:
                tracker.add_filter(ValueFilter(target, values))
            elif mode == 'other':
                filter_column = request.GET.get('filter_column')
                if filter_column and values:
                    tracker.add_filter(ValueFilter(filter_column, values))
            
            # Store updated tracker in session
            request.session['analysis_tracker'] = tracker.to_dict()
            
            # Generate plot from filtered data
            plot_html = tracker.get_filter_plot_as_html(
                target, 
                full_html=False, 
                include_plotlyjs='cdn'
            )
            
            return JsonResponse({
                'plot_html': plot_html,
                'row_count': len(tracker.current_df)
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=400)