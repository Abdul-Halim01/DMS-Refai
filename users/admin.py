from django.contrib import admin
from .models import User , Setting , UserRole , Criteria
from django.contrib.auth.admin import UserAdmin


# Register your models here.

# customizing the User model required customizing the user admin
class CustomUserAdmin(UserAdmin):
    # show selected fields as a table
    list_display = ['id', 'email','username', 'is_staff','is_superuser','role']    
    ordering = ['-id']

    # grouping the fields in the user info page
    fieldsets = (
        (None, 
                {'fields':('email', 'password',)}
            ),
            ('User Information',
                {'fields':('username', 'first_name', 'last_name' , 'image')}
            ),
            ('Permissions', 
                {'fields':('is_staff', 'is_superuser', 'is_active', 'groups','user_permissions','role')}
            ),
            ('Registration', 
                {'fields':('date_joined', 'last_login',)}
        )
    )


class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    ordering = ['-id']


class CriteriaAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'criteria_type']
    ordering = ['-id']

admin.site.register(User, CustomUserAdmin)
admin.site.register(UserRole , UserRoleAdmin)
admin.site.register(Criteria , CriteriaAdmin)
admin.site.register(Setting)