from django.db import models
from utility.types import Status, Priority
from users.models import User
# Create your models here.





class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    priority = models.CharField(max_length=20 , choices=Priority)
    status = models.CharField(max_length=20 , choices=Status)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} - {self.title}'

