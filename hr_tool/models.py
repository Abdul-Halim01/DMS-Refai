from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator , MaxValueValidator
from utility.types import *
User = get_user_model()

# Create your models here.


class Employee(User):
    position = models.CharField(max_length=100, choices=Position, default='Full-Time')
    department = models.CharField(max_length=100, choices=Department, default='HR')

    class Meta:
        verbose_name = 'employee'
        verbose_name_plural = 'employees'

    def __str__(self) -> str:
        return self.username
    


class Holiday(models.Model):
    employee = models.ForeignKey(Employee , on_delete=models.CASCADE)
    hours = models.CharField(choices=Holiday, max_length=40)
    start = models.DateField()
    end = models.DateField()

    def __str__(self) -> str:
        return f'{self.employee.username} - {self.hours}'



class Absence(models.Model):
    employee = models.ForeignKey(Employee , on_delete=models.CASCADE)
    days = models.IntegerField(validators=[MinValueValidator(1) , MaxValueValidator(1000)])
    reason = models.CharField(max_length=100, choices=Absence,default='_')
    start = models.DateField()
    end = models.DateField()

    def __str__(self) -> str:
        return f'{self.employee.username} - {self.days}'



class Recruitment(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birthday = models.DateField()
    state = models.CharField(max_length=30 , choices=State)
    image = models.ImageField(upload_to='recruiters/images', default='placeholder.jpg')
    position = models.CharField(max_length=100 , choices=Position,default='Initial')
    department = models.CharField(max_length=100)
    resume = models.FileField(upload_to='recruitment/resumes',blank=True,null=True)

    def __str__(self) -> str:
        return f'{self.first_name} {self.last_name}'


class Skill(models.Model):
    name = models.CharField(max_length=50)
    created = models.DateField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name



class WorkGoal(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill , on_delete=models.CASCADE) # modify the on_delete
    created = models.DateField(auto_now_add=True)
    progress = models.CharField(max_length=20 , choices=Progress ,default="0%")

    def __str__(self) -> str:
        return f"{self.employee.username} - {self.skill}"




class HRSettings(models.Model):
    date_format = models.CharField(max_length=20 , choices=DateFormat , default=DateFormat.DMY)
    time_format = models.CharField(max_length=100 , choices=TimeFormat , default=TimeFormat.TWELVE_HOUR)
    language = models.CharField(max_length=100 , choices=Language , default=Language.ENGLISH)
    days_in_month = models.IntegerField(validators=[MinValueValidator(1) , MaxValueValidator(31)] , default=28)

    def __str__(self) -> str:
        return self.name