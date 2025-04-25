import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_donor_insights(df):
    """Generate donor-specific insights about donation patterns and key metrics."""
    insights = []
    
    # Top Donors Analysis
    if 'donation_amount' in df.columns:
        # Top donors by total amount
        donor_totals = df.groupby('organization_name')['donation_amount'].sum().sort_values(ascending=False)
        top_donors = donor_totals.head(3)
        insights.append({
            'type': 'top_donors_amount',
            'message': f"Top 3 donors by total amount: {', '.join([f'{name} (${amount:,.2f})' for name, amount in top_donors.items()])}",
            'severity': 'high'
        })

        # Average donation size
        avg_donation = df['donation_amount'].mean()
        insights.append({
            'type': 'average_donation',
            'message': f"Average donation amount: ${avg_donation:,.2f}",
            'severity': 'medium'
        })

    # Donation Frequency Analysis
    if 'organization_name' in df.columns:
        freq_counts = df['organization_name'].value_counts()
        top_frequent = freq_counts.head(3)
        insights.append({
            'type': 'top_donors_frequency',
            'message': f"Most frequent donors: {', '.join([f'{name} ({count} donations)' for name, count in top_frequent.items()])}",
            'severity': 'high'
        })

    return insights

def generate_engagement_insights(df):
    """Generate insights about donor engagement patterns."""
    insights = []
    
    if 'donation_amount' in df.columns and 'organization_name' in df.columns:
        # Donation consistency
        org_donations = df.groupby('organization_name').agg({
            'donation_amount': ['count', 'mean', 'std']
        })
        
        # Identify consistent donors (low standard deviation)
        consistent_donors = org_donations[
            (org_donations[('donation_amount', 'count')] > 2) &
            (org_donations[('donation_amount', 'std')] < org_donations[('donation_amount', 'mean')] * 0.2)
        ]
        
        if not consistent_donors.empty:
            insights.append({
                'type': 'consistent_donors',
                'message': f"Found {len(consistent_donors)} organizations with consistent donation patterns",
                'severity': 'medium'
            })

    return insights

def generate_retention_insights(df):
    """Generate insights about donor retention and patterns."""
    insights = []
    
    if 'organization_name' in df.columns:
        # Calculate retention rate
        total_donors = df['organization_name'].nunique()
        repeat_donors = df['organization_name'].value_counts()[df['organization_name'].value_counts() > 1].count()
        retention_rate = (repeat_donors / total_donors) * 100 if total_donors > 0 else 0
        
        insights.append({
            'type': 'retention_rate',
            'message': f"Donor retention rate: {retention_rate:.1f}%",
            'severity': 'high' if retention_rate < 50 else 'medium' if retention_rate < 70 else 'low'
        })

    return insights

def generate_statistical_insights(df):
    """Generate statistical insights about donation patterns."""
    insights = []
    
    if 'donation_amount' in df.columns:
        # Distribution analysis
        mean_donation = df['donation_amount'].mean()
        median_donation = df['donation_amount'].median()
        skew = df['donation_amount'].skew()
        
        if abs((mean_donation - median_donation) / median_donation) > 0.2:
            insights.append({
                'type': 'donation_distribution',
                'message': f"Donation distribution is {'positively' if skew > 0 else 'negatively'} skewed " +
                          f"(mean: ${mean_donation:,.2f}, median: ${median_donation:,.2f})",
                'severity': 'medium'
            })

    return insights

def generate_missing_value_insights(df):
    """Generate insights about missing values in the dataset."""
    insights = []
    
    # Calculate missing values for each column
    missing_values = df.isnull().sum()
    total_rows = len(df)
    
    # Filter columns with missing values
    columns_with_missing = missing_values[missing_values > 0]
    
    if len(columns_with_missing) > 0:
        # Generate insights for each column with missing values
        for column, missing_count in columns_with_missing.items():
            missing_percentage = (missing_count / total_rows) * 100
            severity = 'high' if missing_percentage > 20 else 'medium' if missing_percentage > 5 else 'low'
            
            insights.append({
                'type': 'missing_values',
                'message': f"Column '{column}' has {missing_count:,} missing values ({missing_percentage:.1f}%)",
                'severity': severity
            })
        
        # Overall missing values insight
        total_missing = missing_values.sum()
        total_cells = df.size
        overall_missing_percentage = (total_missing / total_cells) * 100
        
        if overall_missing_percentage > 0:
            severity = 'high' if overall_missing_percentage > 15 else 'medium' if overall_missing_percentage > 5 else 'low'
            insights.append({
                'type': 'overall_missing_values',
                'message': f"Dataset contains {total_missing:,} missing values across all columns ({overall_missing_percentage:.1f}% of all data)",
                'severity': severity
            })
    else:
        # No missing values insight
        insights.append({
            'type': 'missing_values',
            'message': "No missing values found in the dataset",
            'severity': 'low'
        })
    
    # Additional data quality checks
    # Check for potential duplicate rows
    duplicate_rows = df.duplicated().sum()
    if duplicate_rows > 0:
        duplicate_percentage = (duplicate_rows / total_rows) * 100
        insights.append({
            'type': 'duplicates',
            'message': f"Found {duplicate_rows:,} duplicate rows ({duplicate_percentage:.1f}% of data)",
            'severity': 'medium'
        })
    
    # Check for columns with all same values
    constant_columns = [col for col in df.columns if df[col].nunique() == 1]
    if constant_columns:
        insights.append({
            'type': 'constant_columns',
            'message': f"Found columns with constant values: {', '.join(constant_columns)}",
            'severity': 'medium'
        })
    
    # Check for potential data entry errors in numeric columns
    for col in df.select_dtypes(include=['float64', 'int64']).columns:
        if col == 'donation_amount':  # Special check for donation amounts
            zero_values = (df[col] == 0).sum()
            negative_values = (df[col] < 0).sum()
            
            if zero_values > 0:
                zero_percentage = (zero_values / total_rows) * 100
                insights.append({
                    'type': 'zero_donations',
                    'message': f"Found {zero_values:,} zero donation amounts ({zero_percentage:.1f}% of donations)",
                    'severity': 'medium'
                })
            
            if negative_values > 0:
                insights.append({
                    'type': 'negative_donations',
                    'message': f"Found {negative_values:,} negative donation amounts",
                    'severity': 'high'
                })
    
    return insights

def generate_all_insights(df):
    """Generate all insights for the dataset."""
    all_insights = []
    
    # Basic data quality insights
    all_insights.extend(generate_missing_value_insights(df))
    
    # Donor-specific insights
    all_insights.extend(generate_donor_insights(df))
    all_insights.extend(generate_engagement_insights(df))
    all_insights.extend(generate_retention_insights(df))
    all_insights.extend(generate_statistical_insights(df))
    
    # Sort insights by severity
    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    all_insights.sort(key=lambda x: severity_order[x['severity']])
    
    return all_insights

def format_currency(amount):
    """Helper function to format currency values."""
    return f"${amount:,.2f}"

def generate_summary_report(df):
    """Generate a comprehensive summary report of donor insights."""
    summary = {
        'total_donations': len(df),
        'total_donors': df['organization_name'].nunique() if 'organization_name' in df.columns else 0,
        'total_amount': df['donation_amount'].sum() if 'donation_amount' in df.columns else 0,
        'avg_donation': df['donation_amount'].mean() if 'donation_amount' in df.columns else 0,
        'insights': generate_all_insights(df)
    }
    return summary

# Reuse your existing plot generation logic
                    # if pd.api.types.is_numeric_dtype(df[col]):
                    #     # For numeric columns                      
                    #     fig = px.histogram(df[col], title=f"Distribution of {col}")
                    #     fig.update_layout(
                    #         title=f"Distribution of {col}",
                    #         xaxis_title=col,
                    #         yaxis_title="Count",
                    #         template="simple_white"
                    #     )
                    # else:
                    #     # For categorical columns
                    #     value_counts = df[col].value_counts().head(10)
                    #     fig = px.bar(
                    #         x=value_counts.index.astype(str), 
                    #         y=value_counts.values,
                    #         title=f"Top 10 values in {col}"
                    #     )
                    #     fig.update_layout(
                    #         xaxis_title=col,
                    #         yaxis_title="Count",
                    #         template="simple_white"
                    #     )
                    