from django.db import models
from django.conf import settings
from form_builder.models import CustomForm
# Create your models here.
class Dataset(models.Model):
    """Model to store uploaded datasets"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(upload_to='datasets/')
    columns = models.JSONField(default=dict)   # Store column names and types
    
    def __str__(self):
        return self.name

class Analysis(models.Model):
    """Model to store analysis configurations"""
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='analyses')
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    filters = models.JSONField(default=dict)  # Store filter configurations
    comparisons = models.JSONField(default=dict)  # Store comparison configurations
    
    def __str__(self):
        return f"{self.name} - {self.dataset.name}"



class AnalysisReport(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    source_type = models.CharField(max_length=50)  # 'file' or 'form'
    source_name = models.CharField(max_length=255)
    form = models.ForeignKey(CustomForm, null=True, blank=True, on_delete=models.CASCADE)
    analysis_data = models.TextField()  # JSON string of analysis results
    
    def __str__(self):
        return self.name
    

class FormEntry(models.Model):
    form = models.ForeignKey(CustomForm, related_name='entries', on_delete=models.CASCADE)
    data = models.JSONField()  # Stores row data as JSON
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Entry {self.id} - {self.form.name}"