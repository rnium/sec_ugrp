from .transcript_generator_manual import get_transcript
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

def render_customdoc(data, admin_name):
    context = map_context_for_transcript(data)
    context['admin_name'] = admin_name
    get_transcript(context)
    print("customdoc generated!", flush=1)