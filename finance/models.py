from django.db import models
from hr_tool.models import Employee

# Create your models here.


class Salary(models.Model):
    employee = models.ForeignKey(Employee , on_delete=models.CASCADE)
    amount = models.FloatField()
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'{self.employee.username}-{self.amount}'
    



# class UpfrontPayment(models.Model):
#     pass


