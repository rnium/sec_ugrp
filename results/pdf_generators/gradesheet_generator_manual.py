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
from results.utils import get_letter_grade
from account.models import StudentAccount
import math

DEBUG_MODE = False

w, h = A4
margin_X = 0.3*inch
margin_Y = 0.2*inch

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


def course_sorting_key(course, dept_name):
    dept_priority = 0
    coursecode_first_part = course.code.split(' ')[0].lower().strip()
    if coursecode_first_part == dept_name.lower():
        dept_priority = 1
    return (-course.semester.semester_no, -course.course_credit, -dept_priority)

def sort_courses(courses, dept_name):
    sorted_courses = sorted(courses, key=lambda course: course_sorting_key(course, dept_name), reverse=False)
    return sorted_courses



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
        *[('BOX', (0+i,0), (0+i,-1), 0.5, colors.black) for i in range(3)],
        ('GRID', (0,0), (-1,0), 0.5, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 7), 
        ('FONTNAME', (0, 0), (-1, -1), 'roboto-m'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('LEFTPADDING', (-2, 1), (-2, -1), 22),
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
    tbl.setStyle(style)
    return tbl
 
 
def build_header(flowables, formdata) -> None:
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
    dept_name_paragraph = Paragraph(f": <b>{formdata['dept']}</b>", style=bold_paragraph_style)
    grading_scheme_table = get_grading_scheme_table()
    student_name = formdata['name']
    table_data = [
        [logo, university, '', ''],
        ['', 'Grade Certificate', '', grading_scheme_table],
        ['', "B. Sc. (Engg.) Examination", ''],
        ['', "Session", f": {formdata['session']}", ''],
        ['Name of the College', '', ": Sylhet Engineering College, Sylhet", ''],
        ['Department', '', dept_name_paragraph, ''],
        [Spacer(1, 0.1*cm), Spacer(1, 0.1*cm), Spacer(1, 0.1*cm), ''],
        ['Registration No.', '', f": {formdata['reg_num']}", ''],
        ['Name of the Student', '', f": {student_name.upper()}", ''],
    ]
    tblstyle_config = [
        ('SPAN', (0, 0), (0, 2)),
        ('SPAN', (1, 0), (-1, 0)), # university
        ('FONTSIZE', (1, 1), (1, 1), 11), # grade cert. fontsize
        ('FONTNAME', (0, 0), (-1, -1), 'roboto-m'), # grade cert. font name
        ('FONTNAME', (1, 1), (1, 1), 'roboto-bold'),
        
        ('SPAN', (-1, 1), (-1, -1)),
        *[('SPAN', (1, 1+i), (2, 1+i)) for i in range(2)],
        *[('SPAN', (0, 4+i), (1, 4+i)) for i in range(5)],
        ('ALIGN', (-1, 1), (-1, 1), 'RIGHT'),
        ('VALIGN', (-1, 1), (-1, 1), 'MIDDLE'),
    ]
    if DEBUG_MODE:
        tblstyle_config.extend([('GRID', (0,0), (-1,-1), 0.25, colors.royalblue)])
        
    tbl = Table(data=table_data, colWidths=[0.75*inch, 0.7*inch, 3.2*inch, 2.8*inch])
    tbl.setStyle(TableStyle(tblstyle_config))
    flowables.append(tbl)
        

def get_courses_data(semester_data, blank_list):
    coursetitle_style = ParagraphStyle(
        name='bold_paragraph_style',
        fontName='roboto-bold',  # Specify the bold font
        fontSize=9,  # Set the font size to 14 points
        alignment=0,
    )
    dataset = []
    # courses = sort_courses(semester_enroll.courses.all(), 'eee')
    courses = semester_data['courses']
    for course in courses:
        data = [
            course['code'],
            Paragraph(course['title'], coursetitle_style),
            *blank_list,
            course['credit'],
            course['gp'],
            course['lg']
        ]
        dataset.append(data)
    return dataset


def build_semester(flowables, semester_data) -> None:
    course_title_extras = ['', '', '', '']
    course_dataset = get_courses_data(semester_data, course_title_extras)
    num_courses = len(course_dataset)
    
    data = [
        [f"{cardinal_repr(int(semester_data['year']))} Year {cardinal_repr(int(semester_data['year_semester']))} Semester", *course_title_extras, f"Held in: {semester_data['held_in']}", '', '', ''],
        ['Course No.', 'Course Title', *course_title_extras, 'Credit', 'Grade Obtained', ''],
        ['', '', '', *course_title_extras, 'Grade Point', 'Letter Grade'],
        # courses
        *course_dataset,
        [*course_title_extras, 'This Semester Total:', '', semester_data['semester_credits'], f"{semester_data['semester_gp']:.2f}", get_letter_grade(semester_data['semester_gp'])],
        [*course_title_extras, 'Cumulative:', '', semester_data['cumulative_credits'], f"{semester_data['cumulative_gp']}", semester_data['cumulative_lg']],
    ]
    header_row_heights = [15] * 3
    course_row_heights = []
    bottom_row_heights = [14] * 2
    for course in semester_data['courses']:
        course_row_heights.append(14 * math.ceil(len(course['title'])/70))
    semester_table_style = TableStyle([
        ('GRID', (0,1), (-1,-3), 0.7, colors.black),
        ('GRID', (-5,-2), (-1,-1), 0.7, colors.black),
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
        ('FONTNAME', (0, 3), (-1, -1), 'roboto-m'), # course about
        ('FONTSIZE', (0, 3), (-1, -3), 9),
        ('VALIGN', (0, 3), (-1, -1), 'MIDDLE'),
         # bottom two rows
        ('SPAN', (-5, -2), (-4, -2)),
        ('SPAN', (-5, -1), (-4, -1)),
        ('FONTNAME', (-5, -2), (-5, -1), 'roboto-bold'),
        ('FONTSIZE', (-5, -2), (-5, -1), 9),
        ('FONTSIZE', (-3, -2), (-1, -1), 9), # bottom totals
        
        
    ])
    table = Table(data=data, colWidths=calculate_column_widths(len(data[0]), w, margin_X), rowHeights=[*header_row_heights, *course_row_heights, *bottom_row_heights])
    table.setStyle(semester_table_style)
    flowables.append(table)

def get_footer_top_table(last_semester_data):
    header_style = ParagraphStyle(
        name='bold_paragraph_style',
        fontName='roboto-bold',  # Specify the bold font
        fontSize=9,  # Set the font size to 14 points
        alignment=1,  # Center alignment
    )
    credit_float = float(last_semester_data['cumulative_credits'])
    cgpa = float(last_semester_data['cumulative_gp'])
    DISTINCTION_TEXT = ""
    if credit_float >= 160 and cgpa >= 3.75:
        DISTINCTION_TEXT = "With Distinction"
    footer_top_data = [
        ['', Paragraph('<u>Final Result</u>', style=header_style), '', '', '', DISTINCTION_TEXT],
        ['', 'Cumulative', 'Credit', 'CGPA', 'Letter Grade', ''],
        ['', 'Final Result', last_semester_data['cumulative_credits'], last_semester_data['cumulative_gp'], last_semester_data['cumulative_lg'], '']
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
    return top_table
        
def get_footer(last_semester_data, include_overall_result):
    top_table = None
    if include_overall_result:
        top_table = get_footer_top_table(last_semester_data)
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
    data = []
    if top_table:
        data.append([top_table])
        data.append([Spacer(1, 18)])
    data.append([signature_table])
    footer_table = Table(data=data)
    return footer_table
    
def add_footer(canvas, doc, last_sem_data, include_overall_result, margin_y=1.4*cm):
    footer = get_footer(last_sem_data, include_overall_result)
    footer.wrapOn(canvas, 0, 0)
    footer.drawOn(canvas=canvas, x=cm, y=0.5*cm)

def get_gradesheet(formdata, excel_data, num_semesters, is_the_last_gradesheet=False) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=margin_Y, title=f"gradesheet: {formdata['reg_num']}")
    story = []
    TOTAL_NUMBER_OF_COURSES = len(excel_data['semester_1']['courses'])
    build_header(story, formdata)
    story.append(Spacer(1, 20))
    
    if num_semesters == 2:
        build_semester(story, excel_data['semester_1'])
        story.append(Spacer(1, 20))
        build_semester(story, excel_data['semester_2'])
        TOTAL_NUMBER_OF_COURSES  += len(excel_data['semester_2']['courses'])
    else:
        story.append(Spacer(1, 40))
        build_semester(story, excel_data['semester_1'])
    last_semester_number = max([int(k.split('_')[-1]) for k in excel_data.keys()])
    last_semester_key = f"semester_{last_semester_number}"
    # if TOTAL_NUMBER_OF_COURSES <= 24:
    #     doc.build(story, onFirstPage=lambda canv, doc: add_footer(canv, doc, excel_data[last_semester_key], is_the_last_gradesheet))
    # else:
    #     story.append(Spacer(1, 40))
    #     story.append(get_footer(excel_data[last_semester_key], is_the_last_gradesheet))
    #     doc.build(story)
    doc.build(story, onFirstPage=lambda canv, doc: add_footer(canv, doc, excel_data[last_semester_key], is_the_last_gradesheet))

    return buffer.getvalue()
    
