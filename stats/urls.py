from django.urls import path
from .views import (analyze_csv, get_unique_values, filter_plot, 
                   apply_global_filters, reset_filters, get_column_types, get_selected_plots, get_column_values, 
                   compare_columns, get_column_type, get_column_types_compare)

from .deepseek_api import get_dataset_insights, analysis_chat_api
from form_builder.views import ListForms, FormDetailView, CreateFormView, CreateRecordView, DeleteRecordView, UpdateRecordView, FormsActionView
from .views import AnalysisView, SaveAnalysisView, DeleteAnalysisView, analyze_form_view, home

urlpatterns = [
    path('analyze/', analyze_csv, name='analyze_csv'),
    path('get_unique_values/', get_unique_values, name='get_unique_values'),
    path('filter_plot/', filter_plot, name='filter_plot'),
    path('apply_global_filters/', apply_global_filters, name='apply_global_filters'),
    path('reset_filters/', reset_filters, name='reset_filters'),
    path('get_column_types/', get_column_types, name='get_column_types'),
    path('get_column_type/', get_column_type, name='get_column_type'),
    path('get_selected_plots/', get_selected_plots, name='get_selected_plots'),
    path('get_column_values/', get_column_values, name='get_column_values'),
    path('compare_columns/', compare_columns, name='compare_columns'),
    path('get_dataset_insights/', get_dataset_insights, name='get_dataset_insights'),
    path('analysis_chat_api/', analysis_chat_api, name='analysis_chat_api'),
    path('get_column_types_compare/', get_column_types_compare, name='get_column_types_compare'),


    #views for analysis page
    path('forms/', ListForms.as_view(), name='forms'),
    path('forms/<int:pk>/', FormDetailView.as_view(), name='form_detail'),
    path('forms/create/', CreateFormView.as_view(), name='create_form'),
    path('forms/<int:pk>/add-record/', CreateRecordView.as_view(), name='add_record'),
    path('forms/<int:pk>/delete-record/', DeleteRecordView.as_view(), name='delete_record'),
    path('forms/<int:pk>/update-record/', UpdateRecordView.as_view(), name='update_record'),
    path('forms/action/', FormsActionView.as_view(), name='forms_action'),
    
    # New URL for analysis
    path('', AnalysisView.as_view(), name='analysis'),
    path('stats/save/', SaveAnalysisView.as_view(), name='save_analysis'),
    path('stats/delete/<int:pk>/', DeleteAnalysisView.as_view(), name='delete_analysis'),
    path('stats/form-analysis/', analyze_form_view, name='analyze_form'),
    path('upload/', home, name='upload_file'),
    path('upload_file2/', home, name='upload_file2'),
]
