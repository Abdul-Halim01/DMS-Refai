"""
Expected columns in the dataset:
- organization_name: Name of the donor organization
- donation_amount: Amount of donation
- donation_date: Date of donation
- donation_category: Type of donation (e.g., 'Regular', 'Campaign', 'Emergency', 'Annual')
- donor_location: Geographic location
- donor_type: Type of donor (e.g., 'Corporate', 'Individual', 'Foundation')
- donation_frequency: Frequency of donations (e.g., 'One-time', 'Monthly', 'Quarterly', 'Annual')
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import calendar

def  generate_donor_insights(df, include_figures=False):
    """Generate comprehensive donor-specific insights, optionally including figure objects."""
    insights = []
    
    if all(col in df.columns for col in ['organization_name', 'donation_amount', 'donation_date']):
        try:
            # Convert donation_date to datetime with proper format
            df['donation_date'] = pd.to_datetime(df['donation_date'], dayfirst=True)
            
            # 1. Top Donors Analysis with Enhanced Details
            donor_totals = df.groupby('organization_name').agg({
                'donation_amount': ['sum', 'count', 'mean', 'std'],
                'donation_date': ['min', 'max']
            }).round(2)
            
            donor_totals.columns = ['total_amount', 'donation_count', 'avg_donation', 
                                  'donation_std', 'first_donation', 'last_donation']
            donor_totals = donor_totals.sort_values('total_amount', ascending=False)
            
            # Calculate additional metrics
            donor_totals['donation_frequency'] = (
                donor_totals['donation_count'] / 
                ((donor_totals['last_donation'] - donor_totals['first_donation']).dt.days / 30)
            ).round(2)
            
            # Top donors insights with detailed analysis
            top_donors = donor_totals.head(3)
            for name, row in top_donors.iterrows():
                donor_df = df[df['organization_name'] == name].copy()
                
                # Monthly donation pattern
                monthly_donations = donor_df.set_index('donation_date')['donation_amount'].resample('ME').agg([
                    'sum', 'count', 'mean'
                ]).fillna(0)
                
                # Create subplot with multiple metrics
                fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=(
                        'Monthly Donation Amounts',
                        'Donation Frequency',
                        'Donation Size Distribution',
                        'Cumulative Donations'
                    )
                )
                
                # Plot 1: Monthly donation amounts
                fig.add_trace(
                    go.Scatter(
                        x=monthly_donations.index,
                        y=monthly_donations['sum'],
                        name='Monthly Total',
                        line=dict(color='blue')
                    ),
                    row=1, col=1
                )
                
                # Plot 2: Donation frequency
                fig.add_trace(
                    go.Bar(
                        x=monthly_donations.index,
                        y=monthly_donations['count'],
                        name='Number of Donations',
                        marker_color='green'
                    ),
                    row=1, col=2
                )
                
                # Plot 3: Donation size distribution
                fig.add_trace(
                    go.Histogram(
                        x=donor_df['donation_amount'],
                        name='Donation Size',
                        nbinsx=20,
                        marker_color='orange'
                    ),
                    row=2, col=1
                )
                
                # Plot 4: Cumulative donations
                cumulative = donor_df.sort_values('donation_date')
                cumulative['cumulative'] = cumulative['donation_amount'].cumsum()
                fig.add_trace(
                    go.Scatter(
                        x=cumulative['donation_date'],
                        y=cumulative['cumulative'],
                        name='Cumulative Total',
                        line=dict(color='red')
                    ),
                    row=2, col=2
                )
                
                # Update layout
                fig.update_layout(
                    height=800,
                    title_text=f"Comprehensive Analysis - {name}",
                    showlegend=True,
                    template='plotly_white'
                )
                
                # Calculate growth metrics
                yoy_growth = calculate_yoy_growth(monthly_donations['sum'])
                consistency_score = calculate_consistency_score(monthly_donations['count'])
                engagement_level = calculate_engagement_level(row['donation_frequency'], consistency_score)
                
                insights.append({
                    'type': 'top_donor_analysis',
                    'message': f"Detailed analysis for {name}: ${float(row['total_amount']):,.2f} total from {int(row['donation_count'])} donations",
                    'severity': 'high',
                    'details': {
                        'donor_name': name,
                        'metrics': {
                            'total_amount': float(row['total_amount']),
                            'donation_count': int(row['donation_count']),
                            'avg_donation': float(row['avg_donation']),
                            'donation_frequency': float(row['donation_frequency']),
                            'relationship_duration': f"{(row['last_donation'] - row['first_donation']).days} days",
                            'yoy_growth': yoy_growth,
                            'consistency_score': consistency_score,
                            'engagement_level': engagement_level
                        },
                        'plot': fig.to_html(full_html=False, include_plotlyjs='cdn'),
                        'recommendations': generate_donor_recommendations(
                            yoy_growth,
                            consistency_score,
                            engagement_level,
                            row['donation_frequency'],
                            float(row['avg_donation']),
                            float(row['total_amount'])
                        ),
                        'figure': fig if include_figures else None,
                        'data': donor_df.copy()
                    }
                })
                
            # 2. Donation Trends Analysis
            monthly_total = df.set_index('donation_date')['donation_amount'].resample('ME').sum()
            monthly_count = df.set_index('donation_date')['donation_amount'].resample('ME').count()
            monthly_avg = df.set_index('donation_date')['donation_amount'].resample('ME').mean()
            
            trend_fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Monthly Donation Totals', 'Number of Donations')
            )
            
            trend_fig.add_trace(
                go.Scatter(
                    x=monthly_total.index,
                    y=monthly_total.values,
                    name='Monthly Total',
                    line=dict(color='blue')
                ),
                row=1, col=1
            )
            
            trend_fig.add_trace(
                go.Bar(
                    x=monthly_count.index,
                    y=monthly_count.values,
                    name='Number of Donations',
                    marker_color='green'
                ),
                row=2, col=1
            )
            
            trend_fig.update_layout(
                height=600,
                title_text="Donation Trends Analysis",
                showlegend=True,
                template='plotly_white'
            )
            
            # Calculate trend metrics
            current_month = monthly_total.iloc[-1]
            prev_month = monthly_total.iloc[-2]
            growth_rate = ((current_month - prev_month) / prev_month * 100) if prev_month != 0 else 0
            
            # Calculate additional metrics
            three_month_avg = monthly_total.tail(3).mean()
            year_ago = monthly_total.iloc[-13] if len(monthly_total) >= 13 else 0
            yoy_change = ((current_month - year_ago) / year_ago * 100) if year_ago != 0 else 0
            
            insights.append({
                'type': 'donation_trends',
                'message': f"Monthly donation trend shows {'positive' if growth_rate > 0 else 'negative'} growth ({growth_rate:.1f}% change)",
                'severity': 'medium' if abs(growth_rate) < 20 else 'high',
                'details': {
                    'plot': trend_fig.to_html(full_html=False, include_plotlyjs='cdn'),
                    'metrics': {
                        'current_month_total': float(current_month),
                        'previous_month_total': float(prev_month),
                        'monthly_growth_rate': float(growth_rate),
                        'three_month_average': float(three_month_avg),
                        'year_over_year_change': float(yoy_change),
                        'average_monthly_donations': float(monthly_count.mean()),
                        'highest_month': float(monthly_total.max()),
                        'lowest_month': float(monthly_total.min())
                    },
                    'recommendations': [
                        "Review successful campaigns for replication",
                        "Identify seasonal patterns",
                        "Plan targeted outreach during peak periods",
                        f"{'Investigate decline and develop recovery plan' if growth_rate < 0 else 'Maintain positive growth momentum'}",
                        f"Focus on donor retention during {monthly_count.idxmax().strftime('%B')}"
                    ],
                    'figure': trend_fig if include_figures else None,
                    'data': df.copy()
                }
            })
            
            # 3. Donation Size Distribution
            avg_donation = df['donation_amount'].mean()
            median_donation = df['donation_amount'].median()
            skew = (avg_donation - median_donation) / avg_donation if avg_donation != 0 else 0
            
            # Create distribution analysis
            dist_fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Donation Size Distribution', 'Donation Size Box Plot')
            )
            
            dist_fig.add_trace(
                go.Histogram(
                    x=df['donation_amount'],
                    name='Distribution',
                    nbinsx=30,
                    marker_color='orange'
                ),
                row=1, col=1
            )
            
            dist_fig.add_trace(
                go.Box(
                    y=df['donation_amount'],
                    name='Box Plot',
                    marker_color='red'
                ),
                row=2, col=1
            )
            
            dist_fig.update_layout(
                height=600,
                title_text='Donation Size Analysis',
                showlegend=True,
                template='plotly_white'
            )
            
            # Calculate distribution metrics
            percentiles = df['donation_amount'].quantile([0.25, 0.5, 0.75, 0.9]).to_dict()
            
            insights.append({
                'type': 'donation_distribution',
                'message': f"Average donation is ${avg_donation:.2f} with {'positive' if skew > 0 else 'negative'} skew",
                'severity': 'low',
                'details': {
                    'plot': dist_fig.to_html(full_html=False, include_plotlyjs='cdn'),
                    'metrics': {
                        'average_donation': float(avg_donation),
                        'median_donation': float(median_donation),
                        'skewness': float(skew),
                        'standard_deviation': float(df['donation_amount'].std()),
                        'minimum_donation': float(df['donation_amount'].min()),
                        'maximum_donation': float(df['donation_amount'].max()),
                        'percentile_25': float(percentiles[0.25]),
                        'percentile_50': float(percentiles[0.5]),
                        'percentile_75': float(percentiles[0.75]),
                        'percentile_90': float(percentiles[0.9])
                    },
                    'recommendations': [
                        "Consider donation tier strategies",
                        "Develop targeted campaigns for different donor segments",
                        "Optimize suggested donation amounts",
                        f"Focus on increasing donations below ${percentiles[0.25]:.2f}",
                        f"Create special recognition for donations above ${percentiles[0.9]:.2f}"
                    ],
                    'figure': dist_fig if include_figures else None,
                    'data': df.copy()
                }
            })
            
            # 2. Seasonal Patterns Analysis
            seasonal_df = df.copy()
            seasonal_df['month'] = seasonal_df['donation_date'].dt.month
            seasonal_df['year'] = seasonal_df['donation_date'].dt.year
            
            monthly_patterns = seasonal_df.groupby('month').agg({
                'donation_amount': ['sum', 'count', 'mean']
            }).round(2)
            
            # Create seasonal plot
            seasonal_fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Monthly Donation Patterns', 'Average Donation by Month')
            )
            
            seasonal_fig.add_trace(
                go.Bar(
                    x=monthly_patterns.index,
                    y=monthly_patterns[('donation_amount', 'sum')],
                    name='Total Donations',
                    marker_color='blue'
                ),
                row=1, col=1
            )
            
            seasonal_fig.add_trace(
                go.Scatter(
                    x=monthly_patterns.index,
                    y=monthly_patterns[('donation_amount', 'mean')],
                    name='Average Donation',
                    line=dict(color='red')
                ),
                row=2, col=1
            )
            
            seasonal_fig.update_layout(
                height=600,
                title_text="Seasonal Donation Patterns",
                showlegend=True,
                template='plotly_white'
            )
            
            # Find peak months and generate insights
            peak_months = monthly_patterns[('donation_amount', 'sum')].nlargest(3)
            low_months = monthly_patterns[('donation_amount', 'sum')].nsmallest(3)
            
            # Calculate key metrics for recommendations
            peak_month_amount = float(peak_months.iloc[0])
            peak_month_name = calendar.month_name[peak_months.index[0]]
            low_months_names = [calendar.month_name[m] for m in low_months.index[:2]]
            low_months_avg = float(low_months.mean())
            growth_potential = ((peak_month_amount - low_months_avg) / low_months_avg) * 100
            
            # Seasonal Patterns recommendations with data-driven insights
            seasonal_recommendations = [
                f"Launch {peak_month_name} campaign with ${peak_month_amount:,.2f} target and matching gift challenge",
                
                f"Develop re-engagement strategy for {', '.join(low_months_names)} to increase giving by {growth_potential:.1f}%",
                
                f"Create year-round giving program to bridge ${peak_month_amount - low_months_avg:,.2f} monthly variance",
                
                f"Implement quarterly bonus matching for donations above ${monthly_patterns[('donation_amount', 'mean')].mean():,.2f}",
                
                f"Launch donor retention program targeting {peak_month_name}'s {int(monthly_patterns[('donation_amount', 'count')].max())} donors"
            ]

            # Additional recommendations based on specific thresholds
            if growth_potential > 100:
                seasonal_recommendations.append(
                    f"URGENT: Address {growth_potential:.1f}% giving gap between peak and low months"
                )
            
            if monthly_patterns[('donation_amount', 'count')].std() > monthly_patterns[('donation_amount', 'count')].mean():
                seasonal_recommendations.append(
                    f"Stabilize monthly donor count: Current variance {monthly_patterns[('donation_amount', 'count')].std():.0f} donors/month"
                )

            insights.append({
                'type': 'seasonal_patterns',
                'message': f"Peak donation month {peak_month_name}: ${peak_month_amount:,.2f}",
                'severity': 'medium' if growth_potential < 100 else 'high',
                'details': {
                    'plot': seasonal_fig.to_html(full_html=False, include_plotlyjs='cdn'),
                    'metrics': {
                        'sections': [
                            {
                                'title': 'Peak Months',
                                'items': [
                                    {
                                        'month': calendar.month_name[month],
                                        'amount': float(amount),
                                        'color': 'text-green-600'
                                    }
                                    for month, amount in peak_months.items()
                                ]
                            },
                            {
                                'title': 'Low Months',
                                'items': [
                                    {
                                        'month': calendar.month_name[month],
                                        'amount': float(amount),
                                        'color': 'text-red-600'
                                    }
                                    for month, amount in low_months.items()
                                ]
                            },
                            {
                                'title': 'Monthly Averages',
                                'items': [
                                    {
                                        'month': calendar.month_name[month],
                                        'amount': float(amount),
                                        'color': 'text-blue-600'
                                    }
                                    for month, amount in monthly_patterns[('donation_amount', 'mean')].items()
                                ]
                            }
                        ]
                    },
                    'recommendations': sorted(seasonal_recommendations, 
                                           key=lambda x: (x.startswith('URGENT'),
                                                        'launch' in x.lower(), 
                                                        len(x)))[:5],
                    'figure': seasonal_fig if include_figures else None,
                    'data': df.copy()
                }
            })
            
            # 3. Donor Segmentation Analysis
            if 'donor_type' in df.columns:
                segment_analysis = df.groupby('donor_type').agg({
                    'donation_amount': ['sum', 'count', 'mean'],
                    'organization_name': 'nunique'
                }).round(2)
                
                segment_analysis.columns = ['total_amount', 'donation_count', 
                                         'avg_donation', 'unique_donors']
                
                # Create segmentation visualization
                segment_fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=(
                        'Total Donations by Segment',
                        'Number of Donors by Segment',
                        'Average Donation by Segment',
                        'Donation Frequency by Segment'
                    )
                )
                
                # Add traces for each subplot
                segment_fig.add_trace(
                    go.Bar(
                        x=segment_analysis.index,
                        y=segment_analysis['total_amount'],
                        name='Total Donations'
                    ),
                    row=1, col=1
                )
                
                segment_fig.add_trace(
                    go.Bar(
                        x=segment_analysis.index,
                        y=segment_analysis['unique_donors'],
                        name='Unique Donors'
                    ),
                    row=1, col=2
                )
                
                segment_fig.add_trace(
                    go.Bar(
                        x=segment_analysis.index,
                        y=segment_analysis['avg_donation'],
                        name='Average Donation'
                    ),
                    row=2, col=1
                )
                
                segment_fig.add_trace(
                    go.Bar(
                        x=segment_analysis.index,
                        y=segment_analysis['donation_count']/segment_analysis['unique_donors'],
                        name='Donations per Donor'
                    ),
                    row=2, col=2
                )
                
                segment_fig.update_layout(
                    height=800,
                    title_text="Donor Segment Analysis",
                    showlegend=True,
                    template='plotly_white'
                )
                
                # Generate segment-specific insights
                top_segment = segment_analysis['total_amount'].idxmax()
                growth_segment = segment_analysis['unique_donors'].idxmax()
                
                insights.append({
                    'type': 'donor_segmentation',
                    'message': f"Leading donor segment: {top_segment} (${float(segment_analysis.loc[top_segment, 'total_amount']):,.2f} total)",
                    'severity': 'high',
                    'details': {
                        'plot': segment_fig.to_html(full_html=False, include_plotlyjs='cdn'),
                        'metrics': {
                            'segment_totals': segment_analysis['total_amount'].to_dict(),
                            'segment_counts': segment_analysis['unique_donors'].to_dict(),
                            'segment_averages': segment_analysis['avg_donation'].to_dict()
                        },
                        'data': df.copy(),
                        'recommendations': generate_segment_recommendations(
                            top_segment,
                            growth_segment,
                            segment_analysis
                        ),
                        'figure': segment_fig if include_figures else None
                    }
                })
            
            # 4. Geographic Analysis (if location data available)
            if 'donor_location' in df.columns:
                location_analysis = df.groupby('donor_location').agg({
                    'donation_amount': ['sum', 'count', 'mean'],
                    'organization_name': 'nunique'
                }).round(2)
                
                location_analysis.columns = ['total_amount', 'donation_count',
                                          'avg_donation', 'unique_donors']
                
                # Create choropleth or bar chart based on location data
                location_fig = px.bar(
                    location_analysis.reset_index(),
                    x='donor_location',
                    y='total_amount',
                    title='Donations by Location',
                    color='avg_donation'
                )
                
                # Find top and emerging locations
                top_locations = location_analysis.nlargest(3, ('total_amount'))
                
                insights.append({
                    'type': 'geographic_analysis',
                    'message': f"Top donating region: {top_locations.index[0]} (${float(top_locations.iloc[0]['total_amount']):,.2f})",
                    'severity': 'medium',
                    'details': {
                        'plot': location_fig.to_html(full_html=False, include_plotlyjs='cdn'),
                        'metrics': {
                            'location_totals': location_analysis['total_amount'].to_dict(),
                            'location_donors': location_analysis['unique_donors'].to_dict(),
                            'location_averages': location_analysis['avg_donation'].to_dict()
                        },
                        'data': df.copy(),
                        'recommendations': generate_location_recommendations(location_analysis),
                        'figure': location_fig if include_figures else None
                    }
                })
            
        except Exception as e:
            print(f"Error in donor analysis: {str(e)}")
            
    return insights

def generate_engagement_insights(df):
    """Generate enhanced engagement insights."""
    insights = []
    
    if 'donation_date' in df.columns and 'organization_name' in df.columns:
        df['donation_date'] = pd.to_datetime(df['donation_date'])
        
        # Donor Loyalty Analysis
        donor_history = df.groupby('organization_name').agg({
            'donation_date': ['min', 'max', 'count'],
            'donation_amount': ['sum', 'mean']
        })
        
        # Long-term donors (more than 1 year)
        long_term_donors = donor_history[
            (donor_history[('donation_date', 'max')] - donor_history[('donation_date', 'min')]).dt.days > 365
        ]
        
        if not long_term_donors.empty:
            insights.append({
                'type': 'donor_loyalty',
                'message': f"Found {len(long_term_donors)} long-term donors (>1 year engagement)",
                'severity': 'high'
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

def generate_all_donor_insights(df):
    """Generate all donor-related insights for the dataset."""
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
        'insights': generate_all_donor_insights(df)
    }
    return summary

def generate_missing_value_insights(df):
    """Generate insights about missing values with detailed analysis."""
    insights = []
    try:
        # Calculate missing values for each column
        missing_values = df.isnull().sum()
        total_rows = len(df)
        
        # Filter columns with missing values
        columns_with_missing = missing_values[missing_values > 0]
        
        if len(columns_with_missing) > 0:
            for column, missing_count in columns_with_missing.items():
                missing_percentage = (missing_count / total_rows) * 100
                severity = 'high' if missing_percentage > 20 else 'medium' if missing_percentage > 5 else 'low'
                
                # Get rows with missing values
                missing_rows = df[df[column].isnull()].copy()
                
                # Generate missing pattern visualization
                fig = px.scatter(df, 
                               x=df.index,
                               y=[column],
                               title=f'Missing Value Pattern - {column}',
                               template='plotly_white')
                
                insights.append({
                    'type': 'missing_values',
                    'message': f"Column '{column}' has {missing_count:,} missing values ({missing_percentage:.1f}%)",
                    'severity': severity,
                    'details': {
                        'column_name': column,
                        'missing_count': missing_count,
                        'missing_percentage': missing_percentage,
                        'rows_with_missing': missing_rows.to_dict('records'),
                        'plot': fig.to_html(full_html=False),
                        'impact_analysis': {
                            'affected_calculations': ['mean', 'median', 'correlation analysis'],
                            'recommendation': get_missing_value_recommendation(missing_percentage)
                        }
                    }
                })
                
    except Exception as e:
        print(f"Error in missing value analysis: {str(e)}")
    
    return insights

def get_missing_value_recommendation(missing_percentage):
    """Generate recommendations based on percentage of missing values."""
    if missing_percentage > 50:
        return "Consider dropping this column or using advanced imputation techniques"
    elif missing_percentage > 20:
        return "Use multiple imputation or advanced modeling techniques"
    else:
        return "Simple imputation (mean/median) might be sufficient"

def generate_donation_patterns_insights(df):
    """Generate detailed insights about donation patterns with comparative analysis."""
    insights = []
    
    if 'donation_date' in df.columns and 'donation_amount' in df.columns:
        try:
            df['donation_date'] = pd.to_datetime(df['donation_date'])
            
            # Monthly analysis
            monthly_data = df.groupby(pd.Grouper(key='donation_date', freq='M')).agg({
                'donation_amount': ['sum', 'count', 'mean'],
                'organization_name': 'nunique'
            })
            monthly_data.columns = ['total_amount', 'donation_count', 'avg_donation', 'unique_donors']
            
            # Calculate month-over-month changes
            monthly_data['amount_change'] = monthly_data['total_amount'].pct_change() * 100
            monthly_data['donor_change'] = monthly_data['unique_donors'].pct_change() * 100
            
            # Seasonal analysis (group by month across years)
            seasonal_data = df.groupby(df['donation_date'].dt.month).agg({
                'donation_amount': ['sum', 'mean', 'count'],
                'organization_name': 'nunique'
            })
            
            # Generate visualization
            fig1 = px.line(monthly_data, 
                          y=['total_amount', 'unique_donors'],
                          title='Monthly Donation Trends',
                          template='plotly_white')
            
            # Seasonal pattern visualization
            fig2 = px.bar(seasonal_data.reset_index(), 
                         x='donation_date',
                         y=('donation_amount', 'sum'),
                         title='Seasonal Donation Pattern',
                         template='plotly_white')
            
            # Find peak months and trends
            peak_month = seasonal_data[('donation_amount', 'sum')].idxmax()
            low_month = seasonal_data[('donation_amount', 'sum')].idxmin()
            
            # Calculate key metrics
            avg_monthly_growth = monthly_data['amount_change'].mean()
            donation_volatility = monthly_data['amount_change'].std()
            
            insights.append({
                'type': 'donation_patterns',
                'message': f"Average monthly growth: {avg_monthly_growth:.1f}% (Volatility: {donation_volatility:.1f}%)",
                'severity': 'medium' if avg_monthly_growth > 0 else 'high',
                'details': {
                    'monthly_trends': {
                        'data': monthly_data.to_dict(),
                        'plot': fig1.to_html(full_html=False)
                    },
                    'seasonal_patterns': {
                        'data': seasonal_data.to_dict(),
                        'plot': fig2.to_html(full_html=False),
                        'peak_month': peak_month,
                        'low_month': low_month
                    },
                    'key_metrics': {
                        'avg_monthly_growth': avg_monthly_growth,
                        'volatility': donation_volatility,
                        'total_donors': monthly_data['unique_donors'].sum(),
                        'avg_donation_size': monthly_data['avg_donation'].mean()
                    },
                    'recommendations': [
                        f"Focus fundraising efforts in month {peak_month} (historical peak)",
                        f"Develop strategies to boost donations in month {low_month} (historical low)",
                        "Consider implementing donor retention programs during volatile periods",
                        generate_pattern_recommendations(avg_monthly_growth, donation_volatility)
                    ],
                    'data': df.copy()
                }
            })
            
        except Exception as e:
            print(f"Error in donation patterns analysis: {str(e)}")
    
    return insights

def generate_pattern_recommendations(growth_rate, volatility):
    """Generate specific recommendations based on donation patterns."""
    recommendations = []
    
    if growth_rate < 0:
        recommendations.append("Urgent: Implement donor retention strategy to address declining donations")
    elif growth_rate < 5:
        recommendations.append("Consider new donor acquisition campaigns to boost growth")
    else:
        recommendations.append("Maintain current growth strategies and focus on donor retention")
        
    if volatility > 20:
        recommendations.append("High volatility: Develop stabilization strategies")
    elif volatility > 10:
        recommendations.append("Moderate volatility: Consider implementing regular giving programs")
        
    return recommendations

def generate_all_insights(df):
    """Generate all insights for the dataset."""
    try:
        all_insights = []
        
        # Basic data quality insights
        all_insights.extend(generate_missing_value_insights(df))
        
        # Donor-specific insights
        all_insights.extend(generate_donor_insights(df))
        
        all_insights.extend(generate_engagement_insights(df))
        all_insights.extend(generate_retention_insights(df))
        all_insights.extend(generate_statistical_insights(df))
        all_insights.extend(generate_donation_patterns_insights(df))
        
        # Sort insights by severity
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        all_insights.sort(key=lambda x: severity_order[x['severity']])
        
        return all_insights
    except Exception as e:
        print(f"Error generating insights: {str(e)}")
        return []

def generate_overview(df):
    """Generate basic overview of the dataset."""
    try:
        overview = {
            'rows': len(df),
            'columns': df.columns.tolist(),
            'numeric_columns': df.select_dtypes(include=['float64', 'int64']).columns.tolist(),
            'categorical_columns': df.select_dtypes(include=['object']).columns.tolist(),
            'missing_values': df.isnull().sum().to_dict()
        }
        return overview
    except Exception as e:
        print(f"Error generating overview: {str(e)}")
        return {}

def generate_summary_statistics(df):
    """Generate summary statistics for numeric columns."""
    try:
        summary_stats = {}
        
        # For numeric columns
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        for col in numeric_cols:
            stats = df[col].describe()
            summary_stats[col] = {
                'mean': stats['mean'],
                'median': df[col].median(),
                'std': stats['std'],
                'min': stats['min'],
                'max': stats['max'],
                'q1': stats['25%'],
                'q3': stats['75%']
            }
        
        # For categorical columns
        cat_cols = df.select_dtypes(include=['object']).columns
        for col in cat_cols:
            value_counts = df[col].value_counts()
            summary_stats[col] = {
                'unique_values': df[col].nunique(),
                'most_common': value_counts.index[0] if not value_counts.empty else None,
                'most_common_count': value_counts.iloc[0] if not value_counts.empty else 0,
                'missing_values': df[col].isnull().sum()
            }
        
        return summary_stats
    except Exception as e:
        print(f"Error generating summary statistics: {str(e)}")
        return {}

def generate_all_plots(df):
    """Generate all plots for the dataset."""
    try:
        plots = {}
        
        # For numeric columns
        for col in df.select_dtypes(include=['float64', 'int64']).columns:
            # Distribution plot (histogram)
            fig = px.histogram(df, x=col, title=f'Distribution of {col}')
            plots[col] = fig.to_html(full_html=False)
            
            # If it's donation_amount, add additional plots
            if col == 'donation_amount':
                # Box plot
                fig = px.box(df, y=col, title=f'Box Plot of {col}')
                plots[f'{col}_box'] = fig.to_html(full_html=False)
        
        # For categorical columns
        for col in df.select_dtypes(include=['object']).columns:
            # Bar chart of value counts
            value_counts = df[col].value_counts()
            fig = px.bar(x=value_counts.index, 
                        y=value_counts.values,
                        title=f'Distribution of {col}')
            plots[col] = fig.to_html(full_html=False)
        
        return plots
    except Exception as e:
        print(f"Error generating plots: {str(e)}")
        return {}

def calculate_yoy_growth(monthly_amounts):
    """Calculate year-over-year growth rate."""
    try:
        # Get the last 12 months and previous 12 months
        current_year = monthly_amounts[-12:].sum()
        previous_year = monthly_amounts[-24:-12].sum()
        
        if previous_year > 0:
            growth = ((current_year - previous_year) / previous_year) * 100
        return round(growth, 2)
        return 0
    except:
        return 0

def calculate_consistency_score(monthly_counts):
    """Calculate donation consistency score (0-100)."""
    try:
        # Calculate the coefficient of variation
        cv = monthly_counts.std() / monthly_counts.mean() if monthly_counts.mean() > 0 else 0
        
        # Convert to a 0-100 score (lower CV = higher consistency)
        score = max(0, min(100, (1 - cv) * 100))
        return round(score, 2)
    except:
        return 0

def calculate_engagement_level(donation_frequency, consistency_score):
    """Calculate overall engagement level."""
    try:
        # Combine frequency and consistency into an engagement score
        engagement_score = (donation_frequency * 0.6) + (consistency_score * 0.4)
        
        # Convert to categorical level
        if engagement_score >= 80:
            return "Very High"
        elif engagement_score >= 60:
            return "High"
        elif engagement_score >= 40:
            return "Medium"
        elif engagement_score >= 20:
            return "Low"
        else:
            return "Very Low"
    except:
        return "Unknown"

def generate_donor_recommendations(yoy_growth, consistency_score, engagement_level, donation_frequency, avg_donation, total_amount):
    """Generate data-driven donor-specific recommendations."""
    recommendations = []
    
    # Calculate target metrics
    monthly_target = avg_donation * 1.2  # 20% increase target
    annual_target = total_amount * (1 + max(0.1, yoy_growth/100))  # 10% minimum growth
    frequency_target = max(1, donation_frequency * 2)  # Double frequency if less than monthly
    
    # Growth-based recommendations
    if yoy_growth < 0:
        recommendations.extend([
            f"URGENT: Launch recovery plan to regain ${abs(yoy_growth/100 * total_amount):,.2f} in lost giving",
            f"Implement 90-day reactivation campaign targeting ${monthly_target:,.2f} monthly giving",
            f"Create personalized stewardship plan to achieve {abs(yoy_growth)}% growth recovery",
            f"Develop multi-channel outreach to restore {frequency_target:.1f} gifts per month",
            f"Launch matching gift program targeting ${annual_target:,.2f} annual total"
        ])
    elif yoy_growth < 10:
        recommendations.extend([
            f"Design upgrade campaign to increase giving by ${monthly_target - avg_donation:,.2f} per gift",
            f"Implement monthly giving program targeting ${monthly_target:,.2f}",
            f"Create donor journey to achieve {frequency_target:.1f} gifts per month",
            f"Launch leadership giving circle at ${annual_target:,.2f} level",
            f"Develop impact reporting for {int(frequency_target * 12)} annual touchpoints"
        ])
    else:
        recommendations.extend([
            f"Establish major donor program at ${annual_target:,.2f} annual level",
            f"Create legacy society for gifts above ${monthly_target * 12:,.2f}",
            f"Develop strategic partnership targeting ${monthly_target:,.2f} monthly support",
            f"Launch ambassador program to engage {int(frequency_target * 12)} annual donors",
            f"Create multi-year pledge program at ${annual_target:,.2f} level"
        ])
    
    return sorted(set(recommendations), 
                 key=lambda x: (x.startswith('URGENT'),
                              'launch' in x.lower(), 
                              len(x)))[:5]

def generate_segment_recommendations(top_segment, growth_segment, segment_analysis):
    """Generate enhanced segment-specific recommendations."""
    recommendations = [
        f"Launch targeted {top_segment} campaign with segment-specific benefits",
        f"Create {growth_segment} ambassador program with clear objectives",
        "Develop cross-segment upgrade pathway with milestone benefits",
        "Launch segment-specific communication strategy with measurable outcomes",
        "Create multi-channel engagement program with segment targeting"
    ]
    
    # Add enhanced segment-specific recommendations
    if 'Corporate' in segment_analysis.index:
        recommendations.extend([
            "Launch corporate matching program with recognition tiers",
            "Create employee giving program with company matches",
            "Develop corporate partnership program with clear ROI",
            "Launch corporate volunteer program with measurable impact",
            "Create corporate advisory board with strategic input"
        ])
    
    if 'Individual' in segment_analysis.index:
        recommendations.extend([
            "Launch major gifts program with clear pathways",
            "Create legacy giving society with professional advisors",
            "Develop peer-to-peer program with ambassador training",
            "Launch monthly giving club with exclusive benefits",
            "Create donor recognition program with clear levels"
        ])
    
    if 'Foundation' in segment_analysis.index:
        recommendations.extend([
            "Create foundation-specific reporting system with metrics",
            "Launch multi-year funding program with clear outcomes",
            "Develop grant calendar with strategic objectives",
            "Create foundation partnership program with shared goals",
            "Launch impact measurement system with regular updates"
        ])
    
    return sorted(set(recommendations))[:5]

def generate_location_recommendations(location_analysis):
    """Generate data-driven location-based recommendations."""
    # Calculate key metrics
    top_location = location_analysis['total_amount'].idxmax()
    top_amount = float(location_analysis['total_amount'].max())
    growth_location = location_analysis['unique_donors'].idxmax()
    growth_donors = int(location_analysis['unique_donors'].max())
    potential_location = location_analysis['avg_donation'].idxmax()
    potential_amount = float(location_analysis['avg_donation'].max())
    
    # Calculate growth opportunities
    location_avg = float(location_analysis['total_amount'].mean())
    growth_potential = ((top_amount - location_avg) / location_avg) * 100
    donor_potential = int(growth_donors * 0.2)  # Target 20% growth
    
    recommendations = [
        f"Launch major donor program in {top_location} targeting ${top_amount:,.2f} annual goal",
        
        f"Develop {growth_location} expansion strategy to recruit {donor_potential} new donors",
        
        f"Create high-impact donor strategy for {potential_location} to reach ${potential_amount:,.2f} average gift",
        
        f"Implement multi-region challenge grant targeting ${location_avg:,.2f} per region",
        
        f"Launch regional ambassador program in {growth_location} to engage {growth_donors} donors"
    ]
    
    # Add data-driven conditional recommendations
    if growth_potential > 50:
        recommendations.append(
            f"URGENT: Address {growth_potential:.1f}% giving gap between {top_location} and regional average"
        )
    
    if location_analysis['unique_donors'].std() > location_analysis['unique_donors'].mean() * 0.5:
        recommendations.append(
            f"Balance regional donor base: Current variance {int(location_analysis['unique_donors'].std())} donors"
        )
    
    return sorted(set(recommendations), 
                 key=lambda x: (x.startswith('URGENT'),
                              'launch' in x.lower(), 
                              len(x)))[:5]

def generate_category_recommendations(category_analysis):
    """Generate data-driven category-specific recommendations."""
    # Calculate key metrics
    top_category = category_analysis['total_amount'].idxmax()
    top_amount = float(category_analysis['total_amount'].max())
    growth_category = category_analysis['count'].idxmax()
    category_count = int(category_analysis['count'].max())
    avg_donation = float(category_analysis['total_amount'].mean())
    
    # Calculate performance metrics
    category_variance = float(category_analysis['total_amount'].std())
    growth_opportunity = ((top_amount - avg_donation) / avg_donation) * 100
    retention_target = int(category_count * 0.8)  # Target 80% retention
    
    recommendations = [
        f"Launch targeted {top_category} campaign to reach ${top_amount:,.2f} goal",
        
        f"Create {growth_category} retention program targeting {retention_target} donors",
        
        f"Develop upgrade strategy to increase average gift from ${avg_donation:,.2f} to ${avg_donation*1.2:,.2f}",
        
        f"Implement cross-category challenge to reduce ${category_variance:,.2f} variance",
        
        f"Launch donor pathway program targeting {int(category_count*0.2)} new {growth_category} donors"
    ]
    
    # Add data-driven conditional recommendations
    if growth_opportunity > 30:
        recommendations.append(
            f"URGENT: Address {growth_opportunity:.1f}% giving gap in {top_category} category"
        )
    
    if category_analysis['count'].std() > category_analysis['count'].mean() * 0.3:
        recommendations.append(
            f"Stabilize category performance: Current variance {int(category_analysis['count'].std())} donors"
        )
    
    return sorted(set(recommendations), 
                 key=lambda x: (x.startswith('URGENT'),
                              'launch' in x.lower(), 
                              len(x)))[:5]