from django import template
from django.core.serializers.json import DjangoJSONEncoder
import json

register = template.Library()

@register.filter(name='to_json')
def to_json(value):
    """Convert a value to JSON string"""
    return json.dumps(value, cls=DjangoJSONEncoder) 