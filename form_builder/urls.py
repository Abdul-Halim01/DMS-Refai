from django.urls import path
from . import views


urlpatterns = [
    path('', views.ListForms.as_view(), name='form_builder'),
    path('forms/add', views.CreateFormView.as_view(), name='add_form'),
    path('forms/<int:pk>/add', views.CreateRecordView.as_view(), name='add_record'),
    path('forms/<int:pk>/', views.FormDetailView.as_view(), name='form_detail'),
    path('forms/action', views.FormsActionView.as_view(), name='forms_action'),
]