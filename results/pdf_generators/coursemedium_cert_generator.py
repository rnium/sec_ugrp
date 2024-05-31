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


pdfmetrics.registerFont(TTFont('Bahnschrift', settings.BASE_DIR/'results/static/results/fonts/BAHNSCHRIFT.TTF'))


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
        fontName='Times-Roman',
        fontSize=14,
        textColor=colors.black,
        alignment=TA_CENTER,
    )
    data = [
        ['', Paragraph('(Abdur Rouf )', style=paraStyle)],
        ['', Paragraph('Principal (In-Charge)', style=paraStyle)],
        ['', Paragraph('Sylhet Engineering College,', style=paraStyle)],
        ['', Paragraph('Sylhet.', style=paraStyle)]
    ]
    tbl = Table(data)
    tbl.setStyle(tbl_style)
    flowables.append(tbl)
    

def render_coursemedium_cert(context):
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=A4, title="CourseMedium_certificate.pdf")

    # Sample application letter body
    title_text = "<u><b>Course Medium Certificate</b></u>"
    application_body = (
        f"This is to certify that <i><b><font size='14'>{context['name']}</font></b></i>, Registration number: {context['registration']}\n"
        f"Session: {context['session']}, was awarded a <b>B.Sc. in Engineering degree</b> from the\n"
        f"department of {context['dept']} at Sylhet Engineering College under the School of\n"
        "Applied Sciences & Technology, Shahjalal University of Science and Technology,\n"
        "Sylhet."
    )
    middle_text = "During his or her studentship, the medium of instruction was English."
    bottom_text = "I wish his or her every success in life."
    # Define styles for the paragraph
    styles = getSampleStyleSheet()
    titleStyle = ParagraphStyle(
        'titleStyle',
        parent=styles['Normal'],
        fontName='Bahnschrift',
        fontSize=20,
        textColor=colors.black,
        alignment=TA_CENTER,
    )
    bodyStyle = ParagraphStyle(
        'bodyStyle',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=14,
        textColor=colors.black,
        alignment=TA_JUSTIFY,
        leading=20,
    )

    flowables = []
    flowables.append(Spacer(1, 140))
    flowables.append(Paragraph(title_text, titleStyle))
    flowables.append(Spacer(1, 70))
    flowables.append(Paragraph(application_body, bodyStyle))
    flowables.append(Spacer(1, 20))
    flowables.append(Paragraph(middle_text, bodyStyle))
    flowables.append(Spacer(1, 20))
    flowables.append(Paragraph(bottom_text, bodyStyle))
    flowables.append(Spacer(1, 60))
    insert_principal_table(flowables)
    pdf.build(flowables)

    return buffer.getvalue()


