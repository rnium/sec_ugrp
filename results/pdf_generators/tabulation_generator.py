from reportlab.lib.pagesizes import letter, TABLOID, landscape
from reportlab.lib.units import cm, inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
import fitz
from PIL import Image
import math
from results.models import Semester, SemesterEnroll, CourseResult, StudentPoint
from typing import List, Tuple, Dict
from results.utils import get_ordinal_number, get_letter_grade, round_up
from results.api.utils import sort_courses

TABLE_FONT_SIZE = 7
pageSize = (8.5*inch, 14*inch)
h, w = pageSize


class SemesterDataContainer:
    def __init__(self, semester: Semester):
        regular_coruses = semester.course_set.filter(is_carry_course=False).order_by('id')
        created_drop_courses = semester.course_set.filter(is_carry_course=True).order_by('id')
        drop_courses = semester.drop_courses.all().order_by('id')
        self.semester = semester
        self.regular_courses = regular_coruses
        self.created_drop_courses = created_drop_courses
        self.drop_courses = drop_courses
        self.course_list = [*list(self.drop_courses), *list(created_drop_courses), *list(self.regular_courses)]
        self.num_courses = len(self.course_list)
        self.students = [enroll.student for enroll in semester.semesterenroll_set.all()]
        self.num_students = len(self.students)
        self.has_overall_result_coulumn = (semester.semester_no > 1)
        
        

def cumulative_semester_result(student, semesters, pure_cumulative=True):
    total_credits = 0
    total_points = 0
    # PreviousPoint data
    prevpoint = None
    if (pure_cumulative) and hasattr(student.session, 'previouspoint'):
        prevpoint = student.session.previouspoint
        student_point = StudentPoint.objects.filter(student=student, prev_point=prevpoint).first()
        if student_point:
            total_credits += student_point.total_credits
            total_points += student_point.total_points
    for semester in semesters:
        if prevpoint and (semester.semester_no <= prevpoint.upto_semester_num):
            continue
        enrollment = SemesterEnroll.objects.filter(semester=semester, student=student).first()
        if enrollment:
            total_credits += enrollment.semester_credits
            total_points += enrollment.semester_points
    result = {}
    if total_credits == 0:
        result['grade_point'] = "0"; 
        result['letter_grade'] = "F"
        result['total_credits'] = 0
    else:
        overall_grade_point = (total_points/total_credits)
        result['grade_point'] = round_up(overall_grade_point, 2)
        result['letter_grade'] = get_letter_grade(result['grade_point'])
        result['total_credits'] = total_credits
    # {'grade_point':round(overall_grade_point, 2), 'letter_grade':overall_letter_grade, 'total_credits':total_credits},
    return result

 
def generate_table_header_data(dataContainer: SemesterDataContainer) -> List[List]:
    """
    will return a list of three lists for top three rows of the tabulation table
    """
    has_overall_result =  dataContainer.has_overall_result_coulumn
    title_semester_from_to = ""
    if has_overall_result:
        semester_from = dataContainer.semester.session.semester_set.all().first()
        sem_from_num = semester_from.semester_no
        if hasattr(dataContainer.semester.session, 'previouspoint'):
            sem_from_num = 1
        title_semester_from_to = f"{get_ordinal_number(sem_from_num)} to {get_ordinal_number(dataContainer.semester.semester_no)}\nSemester"
    row1 = [ *['Course Number \u2192\nCredit of the course \u2192', '', '', ''] ,
            *[f"{course.code.upper()}\n{course.course_credit}" for course in dataContainer.course_list],
            *[f"{get_ordinal_number(dataContainer.semester.semester_no)} Semester", "", *([title_semester_from_to, ""] if has_overall_result else [])]]
    
    row2 = [*["SL\nNO.", "Registration", '',''], 
            *['GP' for i in range(dataContainer.num_courses)], 
            *["Credit", "GPA", *(["Credit", "CGPA"] if has_overall_result else [])]]
    
    row3 = [*["", "Student's Name", '',''], 
            *['LG' for i in range(dataContainer.num_courses)], 
            *["", "LG", *(["", "LG"] if has_overall_result else [])]]
    return [row1, row2, row3]


def generate_table_student_data(dataContainer: SemesterDataContainer, render_config: Dict) -> List[List]:
    pageWise_student_data = []
    semester = dataContainer.semester
    recordPerPage = render_config["rows_per_page"]
    sl_number = 1
    for i in range(0, dataContainer.num_students, recordPerPage):
        singlePageData = []
        for student in dataContainer.students[i:i+recordPerPage]:
            # two row per record, top and bottom
            # staring with student info
            row_top = [sl_number, student.registration, '','']
            row_bottom = ["", student.student_name, '','']
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
                        row_top.append('Ab')
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
                
            singlePageData.append(row_top)
            singlePageData.append(row_bottom)
        pageWise_student_data.append(singlePageData)
    return pageWise_student_data
            

def get_table_data(dataContainer: SemesterDataContainer, render_config: Dict):
    header = generate_table_header_data(dataContainer)
    student_data_of_pages = generate_table_student_data(dataContainer, render_config)
    table_data = []
    for records_of_page in student_data_of_pages:
        page_data = [*header, *records_of_page]
        table_data.append(page_data)
    return table_data
    
def get_footer_data(footer_data_raw: Dict):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("topTitle", 
                            styles["Normal"],
                            fontSize = 8))
    main_label = Paragraph("<b>Name, Signature & Date:</b>", style=styles['topTitle'])
    chairman_name = ""
    if footer_data_raw["chairman"] is not None:
        chairman_name = footer_data_raw["chairman"]
    controller_name = ""
    if footer_data_raw["controller"] is not None:
        controller_name = footer_data_raw["controller"]
    exam_committee_members = footer_data_raw.get("committee", [])[:4]
    exam_committee_blanks = ["" for i in range(4-len(exam_committee_members))]
    tabulators = footer_data_raw.get("tabulators", [])[:4]
    tabulator_blanks = ["" for i in range(4-len(tabulators))]
    
    footer_data = [
        [main_label, "", "", "", ""],
        [f"Chairman of the Exam. Committee: {'.' * 100}", "", "", f"Controller of Examination: {'.'*100}", ""],
        ["", chairman_name, "", "", controller_name],
        ["Member of the Exam. Committee", *[f"0{i}) {'.'*50}" for i in range(1,len(exam_committee_members)+1)], *exam_committee_blanks],
        ["", *exam_committee_members, *exam_committee_blanks],
        ["Tabulators:", *[f"0{i}) {'.'*50}" for i in range(1,len(tabulators)+1)], *tabulator_blanks],
        ["", *tabulators, *tabulator_blanks],
    ]
    return footer_data
  
def render_spans(num_rows: int, num_cols: int, nth_semester: int) -> List[Tuple]:
    spans = []
    if (nth_semester == 1 and num_cols < 7) or (nth_semester > 1 and num_cols < 9):
        raise ValueError()
    # first row static spans
    spans.append(('SPAN', (0, 0), (3,0))) 
    spans.append(('SPAN', (-2, 0), (-1, 0)))
    if nth_semester > 1:
        spans.append(('SPAN', (-4, 0), (-3, 0))) 
    # row-wise spans 
    for i in range(1, num_rows, 2):
        spans.append(('SPAN', (0, i), (0, i+1)))
        spans.append(('SPAN', (-2, i), (-2, i+1))) # 2nd rightmost col
        if (nth_semester > 1):
            spans.append(('SPAN', (-4, i), (-4, i+1))) # 4th rightmost col
    # col-wise spans
    for i in range(1, num_rows):
        spans.append(('SPAN', (1, i), (3, i)))
    return spans
    

def render_normal_font_cell_style(num_rows: int, num_cols: int, nth_semester: int) -> List[Tuple]:
    if num_cols < 8 and num_rows < 6:
        raise ValueError()
    styles = []
    for i in range(4, num_rows, 2):
        styles.append(('FONTNAME', (1, i), (1, i), 'Times-Roman'))
    for i in range(3, num_rows, 2):
        styles.append(('FONTNAME', (-2, i), (-2, i), 'Times-Roman'))
        if nth_semester > 1:
            styles.append(('FONTNAME', (-4, i), (-4, i), 'Times-Roman'))
    if nth_semester == 1:
        styles.append(('FONTSIZE', (2, 0), (-3, 0), TABLE_FONT_SIZE-1))
        styles.append(('FONTSIZE', (2, 1), (-3, 2), TABLE_FONT_SIZE))
    else:
        styles.append(('FONTSIZE', (2, 0), (-5, 0), TABLE_FONT_SIZE-1))
        styles.append(('FONTSIZE', (2, 1), (-5, 2), TABLE_FONT_SIZE))
    return styles
    

def calculate_column_widths(num_columns):
    available_width = w - 1.5*inch  # Adjust this value based on your page width
    column_width = available_width / num_columns
    return num_columns * [column_width]

def calculate_table_column_widths(num_columns):
    available_width = w - 1.5*inch  # Adjust this value based on your page width
    column_width = available_width / num_columns
    col_widths_array = [column_width for i in range(num_columns)]
    col_widths_array[0] = (column_width * 0.4)
    col_widths_array[1] = (column_width + (column_width * 0.6))
    return col_widths_array


def insert_header(flowables: list, semesterData: SemesterDataContainer, render_config):
    semester = semesterData.semester
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("topTitle", 
                            styles["Normal"],
                            fontName = "Times-Bold",
                            fontSize = 16,
                            alignment = TA_CENTER))

    styles.add(ParagraphStyle("tablulatio_title", 
                            styles["Normal"],
                            fontName = "Times-Bold",
                            fontSize = 13,
                            alignment = TA_CENTER))

    styles.add(ParagraphStyle("institute_title", 
                            styles["Normal"],
                            fontName = "Times-Bold",
                            fontSize = 9,
                            alignment = TA_LEFT))

    styles.add(ParagraphStyle("exam_title", 
                            styles["Normal"],
                            fontName = "Times-Bold",
                            fontSize = 9,
                            alignment = TA_CENTER))

    styles.add(ParagraphStyle("bottom_row_paragraph1", 
                            styles["Normal"],
                            fontName = "Times-Bold",
                            fontSize = 9))

    styles.add(ParagraphStyle("bottom_row_paragraph2", 
                            styles["bottom_row_paragraph1"],
                            alignment = TA_CENTER))

    styles.add(ParagraphStyle("bottom_row_paragraph3", 
                            styles["bottom_row_paragraph1"],
                            alignment = TA_RIGHT))
    
    bottom_table_style = TableStyle([
        # ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('SPAN', (0, 0), (-1, 0)),
        # ('ALIGN', (1, 0), (2, 0), 'CENTER')
    ])
    
    title_text = "SHAHJALAL UNIVERSITY OF SCIENCE & TECHNOLOGY, SYLHET"
    tablulatio_title = "TABULATION SHEET"
    institute_title = "NAME OF INSTITUTE: SYLHET ENGINEERING COLLEGE, SYLHET"
    exam_title = render_config.get('tabulation_title', f"{semester.semester_name} Final Examination 2022")
    dept_title = f"Name of the Department: {semester.session.dept.fullname}"
    exam_held_month = f"Examination Held in {render_config.get('tabulation_exam_time', semester.start_month)}"
    session = f"Session: {semester.session.session_code_formal}"
    label_data = [
        [Paragraph(institute_title, style=styles["institute_title"]), '', ''],
        ['', Paragraph(exam_title, style=styles["exam_title"]), ''],
        [Paragraph(dept_title, style=styles["bottom_row_paragraph1"]),
        Paragraph(exam_held_month, style=styles["bottom_row_paragraph2"]),
        Paragraph(session, style=styles["bottom_row_paragraph3"]),]
    ]
    flowables.append(Paragraph(title_text, style=styles["topTitle"]))
    flowables.append(Spacer(1, 0.2*cm))
    flowables.append(Paragraph(tablulatio_title, style=styles["tablulatio_title"]))
    flowables.append(Spacer(1, 0.2*cm))
    table = Table(data=label_data, colWidths=calculate_column_widths(len(label_data[0])))
    table.setStyle(bottom_table_style)
    flowables.append(table)


def insert_table(data: List[List], flowables: List, nth_semester: int):
    spans = render_spans(len(data), len(data[0]), nth_semester)
    normal_font_styles = render_normal_font_cell_style(len(data), len(data[0]), nth_semester)
    table_style = TableStyle([
        # ('WORDWRAP', (0, 0), (-1, -1), True),   # Enable word wrap for all cells
        # ('SHRINK', (0, 0), (-1, -1), 1), 
        ('FONTSIZE', (0, 0), (-1, -1), TABLE_FONT_SIZE), 
        # ('BACKGROUND', (0, 0), (-1, 0), colors.grey),    # Header row background color
        # ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Header row text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),            # Center align all cells
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Times-Bold'), # By default: all bold
        *normal_font_styles,
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0.7),
        ('TOPPADDING', (0, 0), (-1, -1), 0.7),
        # ('BACKGROUND', (0, 1), (1, 2), colors.lightblue), # Background color for specific cells
        # ('SPAN', (0, 1), (1, 1)),                         # Merge cells (rowspan and columnspan)
        ('GRID', (0, 0), (-1, -1), 1, colors.black),      # Add grid lines to all cells
        ('FONTSIZE', (2, 3), (-1, -1), TABLE_FONT_SIZE+2),
        ('FONTSIZE', (0, 1), (0, 1), TABLE_FONT_SIZE-2),
        *spans
    ])

    table = Table(data, colWidths=calculate_table_column_widths(len(data[0])))
    # Apply the custom TableStyle to the table
    table.setStyle(table_style)
    flowables.append(table)
    return


def get_footer(footer_data: List[List]):
    PADDING_STYLES = [('BOTTOMPADDING', (0, 0), (-1, -1), 0), ('TOPPADDING', (0, 0), (-1, -1), 0)]
    if len(footer_data) > 2:
        for row in range(2, len(footer_data), 2):
            PADDING_STYLES.append(('BOTTOMPADDING', (0, row), (-1, row), 8))
    ts = TableStyle([
        # ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), TABLE_FONT_SIZE), 
        *PADDING_STYLES
    ])
    table = Table(footer_data, colWidths=calculate_column_widths(len(footer_data[0])))
    table.setStyle(ts)
    return table


def add_footer(canvas, doc, footer_data, margin_y=cm):
    footer = get_footer(footer_data)
    footer.wrapOn(canvas, 0, 0)
    footer.drawOn(canvas=canvas, x=0.7*inch, y=margin_y)


def build_doc_buffer(semesterData:SemesterDataContainer, dataset, render_config, footer_data) -> BytesIO:
    flowables = []
    for data in dataset:
        insert_header(flowables, semesterData, render_config)
        flowables.append(Spacer(1, 0.5*cm))
        insert_table(data, flowables, semesterData.semester.semester_no)
        flowables.append(Spacer(1, 0.5*cm))
        # insert_footer(footer_data, flowables)
        flowables.append(PageBreak())
    # Create the PDF document 
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer,
                            pagesize = landscape(pageSize),
                            # leftMargin = 1*inch,
                            # rightMargin = 1*inch,
                            topMargin = 0.8*cm,
                            bottomMargin = 0.8*cm,
                            title=f"Tabulation sheet"
                            )
    # Building
    doc.build(flowables, onFirstPage=lambda canv, doc: add_footer(canv, doc, footer_data), onLaterPages=lambda canv, doc: add_footer(canv, doc, footer_data))
    return buffer

def get_thumnail_image(pdf_file: BytesIO) -> bytes:
    doc = fitz.open(stream=pdf_file, filetype="pdf")
    page = doc[0]
    zoom_scale = {'x':2.0, 'y':2.0}
    mat = fitz.Matrix(*zoom_scale.values())
    img_pixmap = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", (img_pixmap.width, img_pixmap.height), img_pixmap.samples)
    img_buffer = BytesIO()
    img.save(img_buffer, format="PNG")
    return img_buffer.getvalue()


def get_tabulation_files(semester: Semester, render_config: Dict, footer_data_raw: Dict) -> Dict[str,bytes]:
    datacontainer = SemesterDataContainer(semester)
    dataset = get_table_data(datacontainer, render_config)
    footer_data = get_footer_data(footer_data_raw)
    # filename = f"{get_ordinal_number(semester.semester_no)} semester ({semester.session.dept.upper()} {semester.session.session_code}).pdf"
    buffer = build_doc_buffer(datacontainer, dataset, render_config, footer_data)
    files = {}
    files['pdf_file'] = buffer.getvalue()
    try:
        files['thumbnail_file'] = get_thumnail_image(files['pdf_file']) #thumbnail is in png format
    except Exception as e:
        files['thumbnail_file'] = None
    return files


    

