from results.models import Semester, CourseResult
from typing import List
from results.utils import get_ordinal_number

class SemesterDataContainer:
    def __init__(self, semester: Semester):
        self.semester = semester
        self.regular_courses = semester.course_set.all()
        self.drop_courses = semester.drop_courses.all()
        self.course_list = [*list(self.drop_courses), *list(self.regular_courses)]
        self.num_courses = len(self.course_list)
        self.students = semester.session.studentaccount_set.all()
        self.num_students = self.students.count()
        self.has_overall_result_coulumn = (semester.semester_no >= 1)
        

def generate_table_header_data(dataContainer: SemesterDataContainer) -> List[List]:
    """
    will return a list of three lists for top three rows of the tabulation table
    """
    has_overall_result =  dataContainer.has_overall_result_coulumn
    title_semester_from_to = ""
    if has_overall_result:
        semester_from = dataContainer.semester.session.semester_set.all().first()
        title_semester_from_to = f"{get_ordinal_number(semester_from)} to {get_ordinal_number(dataContainer.semester.semester_no)}\nSemester"
    row1 = [ *['Course Number \u2192\nCredit of the course \u2192', '', '', ''] ,
            *[course.code.upper() for course in dataContainer.course_list], # Drop courses
            *[f"{dataContainer.semester.semester_no} Semester", "", *([title_semester_from_to, ""] if has_overall_result else [])]]
    
    row2 = [*["SL\nNO.", "Registration", '',''], 
            *['GP' for i in range(dataContainer.num_courses)], 
            *["Credit", "GPA", *(["Credit", "CGPA"] if has_overall_result else [])]]
    
    row3 = [*["", "Student's Name", '',''], 
            *['LG' for i in range(dataContainer.num_courses)], 
            *["", "LG", *(["", "LG"] if has_overall_result else [])]]
    return [row1, row2, row3]


def generate_table_student_data(dataContainer: SemesterDataContainer) -> List[List]:
    pageWise_student_data = []
    sl_number = 1
    for student in dataContainer.students:
        # two row per record, top and bottom
        # staring with student info
        row_top = [sl_number, student.registration, '','']
        row_bottom = ["", student.student_name, '','']
        #courses
        total_credits = 0
        total_points = 0
        for course in dataContainer.course_list:
            try:
                course_result = CourseResult.objects.get(student=student, course=course)
            except CourseResult.DoesNotExist:
                row_top.append("")
                row_bottom.append("")
            gp = course_result.grade_point
            lg = course_result.letter_grade
            # if grade point or letter grade is not set, append a blank string to leave it empty in tabulation
            if gp is None:
                row_top.append("")
            if lg is None:
                row_bottom.append("")
            row_top.append(gp)
            row_bottom.append(lg)
            if gp > 0:
                total_credits += course.course_credit
                total_points += (course.course_credit * gp)
        # append semester result
        # append upto this semester result (the overall result)
            
            