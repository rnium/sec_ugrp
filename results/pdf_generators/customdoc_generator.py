from .transcript_generator_manual import get_transcript
from .gradesheet_generator_manual import get_gradesheet
from .utils import merge_pdfs_from_buffers
from results.models import StudentCustomDocument
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from account.models import StudentAccount

def map_context_for_transcript(data):
    context = {
        'name': data['student_data']['name'],
        'reg_num': data['student_data']['registration'],
        'cgpa': data['student_data']['grade_point'],
        'degree': data['student_data']['degree_awarded'],
        'letter_grade': data['student_data']['letter_grade'],
        'credits_complete': data['student_data']['credits_completed'],
        'duration': data['student_data']['period_attended'],
        'exam_scheduled': data['student_data']['years_of_exam_scheduled'],
        'exam_held': data['student_data']['years_of_exam_held_in'],
        'session_degrees_count': data['student_data']['total_number_of_degree_awarded'],
        'students_appears': data['student_data']['students_appeared'],
    }
    return context

def map_formdata_for_gradesheet(data):
    formdata = {
        'dept': data['student_data']['dept_name'],
        'session': data['student_data']['session'],
        'reg_num': data['student_data']['registration'],
        'name': data['student_data']['name'],
        'final_res_credit': data['student_data']['credits_completed'],
        'final_res_cgpa': data['student_data']['grade_point'],
        'final_res_letter_grade': data['student_data']['letter_grade'],
    }
    return formdata


def map_semester_for_gradesheet(data, year_num, year_semester):
    year = data['years'][year_num]
    if len(year) == 0:
        return None
    semester = year[year_semester]
    semester_data = {
        'year': year_num,
        'year_semester': year_semester,
        'held_in': semester['held_in'],
        'semester_credits': semester['semester_credits'],
        'semester_gp': semester['semester_gp'],
        'cumulative_credits': semester['cumulative_credits'],
        'cumulative_gp': semester['cumulative_gp'],
        'cumulative_lg': semester['cumulative_lg'],
        'courses': semester['courses']
    }
    return semester_data


def save_customdoc(student, doctype, data, semester_or_year_num=None):
    c_doc = StudentCustomDocument.objects.filter(
        student=student, doc_type=doctype, sem_or_year_num=semester_or_year_num).first()
    if not c_doc:
        c_doc = StudentCustomDocument(student=student, doc_type=doctype, sem_or_year_num=semester_or_year_num)
    c_doc.document_data = data
    c_doc.save()
    return c_doc


def process_and_save_customdoc_data(data, admin_name):
    reg = data['student_data']['registration']
    student = get_object_or_404(StudentAccount, registration=reg)
    transcript_context = map_context_for_transcript(data)
    transcript_context['admin_name'] = admin_name
    documents = []
    cdoc = save_customdoc(student, 'transcript', transcript_context)
    formdata = map_formdata_for_gradesheet(data)
    for i in range(4):
        excel_data = {}
        year_num = i+1
        for sem_num in data['years'][year_num]:
            semester_data = map_semester_for_gradesheet(data, year_num, sem_num)
            if semester_data is not None:
                excel_data[f'semester_{sem_num}'] = semester_data
                semester_gs_data = {
                    'formdata': formdata,
                    'excel_data': {'semester_1': semester_data}
                }
                nth_sem = ((year_num - 1)*2) + sem_num
                save_customdoc(student, 'sem_gs', semester_gs_data, nth_sem)
        if num_semesters:= len(excel_data):
                yearly_gs_data = {
                    'formdata': formdata,
                    'excel_data': excel_data,
                    'num_semesters': num_semesters,
                }
                save_customdoc(student, 'y_gs', yearly_gs_data, year_num)
                yearly_gs_data['sem_or_year_num'] = year_num
                documents.append(yearly_gs_data)
    if len(documents):
        cdoc = save_customdoc(student, 'all_gss', documents)
    return cdoc


def render_customdoc_document(cdoc: StudentCustomDocument):
    data = cdoc.document_data
    if cdoc.doc_type == 'transcript':
        return get_transcript(data)
    elif cdoc.doc_type == 'sem_gs':
        return get_gradesheet(data['formdata'], data['excel_data'], 1)
    elif cdoc.doc_type == 'y_gs':
        return get_gradesheet(data['formdata'], data['excel_data'], data['num_semesters'])
    elif cdoc.doc_type == 'all_gss':
        documents = []
        for doc_data in  data:
            gradesheet = get_gradesheet(doc_data['formdata'], doc_data['excel_data'], doc_data['num_semesters'])
            documents.append(gradesheet)
        return merge_pdfs_from_buffers(documents).getvalue()