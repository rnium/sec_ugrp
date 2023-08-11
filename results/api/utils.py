from results.models import Course, CourseResult, Semester, SemesterEnroll



def create_course_enrollments(semester: Semester):
    object_prototypes = []
    for student in semester.session.studentaccount_set.all():
        object_prototypes.append(SemesterEnroll(student=student, semester=semester))
    
    SemesterEnroll.objects.bulk_create(object_prototypes)
    


def create_course_results(course: Course):
    object_prototypes = []
    for student in course.semester.session.studentaccount_set.all():
        object_prototypes.append(CourseResult(student=student, course=course))
    
    CourseResult.objects.bulk_create(object_prototypes)
