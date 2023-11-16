from django.contrib.auth.models import User
from account.models import StudentAccount
from results.models import Session, Course, CourseResult, Semester, SemesterEnroll, Department
from celery import shared_task

@shared_task(bind=True)
def restore_data_task(self, dept_id, sessions_data):
    dept = Department.objects.get(id=dept_id)
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
    
    