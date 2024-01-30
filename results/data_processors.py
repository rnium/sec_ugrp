from results.pdf_generators.tabulation_generator import SemesterDataContainer
from results.pdf_generators.tabulation_generator import cumulative_semester_result
from results.models import Semester, CourseResult
from results.utils import get_ordinal_number


def generate_table_header_data(dataContainer: SemesterDataContainer):
    has_overall_result =  dataContainer.has_overall_result_coulumn
    title_semester_from_to = ""
    if has_overall_result:
        semester_from = dataContainer.semester.session.semester_set.all().first()
        sem_from_num = semester_from.semester_no
        if hasattr(dataContainer.semester.session, 'previouspoint'):
            sem_from_num = 1
        title_semester_from_to = f"{get_ordinal_number(sem_from_num)} to {get_ordinal_number(dataContainer.semester.semester_no)} Semester"
    row1 = [ *["", "Course Numbber (Credit)"] ,
            *[f"{course.code.upper()} ({course.course_credit})" for course in dataContainer.course_list],
            *[f"{get_ordinal_number(dataContainer.semester.semester_no)} Semester", "", *([title_semester_from_to, ""] if has_overall_result else [])]]
    
    row2 = [*["SL NO.", "Registration"], 
            *['GP' for i in range(dataContainer.num_courses)], 
            *["Credit", "GPA", *(["Credit", "CGPA"] if has_overall_result else [])]]
    
    row3 = [*["", "Student's Name"], 
            *['LG' for i in range(dataContainer.num_courses)], 
            *["","LG", *(["", "LG"] if has_overall_result else [])]]
    return [row1, row2, row3]


def prepare_table_data(dataContainer: SemesterDataContainer):
    header_data = generate_table_header_data(dataContainer)
    students_data = [*header_data]
    semester = dataContainer.semester
    sl_number = 1
    for student in dataContainer.students:
        row_top = [sl_number, student.registration]
        row_bottom = ['', student.student_name]
        sl_number += 1
        #courses
        total_credits = 0
        total_points = 0
        for course in dataContainer.course_list:
            try:
                course_result = CourseResult.objects.get(student=student, course=course)
            except CourseResult.DoesNotExist:
                row_top.append("")
                row_bottom.append("")
                continue
            gp = course_result.grade_point
            lg = course_result.letter_grade
            # if grade point or letter grade is not set, append a blank string to leave it empty in tabulation
            
            if gp is None or lg is None:
                if gp is None:
                    row_top.append('A')
                if lg is None:
                    row_bottom.append('F')
                continue
            row_top.append(gp)
            row_bottom.append(lg)
            if gp > 0:
                total_credits += course.course_credit
                total_points += (course.course_credit * gp)
        # append semester result
        semester_result = cumulative_semester_result(student, [semester], False) # passing semester in a list beacuse the function expects an iterable
        if semester_result:
            row_top.append(semester_result['total_credits'])
            row_top.append(semester_result['grade_point'])
            row_bottom.append("") # for the span
            row_bottom.append(semester_result['letter_grade'])
        else:
            row_top.append("")
            row_bottom.append("") # for the span
            row_bottom.append("")
        # append upto this semester result (the overall result) (except first semester)
        if dataContainer.semester.semester_no > 1:
            semesters_upto_now = Semester.objects.filter(semester_no__lte=semester.semester_no, session=semester.session)
            semester_result_all = cumulative_semester_result(student, semesters_upto_now)
            if semester_result:
                row_top.append(semester_result_all['total_credits'])
                row_top.append(semester_result_all['grade_point'])
                row_bottom.append("") # for the span
                row_bottom.append(semester_result_all['letter_grade'])
            else:
                row_top.append("")
                row_bottom.append("") # for the span
                row_bottom.append("")
            
        students_data.append(row_top)
        students_data.append(row_bottom)
    return students_data

def get_semester_table_data(semester):
    datacon = SemesterDataContainer(semester)
    return prepare_table_data(datacon)