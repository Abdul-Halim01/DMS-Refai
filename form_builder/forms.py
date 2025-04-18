# in here we will find a way to clean the data before inserting it in the DB
from django import forms    


class AddRecordForm(forms.Form):
    record = forms.CharField(widget=forms.Textarea)

