from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from io import BytesIO
from django.conf import settings
from django.template.loader import render_to_string
from .utils import get_bangla_ordinal_upto_eight, get_year_number_in_bangla, get_fonts_css_txt
from results.models import CourseResult


entry_per_list = 35

def get_examiner_table_rows(excel_data):
    examiners = excel_data['examiners']
    examiners_exterternal = excel_data['external_examiners']
    table = []
    for i in range(0,max(len(examiners), len(examiners_exterternal)),2):
        e1 = examiners[i:i+2]
        for _ in range(2-len(e1)):
            e1.append("")
        e2 = examiners_exterternal[i:i+2]
        for _ in range(2-len(e2)):
            e2.insert(0, "")
        table.append([*e1, *e2])
    return table


def render_scorelist(course, excel_data):
    course_results_qs = CourseResult.objects.filter(course=course, total_score__isnull=False)
    course_results_qs_ordered = course_results_qs.order_by('is_drop_course', '-student__is_regular', 'student__registration')
    course_results = [[cr.student.registration, cr.total_round_up] for cr in course_results_qs_ordered]
    course_results = [*course_results, *excel_data['additional_entries']]
    entry_per_list = excel_data['records_per_column']
    list_items = [course_results[i:i+entry_per_list] for i in range(0, len(course_results), entry_per_list)]
    pages = [list_items[i: i+2] for i in range(0, len(list_items), 2)]
    pages_context = []
    sl_num = 1
    curr_page_num = 1
    print(excel_data['chairman_name'], flush=1)
    for page in pages:
        page_context = {
            'list_items': [],
            'has_next': (len(pages) - curr_page_num > 1)
        }
        for i in range(2):
            li_context = {
                'results': [],
            }
            if i >= len(page):
                li = []
                li_context['blank_li'] = True
            else:
                li = page[i]
                li_context['blank_li'] = False
            li_context['empty'] = list(range(entry_per_list - len(li)))
            for res in li:
                res_context = {
                    'sl_num': sl_num,
                    'reg': res[0],
                    'total': res[1],
                }
                li_context['results'].append(res_context)
                sl_num += 1
            page_context['list_items'].append(li_context)
        curr_page_num += 1
        pages_context.append(page_context)
    context = {'pages': pages_context}
    context['examiners_table'] = get_examiner_table_rows(excel_data)
    context['course'] = course
    context['year_num'] = get_bangla_ordinal_upto_eight(course.semester.year)
    context['year_semester_num'] = get_bangla_ordinal_upto_eight(course.semester.year_semester)
    context['held_in_year'] = get_year_number_in_bangla(course.semester.start_month.strip().split(' ')[-1])
    context['blank_table_rows'] = range(9)
    context['chairman_name'] = excel_data['chairman_name']
    sust_logo = settings.BASE_DIR/'results/static/results/images/sust.png'
    context['sust_logo'] = sust_logo
    html_text = render_to_string('results/pdf_templates/scorelist.html', context=context)
    fonts = {
        'BanglaFont': 'kalpurush.ttf',
        'BanglaUnicodeFont': 'SutonnyMJRegular.ttf',
        'Times-roman': 'timesnewroman.ttf',
    }
    font_config = FontConfiguration()
    fonts_css = get_fonts_css_txt(fonts)
    css_filepath = settings.BASE_DIR/f"results/pdf_generators/styles/scorelist.css"
    with open(css_filepath, 'r') as f:
        css_text = f.read()
    html = HTML(string=html_text)
    css = CSS(string=css_text, font_config=font_config)
    css1 = CSS(string=fonts_css, font_config=font_config)
    buffer = BytesIO()
    html.write_pdf(buffer, stylesheets=[css, css1], font_config=font_config)
    return buffer.getvalue()
    