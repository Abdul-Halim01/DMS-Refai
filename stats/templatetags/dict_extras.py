# stats/templatetags/dict_extras.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Return the value for the given key from a dictionary."""
    return dictionary.get(key)

@register.filter
def dict_keys(value):
    """Return the keys of a dictionary."""
    try:
        return value.keys()
    except AttributeError:
        return []

@register.filter
def to_list(value):
    """Convert an iterable (e.g., dict_values) to a list."""
    try:
        return list(value)
    except Exception:
        return value

