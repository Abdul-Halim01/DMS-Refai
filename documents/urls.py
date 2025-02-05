# documents/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.DocumentPageView.as_view(), name='documents'),
    
    path('groups/' , views.ListGroupsView.as_view() , name="groups"),
    path('create-group/' , views.CreateGroupView.as_view() , name="create_group"),
    path('update-group/' , views.UpdateGroupView.as_view() , name="update_group"),
    path('delete-group/<int:pk>' , views.DeleteGroupView.as_view() , name="delete_group"),

    path('list/', views.DocumentListView.as_view(), name='document_list'),
    path('upload/', views.UploadDocumentView.as_view(), name='upload_document'),
    path('<int:pk>/delete/', views.DeleteDocumentView.as_view(), name='delete_document'),
    path('<int:document_id>/download/', views.DownloadDocumentView.as_view(), name='download_document'),
    path('<int:pk>/edit/', views.DocumentEditView.as_view(), name='document_edit'),
    path('perform-action/', views.PerformActionView.as_view(), name='documents_action'),
]

# path('describe/<int:document_id>/', views.DocumentListView.describe_image, name='describe_image'),
