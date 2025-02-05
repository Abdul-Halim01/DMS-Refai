# users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.UserListView.as_view(), name='users_list'), # added pagination
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'), # new
    path('profile/<str:user_id>', views.ProfileView.as_view(), name='profile'), # added update-profile functionality
    path('create-user/', views.AdminCreateUserView.as_view(), name='create_user'),
    path('delete-user/<str:pk>', views.DeleteUserView.as_view(), name='delete_user'), # new
    path('change-password/<str:user_id>', views.AdminChangePasswordView.as_view(), name='change_password'), # new 
    path('perform-action/', views.PerformActionView.as_view(), name='users_action'), # new
]
