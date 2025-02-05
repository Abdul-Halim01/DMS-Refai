# pr_tool/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('salaries/' , views.ListSalariesView.as_view() , name="salary_list"),
    path('create-salary/' , views.CreateSalaryView.as_view() , name="create_salary"),
    path('salary-info/<str:pk>' , views.UpdateSalaryView.as_view() , name="salary_info"),
    path('delete-salary/<str:pk>' , views.DeleteSalaryView.as_view() , name="delete_salary"),
]
