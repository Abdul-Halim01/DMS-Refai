# Generated by Django 5.1 on 2025-04-19 22:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hr_tool", "0008_department_position_remove_employee_department_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="department",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="hr_tool.department",
            ),
        ),
        migrations.AddField(
            model_name="employee",
            name="position",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="hr_tool.position",
            ),
        ),
        migrations.AddField(
            model_name="recruitment",
            name="department",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="hr_tool.department",
            ),
        ),
        migrations.AddField(
            model_name="recruitment",
            name="position",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="hr_tool.position",
            ),
        ),
    ]
