from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render
from documents.models import Document, DocumentGroup
from users.models import User
from form_builder.models import CustomForm
from tasks.models import Task
from hr_tool.models import Employee


@method_decorator(login_required, name='dispatch')
class DashboardView(View):
    def get(self,request):
        total_documents = Document.objects.count()
        total_groups = DocumentGroup.objects.count()
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        total_forms = CustomForm.objects.count()
        total_tasks = Task.objects.count()
        total_finished_tasks = Task.objects.filter(status='finished').count()
        total_employees = Employee.objects.count()
        return render(request , 'dashboard.html', {'total_documents': total_documents, 'total_groups': total_groups, 'total_users': total_users, 'active_users': active_users, 'total_forms': total_forms, 'total_tasks': total_tasks, 'total_finished_tasks': total_finished_tasks, 'total_employees': total_employees})


