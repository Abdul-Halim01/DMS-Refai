# your_app/templatetags/task_filters.py

from django import template

register = template.Library()

@register.filter
def count_by_status(tasks, status):
    return tasks.filter(status=status).count()

@register.filter
def get_item(obj, key):
    """
    Template filter to access dictionary items by key or object attributes
    
    Usage in templates:
    {{ my_dict|get_item:key_variable }}
    {{ my_object|get_item:'attribute_name' }}
    """
    try:
        # First try to access as dictionary
        if isinstance(obj, dict):
            return obj.get(key, '')
        # Then try to access as object attribute
        else:
            return getattr(obj, key, '')
    except (TypeError, AttributeError):
        # Return empty string if access fails
        return ''