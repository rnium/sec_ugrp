from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from io import BytesIO
from .utils import get_fonts_css_txt
from django.conf import settings
from django.template.loader import render_to_string


def get_context_data(course):
    data = {}
    registrations = [res.student.registration for res in course.courseresult_set.all()]
    num_sublists = 17
    sublist_length = 6
    data['registrations_row'] = []
    for i in range(num_sublists):
        j = i
        res = []
        for _ in range(sublist_length):
            if (j < len(registrations)):
                res.append(registrations[j])
            else:
                res.append("")
            j += 17
        data['registrations_row'].append(res)
    return data

def render_topsheet(course):
    context = {}
    sust_logo = settings.BASE_DIR/'results/static/results/images/sust.png'
    context['sust_logo'] = sust_logo
    context = {**context, **get_context_data(course)}
    html_text = render_to_string('results/pdf_templates/topsheet.html', context=context)
    fonts = {
        'BanglaFont': 'kalpurush.ttf',
        'BanglaUnicodeFont': 'SutonnyMJBold.ttf',
        'Times-roman': 'timesnewroman.ttf',
    }
    font_config = FontConfiguration()
    fonts_css = get_fonts_css_txt(fonts)
    css_filepath = settings.BASE_DIR/f"results/pdf_generators/styles/topsheet.css"
    with open(css_filepath, 'r') as f:
        css_text = f.read()
    html = HTML(string=html_text)
    css = CSS(string=css_text, font_config=font_config)
    css1 = CSS(string=fonts_css, font_config=font_config)
    buffer = BytesIO()
    html.write_pdf(buffer, stylesheets=[css, css1], font_config=font_config)
    return buffer.getvalue()