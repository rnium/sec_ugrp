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
    

def render_customdoc(data, admin_name):
    reg = data['student_data']['registration']
    student = get_object_or_404(StudentAccount, registration=reg)
    transcript_context = map_context_for_transcript(data)
    transcript_context['admin_name'] = admin_name
    documents = []
    transcript = get_transcript(transcript_context)
    t_doc = StudentCustomDocument.objects.filter(student=student, doc_type='transcript').first()
    if t_doc:
        t_doc.document.delete()
    else:
        t_doc = StudentCustomDocument(student=student, doc_type='transcript')
    t_doc.document.save(f"{reg}_customtranscript"+'.pdf', ContentFile(transcript))
    t_doc.save()
    formdata = map_formdata_for_gradesheet(data)
    for i in range(4):
        excel_data = {}
        year_num = i+1
        for sem_num in data['years'][year_num]:
            semester_data = map_semester_for_gradesheet(data, year_num, sem_num)
            if semester_data is not None:
                excel_data[f'semester_{sem_num}'] = semester_data
                semester_gs = get_gradesheet(formdata, {'semester_1': semester_data}, 1)
                nth_sem = ((year_num - 1)*2) + sem_num
                gs_doc = StudentCustomDocument.objects.filter(student=student, doc_type='sem_gs', sem_or_year_num=nth_sem).first()
                if gs_doc:
                    gs_doc.document.delete()
                else:
                    gs_doc = StudentCustomDocument(student=student, doc_type='sem_gs', sem_or_year_num=nth_sem)
                gs_doc.document.save(f"{reg}_customgradesheet_sem{year_num}" + '.pdf', ContentFile(semester_gs))
                gs_doc.save()
        if num_semesters:= len(excel_data):
                gradesheet = get_gradesheet(formdata, excel_data, num_semesters)
                gs_doc = StudentCustomDocument.objects.filter(student=student, doc_type='y_gs', sem_or_year_num=year_num).first()
                if gs_doc:
                    gs_doc.document.delete()
                else:
                    gs_doc = StudentCustomDocument(student=student, doc_type='y_gs', sem_or_year_num=year_num)
                gs_doc.document.save(f"{reg}_customgradesheet_y{year_num}" + '.pdf', ContentFile(gradesheet))
                gs_doc.save()
                documents.append(gradesheet)
    merged_buffer = merge_pdfs_from_buffers(documents)
    return merged_buffer.getvalue()