# pr_tool/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('' , views.MainHR.as_view() , name="hr"),

    path('employees/' , views.ListEmployeesView.as_view() , name="employee_list"),
    path('create-employee/' , views.CreateEmployeeView.as_view() , name="create_employee"),
    path('employee/<str:pk>' , views.UpdateEmployeeView.as_view() , name="employee_profile"),
    path('employee-action' , views.EmployeesActionView.as_view() , name="employees_action"),
    path('delete-employee/<str:pk>' , views.DeleteEmployeeView.as_view() , name="delete_employee"),

    # holidays allocated by admin to employees
    path('holidays/' , views.ListHolidaysView.as_view() , name="holidays_list"),
    path('holidays/action' , views.HolidaysActionView.as_view() , name="holidays_action"),
    path('create-holiday/' , views.CreateHolidayView.as_view() , name="create_holiday"),
    path('holiday/<str:pk>' , views.UpdateHolidayView.as_view() , name="holiday_info"),
    path('delete-holiday/<str:pk>' , views.DeleteHolidayView.as_view() , name="delete_holiday"),

    # employee's absences with/without reason by admin
    path('absences/' , views.ListAbsenceView.as_view() , name="absences_list"),
    path('absences/action/' , views.AbsenceActionView.as_view() , name="absences_action"),
    path('create-absence/' , views.CreateAbsenceView.as_view() , name="create_absence"),
    path('absence/<str:pk>' , views.UpdateAbsenceView.as_view() , name="absence_info"),
    path('delete-absence/<str:pk>' , views.DeleteAbsenceView.as_view() , name="delete_absence"),

    # Recruitment to store info about recruiters and thier interview process
    path('recruiters/' , views.ListRecruitersView.as_view() , name="recruiters_list"),
    path('recruiters/action' , views.RecruitersActionView.as_view() , name="recruiters_action"),
    path('recruiter/<int:id>' , views.RecruiterProfileView.as_view() , name="recruiter_profile"),
    path('recruiter/<str:pk>/delete' , views.DeleteRecruiterView.as_view() , name="delete_recruiter"),

    # Development Tracking
    path('goals-skills/' , views.GoalsSkillsView.as_view() , name="goals_skills"),
    path('goals/' , views.ListGoalsView.as_view() , name="goals_list"),
    path('goals/action' , views.GoalsActionView.as_view() , name="goals_action"),
    path('goal/<int:id>' , views.GoalDetailView.as_view() , name="goal_info"),
    path('goals/add' , views.CreateGoalView.as_view() , name="create_goal"),
    path('goals/<str:pk>/delete' , views.DeleteGoalView.as_view() , name="delete_goal"),

    path('skills/' , views.ListSkillsView.as_view() , name="skills_list"),
    path('skills/action' , views.SkillsActionView.as_view() , name="skills_action"),
    path('skill/<int:id>' , views.SkillDetailView.as_view() , name="skill_info"),
    path('skills/add' , views.CreateSkillView.as_view() , name="create_skill"),
    path('skills/<str:pk>/delete' , views.DeleteSkillView.as_view() , name="delete_skill"),

    path('departments/' , views.ListDepartmentsView.as_view() , name="departments"),
    path('departments/add' , views.CreateDepartmentView.as_view() , name="create_department"),
    path('departments/action' , views.DepartmentsActionView.as_view() , name="departments_action"),
    path('department/<str:pk>' , views.DepartmentDetailView.as_view() , name="department_info"),
    path('department/<str:pk>/delete' , views.DeleteDepartmentView.as_view() , name="delete_department"),

    path('positions/' , views.ListPositionsView.as_view() , name="positions"),
    path('positions/add' , views.CreatePositionView.as_view() , name="create_position"),
    path('positions/action' , views.PositionsActionView.as_view() , name="positions_action"),
    path('position/<str:pk>' , views.PositionDetailView.as_view() , name="position_info"),
    path('position/<str:pk>/delete' , views.DeletePositionView.as_view() , name="delete_position"),

    path('hr_settings/' , views.SettingsView.as_view() , name="hr_settings")
    
]
