from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from io import BytesIO
from .utils import get_fonts_css_txt
from django.conf import settings
from django.template.loader import render_to_string
from datetime import datetime
from results.models import CourseResult
from .utils import get_bangla_number, get_bangla_ordinal_upto_eight, get_session_code_in_bangla, get_bangla_date


def get_table_rows(data_list, num_rows, num_cols):
    table_rows = []
    for i in range(num_rows):
        j = i
        res = []
        for _ in range(num_cols):
            if (j < len(data_list)):
                res.append(data_list[j])
            else:
                res.append("")
            j += num_rows
        table_rows.append(res)
    return table_rows
        
def get_context_data(course, data):
    context_data = {}
    additional_registrations = [d[0] for d in data['additional_entries']]
    course_results_qs = CourseResult.objects.filter(course=course, total_score__isnull=False)
    course_results_qs_ordered = course_results_qs.order_by('is_drop_course', '-student__is_regular', 'student__registration')
    registrations = [res.student.registration for res in course_results_qs_ordered]
    registrations = [*registrations, *additional_registrations]
    context_data['registrations_row'] = get_table_rows(registrations, 17, 6)
    context_data['expelled_rows'] = get_table_rows(data['expelled_registrations'], 3, 6)
    context_data['expelled_count'] = get_bangla_number(len(data['expelled_registrations']))
    total_answersheets = data['total_answersheets']
    part_A_answersheets = data['part_A_answersheets']
    part_B_answersheets = data['part_B_answersheets']
    if part_A_answersheets == None:
        part_A_answersheets = len(registrations)
    if part_B_answersheets == None:
        part_B_answersheets = len(registrations)
    if total_answersheets == None:
        total_answersheets = 2 * len(registrations)
    context_data['total_answersheets'] = get_bangla_number(total_answersheets)
    context_data['part_A_answersheets'] = get_bangla_number(part_A_answersheets)
    context_data['part_B_answersheets'] = get_bangla_number(part_B_answersheets)
    context_data['year_num'] = get_bangla_ordinal_upto_eight(course.semester.year)
    context_data['year_semester_num'] = get_bangla_ordinal_upto_eight(course.semester.year_semester)
    context_data['session_code'] = get_session_code_in_bangla(course.semester.session.session_code)
    context_data['held_in_year'] = get_bangla_number(course.semester.start_month.strip().split(' ')[-1])
    date = data['exam_date']
    if isinstance(date, datetime):
        formatted_date_str = date.strftime("%d/%m/%Y")
        date = get_bangla_date(formatted_date_str)
    context_data['exam_date'] = date
    return context_data

def render_topsheet(course, data):
    context = {}
    sust_logo = settings.BASE_DIR/'results/static/results/images/sust.png'
    context['sust_logo'] = sust_logo
    context = {**context, **get_context_data(course, data)}
    context['data'] = data
    context['course'] = course
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