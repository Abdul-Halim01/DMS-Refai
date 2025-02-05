# your_app/templatetags/task_filters.py

from django import template

register = template.Library()

@register.filter
def count_by_status(tasks, status):
    return tasks.filter(status=status).count()