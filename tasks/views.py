from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from .models import Task
from django.db.models import QuerySet
from typing import Any
from django.shortcuts import render
from django.views import View
from django.contrib.auth.decorators import user_passes_test
import json
from django.utils.decorators import method_decorator



# Create your views here.




class TaskList(ListView):
    model = Task
    template_name = 'tasks/tasks.html'
    context_object_name = 'tasks'
    paginate_by = 5

    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset()
        q = self.request.GET.get('q' , None)
        if q:
            queryset = queryset.filter(
                title__startswith = q
            )
        return queryset


class TaskKanban(View):
    def get(self, request):
        tasks = Task.objects.all()
        context = {
            'tasks': tasks
        }
        return render(request, 'tasks/tasks_kanban.html', context)

class TaskCreate(CreateView):
    model = Task
    template_name = 'tasks/add_task.html'
    fields = ['title', 'description','user' ,'priority', 'status']
    success_url = reverse_lazy('tasks-list')

class TaskUpdate(UpdateView):
    model = Task
    template_name = 'tasks/task_info.html'
    fields = ['title', 'description', 'priority', 'status']
    success_url = reverse_lazy('tasks-list')

class TaskDelete(DeleteView):
    model = Task
    success_url = reverse_lazy('tasks-list') 


class TaskAction(DeleteView): # override
    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    def post(self,request):
        selected_ids = json.loads(request.POST.get('selected_ids'))
        tasks = Task.objects.filter(id__in=selected_ids)

        # perform DB operation depending on the chosen action
        if request.POST.get('action') == 'delete':
            tasks.delete()
        return redirect('tasks-list')
