from django.db import models

# Create your models here.


class CustomForm(models.Model):
    name = models.CharField(max_length=100)
    language = models.CharField(default="en", max_length=100)

    def __str__(self):
        return self.name

