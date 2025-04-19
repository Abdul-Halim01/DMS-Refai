from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView , DeleteView , CreateView , UpdateView
from .models import Salary
from django.db.models.query import QuerySet
from typing import Any

# Create your views here.


@method_decorator(login_required, name='dispatch')
class CreateSalaryView(CreateView):
    model = Salary
    fields = '__all__'
    template_name = 'hr_tool/salary/create_salary.html'
    success_url = '/hr/salaries/'


@method_decorator(login_required, name='dispatch')
class ListSalariesView(ListView):
    model = Salary
    template_name = 'hr_tool/salary/salaries.html'
    context_object_name = 'salaries'
    paginate_by = 10

    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset()
        q = self.request.GET.get('q' , None)
        if q:
            queryset = queryset.filter(
                employee__username__startswith = q
            )
        return queryset


@method_decorator(login_required, name='dispatch')
class UpdateSalaryView(UpdateView):
    model = Salary
    fields = '__all__'
    template_name = 'hr_tool/salary/salary_info.html'
    success_url = '/hr/salaries/'


@method_decorator(login_required, name='dispatch')
class DeleteSalaryView(DeleteView):
    model = Salary
    template_name = 'hr_tool/salary/delete_salary.html'
    context_object_name = 'salary'
    success_url = '/hr/salaries/'
