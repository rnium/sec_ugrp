from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer
from reportlab.platypus import Paragraph
from reportlab.platypus import Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
from io import BytesIO
from django.conf import settings
from results.utils import get_letter_grade, get_ordinal_number
from results.models import SemesterEnroll

DEBUG_MODE = False

w, h = A4
margin_X = 0.5*inch
margin_Y = 0.5*inch

CARDINAL_NUMBERS = {1: "First", 2: "Second", 3: "Third", 4: "Fourth"}
cardinal_repr = lambda n: CARDINAL_NUMBERS.get(n) # Cardinal representation

pdfmetrics.registerFont(TTFont('roboto', settings.BASE_DIR/'results/static/results/fonts/Roboto-Regular.ttf'))
pdfmetrics.registerFont(TTFont('roboto-bold', settings.BASE_DIR/'results/static/results/fonts/Roboto-Bold.ttf'))
pdfmetrics.registerFont(TTFont('roboto-italic', settings.BASE_DIR/'results/static/results/fonts/Roboto-MediumItalic.ttf'))
pdfmetrics.registerFont(TTFont('roboto-m', settings.BASE_DIR/'results/static/results/fonts/Roboto-Medium.ttf'))


def calculate_column_widths(num_columns, container_width, margin):
    available_width = container_width - 2*margin 
    column_width = available_width / num_columns
    return [column_width] * num_columns

def get_grading_scheme_table() -> Table:
    data = [
        ['Numerical Grade', 'Letter Grade', 'Grade Point'],
        ['80% or above', 'A+', '4.00'],
        ['75% to less than 80%', 'A', '3.75'],
        ['70% to less than 75%', 'A-', '3.50'],
        ['65% to less than 70%', 'B+', '3.25'],
        ['60% to less than 65%', 'B', '3.00'],
        ['55% to less than 60%', 'B-', '2.75'],
        ['50% to less than 55%', 'C+', '2.50'],
        ['45% to less than 50%', 'C', '2.25'],
        ['40% to less than 45%', 'C-', '2.00'],
        ['less than 40%', 'F', '0.00'],
    ]
    style = TableStyle([
        *[('BOX', (0+i,0), (0+i,-1), 0.25, colors.gray) for i in range(3)],
        ('GRID', (0,0), (-1,0), 0.25, colors.gray),
        ('FONTSIZE', (0, 0), (-1, -1), 7), 
        ('FONTNAME', (0, 0), (-1, -1), 'roboto-m'),
        # ('LINEABOVE', (0, 0), (-1, -1), 0.1, colors.white),  # Remove top row separator line
        # ('LINEBELOW', (0, 0), (-1, -1), 0.1, colors.white),
        # ('BOX', (0, 0), (-1, -1), 0.25, colors.gray),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])

    # Create a Table
    first_col_str = data[0][0]
    second_col_str = data[0][1]
    third_col_str = data[0][2]
    for dataset in data[1:]:
        first_col_str += "\n" + dataset[0]
        second_col_str += "\n" + dataset[1]
        third_col_str += "\n" + dataset[2]
    rowHeights = [11]
    rowHeights.extend([10 for i in range(len(data)-1)])
    
     
    tbl = Table(data=data, rowHeights=rowHeights)
    tbl.setStyle(style);
    return tbl
 
 
def build_header(flowables, student) -> None:
    logo = Image(settings.BASE_DIR/'results/static/results/images/sust.png', width=45.5, height=50)
    bold_paragraph_style = ParagraphStyle(
        name='bold_paragraph_style',
        fontSize=10,  # Set the font size to 14 points
    )
    univ_style = ParagraphStyle(
        name='bold_paragraph_style',
        fontName='roboto-bold',  # Specify the bold font
        fontSize=11,  # Set the font size to 14 points
        alignment=0,  # Center alignment
    )
    university = Paragraph('SHAHJALAL UNIVERSITY OF SCIENCE AND TECHNOLOGY, SYLHET, BANGLADESH.', univ_style)
    dept_name_paragraph = Paragraph(f": <b>{student.session.dept.fullname}</b>", style=bold_paragraph_style)
    grading_scheme_table = get_grading_scheme_table()
    table_data = [
        [logo, university, '', ''],
        ['', 'Grade Certificate', '', grading_scheme_table],
        ['', "B. Sc. (Engg.) Examination", ''],
        ['', "Session", f": {student.session.session_code}", ''],
        ['Name of the College', '', ": Sylhet Engineering College, Sylhet", ''],
        ['Department', '', dept_name_paragraph, ''],
        [Spacer(1, 0.1*cm), Spacer(1, 0.1*cm), Spacer(1, 0.1*cm), ''],
        ['Registration No.', '', f": {student.registration}", ''],
        ['Name of the Student', '', f": {student.student_name.upper()}", ''],
    ]
    tblstyle_config = [
        ('SPAN', (0, 0), (0, 2)),
        ('SPAN', (1, 0), (-1, 0)), # university
        ('FONTSIZE', (1, 1), (1, 1), 11), # grade cert. fontsize
        ('FONTNAME', (1, 1), (1, 1), 'roboto'), # grade cert. font name
        
        ('SPAN', (-1, 1), (-1, -1)),
        *[('SPAN', (1, 1+i), (2, 1+i)) for i in range(2)],
        *[('SPAN', (0, 4+i), (1, 4+i)) for i in range(5)],
        ('ALIGN', (-1, 1), (-1, 1), 'RIGHT'),
        ('VALIGN', (-1, 1), (-1, 1), 'MIDDLE'),
    ]
    if DEBUG_MODE:
        tblstyle_config.extend([('GRID', (0,0), (-1,-1), 0.25, colors.royalblue)])
        
    tbl = Table(data=table_data, colWidths=[0.75*inch, 0.7*inch, 3*inch, 2.8*inch])
    tbl.setStyle(TableStyle(tblstyle_config))
    flowables.append(tbl)


def cumulative_semester_data(student, semester_upto):
    data = {}
    enrolls = SemesterEnroll.objects.filter(semester__semester_no__lte=semester_upto, student=student)
    credits_count = 0
    points_count = 0
    for enroll in enrolls:
        credits_count += enroll.semester_credits
        points_count += enroll.semester_points
    if points_count:
        data['credit'] = credits_count
        data['grade_point'] = points_count / credits_count
        data['letter_grade'] = get_letter_grade(data['grade_point'])
    return data
        

def get_courses_data(semester_enroll, blank_list):
    dataset = []
    courses = semester_enroll.courses.all()
    for course in courses:
        record = course.courseresult_set.filter(student=semester_enroll.student).first()
        data = [
            course.code,
            course.title,
            *blank_list,
            course.course_credit if record.grade_point else 0,
            record.grade_point,
            record.letter_grade
        ]
        dataset.append(data)
    return dataset


def build_semester(flowables, semester_enroll, cumulative_data) -> None:
    course_title_extras = ['', '', '', '']
    course_dataset = get_courses_data(semester_enroll, course_title_extras)
    num_courses = len(course_dataset)
    
    data = [
        [f'{cardinal_repr(semester_enroll.semester.year)} Year {cardinal_repr(semester_enroll.semester.year_semester)} Semester', *course_title_extras, f'Held in: {semester_enroll.semester.start_month}', '', '', ''],
        ['Course No.', 'Course Title', *course_title_extras, 'Credit', 'Grade Obtained', ''],
        ['', '', '', *course_title_extras, 'Grade Point', 'Letter Grade'],
        # courses
        *course_dataset,
        [*course_title_extras, 'This Semester Total:', '', semester_enroll.semester_credits, f'{semester_enroll.semester_gpa:.2f}', get_letter_grade(semester_enroll.semester_gpa)],
        [*course_title_extras, 'Cumulative:', '', cumulative_data['credit'], f"{cumulative_data['grade_point']:.2f}", cumulative_data['letter_grade']],
    ]
    header_row_heights = [15] * 3
    course_row_heights = [14] * num_courses
    bottom_row_heights = [14] * 2
    semester_table_style = TableStyle([
        ('GRID', (0,1), (-1,-3), 0.15, colors.gray),
        ('GRID', (-5,-2), (-1,-1), 0.15, colors.gray),
        # top header spans
        ('SPAN', (0, 0), (-5, 0)),
        ('SPAN', (-4, 0), (-1, 0)),
        # table header
        ('SPAN', (0, 1), (0, 2)),
        ('SPAN', (1, 1), (1, 2)),
        ('SPAN', (-3, 1), (-3, 2)),
        ('SPAN', (-2, 1), (-1, 1)),
        ('SPAN', (1, 1), (-4, 2)), # course title span
        ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
        ('ALIGN', (0, 3), (0, -1), 'CENTER'), # Course number
        ('VALIGN', (0, 1), (-3, 1), 'MIDDLE'),
        ('VALIGN', (-2, 2), (-1, 2), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 2), 'roboto-bold'),
        ('FONTSIZE', (0, 0), (-1, 2), 9),
        ('FONTSIZE', (-2, 2), (-1, 2), 7),
        *[('SPAN', (1, 3+i), (-4, 3+i)) for i in range(num_courses)], # course title spans
        ('ALIGN', (-3, 3), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 3), (-1, -3), 'roboto'), # course about
        ('FONTSIZE', (0, 3), (-1, -3), 9),
        ('VALIGN', (0, 3), (-1, -1), 'MIDDLE'),
         # bottom two rows
        ('SPAN', (-5, -2), (-4, -2)),
        ('SPAN', (-5, -1), (-4, -1)),
        ('FONTNAME', (-5, -2), (-5, -1), 'roboto-bold'),
        ('FONTSIZE', (-5, -2), (-5, -1), 9),
        ('FONTSIZE', (-3, -2), (-1, -1), 9), # bottom totals
        
        
    ])
    table = Table(data=data, colWidths=calculate_column_widths(len(data[0]), w, margin_X+0.2*cm), rowHeights=[*header_row_heights, *course_row_heights, *bottom_row_heights])
    table.setStyle(semester_table_style)
    flowables.append(table)
  
    
def get_footer(second_sem_cumulative):
    header_style = ParagraphStyle(
        name='bold_paragraph_style',
        fontName='roboto-bold',  # Specify the bold font
        fontSize=9,  # Set the font size to 14 points
        alignment=1,  # Center alignment
    )
    footer_top_data = [
        ['', Paragraph('<u>Final Result</u>', style=header_style), '', '', '', 'With Distinction'],
        ['', 'Cumulative', 'Credit', 'CGPA', 'Letter Grade', ''],
        ['', 'Final Result', second_sem_cumulative['credit'], f"{second_sem_cumulative['grade_point']:.2f}", second_sem_cumulative['letter_grade'], '']
    ]
    footer_top_style_config = [
        ('SPAN', (1, 0), (-2, 0)),
        ('SPAN', (-1, 0), (-1, -1)),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (-1, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (-1, -1), 'roboto-bold'),
    ]
    if DEBUG_MODE:
        footer_top_style_config.extend([('GRID', (0,0), (-1,-1), 0.25, colors.brown)])
    colwidths = [1.4*inch, inch, inch, inch, inch, 1.5*inch]
    top_table = Table(data=footer_top_data, colWidths=colwidths)
    top_table.setStyle(TableStyle(footer_top_style_config))
    # signature table
    datenow = datetime.now()
    footer_bottom_data = [
        ['', '.'*30, '.'*30, '.'*45],
        [f"Printed on:  {datenow.strftime('%d-%B-%y')}", 'Prepared by', 'Compared by', 'Deputy Controller of Examinations']
    ]
    footer_bottom_tbl_style_config = [
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('FONTNAME', (0, 0), (-1, 0), 'roboto-italic'),
        ('FONTNAME', (0, -1), (-2, -1), 'roboto-italic'),
        ('FONTNAME', (-1, -1), (-1, -1), 'roboto-m'),
    ]
    if DEBUG_MODE:
        footer_bottom_tbl_style_config.extend([('GRID', (0,0), (-1,-1), 0.25, colors.ReportLabGreen)])
    row_heights = [10] * 2
    signature_table = Table(data=footer_bottom_data, colWidths=calculate_column_widths(len(footer_bottom_data[0]), w, 1.2*cm), rowHeights=row_heights)
    signature_table.setStyle(TableStyle(footer_bottom_tbl_style_config))
    footer_table = Table(data=[
        [top_table],
        [Spacer(1, 18)],
        [signature_table]
    ])
    return footer_table
    
def add_footer(canvas, doc, second_sem_cumulative):
    footer = get_footer(second_sem_cumulative)
    footer.wrapOn(canvas, 0, 0)
    footer.drawOn(canvas=canvas, x=cm, y=cm)

def get_gradesheet(student, year_first_sem_enroll, year_second_sem_enroll) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=margin_Y, title=f"{student.registration} - {get_ordinal_number(year_first_sem_enroll.semester.year)} year gradesheet")
    story = []
    
    build_header(story, student)
    story.append(Spacer(1, 20))
    first_sem_cumulative = cumulative_semester_data(student, year_first_sem_enroll.semester.semester_no)
    second_sem_cumulative = cumulative_semester_data(student, year_second_sem_enroll.semester.semester_no)
    build_semester(story, year_first_sem_enroll, first_sem_cumulative)
    story.append(Spacer(1, 20))
    build_semester(story, year_second_sem_enroll, second_sem_cumulative)
    doc.build(story, onFirstPage=lambda canv, doc: add_footer(canv, doc, second_sem_cumulative))
    return buffer.getvalue()
    