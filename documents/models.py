# documents/models.py

from django.db import models
from django.contrib.auth import get_user_model
# from django.utils.text import humanize
from utility.types import *


User = get_user_model()

class Document(models.Model):
    group = models.ForeignKey('DocumentGroup' , on_delete=models.SET_NULL , null=True)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    permissin_level = models.CharField(max_length=10, choices=PermissionLevel, default='public')
    file_type = models.CharField(max_length=10, choices=FileType)
    is_private = models.BooleanField(default=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE , null=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(null=True,blank=True)
    description = models.TextField(blank=True, null=True)
    language = models.CharField(max_length=2, choices=Language, default='en')
    size = models.IntegerField(default=0) # size in MB

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Auto-detect file type
        if self.file.name.endswith(('jpg', 'jpeg', 'png', 'PNG','gif')):
            self.file_type = 'image'
        elif self.file.name.endswith(('mp4', 'mkv', 'avi')):
            self.file_type = 'video'
        elif self.file.name.endswith(('mp3', 'wav', 'ogg' , 'm4a', 'acc','aac')):
            self.file_type = 'audio'
        elif self.file.name.endswith(('csv', 'xlsx', 'xls')):
            self.file_type = 'document_Excel'
        elif self.file.name.endswith(('ppt', 'pptx')):
            self.file_type = 'document_PowePoint'
        elif self.file.name.endswith(('doc', 'docx')):
                self.file_type = 'document_word'
        elif self.file.name.endswith(('pdf')):
            self.file_type = 'document_Pdf'
        elif self.file.name.endswith(('txt')):
                self.file_type = 'document_txt'
        else:
            self.file_type = 'unknown_document'  # Default to document if unknown
            
        # Auto set the file size in MB
        if self.file:
            self.size = self.file.size / (1024 * 1024)  # Convert bytes to MB
            
        super().save(*args, **kwargs)


    def has_access(self, user):
        # Check user permissions here 
        if user.is_superuser or self.uploaded_by == user:
            return True
        return False
    
    def is_gif(self):
        filename = self.file.name  # احصل على اسم الملف
        return filename.endswith('.gif')



class DocumentGroup(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name





