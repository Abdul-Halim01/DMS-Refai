# hr_tool/views.py
from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render, redirect
from django.views import View
from .models import *
from .forms import EmployeeRegistrationForm , EmployeeUpdateForm , HolidayForm , WorkGoalForm , HRSettingsForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import get_user_model
from django.views.generic import ListView , DeleteView , CreateView , UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from utility.mixins import ModeratorRequiredMixin
from utility.helper import change_format , reverse_format
from django.contrib.auth.decorators import permission_required

User = get_user_model()

# Create your views here.

class MainHR(ModeratorRequiredMixin, View):
    def get(slef,request):
        return render(request , 'hr_tool/HR.html')


# @login_required_decorator
class ListEmployeesView(ModeratorRequiredMixin, ListView):
    model = Employee
    template_name = 'hr_tool/employee/employees.html'
    context_object_name = 'employees'
    paginate_by = 5

    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset()
        q = self.request.GET.get('q' , None)
        if q:
            queryset = queryset.filter(
                username__startswith = q
            )
        return queryset




# @method_decorator(login_required, name='dispatch')
# class CreateEmployeeView(View):
#     def get(self,request):
#         form = EmployeeRegistrationForm()
#         return render(request , 'hr_tool/create_employee.html' , context={'form':form})
    
#     def post(self,request):
#         form = EmployeeRegistrationForm(request.POST)
#         if form.is_valid():
#             user = User.objects.create(
#                 username = form.cleaned_data['username'],
#                 email = form.cleaned_data['email'],
#             )
#             user.set_password(form.cleaned_data['password1'])
#             Employee.objects.create(
#                 user=user,
#                 department=form.cleaned_data['department'],
#                 position=form.cleaned_data['position']
#             )
#             return redirect('employee_list')
#         return redirect('create_employee')




class CreateEmployeeView(ModeratorRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeRegistrationForm
    template_name = 'hr_tool/employee/create_employee.html'
    success_url = '/hr/employees/'
    



# @login_required_decorator
class DeleteEmployeeView(ModeratorRequiredMixin, DeleteView):
    model = Employee
    template_name = 'hr_tool/employee/delete_employee.html'

    context_object_name = 'employee'
    success_url = '/hr/employees/'
    
    

# @login_required_decorator
class UpdateEmployeeView(ModeratorRequiredMixin, UpdateView):
    model = Employee
    template_name = 'hr_tool/employee/employee_profile.html'
    form_class = EmployeeUpdateForm
    success_url = '/hr/employees/'

    # add extra data for each employee in the context
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        holidays = Holiday.objects.filter(employee=self.object).count() # get number of holidays for the employee
        absences = Absence.objects.filter(employee=self.object).count() # get number of absences for the employee
        context['holidays'] = holidays 
        context['absences'] = absences 
        return context



class EmployeesActionView(ModeratorRequiredMixin, View):
    def post(self,request):
        selected_items = request.POST.getlist('selected_items')
        employees = Employee.objects.filter(id__in=selected_items)



        # perform DB operation depending on the chosen action
        if request.POST.get('action') == 'delete':
            employees.delete()
        return redirect('employees_list')
        


@method_decorator(login_required, name='dispatch')
class CreateHolidayView(ModeratorRequiredMixin, View):
    def get(self,request):
        form = HolidayForm()
        return render(request , 'hr_tool/holiday/create_holiday.html' , {'form' : form})
    
    def post(self,requset):
        form = HolidayForm(requset.POST)
        if form.is_valid():
            holiday = form.save(commit=False)
            start_date, end_date = form.cleaned_data['daterange'].split('-')
            holiday.start = change_format(start_date)
            holiday.end = change_format(end_date)
            holiday.save()
            return redirect('holidays_list')
        return redirect('create_holiday')


@method_decorator(login_required, name='dispatch')
class ListHolidaysView(ModeratorRequiredMixin, ListView):
    model = Holiday
    template_name = 'hr_tool/holiday/holidays.html'
    context_object_name = 'holidays'
    paginate_by = 5

    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset()
        q = self.request.GET.get('q' , None)
        if q:
            queryset = queryset.filter(
                employee__username__startswith = q
            )
        return queryset



class HolidaysActionView(ModeratorRequiredMixin, View):
    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    def post(self,request):
        selected_items = request.POST.getlist('selected_items')
        holidays = Holiday.objects.filter(id__in=selected_items)

        # perform DB operation depending on the chosen action
        if request.POST.get('action') == 'delete':
            holidays.delete()
        return redirect('holidays_list')



@method_decorator(login_required, name='dispatch')
class UpdateHolidayView(ModeratorRequiredMixin, View):
    def get(self,request,pk):
        holiday = Holiday.objects.get(id=pk)
        form = HolidayForm(instance=holiday)
        start = reverse_format(holiday.start)
        end = reverse_format(holiday.end)
        form.initial['daterange'] = f"{start} - {end}"
        print(form.initial['daterange'])
        return render(request , 'hr_tool/holiday/holiday_info.html' , {'form' : form})
    
    def post(self,requset,pk):
        form = HolidayForm(requset.POST , instance=Holiday.objects.get(id=pk))
        if form.is_valid():
            holiday = form.save(commit=False)
            start_date, end_date = form.cleaned_data['daterange'].split('-')
            holiday.start = change_format(start_date)
            holiday.end = change_format(end_date)
            holiday.save()
            return redirect('holidays_list')
        return redirect('holiday_info')


@method_decorator(login_required, name='dispatch')
class DeleteHolidayView(ModeratorRequiredMixin, DeleteView):
    model = Holiday
    template_name = 'hr_tool/holiday/delete_holiday.html'
    context_object_name = 'holiday'
    success_url = '/hr/holidays/'



@method_decorator(login_required, name='dispatch')
class CreateAbsenceView(ModeratorRequiredMixin, CreateView):
    model = Absence
    fields = '__all__'
    template_name = 'hr_tool/absence/create_absence.html'
    success_url = '/hr/absences/'


@method_decorator(login_required, name='dispatch')
class ListAbsenceView(ModeratorRequiredMixin, ListView):
    model = Absence
    template_name = 'hr_tool/absence/absences.html'
    context_object_name = 'absences'
    paginate_by = 5

    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset()
        q = self.request.GET.get('q' , None)
        if q:
            queryset = queryset.filter(
                employee__username__startswith = q
            )
        return queryset



class AbsenceActionView(ModeratorRequiredMixin, View):
    def post(self,request):
        selected_items = request.POST.getlist('selected_items')
        absences = Absence.objects.filter(id__in=selected_items)

        # perform DB operation depending on the chosen action
        if request.POST.get('action') == 'delete':
            absences.delete()
        return redirect('absences_list')

@method_decorator(login_required, name='dispatch')
class UpdateAbsenceView(ModeratorRequiredMixin, UpdateView):
    model = Absence
    fields = '__all__'
    template_name = 'hr_tool/absence/absence_info.html'
    success_url = '/hr/absences/'
    context_object_name = 'absence'


@method_decorator(login_required, name='dispatch')
class DeleteAbsenceView(ModeratorRequiredMixin, DeleteView):
    model = Absence
    template_name = 'hr_tool/absence/list_absences.html'
    success_url = '/hr/absences/'
    context_object_name = 'absence'




class ListRecruitersView(ModeratorRequiredMixin, ListView):
    model = Recruitment
    template_name = 'hr_tool/recruitment/list_recruiters.html'
    context_object_name = 'recruiters'
    paginate_by = 5

    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset()
        q = self.request.GET.get('q' , None)
        if q:
            queryset = queryset.filter(
                first_name__startswith = q
            )
        return queryset
    


class RecruitersActionView(ModeratorRequiredMixin, View):
    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    def post(self,request):
        selected_items = request.POST.getlist('selected_items')
        recruiters = Recruitment.objects.filter(id__in=selected_items) 

        # perform DB operation depending on the chosen action
        if request.POST.get('action') == 'delete':
            recruiters.delete()
        return redirect('recruiters_list')




class RecruiterProfileView(ModeratorRequiredMixin, UpdateView):
    model = Recruitment
    template_name = 'hr_tool/recruitment/recruiter_profile.html'
    success_url = '/hr/recruiters/'
    context_object_name = 'recruiter'




class DeleteRecruiterView(ModeratorRequiredMixin, DeleteView):
    model = Recruitment
    template_name = 'hr_tool/recruitment/delete_recruite.html'
    success_url = '/hr/recruiters/'
    context_object_name = 'recruiter'




class ListGoalsView(ModeratorRequiredMixin, ListView):
    model = WorkGoal
    template_name = 'hr_tool/goals/goals.html'
    context_object_name = 'goals'
    paginate_by = 5

    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset()
        q = self.request.GET.get('q' , None)
        if q:
            queryset = queryset.filter(
                employee__username__startswith = q
            )
        return queryset


class GoalsSkillsView(ModeratorRequiredMixin, View):
    def get(self,request):
        return render(request , 'hr_tool/goals/goals_skills.html')



class CreateGoalView(ModeratorRequiredMixin, CreateView):
    model = WorkGoal
    template_name = 'hr_tool/goals/create_goal.html'
    success_url = '/hr/goals/'
    form_class = WorkGoalForm


class GoalDetailView(ModeratorRequiredMixin, UpdateView):
    model = WorkGoal
    template_name = 'hr_tool/goals/goal_detail.html'
    context_object_name = 'goal'

class DeleteGoalView(ModeratorRequiredMixin, DeleteView):
    model = WorkGoal
    template_name = 'hr_tool/goals/delete_goal.html'
    success_url = '/hr/goals/'
    context_object_name = 'goal'


class GoalsActionView(ModeratorRequiredMixin, View):
    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    def post(self,request):
        selected_items = request.POST.getlist('selected_items')
        goals = WorkGoal.objects.filter(id__in=selected_items)

        # perform DB operation depending on the chosen action
        if request.POST.get('action') == 'delete':
            goals.delete()
        return redirect('goals_list')


class ListSkillsView(ModeratorRequiredMixin, ListView):
    model = Skill
    template_name = 'hr_tool/goals/skills.html'
    context_object_name = 'skills'
    paginate_by = 5

    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset()
        q = self.request.GET.get('q' , None)
        if q:
            queryset = queryset.filter(
                name__startswith = q
            )
        return queryset


class CreateSkillView(ModeratorRequiredMixin, CreateView):
    model = Skill
    fields = ['name']
    template_name = 'hr_tool/goals/create_skill.html'
    success_url = '/hr/skills/'


class SkillDetailView(ModeratorRequiredMixin, UpdateView):
    model = Skill
    template_name = 'hr_tool/goals/skill_detail.html'
    context_object_name = 'skill'

class DeleteSkillView(ModeratorRequiredMixin, DeleteView):
    model = Skill
    template_name = 'hr_tool/goals/delete_skill.html'
    success_url = '/hr/skills/'
    context_object_name = 'skill'



class SkillsActionView(ModeratorRequiredMixin, View):
    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    def post(self,request):
        selected_items = request.POST.getlist('selected_items')
        skills = Skill.objects.filter(id__in=selected_items)
        # perform DB operation depending on the chosen action
        if request.POST.get('action') == 'delete':
            skills.delete()
        return redirect('skills_list')



class SettingsView(ModeratorRequiredMixin, View):
    def get(self,request):
        settings_instance = HRSettings.objects.first()
        form = HRSettingsForm(instance=settings_instance)
        return render(request , 'hr_tool/hr_settings.html' , {'form' : form})

    def post(self,request):
        form = HRSettingsForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('hr_settings')
        return redirect('hr_settings')
