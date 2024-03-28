from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from io import BytesIO
from django.conf import settings
from django.template.loader import render_to_string

def get_fonts_css_txt(font_names):
    css_text = ""
    for font_name in font_names.keys():
        font_path = settings.BASE_DIR/f"results/pdf_generators/fonts/{font_names[font_name]}"
        css_text += f"""@font-face {{
                        font-family: {font_name};
                        src: url(file://{font_path});}}"""
    return css_text

def render_coursereport(course, from_session):
    if from_session:
        course_results = course.courseresult_set.filter(is_drop_course=True, student__session=from_session)
    else:
        course_results = course.courseresult_set.all()
    course_results = course_results.order_by('is_drop_course', '-student__session__from_year', '-student__is_regular', 'student__registration')
    html_text = render_to_string('results/pdf_templates/course_report.html', context={'course':course, 'from_session':from_session, 'course_results':course_results})
    fonts = {
        'TimesNewRoman': 'timesnewroman.ttf',
        'TimesNewRomanBold': 'timesnewromanbold.ttf',
    }
    font_config = FontConfiguration()
    fonts_css = get_fonts_css_txt(fonts)
    css_filepath = settings.BASE_DIR/f"results/pdf_generators/styles/course_report.css"
    with open(css_filepath, 'r') as f:
        css_text = f.read()
    html = HTML(string=html_text)
    css = CSS(string=css_text, font_config=font_config)
    css1 = CSS(string=fonts_css, font_config=font_config)
    buffer = BytesIO()
    html.write_pdf(buffer, stylesheets=[css, css1], font_config=font_config)
    return buffer.getvalue()
    