from results.models import Semester, CourseResult
from typing import List
from results.utils import get_ordinal_number

def generate_table_header_data(semester: Semester) -> List[List]:
    """
    will return a list of three list for top three rows of the tabulation
    """
    regular_courses = semester.course_set.all()
    drop_courses = semester.drop_courses.all()
    has_overall_result_coulumn =  (semester.semester_no != 1)
    title_semester_from_to = ""
    if has_overall_result_coulumn:
        semester_from = semester.session.semester_set.all()[0]
        title_semester_from_to = f"{get_ordinal_number(semester_from)} to {get_ordinal_number(semester.semester_no)}\nSemester"
    row1 = [ *['Course Number \u2192\nCredit of the course \u2192', '', '', ''] ,
            *[course.code.upper() for course in drop_courses], # Drop courses
            *[course.code.upper() for course in regular_courses], # Regular Courses
            *[f"{semester.semester_no} Semester", "", *([title_semester_from_to, ""] if has_overall_result_coulumn else [])]]
    
    row2 = [*["SL\nNO.", "Registration", '',''], 
            *['GP' for i in range((drop_courses.count() + regular_courses.count()))], 
            *["Credit", "GPA", *(["Credit", "CGPA"] if has_overall_result_coulumn else [])]]
    
    row3 = [*["", "Student's Name", '',''], 
            *['LG' for i in range((drop_courses.count() + regular_courses.count()))], 
            *["", "LG", *(["", "LG"] if has_overall_result_coulumn else [])]]
    return [row1, row2, row3]