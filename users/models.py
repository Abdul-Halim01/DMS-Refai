# users/models.py
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from utility.types import Role



class Criteria(models.Model):
    CRITERIA_TYPE_CHOICES = [
        ('delete', 'Delete'),
        ('add', 'Add'),
        ('edit', 'Edit'),
    ]
    name = models.CharField(max_length=20)
    criteria_type = models.CharField(max_length=20, choices=CRITERIA_TYPE_CHOICES)

    def __str__(self) -> str:
        return f"{self.name} - {self.criteria_type}"


class UserRole(models.Model):
    name = models.CharField(max_length=20)
    criteria = models.ManyToManyField(Criteria, related_name='user_roles')

    def __str__(self) -> str:
        return self.name



class User(AbstractUser):
    phonenumber = models.CharField(max_length=15, validators=[RegexValidator(regex=r'^\d{7,15}$', message='Phone number must be between 7 and 15 digits')], null=True, blank=True)
    image = models.ImageField(upload_to='users/images',default='placeholder.jpg',null=True,blank=True)       
    role = models.ForeignKey(UserRole, on_delete=models.CASCADE, null=True, blank=True)
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
    upload_limit = models.IntegerField(validators=[MinValueValidator(10)])

    @property
    def activate(self):
        self.is_active = True
        self.save()
    
    @property
    def deactivate(self):
        self.is_active = False
        self.save()

    # def check_upload_limit(self, file_size):
    #     if file_size + self.upload_limit :
    #         return True

    def __str__(self):
        return self.username




class Setting(models.Model):
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
            if Setting.objects.exists():
                raise ValidationError("Only one Settings instance is allowed.")
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)