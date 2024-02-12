from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from io import BytesIO
from django.conf import settings
from django.template.loader import render_to_string
from .utils import get_bangla_ordinal_upto_eight, get_year_number_in_bangla, get_fonts_css_txt


entry_per_list = 31


def render_scorelist(course, examiner, designation):
    course_results = course.courseresult_set.all()
    course_results = list(course_results.order_by('is_drop_course', '-student__is_regular', 'student__registration'))
    list_items = [course_results[i:i+entry_per_list] for i in range(0, len(course_results), entry_per_list)]
    pages = [list_items[i: i+2] for i in range(0, len(list_items), 2)]
    pages_context = []
    sl_num = 1
    curr_page_num = 1
    for page in pages:
        page_context = {
            'list_items': [],
            'has_next': (len(pages) - curr_page_num > 1)
        }
        for li in page:
            li_context = {
                'results': [],
                'empty': list(range(entry_per_list - len(li)))
            }
            for res in li:
                res_context = {
                    'sl_num': sl_num,
                    'reg': res.student.registration,
                    'total': res.total_round_up,
                }
                li_context['results'].append(res_context)
                sl_num += 1
            page_context['list_items'].append(li_context)
        curr_page_num += 1
        pages_context.append(page_context)
    context = {'pages': pages_context}
    context['examiner'] = examiner
    context['designation'] = designation
    context['course'] = course
    context['year_num'] = get_bangla_ordinal_upto_eight(course.semester.year)
    context['year_semester_num'] = get_bangla_ordinal_upto_eight(course.semester.year_semester)
    context['held_in_year'] = get_year_number_in_bangla(course.semester.start_month.strip().split(' ')[-1])
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
    