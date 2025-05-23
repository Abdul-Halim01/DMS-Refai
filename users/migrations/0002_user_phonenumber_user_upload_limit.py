# Generated by Django 5.1 on 2025-02-07 16:12

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="phonenumber",
            field=models.CharField(
                default="05464334",
                max_length=15,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Phone number must be between 7 and 15 digits",
                        regex="^\\d{7,15}$",
                    )
                ],
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="user",
            name="upload_limit",
            field=models.IntegerField(
                default=100, validators=[django.core.validators.MinValueValidator(10)]
            ),
            preserve_default=False,
        ),
    ]
