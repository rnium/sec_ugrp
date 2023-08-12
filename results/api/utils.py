from results.models import Course, CourseResult, Semester, SemesterEnroll



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
        
        
    