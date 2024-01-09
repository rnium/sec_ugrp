from django import template
from results.utils import get_ordinal_number, get_letter_grade

register = template.Library()

@register.filter
def ordinal_num(n):
    return get_ordinal_number(n)


@register.filter
def floating_two_point(n):
    if n is None:
        return
    return round(n, 2)

@register.filter
def to_letter_grade(gp):
    return get_letter_grade(gp)

@register.filter
def point_zero_to_int_else_float(n):
    int_n = int(n)
    if int_n == n:
        return int_n
    else:
        return n
    
@register.filter
def count_carry_records(session_id, course):
    if session_id is None:
        return None
    course_res = course.courseresult_set.filter(student__session__id=int(session_id))
    return course_res.count()