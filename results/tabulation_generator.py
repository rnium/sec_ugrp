from results.models import Semester, CourseResult
from typing import List
from results.utils import get_ordinal_number

def generate_table_header_data(semester: Semester) -> List[List]:
    # will return a list of three list for top three rows of the tabulation
    has_overall_result_coulumn =  (semester.semester_no != 1)
    title_semester_from_to = ""
    if has_overall_result_coulumn:
        semester_from = semester.session.semester_set.all()[0]
        title_semester_from_to = f"{get_ordinal_number(semester_from)} to {get_ordinal_number(semester.semester_no)}\nSemester"
    header_data = []
    row1 = [ *['Course Number \u2192\nCredit of the course \u2192', '', '', ''] ,
            *[f"EEE {int(i/10)+1}0{i%10}\n3.00" for i in range(1, 19)], # Drop courses
            *[f"EEE {int(i/10)+1}0{i%10}\n3.00" for i in range(1, 19)], # Regular Courses
            *[f"{semester.semester_no} Semester", "", *([title_semester_from_to, ""] if has_overall_result_coulumn else [])]]
    
    row2 = [*["SL\nNO.", "Registration", '',''], *['GP' for i in range(18)], *["Credit", "GPA", "Credit", "CGPA"]]
    row3 = [*["", "Student's Name", '',''], *['LG' for i in range(18)], *["", "LG", "", "LG"]]