from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
import json
from .cursor_db import create_form
from django.views import View
from django.utils.decorators import method_decorator

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
                    'redirect_url': f'/forms/{result["form_id"]}'  # You'll need to create this URL pattern
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to create form'
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



# class FormListView(View):
#     def get(self, request):
#         forms = get_all_forms()
#         return render(request, 'form_builder/form_list.html', {'forms': forms})



class AddFormView(View):
    def get(self, request):
        return render(request, 'form_builder/add_form.html')




