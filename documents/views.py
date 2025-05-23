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


login_required_m =  method_decorator(login_required(login_url='login') , name="dispatch")



@login_required_m
class DocumentPageView(View):
    def get(self,request):
        total_documents = Document.objects.count()
        total_groups = DocumentGroup.objects.count()
        return render(request , 'documents/documents.html', {'total_documents': total_documents, 'total_groups': total_groups})



@login_required_m
class ListGroupsView(generic.ListView):
    model = DocumentGroup
    template_name = 'group/groups.html'
    context_object_name = 'groups'


@login_required_m
class DeleteGroupView(generic.DeleteView):
    model = DocumentGroup
    template_name = 'group/delete_group.html'
    success_url = '/documents/groups/'


class CreateGroupView(generic.CreateView):
    model = DocumentGroup
    fields = ['name','description']
    template_name = 'group/create_group.html'
    success_url = '/documents/groups/'


class UpdateGroupView(generic.UpdateView):
    model = DocumentGroup
    fields = ['name']
    template_name = 'group/group_form.html'
    success_url = '/documents/groups/'



class GroupActionView(generic.View):
    def post(self,request):
        selected_ids = json.loads(request.POST.get('selected_ids'))
        group = DocumentGroup.objects.filter(id__in=selected_ids)
        if request.POST.get('action') == 'delete':
            group.delete()
        return redirect('/documents/groups/')



@login_required_m
class DocumentListView(generic.ListView):
    model = Document
    paginate_by = 10
    fields = ['id' ,'group', 'file' , 'type' , 'uploaded_by' , 'upload_date']
    template_name = 'documents/documents_list.html'
    context_object_name = 'documents'



@login_required_m
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
    


@login_required_m
class DocumentEditView(generic.UpdateView):
    model = Document
    form_class = DocumentEditForm
    template_name = 'documents/document_edit.html'
    success_url = reverse_lazy('document_list')



@login_required_m
class DeleteDocumentView(generic.DeleteView):
    model = Document
    template_name = 'documents/delete_document.html'
    success_url = reverse_lazy('document_list')
    
    def dispatch(self, request, *args, **kwargs):
        document = self.get_object()
        if document.uploaded_by != request.user and not request.user.is_staff:
            return HttpResponseForbidden("You don't have permission to delete this document")
        return super().dispatch(request, *args, **kwargs)




class DownloadDocumentView(View):
    def get(self, request, document_id):
        document = get_object_or_404(Document, id=document_id)
        if not document.has_access(request.user):
            return HttpResponseForbidden('You do not have permission to download this document.')
        mimetype, _ = mimetypes.guess_type(document.file.path)
        response = HttpResponse(document.file, content_type=mimetype)
        response['Content-Disposition'] = f'attachment; filename="{document.title}.{document.file.url.split(".")[-1]}"'
        return response









# @login_required_m
class PerformActionView(View):
    def post(self,request):

        selected_ids = json.loads(request.POST.get('selected_ids'))
        documents = Document.objects.filter(id__in=selected_ids)

        # perform DB operation depending on the chosen action
        if request.POST.get('action') == 'delete':
            documents.delete()
        return redirect('document_list')



