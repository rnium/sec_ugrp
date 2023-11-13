from django.contrib.auth import authenticate
from account.models import StudentAccount
from results.models import Session, Course, CourseResult, Semester, SemesterEnroll, Department
from django.forms.models import model_to_dict
from io import StringIO
import json


def create_course_enrollments(semester: Semester):
    object_prototypes = []
    for student in semester.session.studentaccount_set.all():
        object_prototypes.append(SemesterEnroll(student=student, semester=semester))
    
    SemesterEnroll.objects.bulk_create(object_prototypes)
    
def add_course_to_enrollments(course: Course):
    enrollments = SemesterEnroll.objects.filter(semester=course.semester)
    for enroll in enrollments:
        enroll.courses.add(course)

def create_course_results(course: Course):
    object_prototypes = []
    for student in course.semester.session.studentaccount_set.all():
        object_prototypes.append(CourseResult(student=student, course=course))
    
    CourseResult.objects.bulk_create(object_prototypes)


def format_render_config(request):
    data = {
        'render_config': request.data.get('render_config', {'tabulation_title':'', 'tabulation_exam_time':''}),
        'footer_data': {
            'chairman': request.data['footer_data_raw']['chairman'],
            'controller': request.data['footer_data_raw']['controller'],
            # member and tabulators
        }
    }
    members = request.data['footer_data_raw']['committee']
    for i, member in enumerate(members):
        data['footer_data'][f'committee_mem_{i+1}'] = member
    tabulators = request.data['footer_data_raw']['tabulators']
    for i, tabulator in enumerate(tabulators):
        data['footer_data'][f'tabulator_{i+1}'] = tabulator
    return data


def is_confirmed_user(request, username):
    password = request.data.get('password')
    user = authenticate(request, username=username, password=password)
    return ((user is not None) and (request.user == user))

def course_sorting_key(course: Course, dept_name):
    dept_priority = 0
    coursecode_first_part = course.code.split(' ')[0].lower().strip()
    if coursecode_first_part == dept_name.lower():
        dept_priority = 1
    return (course.course_credit, dept_priority)

def sort_courses(courses, dept_name):
    sorted_courses = sorted(courses, key=lambda course: course_sorting_key(course, dept_name), reverse=True)
    return sorted_courses

def create_backup(dept: Department):
    backup_data = {
        "dept": dept.name,
        "sessions": []
    }
    sessions = Session.objects.filter(dept=dept)
    for session in sessions:
        session_data = {
            'session_meta' : model_to_dict(session),
            'students': [],
            'semesters': []
        }
        for student in StudentAccount.objects.filter(session=session):
            student_data = model_to_dict(student)
            student_data.pop('profile_picture')
            session_data['students'].append(student_data)
        semesters = Semester.objects.filter(session=session)
        for semester in semesters:
            # items: courses, enrollments
            semester_data = {
                'semester_meta': model_to_dict(semester),
                'courses': [],
                'enrolls': []
            }
            semester_drop_courses = [course.id for course in semester_data['semester_meta']['drop_courses']]
            semester_data['semester_meta']['drop_courses'] = semester_drop_courses
            courses = Course.objects.filter(semester=semester)
            for course in courses:
                course_data = {
                    'course_meta': model_to_dict(course),
                    'course_results': []
                }
                course_results = CourseResult.objects.filter(course=course)
                for result in course_results:
                    course_data['course_results'].append(model_to_dict(result))
                semester_data['courses'].append(course_data)
            enrolls = SemesterEnroll.objects.filter(semester=semester)
            for enroll in enrolls:
                enroll_data = model_to_dict(enroll)
                enrolled_courses = [course.id for course in enroll_data['courses']]
                enroll_data['courses'] = enrolled_courses
                semester_data['enrolls'].append(enroll_data)
                
            session_data['semesters'].append(semester_data)
        backup_data['sessions'].append(session_data)
    
    return backup_data
    
        
    