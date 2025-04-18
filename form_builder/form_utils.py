from django import forms
from .cursor_db import get_form_fields


def create_dynamic_form(form_name):
    """Creates a dynamic Django form based on the table structure."""
    fields = get_form_fields(form_name)
    
    # Create a form class dynamically
    form_fields = {}
    
    for field_name in fields:
        # Here we're making assumptions about field types based on naming conventions
        # In a production app, you might want to store field types in metadata
        if 'email' in field_name:
            form_fields[field_name] = forms.EmailField(label=field_name.replace('_', ' ').title())
        elif 'date' in field_name:
            form_fields[field_name] = forms.DateField(
                label=field_name.replace('_', ' ').title(),
                widget=forms.DateInput(attrs={'type': 'date'})
            )
        elif 'time' in field_name:
            form_fields[field_name] = forms.TimeField(
                label=field_name.replace('_', ' ').title(),
                widget=forms.TimeInput(attrs={'type': 'time'})
            )
        elif 'number' in field_name or field_name.endswith('_id'):
            form_fields[field_name] = forms.IntegerField(label=field_name.replace('_', ' ').title())
        elif 'boolean' in field_name or field_name.startswith('is_'):
            form_fields[field_name] = forms.BooleanField(
                label=field_name.replace('_', ' ').title(),
                required=False
            )
        elif 'description' in field_name or 'text' in field_name:
            form_fields[field_name] = forms.CharField(
                label=field_name.replace('_', ' ').title(),
                widget=forms.Textarea
            )
        else:
            form_fields[field_name] = forms.CharField(
                label=field_name.replace('_', ' ').title(),
                max_length=255
            )
    
    # Create the form class dynamically
    DynamicForm = type(
        f"{form_name.title().replace('_', '')}Form",
        (forms.Form,),
        form_fields
    )
    
    return DynamicForm


def create_dynamic_model_form(form_name, model_class):
    """Creates a dynamic Django ModelForm for a given model class."""
    fields = get_form_fields(form_name)
    
    # Create a ModelForm class dynamically
    class Meta:
        model = model_class
        fields = fields
    
    form_attrs = {
        'Meta': Meta,
    }
    
    DynamicModelForm = type(
        f"{form_name.title().replace('_', '')}ModelForm",
        (forms.ModelForm,),
        form_attrs
    )
    
    return DynamicModelForm


def get_field_type_from_name(field_name):
    """Infers a reasonable field type based on the field name."""
    if 'email' in field_name:
        return 'email'
    elif 'date' in field_name:
        return 'date'
    elif 'time' in field_name:
        return 'time'
    elif 'number' in field_name or field_name.endswith('_id'):
        return 'number'
    elif 'boolean' in field_name or field_name.startswith('is_'):
        return 'checkbox'
    elif 'description' in field_name or 'text' in field_name:
        return 'textarea'
    else:
        return 'text'  # Default to text 