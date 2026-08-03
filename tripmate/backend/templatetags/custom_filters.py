from django import template

register = template.Library()


@register.filter
def split(value, arg=','):
    """Split a string by a delimiter. Usage: {{ "a,b,c"|split:"," }}"""
    return value.split(arg)


@register.filter
def trim(value):
    """Strip whitespace from a string. Usage: {{ " hello "|trim }}"""
    return value.strip() if isinstance(value, str) else value
