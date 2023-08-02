from results.models import Course, CourseResult


def create_course_results(course: Course):
    object_prototypes = []
    for student in course.semester.session.studentaccount_set.all():
        object_prototypes.append(CourseResult(student=student, course=course))
    print("creating obj")
    
    CourseResult.objects.bulk_create(object_prototypes)