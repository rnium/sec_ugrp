from django import template
from results.utils import get_ordinal_number

register = template.Library()

@register.filter
def ordinal_num(n):
    return get_ordinal_number(n)