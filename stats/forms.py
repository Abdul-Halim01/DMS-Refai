# forms.py
from django import forms

class CsvUploadForm(forms.Form):
    csv_file = forms.FileField(
        label='Select CSV File',
        help_text='Max file size: 10MB. Only CSV files are accepted.',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        })
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