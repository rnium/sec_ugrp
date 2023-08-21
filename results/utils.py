from django.shortcuts import render

SEC_GRADING_SCHEMA = {
    "A+" : {"min": 80, "max":100, "grade_point":4.0},
    "A" : {"min": 75, "max":79.999, "grade_point":3.75},
    "A-" : {"min": 70, "max":74.999, "grade_point":3.50},
    "B+" : {"min": 65, "max":69.999, "grade_point":3.25},
    "B" : {"min": 60, "max":64.999, "grade_point":3.00},
    "B-" : {"min": 55, "max":59.999, "grade_point":2.75},
    "C+" : {"min": 50, "max":54.999, "grade_point":2.50},
    "C" : {"min": 45, "max":49.999, "grade_point":2.25},
    "C-" : {"min": 40, "max":44.999, "grade_point":2.00},
    "F" : {"min": 0, "max":39.999, "grade_point":0.00},
}

def get_ordinal_number(value):
    try:
        value = int(value)
    except (ValueError, TypeError):
        return value
    if value % 100 in {11, 12, 13}:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(value % 10, 'th')
    return f'{value}{suffix}'


def calculate_grade_point(obtained_score, max_marks):
    if obtained_score is None:
        return None
    score = (obtained_score/max_marks) * 100
    for LG, schema in SEC_GRADING_SCHEMA.items():
        if schema['min'] <= score <= schema['max']:
            return schema['grade_point']


def calculate_letter_grade(obtained_score, max_marks):
    if obtained_score is None:
        return None
    score = (obtained_score/max_marks) * 100
    for LG, schema in SEC_GRADING_SCHEMA.items():
        if schema['min'] <= score <= schema['max']:
            return LG

def get_letter_grade(grade_point):
    if grade_point is None:
        return None
    for LG, schema in SEC_GRADING_SCHEMA.items():
        if grade_point >= schema['grade_point']:
            return LG
        
def render_error(request, msg=None, secondary_msg=None):
    context = {
        "error" : msg if msg is not None else "An Error Occurred!"
    }
    if secondary_msg:
        context['secondary_msg'] = secondary_msg
    return render(request, "results/error_details.html", context=context)