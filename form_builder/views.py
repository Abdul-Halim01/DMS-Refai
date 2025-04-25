from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
import json
from django.shortcuts import redirect
from .cursor_db import add_form, get_form, add_record, remove_record, update_record, get_form_fields, insert_record_with_fields
from django.views import View
from django.utils.decorators import method_decorator
from .models import *
from django.views import generic
from .form_utils import create_dynamic_form
from django.db import connection
from utility.mixins import form_criteria_add_perm, form_criteria_edit_perm, form_criteria_delete_perm


@method_decorator(form_criteria_edit_perm, name='dispatch')
class ListForms(generic.ListView):
    model = CustomForm
    context_object_name = 'forms'
    template_name = "form_builder/forms.html"

@method_decorator(form_criteria_edit_perm, name='dispatch')
class FormDetailView(View):
    def get(self, request, pk):
        try:
            form = CustomForm.objects.get(id=pk)
            form_name = form.name
            form_data = get_form(form_name)
            form_fields = get_form_fields(form_name)
            
            # Transform the raw data tuples into dictionaries
            records = []
            for record in form_data:
                record_dict = {
                    'id': record[0],
                    'created_at': record[1],
                }
                # Add the dynamic field values
                for i, field in enumerate(form_fields, start=2):  # Start at index 2 since id and created_at are first
                    if i < len(record):
                        record_dict[field] = record[i]
                records.append(record_dict)
            context = {
                'form_id': form.id,
                'records': records,
                'fields': ['ID', 'Created At'] + form_fields  # Include default columns
            }
            return render(request, 'form_builder/form_detail.html', context)
        except CustomForm.DoesNotExist:
            return redirect('form_builder')  # Redirect to forms list if form not found


@method_decorator(form_criteria_add_perm, name='dispatch')
class CreateFormView(View):
    def get(self, request):
        return render(request, 'form_builder/create_form.html')
        
    def post(self, request):
        try:
            data = json.loads(request.body)
            form_name = data.get('form_name')
            form_language = data.get('form_language')
            fields = data.get('fields', [])
            
            if not form_name:
                return JsonResponse({
                    'success': False,
                    'error': 'Form name is required'
                })
                
            if not fields:
                return JsonResponse({
                    'success': False,
                    'error': 'At least one field is required'
                })
            
            # Create the form and its table
            result = add_form(form_name, fields, form_language)
            
            if result['success']:
                return JsonResponse({
                    'success': True,
                    'redirect_url': f'/form-builder/forms/{result["form_id"]}'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Failed to create form')
                })
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
                

@method_decorator(form_criteria_add_perm, name='dispatch')
class CreateRecordView(View):
    def get(self, request, pk):
        try:
            custom_form = CustomForm.objects.get(id=pk)
            form_name = custom_form.name
            
            # Create a dynamic form based on table structure
            DynamicForm = create_dynamic_form(form_name)
            form = DynamicForm()
            
            context = {
                'form': form,
                'form_name': form_name,
                'form_id': pk
            }
            
            return render(request, 'form_builder/add_record.html', context)
        except CustomForm.DoesNotExist:
            return redirect('form_builder')
    
    def post(self, request, pk):
        try:
            custom_form = CustomForm.objects.get(id=pk)
            form_name = custom_form.name
            
            # Create dynamic form and validate data
            DynamicForm = create_dynamic_form(form_name)
            form = DynamicForm(request.POST)
            
            if form.is_valid():
                # Extract validated data
                cleaned_data = form.cleaned_data
                
                # Get fields and values for insertion
                fields = list(cleaned_data.keys())
                values = [cleaned_data[field] for field in fields]
                
                # Insert the record using our utility function
                insert_record_with_fields(form_name, fields, values)
                
                return redirect(f'/form-builder/forms/{pk}/')
            else:
                # If form is invalid, show errors
                context = {
                    'form': form,
                    'form_name': form_name,
                    'form_id': pk
                }
                return render(request, 'form_builder/add_record.html', context)
                
        except CustomForm.DoesNotExist:
            return redirect('form_builder')
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


@method_decorator(form_criteria_delete_perm, name='dispatch')
class DeleteRecordView(View):
    def get(self, request, pk, record_id):
        form_name = CustomForm.objects.get(id=pk).name
        remove_record(form_name, record_id)
        return redirect(f'/form-builder/forms/{pk}/')


@method_decorator(form_criteria_edit_perm, name='dispatch')
class UpdateRecordView(View):
    def get(self, request, pk):
        form_name = CustomForm.objects.get(id=pk).name
        return render(request, 'form_builder/update_record.html')


@method_decorator(form_criteria_delete_perm, name='dispatch')
class FormsActionView(View):
    def post(self, request):
        data = json.loads(request.body)
        action = data.get('action')
        selected_ids = data.get('selected_ids', [])
        
        if action == 'delete':
            CustomForm.objects.filter(id__in=selected_ids).delete()
            return JsonResponse({
                'success': True,
                'message': 'Forms deleted successfully'
            })
        


@method_decorator(form_criteria_edit_perm, name='dispatch')
class ExportFormPdfView(View):
    def get(self, request, pk):
        try:
            form = CustomForm.objects.get(id=pk)
            form_name = form.name
            from utility.export_form_pdf import export_form_pdf
            return export_form_pdf(form_name)
        except CustomForm.DoesNotExist:
            return redirect('form_builder')
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

@method_decorator(form_criteria_edit_perm, name='dispatch')
class ExportFormExcelView(View):
    def get(self, request, pk):
        try:
            form = CustomForm.objects.get(id=pk)
            form_name = form.name
            from utility.export_form_excel import export_form_excel
            return export_form_excel(form_name)
        except CustomForm.DoesNotExist:
            return redirect('form_builder')
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
