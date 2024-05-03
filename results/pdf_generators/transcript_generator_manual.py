from typing import List, Dict
from io import BytesIO
from django.conf import settings
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

DEBUG_MODE = False

w, h = 21.6*cm, 34*cm
margin_X = 1*cm
margin_Y = 1*cm

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
        ('FONTSIZE', (0, 0), (-1, -1), 7), 
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
    tbl.setStyle(TableStyle(style_config));
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
        ('FONTSIZE', (0, 0), (-1, -1), 9), 
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
    table_fontSize = 9
    table_fontName_normal = 'Times-Roman'
    table_fontName_bold = 'Times-Bold'
    normalStyle = ParagraphStyle(
        name='normalStyle',
        fontName='Times',
        fontSize=table_fontSize,
        textColor=colors.black,
    )
    university_paragraph = Paragraph("Shahjalal University of Science & Technology<br/>P.O.: University, Sylhet, Bangladesh.", style=normalStyle)
    bottom_info = """The results of the student mentioned above are compiled considering aggregated of <u>four years for B. Sc. (Engg.)</u><br/>examinations.
    Additional sheets containing the subject studied, course number and grade obtained in each course<br/>are enclosed."""
    # Extracting requied data
    NAME = context['name']
    REGISTRATION = int(context['reg_num'])
    STUDENT_CGPA = context['cgpa']
    STUDENT_LG = context['letter_grade']
    CREDITS_COMPLETE = context['credits_complete']
    DEGREE = context['degree']
    DURARTION_ATTENDED = context['duration']
    LAST_SEMESTER_SHEDULE_TIME = context['exam_scheduled']
    LAST_SEMESTER_HELD_TIME = context['exam_held']
    GRADES_STATS = context['session_degrees_count']
    NUM_APPEARED_STUDENTS = context['students_appears']
    
    WITH_DISTINCTION_TXT = ""
    if float(STUDENT_CGPA) >= 3.75 and float(CREDITS_COMPLETE) >= 160:
        WITH_DISTINCTION_TXT = "(With Distinction)"
    
    data = [
        ["1.", 'Name of the Student', ':', NAME.upper()],
        ["2.", 'Name of the College', ':', 'Sylhet Engineering College, Sylhet'],
        ["3.", 'Name of the University', ':', university_paragraph],
        ["4.", 'Registration & Exam Roll No.', ':', REGISTRATION],
        ["5.", 'Period Attended', ':', f'{DURARTION_ATTENDED}'],
        ["6.", 'Years of Examination', ':', get_yearOfExamsTable(LAST_SEMESTER_SHEDULE_TIME, LAST_SEMESTER_HELD_TIME)],
        ["7.", 'Degree(s) Awarded', ':', DEGREE],
        ["8.", 'Grading System', ':', get_grading_scheme_table()],
        [Spacer(1, 10)],
        ["9.", 'Credits Completed', ':', CREDITS_COMPLETE],
        ["10.", 'Cumulative  Grade Point Obtained', ':', Paragraph(f"CGPA: <b>{STUDENT_CGPA} {WITH_DISTINCTION_TXT}</b>", style=normalStyle)],
        ["11.", 'Letter Grade Obtained', ':', Paragraph(f"<b>{STUDENT_LG}</b>", style=normalStyle)],
        ["12.", 'Total Number of Students Appeared', ':', Paragraph(f"<b>{NUM_APPEARED_STUDENTS}</b>", style=normalStyle)],
        ["13."
         , Paragraph(
             'Total Number of  Degree Awarded<br/>this Year in Applicant\'s Academic Field', style=normalStyle
         )
         , ':'
         , Paragraph(
            f"<b>{GRADES_STATS}</b>",
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
        ('FONTSIZE', (0, 0), (-1, -1), 10), 
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
    
