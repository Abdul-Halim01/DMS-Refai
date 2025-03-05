from django.urls import path
from . import views


urlpatterns = [
    path('', views.CreateFormView.as_view(), name='form_builder'),
    path('forms/add', views.CreateFormView.as_view(), name='add_form'),
    path('forms/', views.ListForms.as_view(), name='form_list'),
    path('forms/<int:pk>/', views.FormDetailView.as_view(), name='form_detail'),
]