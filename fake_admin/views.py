# fake_admin/views.py
from django.shortcuts import render
from django.http import HttpResponseForbidden

def fake_admin_view(request):
    return HttpResponseForbidden("You are not authorized to access this page.")
