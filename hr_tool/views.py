# hr_tool/views.py
from typing import Any
import json
from django.db.models.query import QuerySet
from django.shortcuts import render, redirect
from django.views import View
from .models import *
# from users.models import User
from .forms import EmployeeRegistrationForm , EmployeeUpdateForm , HolidayForm , WorkGoalForm , HRSettingsForm , AbsenceForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import get_user_model
import datetime
from django.http import HttpResponse
from .resources import EmployeeResource, HolidayResource, AbsenceResource, RecruitmentResource
from utility.mixins import hr_criteria_add_perm, hr_criteria_delete_perm, hr_criteria_edit_perm
from django.views.generic import ListView, DeleteView, CreateView, UpdateView
from utility.helper import change_format, reverse_format
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test

User = get_user_model()


@method_decorator(user_passes_test(hr_criteria_add_perm), name='dispatch')
class MainHR(View):
    def get(self, request):
        total_holidays = Holiday.objects.count()
        total_absences = Absence.objects.count()
        total_employees = Employee.objects.count()
        active_employees = Employee.objects.filter(is_active=True).count()
        approved_holidays = Holiday.objects.filter(accepted=True).count()
        total_recruiters = Recruitment.objects.count()
        total_goals = WorkGoal.objects.count()
        total_skills = Skill.objects.count()
        total_departments = Department.objects.count()
        total_positions = Position.objects.count()
        return render(request, 'hr_tool/HR.html', {
            'total_holidays': total_holidays,
            'total_absences': total_absences,
            'total_employees': total_employees,
            'active_employees': active_employees,
            'approved_holidays': approved_holidays,
            'total_recruiters': total_recruiters,
            'total_goals': total_goals,
            'total_skills': total_skills,
            'total_departments': total_departments,
            'total_positions': total_positions
        })


@method_decorator(user_passes_test(hr_criteria_add_perm), name='dispatch')
class ListEmployeesView(ListView):
    model = Employee
    template_name = 'hr_tool/employee/employees.html'
    context_object_name = 'employees'
    paginate_by = 10

    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset()
        q = self.request.GET.get('q', None)
        if q:
            queryset = queryset.filter(
                username__startswith=q
            )
        return queryset


@method_decorator(user_passes_test(hr_criteria_add_perm), name='dispatch')
class CreateEmployeeView(CreateView):
    model = Employee
    form_class = EmployeeRegistrationForm
    template_name = 'hr_tool/employee/create_employee.html'
    success_url = '/hr/employees/'

    def form_invalid(self, form):
        # Print form errors for debugging
        print(form.errors)
        return super().form_invalid(form)


@method_decorator(user_passes_test(hr_criteria_delete_perm), name='dispatch')
class DeleteEmployeeView(DeleteView):
    model = Employee
    template_name = 'hr_tool/employee/delete_employee.html'
    context_object_name = 'employee'
    success_url = '/hr/employees/'


@method_decorator(user_passes_test(hr_criteria_edit_perm), name='dispatch')
class UpdateEmployeeView(UpdateView):
    model = Employee
    template_name = 'hr_tool/employee/employee_profile.html'
    form_class = EmployeeUpdateForm
    success_url = '/hr/employees/'

    # add extra data for each employee in the context
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        holidays = Holiday.objects.filter(employee=self.object).count()  # get number of holidays for the employee
        absences = Absence.objects.filter(employee=self.object).count()  # get number of absences for the employee
        context['holidays'] = holidays
        context['absences'] = absences
        return context


@method_decorator(user_passes_test(hr_criteria_delete_perm), name='dispatch')
class EmployeesActionView(View):
    def post(self, request):
        selected_items = request.POST.getlist('selected_items')
        employees = Employee.objects.filter(id__in=selected_items)

        if request.POST.get('action') == 'delete':
            employees.delete()
        elif request.POST.get('action') == 'export_excel':
            employee_resource = EmployeeResource()
            dataset = employee_resource.export(employees)
            dataset = dataset.export(format='xlsx')
            response = HttpResponse(
                dataset,
                content_type='application/vnd.ms-excel'
            )
            response['Content-Disposition'] = f'attachment; filename="employees_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
            return response

        return redirect('employees_list')


@method_decorator([login_required, user_passes_test(hr_criteria_add_perm)], name='dispatch')
class CreateHolidayView(View):
    def get(self, request):
        form = HolidayForm()
        return render(request, 'hr_tool/holiday/create_holiday.html', {'form': form})

    def post(self, request):
        form = HolidayForm(request.POST)
        if form.is_valid():
            holiday = form.save(commit=False)
            start_date, end_date = form.cleaned_data['daterange'].split('-')
            holiday.start = change_format(start_date)
            holiday.end = change_format(end_date)
            holiday.save()
            return redirect('holidays_list')
        return redirect('create_holiday')


@method_decorator([login_required, user_passes_test(hr_criteria_add_perm)], name='dispatch')
class ListHolidaysView(ListView):
    model = Holiday
    template_name = 'hr_tool/holiday/holidays.html'
    context_object_name = 'holidays'
    paginate_by = 10

    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset()
        q = self.request.GET.get('q', None)
        if q:
            queryset = queryset.filter(
                employee__username__startswith=q
            )
        return queryset


@method_decorator(user_passes_test(hr_criteria_delete_perm), name='dispatch')
class HolidaysActionView(View):
    def post(self, request):
        selected_items = json.loads(request.POST.get('selected_ids', '[]'))
        holidays = Holiday.objects.filter(id__in=selected_items)

        # perform DB operation depending on the chosen action
        if request.POST.get('action') == 'delete':
            holidays.delete()

        elif request.POST.get('action') == 'export_excel':
            holiday_resource = HolidayResource()
            dataset = holiday_resource.export(holidays)
            dataset = dataset.export(format='xlsx')
            response = HttpResponse(
                dataset,
                content_type='application/vnd.ms-excel'
            )
            response['Content-Disposition'] = f'attachment; filename="holidays_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
            return response

        return redirect('holidays_list')


@method_decorator([login_required, user_passes_test(hr_criteria_edit_perm)], name='dispatch')
class UpdateHolidayView(View):
    def get(self, request, pk):
        holiday = Holiday.objects.get(id=pk)
        form = HolidayForm(instance=holiday)
        return render(request, 'hr_tool/holiday/holiday_info.html', {'form': form})

    def post(self, request, pk):
        form = HolidayForm(request.POST, instance=Holiday.objects.get(id=pk))
        if form.is_valid():
            form.save()
            return redirect('holidays_list')
        return redirect('holiday_info')


@method_decorator([login_required, user_passes_test(hr_criteria_delete_perm)], name='dispatch')
class DeleteHolidayView(DeleteView):
    model = Holiday
    template_name = 'hr_tool/holiday/delete_holiday.html'
    context_object_name = 'holiday'
    success_url = '/hr/holidays/'


@method_decorator([login_required, user_passes_test(hr_criteria_add_perm)], name='dispatch')
class CreateAbsenceView(CreateView):
    model = Absence
    form_class = AbsenceForm
    template_name = 'hr_tool/absence/create_absence.html'
    success_url = '/hr/absences/'


@method_decorator([login_required, user_passes_test(hr_criteria_add_perm)], name='dispatch')
class ListAbsenceView(ListView):
    model = Absence
    template_name = 'hr_tool/absence/absences.html'
    context_object_name = 'absences'
    paginate_by = 10

    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset()
        q = self.request.GET.get('q', None)
        if q:
            queryset = queryset.filter(
                employee__username__startswith=q
            )
        return queryset


@method_decorator(user_passes_test(hr_criteria_delete_perm), name='dispatch')
class AbsenceActionView(View):
    def post(self, request):
        selected_ids = json.loads(request.POST.get('selected_ids', '[]'))
        absences = Absence.objects.filter(id__in=selected_ids)
        # perform DB operation depending on the chosen action
        if request.POST.get('action') == 'delete':
            absences.delete()

        elif request.POST.get('action') == 'export_excel':
            absence_resource = AbsenceResource()
            dataset = absence_resource.export(absences)
            dataset = dataset.export(format='xlsx')
            response = HttpResponse(
                dataset,
                content_type='application/vnd.ms-excel'
            )
            response['Content-Disposition'] = f'attachment; filename="absences_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
            return response

        return redirect('absences_list')


@method_decorator([login_required, user_passes_test(hr_criteria_edit_perm)], name='dispatch')
class UpdateAbsenceView(UpdateView):
    model = Absence
    form_class = AbsenceForm
    template_name = 'hr_tool/absence/absence_info.html'
    success_url = '/hr/absences/'
    context_object_name = 'absence'


@method_decorator([login_required, user_passes_test(hr_criteria_delete_perm)], name='dispatch')
class DeleteAbsenceView(DeleteView):
    model = Absence
    template_name = 'hr_tool/absence/list_absences.html'
    success_url = '/hr/absences/'
    context_object_name = 'absence'


@method_decorator(user_passes_test(hr_criteria_add_perm), name='dispatch')
class ListRecruitersView(ListView):
    model = Recruitment
    template_name = 'hr_tool/recruitment/list_recruiters.html'
    context_object_name = 'recruiters'
    paginate_by = 10

    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset()
        q = self.request.GET.get('q', None)
        if q:
            queryset = queryset.filter(
                first_name__startswith=q
            )
        return queryset


@method_decorator(user_passes_test(hr_criteria_delete_perm), name='dispatch')
class RecruitersActionView(View):
    def post(self, request):
        selected_ids = json.loads(request.POST.get('selected_ids'))
        recruiters = Recruitment.objects.filter(id__in=selected_ids)

        # perform DB operation depending on the chosen action
        if request.POST.get('action') == 'delete':
            recruiters.delete()

        elif request.POST.get('action') == 'export_excel':
            recruiter_resource = RecruitmentResource()
            dataset = recruiter_resource.export(recruiters)
            dataset = dataset.export(format='xlsx')

            response = HttpResponse(
                dataset,
                content_type='application/vnd.ms-excel'
            )
            response['Content-Disposition'] = f'attachment; filename="recruiters_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
            return response

        return redirect('recruiters_list')


@method_decorator(user_passes_test(hr_criteria_edit_perm), name='dispatch')
class RecruiterProfileView(UpdateView):
    model = Recruitment
    template_name = 'hr_tool/recruitment/recruiter_profile.html'
    success_url = '/hr/recruiters/'
    context_object_name = 'recruiter'


@method_decorator(user_passes_test(hr_criteria_delete_perm), name='dispatch')
class DeleteRecruiterView(DeleteView):
    model = Recruitment
    template_name = 'hr_tool/recruitment/delete_recruite.html'
    success_url = '/hr/recruiters/'
    context_object_name = 'recruiter'


@method_decorator(user_passes_test(hr_criteria_add_perm), name='dispatch')
class ListGoalsView(ListView):
    model = WorkGoal
    template_name = 'hr_tool/goals/goals.html'
    context_object_name = 'goals'
    paginate_by = 10

    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset()
        q = self.request.GET.get('q', None)
        if q:
            queryset = queryset.filter(
                employee__username__startswith=q
            )
        return queryset


class GoalsSkillsView(View):
    def get(self, request):
        return render(request, 'hr_tool/goals/goals_skills.html')


@method_decorator(user_passes_test(hr_criteria_add_perm), name='dispatch')
class CreateGoalView(CreateView):
    model = WorkGoal
    template_name = 'hr_tool/goals/create_goal.html'
    success_url = '/hr/goals/'
    form_class = WorkGoalForm


@method_decorator(user_passes_test(hr_criteria_edit_perm), name='dispatch')
class GoalDetailView(UpdateView):
    model = WorkGoal
    template_name = 'hr_tool/goals/goal_detail.html'
    context_object_name = 'goal'


@method_decorator(user_passes_test(hr_criteria_delete_perm), name='dispatch')
class DeleteGoalView(DeleteView):
    model = WorkGoal
    template_name = 'hr_tool/goals/delete_goal.html'
    success_url = '/hr/goals/'
    context_object_name = 'goal'


@method_decorator(user_passes_test(hr_criteria_delete_perm), name='dispatch')
class GoalsActionView(View):
    def post(self, request):
        selected_items = json.loads(request.POST.get('selected_ids'))
        goals = WorkGoal.objects.filter(id__in=selected_items)

        # perform DB operation depending on the chosen action
        if request.POST.get('action') == 'delete':
            goals.delete()
        return redirect('goals_list')


@method_decorator(user_passes_test(hr_criteria_add_perm), name='dispatch')
class ListSkillsView(ListView):
    model = Skill
    template_name = 'hr_tool/goals/skills.html'
    context_object_name = 'skills'
    paginate_by = 10

    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset()
        q = self.request.GET.get('q', None)
        if q:
            queryset = queryset.filter(
                name__startswith=q
            )
        return queryset


@method_decorator(user_passes_test(hr_criteria_add_perm), name='dispatch')
class CreateSkillView(CreateView):
    model = Skill
    fields = ['name']
    template_name = 'hr_tool/goals/create_skill.html'
    success_url = '/hr/skills/'


@method_decorator(user_passes_test(hr_criteria_edit_perm), name='dispatch')
class SkillDetailView(UpdateView):
    model = Skill
    template_name = 'hr_tool/goals/skill_detail.html'
    context_object_name = 'skill'


@method_decorator(user_passes_test(hr_criteria_delete_perm), name='dispatch')
class DeleteSkillView(DeleteView):
    model = Skill
    template_name = 'hr_tool/goals/delete_skill.html'
    success_url = '/hr/skills/'
    context_object_name = 'skill'


@method_decorator(user_passes_test(hr_criteria_delete_perm), name='dispatch')
class SkillsActionView(View):
    def post(self, request):
        selected_items = json.loads(request.POST.get('selected_ids'))
        skills = Skill.objects.filter(id__in=selected_items)
        # perform DB operation depending on the chosen action
        if request.POST.get('action') == 'delete':
            skills.delete()
        return redirect('skills_list')


class SettingsView(View):
    def get(self, request):
        settings_instance = HRSettings.objects.first()
        form = HRSettingsForm(instance=settings_instance)
        return render(request, 'hr_tool/hr_settings.html', {'form': form})

    def post(self, request):
        form = HRSettingsForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('hr_settings')
        return redirect('hr_settings')


@method_decorator(user_passes_test(hr_criteria_add_perm), name='dispatch')
class ListDepartmentsView(ListView):
    model = Department
    template_name = 'hr_tool/departments/departments.html'
    context_object_name = 'departments'
    paginate_by = 10

@method_decorator(user_passes_test(hr_criteria_add_perm), name='dispatch')
class CreateDepartmentView(CreateView):
    model = Department
    template_name = 'hr_tool/departments/create_department.html'
    success_url = '/hr/departments/'
    fields = ['name', 'description']

@method_decorator(user_passes_test(hr_criteria_edit_perm), name='dispatch')
class DepartmentDetailView(UpdateView):
    model = Department
    fields = ['name', 'description']
    template_name = 'hr_tool/departments/department_info.html'
    context_object_name = 'department'
    success_url = '/hr/departments/'

@method_decorator(user_passes_test(hr_criteria_delete_perm), name='dispatch')
class DeleteDepartmentView(DeleteView):
    model = Department
    template_name = 'hr_tool/departments/delete_department.html'
    success_url = '/hr/departments/'
    context_object_name = 'department'

@method_decorator(user_passes_test(hr_criteria_delete_perm), name='dispatch')
class DepartmentsActionView(View):
    def post(self, request):
        selected_items = json.loads(request.POST.get('selected_ids'))
        departments = Department.objects.filter(id__in=selected_items)
        if request.POST.get('action') == 'delete':
            departments.delete()
        return redirect('departments_list')


@method_decorator(user_passes_test(hr_criteria_add_perm), name='dispatch')
class ListPositionsView(ListView):
    model = Position
    template_name = 'hr_tool/positions/positions.html'
    context_object_name = 'positions'
    paginate_by = 10

@method_decorator(user_passes_test(hr_criteria_add_perm), name='dispatch')
class CreatePositionView(CreateView):
    model = Position
    template_name = 'hr_tool/positions/create_position.html'
    success_url = '/hr/positions/'
    fields = ['name', 'description']

@method_decorator(user_passes_test(hr_criteria_edit_perm), name='dispatch')
class PositionDetailView(UpdateView):
    model = Position
    fields = ['name', 'description']
    template_name = 'hr_tool/positions/position_info.html'
    context_object_name = 'position'
    success_url = '/hr/positions/'

@method_decorator(user_passes_test(hr_criteria_delete_perm), name='dispatch')
class DeletePositionView(DeleteView):
    model = Position
    template_name = 'hr_tool/positions/delete_position.html'
    success_url = '/hr/positions/'
    context_object_name = 'position'


@method_decorator(user_passes_test(hr_criteria_delete_perm), name='dispatch')
class PositionsActionView(View):
    def post(self, request):
        selected_items = json.loads(request.POST.get('selected_ids'))
        positions = Position.objects.filter(id__in=selected_items)
        if request.POST.get('action') == 'delete':
            positions.delete()
        return redirect('positions_list')
