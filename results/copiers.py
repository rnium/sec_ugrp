from django.forms.models import model_to_dict
from results.models import Semester, ExamCommittee, Course


def copy_committee(from_semester, to_semester):
    from_committee, created = ExamCommittee.objects.get_or_create(semester=from_semester)
    to_committee, created = ExamCommittee.objects.get_or_create(semester=to_semester)
    to_committee.chairman = from_committee.chairman
    to_committee.members.set(from_committee.members.all())
    to_committee.tabulators.set(from_committee.tabulators.all())
    to_committee.save()

def copy_courses(from_semester: Semester, to_semester: Semester, user):
    for course in from_semester.course_set.all().order_by('id'):
        course_data = model_to_dict(course, exclude=['semester', 'added_by', 'added_in', 'identifier', 'id'])
        new_course = Course(semester=to_semester, added_by=user, **course_data)
        new_course.save()
    to_semester.drop_courses.set(from_semester.drop_courses.all())
        
def find_from_semester(target_semester_no):
    semesters_qs = Semester.objects.filter(
        semester_no=target_semester_no, is_running=True, part_no = 0, repeat_number = 0
    ).order_by('-session__from_year')
    return semesters_qs.first()


def copyCoursesAndSemesters(to_semester, user):
    from_sem = find_from_semester(to_semester.semester_no)
    if to_semester == None or from_sem == None:
        return
    copy_committee(from_sem, to_semester)
    copy_courses(from_sem, to_semester, user)