# users/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm 
from django.contrib.auth import get_user_model
from .models import UserRole
User = get_user_model()


class UserRegistrationForm(UserCreationForm):
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role','upload_limit','phonenumber']



class UserUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['username', 'email', 'role']


class UserRoleForm(forms.ModelForm):

    class Meta:
        model = UserRole
        fields = ['name']


class AdminChangePasswordForm(forms.Form):
    new_password = forms.CharField(
        label="كلمة المرور الجديدة",
        widget=forms.PasswordInput
    )
    confirm_password = forms.CharField(
        label="تأكيد كلمة المرور الجديدة",
        widget=forms.PasswordInput
    )



class UserLoginForm(AuthenticationForm):
    username = forms.CharField(max_length=254, widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput)
