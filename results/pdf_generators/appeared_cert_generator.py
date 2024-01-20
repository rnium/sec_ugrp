from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from django.conf import settings


pdfmetrics.registerFont(TTFont('SCRIPT_MT_BOLD', settings.BASE_DIR/'results/static/results/fonts/SCRIPT_MT_BOLD.TTF'))
pdfmetrics.registerFont(TTFont('BodoniMT', settings.BASE_DIR/'results/static/results/fonts/BOD_B.TTF'))
pdfmetrics.registerFont(TTFont('BookAntiqua', settings.BASE_DIR/'results/static/results/fonts/BookAntiqua.ttf'))


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
        fontName='BookAntiqua',
        fontSize=14,
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
    

def render_coursemedium_certificate(info_dict):
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=A4, title="Appeared_certificate.pdf")
    # Sample application letter body
    title_text = "<u><b>APPEARED CERTIFICATE</b></u>"
    body_text = (
        f"This is to certify that {info_dict['name']} son/daughter of "
        f"{info_dict['father_name']} and {info_dict['mother_name']} bearing "
        f"Registration No. {info_dict['registration']} and Session {info_dict['session']} "
        f"completed 4 years academic program of B. Sc Engg. ({info_dict['dept']}) "
        f"and appeared the {info_dict['semester_no']}<super><font size=14>{info_dict['semester_suffix']}</font></super> semester final examination held on "
        f"{info_dict['exam_duration']}. "
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
    flowables.append(Paragraph(title_text, titleStyle))
    flowables.append(Spacer(1, 70))
    flowables.append(Paragraph(body_text, bodyStyle))
    flowables.append(Spacer(1, 20))
    flowables.append(Paragraph(bottom_text, bodyStyle))
    flowables.append(Spacer(1, 60))
    insert_principal_table(flowables)
    pdf.build(flowables)
    return buffer.getvalue()

