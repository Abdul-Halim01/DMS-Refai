from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
import json
from django.shortcuts import redirect
from .cursor_db import add_form, get_form, add_record , remove_record , update_record, get_form_fields
from django.views import View
from django.utils.decorators import method_decorator
from .models import *
from django.views import generic

class ListForms(generic.ListView):
    model = CustomForm
    context_object_name = 'forms'
    template_name = "form_builder/forms.html"

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


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CreateFormView(View):
    def get(self, request):
        return render(request, 'form_builder/create_form.html')
        
    def post(self, request):
        try:
            data = json.loads(request.body)
            form_name = data.get('form_name')
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
            result = add_form(form_name, fields)
            
            if result['success']:
                return JsonResponse({
                    'success': True,
                    'redirect_url': f'/forms/{result["form_id"]}'
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
                



class CreateRecordView(View):
    def get(self, request, pk):
        form_name = CustomForm.objects.get(id=pk).name
        return render(request, 'form_builder/add_record.html')
    
    def post(self, request, pk):
        data = request.body
        form_name = CustomForm.objects.get(id=pk).name
        records = data.get('records', [])
        add_record(form_name, records)

        return redirect(f'/forms/{pk}')
    

class DeleteRecordView(View):
    def get(self, request, pk):
        form_name = CustomForm.objects.get(id=pk).name
        return render(request, 'form_builder/delete_record.html')



class UpdateRecordView(View):
    def get(self, request, pk):
        form_name = CustomForm.objects.get(id=pk).name
        return render(request, 'form_builder/update_record.html')


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
        