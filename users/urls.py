# users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.UsersView.as_view(), name='users'), # added pagination
    path('list/', views.UserListView.as_view(), name='users_list'), # added pagination
    path('roles/' , views.UserRolesView.as_view() , name="user_roles"),
    path('roles/action/' , views.UserRolesActionView.as_view() , name="user_roles_action"),
    path('roles/add/' , views.CreateUserRoleView.as_view() , name="add_user_role"),
    path('roles/delete/<str:pk>' , views.DeleteUserRoleView.as_view() , name="delete_user_role"),
    path('roles/<str:pk>' , views.UserRoleInfoView.as_view() , name="user_role_info"),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'), # new
    path('<str:user_id>', views.ProfileView.as_view(), name='profile'), # added update-profile functionality
    path('add/', views.AdminCreateUserView.as_view(), name='create_user'),
    path('delete/<str:pk>', views.DeleteUserView.as_view(), name='delete_user'), # new
    path('change-password/<str:user_id>', views.AdminChangePasswordView.as_view(), name='change_password'), # new 
    path('action/', views.PerformActionView.as_view(), name='users_action'), # new
]
