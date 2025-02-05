# users/models.py
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
        ('normal', 'Normal User'),
    ]
    image = models.ImageField(upload_to='users/images',default='placeholder.jpg',null=True,blank=True)       
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='normal')
    # upload_limit = models.IntegerField(validators=).
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',  # Custom related name to avoid clashes
        blank=True,
        help_text=('The groups this user belongs to. A user will get all permissions '
                   'granted to each of their groups.'),
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions_set',  # Custom related name to avoid clashes
        blank=True,
        help_text='Specific permissions for this user.',
        related_query_name='custom_user_permissions',
    )

    @property
    def activate(self):
        self.is_active = True
        self.save()
    
    @property
    def deactivate(self):
        self.is_active = False
        self.save()

    def __str__(self):
        return self.username




class Settings(models.Model):
    DATE_CHOICES = [
        ('MM/DD/YY', 'DD/MM/YY'),
    ]
    date_format = models.CharField(max_length=30 , choices=DATE_CHOICES)
    info = models.CharField(max_length=100,default='test')

    @classmethod
    def get_instance(cls):
        instance = cls.objects.first()
        if instance is None:
            instance = cls()
        return instance
    
    def clean(self):
        if self.pk is None:
            if Settings.objects.exists():
                raise ValidationError("Only one Settings instance is allowed.")
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)