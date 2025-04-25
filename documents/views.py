from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponse, HttpResponseForbidden
from django.urls import reverse_lazy
from .models import Document, DocumentGroup
from .forms import DocumentUploadForm, DocumentEditForm
import mimetypes
import json
from django.views import generic
from utility.mixins import documents_criteria_add_perm, documents_criteria_edit_perm, documents_criteria_delete_perm



@method_decorator(documents_criteria_edit_perm, name='dispatch')
class DocumentPageView(View):
    def get(self,request):
        total_documents = Document.objects.count()
        total_groups = DocumentGroup.objects.count()
        return render(request , 'documents/documents.html', {'total_documents': total_documents, 'total_groups': total_groups})



@method_decorator(documents_criteria_edit_perm, name='dispatch')
class ListGroupsView(generic.ListView):
    model = DocumentGroup
    template_name = 'group/groups.html'
    context_object_name = 'groups'


@method_decorator(documents_criteria_delete_perm, name='dispatch')
class DeleteGroupView(generic.DeleteView):
    model = DocumentGroup
    template_name = 'group/delete_group.html'
    success_url = '/documents/groups/'


@method_decorator(documents_criteria_add_perm, name='dispatch')
class CreateGroupView(generic.CreateView):
    model = DocumentGroup
    fields = ['name','description']
    template_name = 'group/create_group.html'
    success_url = '/documents/groups/'


@method_decorator(documents_criteria_edit_perm, name='dispatch')
class UpdateGroupView(generic.UpdateView):
    model = DocumentGroup
    fields = ['name']
    template_name = 'group/group_form.html'
    success_url = '/documents/groups/'


@method_decorator(documents_criteria_delete_perm, name='dispatch')  
class GroupActionView(generic.View):
    def post(self,request):
        selected_ids = json.loads(request.POST.get('selected_ids'))
        group = DocumentGroup.objects.filter(id__in=selected_ids)
        if request.POST.get('action') == 'delete':
            group.delete()
        return redirect('/documents/groups/')



@method_decorator(documents_criteria_edit_perm, name='dispatch')
class DocumentListView(generic.ListView):
    model = Document
    paginate_by = 10
    fields = ['id' ,'group', 'file' , 'type' , 'uploaded_by' , 'upload_date']
    template_name = 'documents/documents_list.html'
    context_object_name = 'documents'



@method_decorator(documents_criteria_add_perm, name='dispatch')
class UploadDocumentView(View):
    def get(self, request):
        form = DocumentUploadForm()
        return render(request, 'documents/upload.html', {'form': form})
    
    def post(self, request):
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save(commit=False)
            form.instance.uploaded_by = request.user
            form.save()
            return redirect('document_list')
        return render(request, 'documents/upload.html', {'form': form})
    


@method_decorator(documents_criteria_edit_perm, name='dispatch')
class DocumentEditView(generic.UpdateView):
    model = Document
    form_class = DocumentEditForm
    template_name = 'documents/document_edit.html'
    success_url = reverse_lazy('document_list')



@method_decorator(documents_criteria_delete_perm, name='dispatch')
class DeleteDocumentView(generic.DeleteView):
    model = Document
    template_name = 'documents/delete_document.html'
    success_url = reverse_lazy('document_list')
    
    def dispatch(self, request, *args, **kwargs):
        document = self.get_object()
        if document.uploaded_by != request.user and not request.user.is_staff:
            return HttpResponseForbidden("You don't have permission to delete this document")
        return super().dispatch(request, *args, **kwargs)




@method_decorator(documents_criteria_edit_perm, name='dispatch')
class DownloadDocumentView(View):
    def get(self, request, document_id):
        document = get_object_or_404(Document, id=document_id)
        if not document.has_access(request.user):
            return HttpResponseForbidden('You do not have permission to download this document.')
        mimetype, _ = mimetypes.guess_type(document.file.path)
        response = HttpResponse(document.file, content_type=mimetype)
        response['Content-Disposition'] = f'attachment; filename="{document.title}.{document.file.url.split(".")[-1]}"'
        return response









@method_decorator(documents_criteria_edit_perm, name='dispatch')
class PerformActionView(View):
    def post(self,request):

        selected_ids = json.loads(request.POST.get('selected_ids'))
        documents = Document.objects.filter(id__in=selected_ids)

        # perform DB operation depending on the chosen action
        if request.POST.get('action') == 'delete':
            documents.delete()
        return redirect('document_list')



