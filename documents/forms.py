# documents/forms.py

from django import forms
from .models import Document, DocumentGroup


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['file']


class DocumentEditForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['group','file','title','is_private','language','comment','description']

# class DocumentSelectionForm(forms.ModelForm):
#     class Meta:
#         model = Document
#         fields = ['selected']

# class DocumentForm(forms.ModelForm):
#     class Meta:
#         model = Document
#         fields = ['title', 'content']



class DocumentGroupForm(forms.ModelForm):
    class Meta:
        model = DocumentGroup
        fields = ['name']

class DocumentRequestForm(forms.Form):
    recipient_email = forms.EmailField(label='البريد الإلكتروني للمستلم')
    document_id = forms.IntegerField(widget=forms.HiddenInput())