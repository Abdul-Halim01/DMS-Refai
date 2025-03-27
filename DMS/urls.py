"""
URL configuration for DMS project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import DashboardView

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('supersecureadmin/', admin.site.urls),
    path('admin/', include('fake_admin.urls')),  # Fake admin page
    path('secureadmin/', include('fake_admin.urls')),  # Fake admin page
    path('users/', include('users.urls')),
    path('documents/', include('documents.urls')),
    path('tasks/', include('tasks.urls')),
    path('hr/', include('hr_tool.urls')),
    path('form-builder/', include('form_builder.urls')),
    path('stats/', include('stats.urls')),
    # path('error/' , )
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]
