from django.contrib.auth import authenticate
from django.contrib.auth.models import User
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
            if (semester.added_by):
                semester_data['semester_meta']['added_by'] = semester.added_by.username
            courses = Course.objects.filter(semester=semester)
            for course in courses:
                course_data = {
                    'course_meta': model_to_dict(course),
                    'course_results': []
                }
                if course.added_by:
                    course_data['course_meta']['added_by'] = course.added_by.username
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
    
def delete_all_of_dept(dept: Department):
    sessions = dept.session_set.all()
    sessions.delete()


def restore_data(dept, sessions_data):
    semester_drop_courses_prev_IDs = {}
    enrollment_courses_prev_IDs = {}
    semester_hash = {}        # key = previous, value = new object
    enrollment_hash = {}        # key = previous, value = new object
    courses_hash = {}       # key = previous, value = new object
    failed_course_results = []
    for session_data in sessions_data:
        session_data['session_meta'].pop('id')
        session_data['session_meta']['dept'] = dept
        session = Session(**session_data['session_meta'])
        session.save()
        # Students
        for student_data in session_data['students']:
            student_data.pop('user')
            student_data['session'] = session
            StudentAccount.objects.create(**student_data)
        # Semesters
        for sem_data in session_data['semesters']:
            prev_sem_id = sem_data['semester_meta']['id']
            semester_drop_courses_prev_IDs[prev_sem_id] = sem_data['semester_meta']['drop_courses']
            sem_data['semester_meta'].pop('id')
            sem_data['semester_meta'].pop('drop_courses')
            sem_data['semester_meta']['session'] = session
            if sem_data['semester_meta']['added_by']:
                user = User.objects.filter(username=sem_data['semester_meta']['added_by']).first()
                if user:
                    sem_data['semester_meta']['added_by'] = user
            semester = Semester(**sem_data['semester_meta'])
            semester.save()
            semester_hash[prev_sem_id] = semester
            # Courses
            for course_data in sem_data['courses']:
                prev_id = course_data['course_meta']['id']
                course_data['course_meta'].pop('id')
                course_data['course_meta']['semester'] = semester
                if course_data['course_meta']['added_by']:
                    user = User.objects.filter(username=course_data['course_meta']['added_by']).first()
                    if user:
                        course_data['course_meta']['added_by'] = user
                course = Course(**course_data['course_meta'])
                course.save()
                courses_hash[prev_id] = course
                # Course Results
                course_res_bulks = []
                for result_data in course_data['course_results']:
                    result_data.pop('id')
                    result_data['course'] = course
                    try:
                        result_data['student'] = StudentAccount.objects.get(registration=result_data['student'])
                    except Exception as e:
                        failed_course_results.append(result_data)
                        continue
                    course_res_bulks.append(CourseResult(**result_data))
                CourseResult.objects.bulk_create(course_res_bulks)
            # Enrolls
            for enroll_data in sem_data['enrolls']:
                enrollment_prev_id = enroll_data['id']
                enrollment_courses_prev_IDs[enrollment_prev_id] = enroll_data['courses']
                enroll_data.pop('id')
                enroll_data.pop('courses')
                enroll_data['student'] = StudentAccount.objects.get(registration=enroll_data['student'])
                enroll_data['semester'] = semester
                enroll = SemesterEnroll(**enroll_data)
                enroll.save()
                enrollment_hash[enrollment_prev_id] = enroll
    # retry failed courseresult creation 
    course_result_bulks = []
    for result_data in failed_course_results:
        result_data['student'] = StudentAccount.objects.get(registration=result_data['student'])
        course_result_bulks.append(CourseResult(**result_data))
    CourseResult.objects.bulk_create(course_result_bulks)
    # semester drop courses
    for prevId, newSem in semester_hash.items():
        drop_courses = semester_drop_courses_prev_IDs[prevId]
        for prev_course_id in drop_courses:
            newSem.drop_courses.add(courses_hash[prev_course_id])
    # enrolled courses
    for prevId, newEnroll in enrollment_hash.items():
        enrolled_courses = enrollment_courses_prev_IDs[prevId]
        for prev_course_id in enrolled_courses:
            newEnroll.courses.add(courses_hash[prev_course_id])
    
    
                
                    
    