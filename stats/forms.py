# forms.py
from django import forms
from django.core.validators import FileExtensionValidator

class CsvUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="CSV File",
        help_text="Upload a CSV file for analysis",
        validators=[FileExtensionValidator(allowed_extensions=['csv'])]
    )
    report_name = forms.CharField(
        required=False,
        label="Report Name",
        max_length=100
    )

class AnalysisConfigForm(forms.Form):
    target_column = forms.ChoiceField(
        required=False,
        help_text='Select target column for feature importance analysis'
    )
    
    correlation_threshold = forms.FloatField(
        initial=0.8,
        min_value=0,
        max_value=1,
        help_text='Threshold for correlation analysis'
    )
    
    outlier_threshold = forms.FloatField(
        initial=1.5,
        help_text='IQR multiplier for outlier detection'
    )
    
    def __init__(self, *args, columns=None, **kwargs):
        super().__init__(*args, **kwargs)
        if columns:
            self.fields['target_column'].choices = [('', '----')] + [(col, col) for col in columns]