from typing import List, Dict
from io import BytesIO
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from account.models import StudentAccount
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer
from reportlab.platypus import Paragraph
from reportlab.platypus import Image
from reportlab.platypus.flowables import Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from results.utils import get_letter_grade, session_letter_grades_count
from results.models import Semester

DEBUG_MODE = False

w, h = 21.6*cm, 34*cm
margin_X = 1*cm
margin_Y = 1*cm
TABLE_FONT_SIZE = 14

pdfmetrics.registerFont(TTFont('roboto', settings.BASE_DIR/'results/static/results/fonts/Roboto-Regular.ttf'))
pdfmetrics.registerFont(TTFont('roboto-bold', settings.BASE_DIR/'results/static/results/fonts/Roboto-Bold.ttf'))
pdfmetrics.registerFont(TTFont('roboto-italic', settings.BASE_DIR/'results/static/results/fonts/Roboto-MediumItalic.ttf'))
pdfmetrics.registerFont(TTFont('roboto-m', settings.BASE_DIR/'results/static/results/fonts/Roboto-Medium.ttf'))



class HorizontalLine(Flowable):
    def __init__(self, width, thickness=1, color=colors.black):
        self.width = width
        self.thickness = thickness
        self.color = color

    def wrap(self, available_width, available_height):
        return self.width, self.thickness

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(-100, 0, self.width, 0)
        

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
    style_config = [
        ('FONTSIZE', (0, 0), (-1, -1), TABLE_FONT_SIZE-2), 
        ('FONTNAME', (0, 0), (-1, -1), 'Times-Bold'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (-2, 1), (-2, -1), 18),
    ]
    if DEBUG_MODE:
        style_config.extend([('GRID', (0,0), (-1,-1), 0.25, colors.ReportLabGreen)])
    

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
    tbl.setStyle(TableStyle(style_config))
    return tbl

def get_yearOfExamsTable(scheduled, held) -> Table:
    data = [
        ['(a) Scheduled', f':  {scheduled}'],
        ['(b) Held On', f':  {held}'],
    ]
    style_config = [
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Times-Roman'), 
        ('FONTNAME', (-1, 0), (-1, -1), 'Times-Bold'), 
        ('FONTSIZE', (0, 0), (-1, -1), TABLE_FONT_SIZE), 
        ('LEFTPADDING', (0, 0), (0, -1), 0),
        ('LEFTPADDING', (-1, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]
    if DEBUG_MODE:
        style_config.extend([('GRID', (0,0), (-1,-1), 0.25, colors.royalblue)])
    table = Table(data=data)
    table.setStyle(TableStyle(style_config))
    return table
        
def get_main_table(context: Dict) -> Table:
    table_fontSize = TABLE_FONT_SIZE
    table_fontName_normal = 'Times-Roman'
    table_fontName_bold = 'Times-Bold'
    normalStyle = ParagraphStyle(
        name='normalStyle',
        fontName='Times',
        fontSize=table_fontSize,
        textColor=colors.black,
    )
    university_paragraph = Paragraph("Shahjalal University of Science & Technology<br/>P.O.: University, Sylhet, Bangladesh.", style=normalStyle)
    bottom_info = """The results of the student mentioned above are compiled considering aggregated of <u>four years for B. Sc. (Engg.)</u> examinations.
    Additional sheets containing the subject studied, course number and grade obtained in each course are enclosed."""
    # Extracting requied data
    student = context['student']
    STUDENT_CGPA = student.total_points / student.credits_completed
    PERIOD_ATTENDED_FROM_YEAR = str(student.registration)[:4]
    LAST_SEMESTER_SHEDULE_TIME = context['last_semester'].start_month.split(' ')[-1]
    LAST_SEMESTER_HELD_TIME = context['last_semester'].held_in.split(' ')[-1]
    NUM_INCOMPLETE_STUDENTS = 0
    final_semesters = Semester.objects.filter(session=student.session, semester_no=8, repeat_number=0)
    for semester in final_semesters:
        NUM_INCOMPLETE_STUDENTS += semester.semesterenroll_set.filter(student__credits_completed__lt=160).count()
    WITH_DISTINCTION_TXT = ""
    if student.with_distinction:
        WITH_DISTINCTION_TXT = "(With Distinction)"
    if NUM_INCOMPLETE_STUDENTS == 0:
        NUM_INCOMPLETE_STUDENTS = 'Nil'
    LAST_SEMESTER_ENROLLS_COUNT = 0
    last_sem = context['last_semester']
    last_semester_all_parts = Semester.objects.filter(session=last_sem.session, semester_no=last_sem.semester_no, repeat_number=last_sem.repeat_number)
    last_semester_enrolled_students = []
    for sem in last_semester_all_parts:
        LAST_SEMESTER_ENROLLS_COUNT += sem.semesterenroll_set.count()
        last_semester_enrolled_students.extend([enroll.student for enroll in sem.semesterenroll_set.all()])
    GRADES_COUNT = session_letter_grades_count(last_semester_enrolled_students)
    data = [
        ["1.", 'Name of the Student', ':', student.student_name.upper()],
        ["2.", 'Name of the College', ':', 'Sylhet Engineering College, Sylhet'],
        ["3.", 'Name of the University', ':', university_paragraph],
        ["4.", 'Registration & Exam Roll No.', ':', student.registration],
        ["5.", 'Period Attended', ':', f'{PERIOD_ATTENDED_FROM_YEAR}-{LAST_SEMESTER_HELD_TIME}'],
        ["6.", 'Years of Examination', ':', get_yearOfExamsTable(LAST_SEMESTER_SHEDULE_TIME, LAST_SEMESTER_HELD_TIME)],
        ["7.", 'Degree(s) Awarded', ':', f'B.Sc. (Engg.) in {student.session.dept.fullname}'],
        ["8.", 'Grading System', ':', get_grading_scheme_table()],
        [Spacer(1, 10)],
        ["9.", 'Credits Completed', ':', student.credits_completed],
        ["10.", 'Cumulative  Grade Point Obtained', ':', Paragraph(f"CGPA: <b>{round(STUDENT_CGPA, 2)} {WITH_DISTINCTION_TXT}</b>", style=normalStyle)],
        ["11.", 'Letter Grade Obtained', ':', Paragraph(f"<b>{get_letter_grade(STUDENT_CGPA)}</b>", style=normalStyle)],
        ["12.", 'Total Number of Students Appeared', ':', Paragraph(f"<b>{LAST_SEMESTER_ENROLLS_COUNT}</b>", style=normalStyle)],
        ["13."
         , Paragraph(
             'Total Number of  Degree Awarded<br/>this Year in Applicant\'s Academic Field', style=normalStyle
         )
         , ':'
         , Paragraph(
            f"<b>A+ = {GRADES_COUNT['A+']}, A = {GRADES_COUNT['A']}, A- = {GRADES_COUNT['A-']}, B+ = {GRADES_COUNT['B+']}, B = {GRADES_COUNT['B']}, B- = {GRADES_COUNT['B-']}, C+ = {GRADES_COUNT['C+']}, C = {GRADES_COUNT['C']}, C- = {GRADES_COUNT['C-']}, Withheld = Nil, Incomplete = {NUM_INCOMPLETE_STUDENTS}</b>",
            style=normalStyle
         )
        ],
        ["14.", 'Medium of Instruction', ':', Paragraph("<b>English</b>", style=normalStyle)],
        [Paragraph(bottom_info, normalStyle), '', '', '']
    ]
    style_config = [
        ('ALIGN', (0,0), (0,-1), "RIGHT"),
        ('VALIGN', (0,0), (-1,-1), "TOP"),
        ('FONTSIZE', (0, 0), (-1, -1), table_fontSize), 
        ('FONTNAME', (0, 0), (-1, -1), table_fontName_normal), 
        ('FONTNAME', (-1, 0), (-1, 1), table_fontName_bold), # Student Name and College
        ('FONTNAME', (2, 0), (2, -1), table_fontName_bold), # Colon Column
        ('FONTNAME', (-1, 3), (-1, 4), table_fontName_bold), # Regisration No.and Peroid attended
        ('FONTNAME', (-1, 6), (-1, 6), table_fontName_bold), # Degree(s) Awarded
        ('FONTNAME', (-1, 9), (-1, 9), table_fontName_bold), # Credits
        ('SPAN', (0, -1), (-1, -1)), # Bottom info
        ('LEFTPADDING', (0, -1), (0, -1), 20),
        ('RIGHTPADDING', (0, -1), (0, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, -1), (0, -1), 30),
        ('ALIGN', (0, -1), (0, -1), "CENTER"),
    ]
    if DEBUG_MODE:
        style_config.extend([('GRID', (0,0), (-1,-1), 0.25, colors.gray)])
    colwidths = [0.6*cm, 2.5*inch, 0.5*cm, 3.5*inch]
    table = Table(data=data, colWidths=colwidths)
    table.setStyle(TableStyle(style_config))
    return table

def build_body(flowables: List, context: Dict) -> None:
    title_style = ParagraphStyle(
        name='TitleStyle',
        fontName='Times-Bold',
        fontSize=11,
        textColor=colors.black,
        alignment=1,
    )
    flowables.append(Paragraph("<u>TRANSCRIPT OF ACADEMIC RECORDS</u>", style=title_style))
    flowables.append(Spacer(1, 20))
    flowables.append(get_main_table(context))

def get_footer(context):
    footer_data = [
        [f"Prepared by: {context['admin_name']}", 'Compared by:', 'Deputy Controller of Examinations']
    ]
    style_config = [
        ('FONTSIZE', (0, 0), (-1, -1), TABLE_FONT_SIZE), 
        ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
        ('LEFTPADDING', (0, 0), (0, 0), 0),
        ('ALIGN', (-1, 0), (-1, 0), 'CENTER'),
    ]
    if DEBUG_MODE:
        style_config.extend([('GRID', (0,0), (-1,-1), 0.25, colors.ReportLabLightBlue)])
        
    signature_table = Table(data=footer_data, colWidths=calculate_column_widths(len(footer_data[0]), w-2*cm, 1.2*cm))
    signature_table.setStyle(TableStyle(style_config))
    
    return signature_table
  
def add_footer(canvas, doc, context):
    footer = get_footer(context)
    footer.wrapOn(canvas, 0, 0)
    footer.drawOn(canvas=canvas, x=0.9*inch, y=1*inch)  

def get_transcript(context: Dict):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(w,h), topMargin=margin_Y, title="Academic Transcript")
    story = []
    story.append(Spacer(1, 5.7*cm))
    build_body(story, context)
   
    doc.build(story, onFirstPage=lambda canv, doc: add_footer(canvas=canv, doc=doc, context=context))
    return buffer.getvalue()


def render_transcript_for_student(request, registration, student=None):
    if student is None:
        student = get_object_or_404(StudentAccount, registration=registration)
    last_enroll = student.semesterenroll_set.all().order_by('-semester__semester_no', '-semester__part_no', '-semester__repeat_number').first()
    if last_enroll is not None:
        context = {
            'admin_name': request.user.adminaccount.user_full_name,
            'student': student,
            'last_semester': last_enroll.semester
        }
        sheet_pdf = get_transcript(context=context)
        return sheet_pdf
    else:
        raise ValidationError('Transcript not available!')
