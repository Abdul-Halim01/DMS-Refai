from django.urls import path
from . import views

urlpatterns = [
    path('', views.TaskList.as_view(), name='tasks-list'),
    path('kanban/', views.TaskKanban.as_view(), name='task-kanban'),
    path('create/', views.TaskCreate.as_view(), name='task-create'),
    path('action/', views.TaskAction.as_view(), name='tasks-action'),
    path('<int:pk>/update/', views.TaskUpdate.as_view(), name='task-update'),
    path('<int:pk>/delete/', views.TaskDelete.as_view(), name='task-delete'),
    path('<int:pk>/update-status/', views.TaskStatusUpdate.as_view(), name='task-update-status'),
]

