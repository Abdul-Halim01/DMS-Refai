from django.urls import path
from .views import home, analyze_csv, get_unique_values, filter_plot, compare_plot, apply_global_filters, reset_filters, get_column_types, generate_report 


urlpatterns = [
    path('', home, name='stats'),
    path('analyze/', analyze_csv, name='analyze_csv'),
    path('get_unique_values/', get_unique_values, name='get_unique_values'),
    path('filter_plot/', filter_plot, name='filter_plot'),
    path('compare_plot/', compare_plot, name='compare_plot'),
    path('apply_global_filters/', apply_global_filters, name='apply_global_filters'),
    path('reset_filters/', reset_filters, name='reset_filters'),
    path('get_column_types/', get_column_types, name='get_column_types'),
    path('generate-report/', generate_report, name='generate_report'),
]
