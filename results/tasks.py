from django.contrib.auth.models import User
from account.models import StudentAccount
from results.models import Session, Course, CourseResult, Semester, SemesterEnroll, Department
from celery import shared_task
from celery_progress.backend import ProgressRecorder
import time

@shared_task(bind=True)
def restore_dept_data_task(self, dept_id, sessions_data, total_objects):
    dept = Department.objects.get(id=dept_id)
    semester_drop_courses_prev_IDs = {}
    enrollment_courses_prev_IDs = {}
    semester_hash = {}        # key = previous, value = new object
    enrollment_hash = {}        # key = previous, value = new object
    courses_hash = {}       # key = previous, value = new object
    courseresults_hash = {}      # key = previous, value = new object
    retake_hash = {}    # key = new object, value = carry_of course_result id
    failed_course_results = []
    progress_recorder = ProgressRecorder(self)
    count = 0
    progress_recorder.set_progress(count, total_objects)
    for session_data in sessions_data:
        session_data['session_meta'].pop('id')
        session_data['session_meta']['dept'] = dept
        session = Session(**session_data['session_meta'])
        session.save()
        count += 1
        progress_recorder.set_progress(count, total_objects)
        # Students
        for student_data in session_data['students']:
            student_data.pop('user')
            student_data['session'] = session
            StudentAccount.objects.create(**student_data)
            count += 1
            progress_recorder.set_progress(count, total_objects)
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
                else:
                    sem_data['semester_meta']['added_by'] = None
            semester = Semester(**sem_data['semester_meta'])
            semester.save()
            count += 1
            progress_recorder.set_progress(count, total_objects)
            semester_hash[prev_sem_id] = semester
            # Courses
            for course_data in sem_data['courses']:
                course_data['course_meta'].pop('id')
                course_data['course_meta']['semester'] = semester
                if course_data['course_meta']['added_by']:
                    user = User.objects.filter(username=course_data['course_meta']['added_by']).first()
                    if user:
                        course_data['course_meta']['added_by'] = user
                    else:
                        course_data['course_meta']['added_by'] = None
                course = Course(**course_data['course_meta'])
                course.save()
                count += 1
                progress_recorder.set_progress(count, total_objects)
                courses_hash[course.identifier] = course
                # Course Results
                for result_data in course_data['course_results']:
                    result_id = result_data['id']
                    result_data.pop('id')
                    result_data['course'] = course
                    try:
                        result_data['student'] = StudentAccount.objects.get(registration=result_data['student'])
                    except Exception as e:
                        failed_course_results.append(result_data)
                        continue
                    retake_of_id = result_data['retake_of']
                    result_data.pop('retake_of')
                    course_res_new = CourseResult(**result_data)
                    course_res_new.save()
                    courseresults_hash[result_id] = course_res_new
                    if retake_of_id:
                        retake_hash[course_res_new] = retake_of_id
                    count += 1
                progress_recorder.set_progress(count, total_objects)
                time.sleep(0.2)
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
                count += 1
                progress_recorder.set_progress(count, total_objects)
                enrollment_hash[enrollment_prev_id] = enroll
    # retry failed courseresult creation 
    for result_data in failed_course_results:
        result_data['student'] = StudentAccount.objects.get(registration=result_data['student'])
        retake_of_id = result_data['retake_of']
        result_data.pop('retake_of')
        course_res_new = CourseResult(**result_data)
        course_res_new.save()
        courseresults_hash[result_id] = course_res_new
        if retake_of_id:
            retake_hash[course_res_new] = retake_of_id
        count += 1
    progress_recorder.set_progress(count, total_objects)
    time.sleep(0.2)
    # Binding Retakings
    for new_result, retake_of_id in retake_hash.items():
        new_result.retake_of = courseresults_hash[retake_of_id]
        new_result.save()
    # semester drop courses
    for prevId, newSem in semester_hash.items():
        drop_courses = semester_drop_courses_prev_IDs[prevId]
        for prev_course_id in drop_courses:
            newSem.drop_courses.add(courses_hash[prev_course_id])
        count += len(drop_courses)
        progress_recorder.set_progress(count, total_objects)
    time.sleep(0.2)
    # enrolled courses
    for prevId, newEnroll in enrollment_hash.items():
        enrolled_courses = enrollment_courses_prev_IDs[prevId]
        for prev_course_id in enrolled_courses:
            newEnroll.courses.add(courses_hash[prev_course_id])
        count += len(enrolled_courses)
        progress_recorder.set_progress(count, total_objects)
    

@shared_task(bind=True)
def restore_session_data_task(self, dept_id, session_data, total_objects):
    dept = Department.objects.get(id=dept_id)
    courseresults_hash = {}      # key = previous, value = new object
    retake_hash = {}    # key = new object, value = carry_of course_result id
    progress_recorder = ProgressRecorder(self)
    count = 0
    session_meta = session_data['session_meta']
    session_meta.pop('id')
    session_meta['dept'] = dept
    session = Session(**session_data['session_meta'])
    session.save()
    count += 1
    progress_recorder.set_progress(count, total_objects)
    # Students
    for student_data in session_data['students']:
        student_data.pop('user')
        student_data['session'] = session
        StudentAccount.objects.create(**student_data)
        count += 1
        progress_recorder.set_progress(count, total_objects)
    # Semesters
    for sem_data in session_data['semesters']:
        sem_data['semester_meta'].pop('id')
        drop_course_identifiers = sem_data['semester_meta']['drop_courses']
        sem_data['semester_meta'].pop('drop_courses')
        sem_data['semester_meta']['session'] = session
        if sem_data['semester_meta']['added_by']:
            user = User.objects.filter(username=sem_data['semester_meta']['added_by']).first()
            if user:
                sem_data['semester_meta']['added_by'] = user
            else:
                sem_data['semester_meta']['added_by'] = None
        semester = Semester(**sem_data['semester_meta'])
        semester.save()
        count += 1
        progress_recorder.set_progress(count, total_objects)
        for identifier in drop_course_identifiers:
            semester.drop_courses.add(Course.objects.get(identifier=identifier))
            count += 1
            progress_recorder.set_progress(count, total_objects)
        # Courses
        for course_data in sem_data['courses']:
            # course_data['course_meta'].pop('id')
            course_data['course_meta']['semester'] = semester
            if course_data['course_meta']['added_by']:
                user = User.objects.filter(username=course_data['course_meta']['added_by']).first()
                if user:
                    course_data['course_meta']['added_by'] = user
                else:
                    course_data['course_meta']['added_by'] = None
            course = Course(**course_data['course_meta'])
            course.save()
            count += 1
            progress_recorder.set_progress(count, total_objects)
            # Course Results
            for result_data in course_data['course_results']:
                result_id = result_data['id']
                result_data.pop('id')
                result_data['course'] = course
                result_data['student'] = StudentAccount.objects.get(registration=result_data['student'])
                retake_of_id = result_data['retake_of']
                result_data.pop('retake_of')
                course_res_new = CourseResult(**result_data)
                course_res_new.save()
                courseresults_hash[result_id] = course_res_new
                if retake_of_id:
                    retake_hash[course_res_new] = retake_of_id
                count += 1
            progress_recorder.set_progress(count, total_objects)                    
        # Enrolls
        for enroll_data in sem_data['enrolls']:
            enrolled_course_identifiers = enroll_data['courses']
            enroll_data.pop('id')
            enroll_data.pop('courses')
            enroll_data['student'] = StudentAccount.objects.get(registration=enroll_data['student'])
            enroll_data['semester'] = semester
            enroll = SemesterEnroll(**enroll_data)
            enroll.save()
            count += 1
            progress_recorder.set_progress(count, total_objects)
            for identifier in enrolled_course_identifiers:
                enroll.courses.add(Course.objects.get(identifier=identifier))
                count += 1
                progress_recorder.set_progress(count, total_objects)            
    # Binding Retakings
    for new_result, retake_of_id in retake_hash.items():
        new_result.retake_of = courseresults_hash[retake_of_id]
        new_result.save()
    progress_recorder.set_progress(total_objects, total_objects)
    
@shared_task
def update_student_accounts(reg_nums):
    for reg in reg_nums:
        account = StudentAccount.objects.filter(registration=reg).first()
        if account:
            account.update_stats()