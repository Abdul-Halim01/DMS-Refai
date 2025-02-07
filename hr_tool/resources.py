from import_export import resources
from .models import Employee, Holiday , Recruitment, Absence
from django.contrib.auth import get_user_model

User = get_user_model()


class EmployeeResource(resources.ModelResource):
    class Meta:
        model = Employee
        fields = ['id', 'email', 'phonenumber', 'position','department', 'start_date', 'address', 'social_status']


class HolidayResource(resources.ModelResource):
    class Meta:
        model = Holiday
        fields = ['id', 'employee', 'hours', 'start', 'end']


class RecruitmentResource(resources.ModelResource):
    class Meta:
        model = Recruitment
        fields = ['first_name', 'last_name', 'birthday', 'state', 'position', 'department']


class AbsenceResource(resources.ModelResource):
    class Meta:
        model = Absence
        fields = ['id', 'employee', 'days', 'reason', 'start', 'end']

