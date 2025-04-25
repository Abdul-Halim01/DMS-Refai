# users/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegistrationForm, UserUpdateForm, AdminChangePasswordForm, UserRoleForm
from django.contrib.auth import get_user_model
from django.views.generic import ListView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import *
from utility.mixins import users_criteria_add_perm, users_criteria_edit_perm, users_criteria_delete_perm
import json
User = get_user_model()

# Decorators for permissions
add_perm_decorator = user_passes_test(users_criteria_add_perm)
edit_perm_decorator = user_passes_test(users_criteria_edit_perm)
delete_perm_decorator = user_passes_test(users_criteria_delete_perm)

@method_decorator([login_required, add_perm_decorator], name='dispatch')
class UserRolesView(ListView):
    model = UserRole
    template_name = 'users/roles/user_roles.html'
    context_object_name = 'user_roles'
    paginate_by = 10  # set pagination to an appropriate number

    def get_queryset(self):
        q = self.request.GET.get('q', '')
        if self.request.htmx:
            self.template_name = 'partials/users_roles_partial.html'
            if q:
                return super().get_queryset().filter(name__icontains=q)
        else:
            return super().get_queryset()

@method_decorator([login_required, edit_perm_decorator], name='dispatch')
class UserRoleInfoView(View):
    def get(self, request, pk):
        user_role = UserRole.objects.get(id=pk)
        return render(request, 'users/roles/user_role_form.html', {'user_role': user_role})

@method_decorator([login_required, add_perm_decorator], name='dispatch')
class CreateUserRoleView(View):
    def get(self, request):
        form = UserRoleForm()
        return render(request, 'users/roles/user_role_form.html', {'form': form})

    def post(self, request):
        form = UserRoleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('user_roles')
        return render(request, 'users/roles/user_role_form.html', {'form': form})

@method_decorator([login_required, delete_perm_decorator], name='dispatch')
class DeleteUserRoleView(View):
    def get(self, request, pk):
        try:
            role = UserRole.objects.get(id=pk)
            role.delete()
            return redirect('user_roles')
        except UserRole.DoesNotExist:
            return redirect('404')

@method_decorator([login_required, delete_perm_decorator], name='dispatch')
class UserRolesActionView(View):
    def post(self, request):
        selected_items = json.loads(request.POST.get('selected_ids', '[]'))
        roles = UserRole.objects.filter(id__in=selected_items)

        # perform DB operation depending on the chosen action
        if request.POST.get('action') == 'delete':
            roles.delete()
        return redirect('user_roles')

@method_decorator([login_required, add_perm_decorator], name='dispatch')
class UsersView(View):
    def get(self, request):
        total_users = User.objects.count()
        total_roles = UserRole.objects.count()
        return render(request, 'users/users.html', {'total_users': total_users, 'total_roles': total_roles})

@method_decorator([login_required, add_perm_decorator], name='dispatch')
class UserListView(ListView):
    model = User
    template_name = 'users/users_list.html'
    context_object_name = 'users'
    paginate_by = 10  # set pagination to an appropriate number

    def get_queryset(self):
        q = self.request.GET.get('q', '')
        if self.request.htmx:
            self.template_name = 'partials/users_partial.html'
            if q:
                return super().get_queryset().filter(username__icontains=q)
        else:
            return super().get_queryset()

@method_decorator([login_required, add_perm_decorator], name='dispatch')
class AdminCreateUserView(View):
    def get(self, request):
        form = UserRegistrationForm()
        return render(request, 'users/admin_create_user.html', {'form': form})

    def post(self, request):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if user.role == 'admin':
                user.is_superuser = True
                user.is_staff = True
            user.save()
            return redirect('users_list')  # Or redirect to a user management page
        return render(request, 'users/admin_create_user.html', {'form': form})

# LoginView does not require user to be logged in or have permissions
class LoginView(View):
    def get(self, request):
        form = AuthenticationForm()
        return render(request, 'users/login.html', {'form': form})

    def post(self, request):
        email = request.POST.get('username')  # Get email from the username field
        password = request.POST.get('password')
        try:
            user = User.objects.get(email=email)  # Get user by email
            user = authenticate(request, username=user.username, password=password)  # Authenticate with username
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                form = AuthenticationForm(request, data=request.POST)
                form.add_error(None, "Invalid email or password")
        except User.DoesNotExist:
            form = AuthenticationForm(request, data=request.POST)
            form.add_error(None, "Invalid email or password")

        return render(request, 'users/login.html', {'form': form})

@method_decorator([login_required], name='dispatch')
class LogoutView(View):
    def get(self, request):
        if request.user:
            logout(request)
            return redirect('login')
        else:
            return HttpResponse('you are not logged in')

@method_decorator([login_required, edit_perm_decorator], name='dispatch')
class ProfileView(View):
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            form = UserUpdateForm(instance=user)
        except User.DoesNotExist:
            return HttpResponse('user does not exist')
        return render(request, 'users/profile.html', {'form': form, 'user': user})

    def post(self, request, user_id):
        user = User.objects.get(id=user_id)
        form = UserUpdateForm(request.POST, instance=user)

        if form.is_valid():
            form.save()
            return redirect('users_list')  # Or redirect to a user management page
        return render(request, 'users/profile.html', {'form': form})

@method_decorator([login_required, delete_perm_decorator], name='dispatch')
class DeleteUserView(DeleteView):
    model = User
    template_name = 'users/delete_user.html'
    context_object_name = 'user'
    success_url = '/users'

@method_decorator([login_required, delete_perm_decorator], name='dispatch')
class PerformActionView(View):
    def post(self, request):
        selected_items = json.loads(request.POST.get('selected_ids', '[]'))
        users = User.objects.filter(id__in=selected_items)

        # perform DB operation depending on the chosen action
        if request.POST.get('action') == 'delete':
            users.delete()
        elif request.POST.get('action') == 'activate':
            users.update(is_active=True)
        elif request.POST.get('action') == 'deactivate':
            users.update(is_active=False)
        return redirect('users_list')

@method_decorator([login_required, edit_perm_decorator], name='dispatch')
class AdminChangePasswordView(View):
    def get(self, request, user_id):
        form = AdminChangePasswordForm()
        return render(request, 'users/change_password.html', {'form': form})

    def post(self, request, user_id):
        form = AdminChangePasswordForm(request.POST)
        try:
            user = User.objects.get(pk=user_id)
            # if the form is valid and the passwords match then set a new password
            if form.is_valid():
                user.set_password(form.cleaned_data['new_password'])
                user.save()
                return redirect('profile', user_id=user_id)
        except User.DoesNotExist:
            return HttpResponse("User does not exist")
