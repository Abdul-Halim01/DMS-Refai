# stats/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Return the value for the given key from a dictionary."""
    return dictionary.get(key)

@register.filter
def to_list(value):
    return list(value)

@register.filter
def dict_keys(dictionary):
    return dictionary.keys()