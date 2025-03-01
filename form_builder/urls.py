from django.urls import path
from . import views


urlpatterns = [
    path('', views.CreateFormView.as_view(), name='form_builder'),
    path('forms/add', views.AddFormView.as_view(), name='add_form'),
    # path('forms/', views.form_list_view, name='form_list'),
]