from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
import json
from .cursor_db import create_form, get_form
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
        # try:
        form_name = CustomForm.objects.get(id=pk).name
        form = get_form(form_name)
        return render(request, 'form_builder/form_detail.html')
        # except CustomForm.DoesNotExist:
        #     pass


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
            result = create_form(form_name, fields)
            
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
        return render(request, 'form_builder/create_record.html')




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
        