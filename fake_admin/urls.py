# fake_admin/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.fake_admin_view, name='fake_admin'),
]
