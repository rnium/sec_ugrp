from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch, cm, mm
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from django.conf import settings
import datetime


pageSize = (217*mm, 281*mm)
width, height = pageSize
marginTop = 40*mm
marginBottom = 20*mm
sideMargin = 1.5*cm



pdfmetrics.registerFont(TTFont('SCRIPT_MT_BOLD', settings.BASE_DIR/'results/static/results/fonts/SCRIPT_MT_BOLD.TTF'))
pdfmetrics.registerFont(TTFont('BodoniMT', settings.BASE_DIR/'results/static/results/fonts/BOD_B.TTF'))
pdfmetrics.registerFont(TTFont('BookAntiqua', settings.BASE_DIR/'results/static/results/fonts/BookAntiqua.ttf'))

def insert_top_table(flowables, ref):
    tbl_style = TableStyle([
        # ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT')
    ])
    styles = getSampleStyleSheet()
    refStyle = ParagraphStyle(
        'refStyle',
        parent=styles['Normal'],
        leftIndent=10
    )
    data = [
        [Paragraph(ref, style=refStyle), datetime.datetime.now().strftime("%d/%m/%Y")]
    ]
    tbl = Table(data)
    tbl.setStyle(tbl_style)
    flowables.append(tbl)
    


def insert_principal_table(flowables):
    tbl_style = TableStyle([
        # ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ])
    styles = getSampleStyleSheet()
    paraStyle = ParagraphStyle(
        'paraStyle',
        parent=styles['Normal'],
        fontName='BodoniMT',
        fontSize=16,
        textColor=colors.black,
        alignment=TA_CENTER,
    )
    data = [
        ['', Paragraph('(Abdur Rouf)', style=paraStyle)],
        ['', Paragraph('Principal (In-Charge)', style=paraStyle)],
        ['', Paragraph('Sylhet Engineering College,', style=paraStyle)],
        ['', Paragraph('Sylhet.', style=paraStyle)]
    ]
    tbl = Table(data)
    tbl.setStyle(tbl_style)
    flowables.append(tbl)
    

def render_appearance_certificate(context):
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=pageSize,
        topMargin=marginTop,
        bottomMargin=marginBottom,
        leftMargin=sideMargin,
        rightMargin=sideMargin, 
        title="Appeared_certificate.pdf")
    # Sample application letter body
    title_text = "<u><b>APPEARED CERTIFICATE</b></u>"
    body_text = (
        f"This is to certify that {context['name']} son/daughter of "
        f"{context['father_name']} and {context['mother_name']} bearing "
        f"Registration No. {context['registration']} and Session {context['session']} "
        f"completed {context['completed_years']} years academic program of B. Sc Engg. ({context['dept']}) "
        f"and appeared the {context['semester_no']}<super><font size=14>{context['semester_suffix']}</font></super> semester final examination held on "
        f"{context['exam_duration']}. "
    )
    bottom_text = "I wish him/her every success in life."
    # Define styles for the paragraph
    styles = getSampleStyleSheet()
    titleStyle = ParagraphStyle(
        'titleStyle',
        parent=styles['Normal'],
        fontName='BodoniMT',
        fontSize=18,
        textColor=colors.black,
        alignment=TA_CENTER,
    )
    bodyStyle = ParagraphStyle(
        'bodyStyle',
        parent=styles['Normal'],
        fontName='SCRIPT_MT_BOLD',
        fontSize=19,
        textColor=colors.black,
        alignment=TA_JUSTIFY,
        leading=26,
    )

    flowables = []
    flowables.append(Spacer(1, 20))
    insert_top_table(flowables, context.get('ref', ''))
    flowables.append(Spacer(1, 50))
    flowables.append(Paragraph(title_text, titleStyle))
    flowables.append(Spacer(1, 70))
    flowables.append(Paragraph(body_text, bodyStyle))
    flowables.append(Spacer(1, 20))
    flowables.append(Paragraph(bottom_text, bodyStyle))
    flowables.append(Spacer(1, 60))
    insert_principal_table(flowables)
    pdf.build(flowables)
    return buffer.getvalue()

