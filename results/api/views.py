from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse, FileResponse
from django.template.loader import render_to_string
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.exceptions import APIException
from rest_framework.generics import CreateAPIView, UpdateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework.response import Response
from rest_framework import status
from .serializer import (SessionSerializer, SemesterSerializer,
                         CourseSerializer, CourseResultSerializer, StudentStatsSerializer)
from .permission import IsCampusAdmin
from results.models import (Department, Session, Semester, Course, PreviousPoint,
                            CourseResult, SemesterDocument, SemesterEnroll, Backup)
from account.models import StudentAccount
from . import utils
from results.utils import get_ordinal_number, get_letter_grade, get_ordinal_suffix
from results.pdf_generators.tabulation_generator import get_tabulation_files
from results.pdf_generators.gradesheet_generator_manual import get_gradesheet
from results.pdf_generators.transcript_generator_manual import get_transcript
from results.tasks import restore_data_task
from io import BytesIO
from datetime import datetime
import time
import openpyxl
import json
import base64


def user_is_super_OR_dept_admin(request):
    if hasattr(request.user, 'adminaccount'):
        return request.user.adminaccount.is_super_admin or (request.user.adminaccount.dept is not None)
    else:
        return False
    
class BadrequestException(APIException):
    status_code = 403
    default_detail = 'Bad Request'
    

class SessionCreate(CreateAPIView):
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated, IsCampusAdmin]
    queryset = Session.objects.all()
    
    def perform_create(self, serializer):
        try:
            super().perform_create(serializer)
        except Exception as e:
            raise BadrequestException(str(e))


class SemesterCreate(CreateAPIView):
    serializer_class = SemesterSerializer
    permission_classes = [IsAuthenticated, IsCampusAdmin]
    
    def get_queryset(self):
        pk = self.kwargs.get("pk")
        sessions = Session.objects.filter(id=pk)
        return sessions
    
    def perform_create(self, serializer):
        try:
            super().perform_create(serializer)
            # create enrollments. this sould be removed in future version
            pk = serializer.data.get('id')
            semester = Semester.objects.get(pk=pk)
            utils.create_course_enrollments(semester)
        except Exception as e:
            raise BadrequestException(str(e))


class SemesterUpdate(UpdateAPIView):
    serializer_class = SemesterSerializer
    permission_classes = [IsAuthenticated, IsCampusAdmin]
    
    def get_queryset(self):
        pk = self.kwargs.get("pk")
        semester = Semester.objects.filter(id=pk)
        return semester
    
    def patch(self, request, *args, **kwargs):
        try:
            return self.partial_update(request, *args, **kwargs)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    

class CourseCreate(CreateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsCampusAdmin]
    queryset = Course.objects.all()
    
    def create(self, request, *args, **kwargs):
        data = request.data
        data['added_by'] = request.user.id
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            self.perform_create(serializer)
            course_id = serializer.data.get('id')
            course = Course.objects.get(id=course_id)
            utils.add_course_to_enrollments(course=course)
            utils.create_course_results(course=course)
            return Response(serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)
    
    
    def perform_create(self, serializer):
        try:
            super().perform_create(serializer)
        except Exception as e:
            raise BadrequestException(str(e))


class CourseUpdate(UpdateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsCampusAdmin]
    
    def get_queryset(self):
        pk = self.kwargs.get("pk")
        courses = Course.objects.filter(id=pk)
        return courses
    
    def patch(self, request, *args, **kwargs):
        try:
            return_value = self.partial_update(request, *args, **kwargs)
            # update courseresult and then enrollments of the course
            course = self.get_object()
            for course_result in course.courseresult_set.all():
                course_result.save()
            semester_enrollments = course.enrollment.all()
            for enrollment in semester_enrollments:
                enrollment.update_stats()
            return return_value
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(["POST"])
def updateDropCourses(request, pk):
    try:
        semester = Semester.objects.get(pk=pk)
    except Semester.DoesNotExist:
        return Response(data={"details": "Semester not found"}, status=status.HTTP_404_NOT_FOUND)
    if request.user.adminaccount.is_super_admin or request.user.adminaccount.dept == semester.session.dept:
        try:
            add_courses = request.data['add_courses']
            remove_courses = request.data['remove_courses']
        except Exception as e:
            return Response(data={"details": "Invalid data format"}, status=status.HTTP_400_BAD_REQUEST)
        for course_id in add_courses:
            course = get_object_or_404(Course, pk=course_id)
            if course not in semester.drop_courses.all():
                semester.drop_courses.add(course)
        for course_id in remove_courses:
            course = get_object_or_404(Course, pk=course_id)
            if course in semester.drop_courses.all():
                semester.drop_courses.remove(course)
        return Response(data={"details": "complete"})


class SessionStudentStats(ListAPIView):
    serializer_class = StudentStatsSerializer
    permission_classes = [IsAuthenticated, IsCampusAdmin]
    def get_object(self):
        # get the course object first before getting queryset
        pk = self.kwargs.get('pk')
        session = get_object_or_404(Session, pk=pk)
        self.check_object_permissions(self.request, session)
        return session
    
    def get_queryset(self):
        session = self.get_object()
        return session.studentaccount_set.all()
    

class CourseResultList(ListAPIView):
    serializer_class = CourseResultSerializer
    permission_classes = [IsAuthenticated, IsCampusAdmin]
    def get_object(self):
        # get the course object first before getting queryset
        pk = self.kwargs.get('pk')
        course = get_object_or_404(Course, pk=pk)
        self.check_object_permissions(self.request, course.semester.session)
        return course
    
    def get_queryset(self):
        course = self.get_object()
        course_results = CourseResult.objects.filter(course=course).order_by('-student__is_regular', 'student__registration')
        return course_results
    
    def check_or_generate_entries(self, course):
        ## Autogenerate missing entries of the session, REMOVE this in Version-2
        # REMOVE THIS FUNCTION IN Version-2
        session = course.semester.session
        course_results_all = CourseResult.objects.filter(course=course)
        course_results = course_results_all.filter(is_drop_course=False)
        if (course_results.count() != session.num_students):
            existing_students = set([course_res.student for course_res in course_results])
            session_students = set(session.studentaccount_set.all())
            missing_students = list(session_students.symmetric_difference(existing_students))
            for student in missing_students:
                semester_enroll = SemesterEnroll.objects.filter(semester=course.semester, student=student).first()
                if (semester_enroll is None):
                    try:
                        semester_enroll = SemesterEnroll(semester=course.semester, student=student)
                        semester_enroll.save()
                    except ValidationError:
                        continue
                try:
                    course_res = CourseResult(student=student, course=course)
                    course_res.save()
                except Exception as e:
                    continue
                semester_enroll.courses.add(course)
                    
            return CourseResult.objects.filter(course=course)
        else:
            return course_results_all

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_missing_entries(request, pk):
    try:
        course = Course.objects.get(pk=pk)
    except Course.DoesNotExist:
        return Response(data={"details": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    course_results = course.courseresult_set.all()
    existing_students = set([course_res.student for course_res in course_results])
    session_students = set(course.semester.session.studentaccount_set.all())
    missing_students = list(session_students.symmetric_difference(existing_students))
    for student in missing_students:
        semester_enroll = SemesterEnroll.objects.filter(semester=course.semester, student=student).first()
        if (semester_enroll is None):
            try:
                semester_enroll = SemesterEnroll(semester=course.semester, student=student)
                semester_enroll.save()
            except ValidationError:
                continue
        try:
            course_res = CourseResult(student=student, course=course)
            course_res.save()
        except Exception as e:
            continue
        semester_enroll.courses.add(course)
            
    return Response(data={"info": f"{len(missing_students)} entry generated"})
      
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def student_retakings(request):
    if not user_is_super_OR_dept_admin(request):
        return Response(data={'info': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
    registration = request.data.get('registration')
    student = get_object_or_404(StudentAccount, registration=registration)
    retaking_course_res = CourseResult.objects.filter(student=student, grade_point=0, is_drop_course=False)
    remaining_retaking = []
    for retaking in retaking_course_res:
        retakes = CourseResult.objects.filter(retake_of=retaking, is_drop_course=True, grade_point__gt=0)
        if retakes.count() == 0:
            remaining_retaking.append({
                'courseresult_id': retaking.id,
                'course_code': retaking.course.code,
            })
    return Response(data={'retaking_courses': remaining_retaking})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def session_retake_list(request, pk):
    if not user_is_super_OR_dept_admin(request):
        return Response(data={'info': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
    session = get_object_or_404(Session, pk=pk)
    students = session.studentaccount_set.all()
    session_retake_data = {}
    for student in students:
        student_record = {
            "avatar_url": student.avatar_url,
            "remaining_credits": 0,
            "records": []
        }
        retaking_course_res = CourseResult.objects.filter(student=student, grade_point=0, is_drop_course=False).order_by("course__semester__semester_no")
        if retaking_course_res.count() == 0:
            continue
        for retaking in retaking_course_res:
            retakes = CourseResult.objects.filter(retake_of=retaking, is_drop_course=True, grade_point__gt=0)
            is_retake_complete = bool(retakes.count())
            if not is_retake_complete:
                student_record['remaining_credits'] += retaking.course.course_credit
            student_record['records'].append({
                'course_code': retaking.course.code,
                'course_url': reverse('results:view_course', args=(student.session.dept.name, 
                                                                   student.session.from_year, 
                                                                   student.session.to_year, 
                                                                   retaking.course.semester.year, 
                                                                   retaking.course.semester.year_semester, retaking.course.code)),
                'completed': is_retake_complete
            })
        session_retake_data[student.registration] = student_record
    return Response(data=session_retake_data)
    

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_course_results(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if hasattr(request.user, 'adminaccount'):
        if (request.user.adminaccount.dept is not None and
            request.user.adminaccount.dept != course.semester.session.dept):
            return Response(status=status.HTTP_403_FORBIDDEN)
    else:
        return Response(status=status.HTTP_403_FORBIDDEN)
    for registration in request.data:
        course_result = get_object_or_404(CourseResult, course=course, student__registration=registration)
        for attr, value in request.data[registration].items():
            setattr(course_result, attr, value)
        try:
            course_result.save()
        except Exception as e:
            print(e)
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
    ## updating stats data: credits, points and gpa for each enrolls
    # romoved: (note: each courseresult related enrollments are now updated after saving the course_result in save() method)
    return Response(status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def render_tabulation(request, pk):
    try:
        semester = Semester.objects.get(pk=pk)
    except Semester.DoesNotExist:
        return Response(data={"details": "Semester not found"}, status=status.HTTP_404_NOT_FOUND)
    try:
        render_config = request.data['render_config']
        footer_data_raw = request.data['footer_data_raw']
    except KeyError:
        return Response(data={"necessary data missing"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        files = get_tabulation_files(semester, render_config, footer_data_raw)
    except Exception as e:
        return Response(data={'details': f"cannot generate tabulation, Error: {e}"}, status=status.HTTP_400_BAD_REQUEST)
    if hasattr(semester, 'semesterdocument'):
        semesterdoc = semester.semesterdocument
    else:
        semesterdoc = SemesterDocument.objects.create(semester=semester)
    filename = f"{get_ordinal_number(semester.semester_no)} semester ({semester.session.dept.name.upper()} {semester.session.session_code})"
    # erasing before saving
    semesterdoc.tabulation_sheet.delete(save=True)
    semesterdoc.tabulation_thumbnail.delete(save=True)
    semesterdoc.tabulation_sheet.save(filename+'.pdf', ContentFile(files["pdf_file"]))
    if (files["thumbnail_file"]):
        semesterdoc.tabulation_thumbnail.save('thumbnail.png', ContentFile(files["thumbnail_file"]))
    semesterdoc.tabulation_sheet_render_by = request.user
    semesterdoc.tabulation_sheet_render_time = timezone.now()
    semesterdoc.tabulatiobn_sheet_render_config = utils.format_render_config(request)
    semesterdoc.save()
    doc_data = {
        'thumbnail': semesterdoc.tabulation_thumbnail.url,
        'tabulation_name': semesterdoc.tabulation_filename,
        'download_url': reverse('results:download_semester_tabulation', kwargs={'pk':semester.id}),
        'render_time': semesterdoc.tabulation_sheet_render_time,
        'renderer_user': semesterdoc.tabulation_sheet_render_by.adminaccount.user_full_name,
    }
    return Response(data=doc_data)
    
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_semester_is_running(request, pk):
    try:
        semester = Semester.objects.get(pk=pk)
    except Semester.DoesNotExist:
        return Response(data={"details": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    # cheking admin user
    if hasattr(request.user, 'adminaccount'):
        if (request.user.adminaccount.dept is not None and
            request.user.adminaccount.dept != semester.session.dept):
            return Response(data={'details': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response(data={'details': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    # checking password
    if not utils.is_confirmed_user(request, username=request.user.username):
        return Response(data={"details": "Incorrect password"}, status=status.HTTP_403_FORBIDDEN)
    semester.is_running = not semester.is_running
    semester.save()
    return Response(data={"status": "ok"})    
    
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_semester(request, pk):
    try:
        semester = Semester.objects.get(pk=pk)
    except Semester.DoesNotExist:
        return Response(data={"details": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    # cheking admin user
    if hasattr(request.user, 'adminaccount'):
        if (request.user.adminaccount.dept is not None and
            request.user.adminaccount.dept != semester.session.dept):
            return Response(data={'details': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response(data={'details': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    # checking password
    if not utils.is_confirmed_user(request, username=request.user.username):
        return Response(data={"details": "Incorrect password"}, status=status.HTTP_403_FORBIDDEN)
    # url to be redirected after deletion
    session_url = reverse('results:view_session', kwargs={
        'dept_name': semester.session.dept.name,
        'from_year': semester.session.from_year,
        'to_year': semester.session.to_year
    })
    # delete
    semester.delete()
    return Response(data={"session_url": session_url})       
 
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_session(request, pk):
    try:
        session = Session.objects.get(pk=pk)
    except Session.DoesNotExist:
        return Response(data={"details": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    # cheking admin user
    if hasattr(request.user, 'adminaccount'):
        if (request.user.adminaccount.dept is not None and
            request.user.adminaccount.dept != session.dept):
            return Response(data={'details': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response(data={'details': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    # checking password
    if not utils.is_confirmed_user(request, username=request.user.username):
        return Response(data={"details": "Incorrect password"}, status=status.HTTP_403_FORBIDDEN)
    # checking if it has courses
    if session.has_semester:
        return Response(data={"details": "This Session cannot be deleted while it has at least one semester"}, status=status.HTTP_406_NOT_ACCEPTABLE)
    # url to be redirected after deletion
    dept_url = reverse('results:view_department', kwargs={
        'dept_name': session.dept.name
    })
    # delete
    session.delete()
    return Response(data={"dept_url": dept_url})    


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_course(request, pk):
    try:
        course = Course.objects.get(pk=pk)
    except Course.DoesNotExist:
        return Response(data={"details": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    # cheking admin user
    if hasattr(request.user, 'adminaccount'):
        if (request.user.adminaccount.dept is not None and
            request.user.adminaccount.dept != course.semester.session.dept):
            return Response(data={'details': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response(data={'details': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    # checking password
    if not utils.is_confirmed_user(request, username=request.user.username):
        return Response(data={"details": "Incorrect password"}, status=status.HTTP_403_FORBIDDEN)
    # checking if it has non empty records
    if bool(num := course.num_nonempty_records):
        return Response(
            data={"details": f"This course cannot be deleted while it has {num} non empty records"}, 
            status=status.HTTP_406_NOT_ACCEPTABLE
        )
    # url to be redirected after deletion
    semester_url = reverse('results:view_semester', kwargs={
        'dept_name': course.semester.session.dept.name,
        'from_year': course.semester.session.from_year,
        'to_year': course.semester.session.to_year,
        'year': course.semester.year,
        'semester': course.semester.year_semester,
    })
    # delete
    course.delete()
    return Response(data={"semester_url": semester_url})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_enrollment(request):
    try:
        enrollment_id = request.data.get('enrollment_id')
        enrollment = SemesterEnroll.objects.get(pk=enrollment_id)
    except SemesterEnroll.DoesNotExist:
        return Response(data={"details": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    # cheking admin user
    if not user_is_super_OR_dept_admin(request):
        return Response(data={'details': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    # checking of semester running
    if not enrollment.semester.is_running:
        return Response(data={'details': "Semester is offline"}, status=status.HTTP_400_BAD_REQUEST)
    # delete
    semester = enrollment.semester
    student = enrollment.student
    course_res = CourseResult.objects.filter(student=student, course__semester=semester)
    course_res.delete()
    enrollment.delete()
    student.update_stats()
    return Response(data={"info": "deleted", "id": enrollment_id, "current_enroll_count": semester.semesterenroll_set.count()})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_course_result(request):
    try:
        course_res_id = request.data.get('courseres_id')
        course_res = CourseResult.objects.get(pk=course_res_id)
    except CourseResult.DoesNotExist:
        return Response(data={"details": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    # cheking admin user
    if not user_is_super_OR_dept_admin(request):
        return Response(data={'details': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    # checking of semester running
    if not course_res.course.semester.is_running:
        return Response(data={'details': "Semester is offline"}, status=status.HTTP_400_BAD_REQUEST)
    # delete
    course_res.delete()
    return Response(data={"info": "deleted"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_new_entry_to_course(request, pk):
    # checking posted data
    try:
        reg_no = request.data['registration']
        semester_id = request.data['semester_id']
        retake_for = request.data['retake_for']
    except KeyError:
        return Response(data={"details":"Data is missing"}, status=status.HTTP_400_BAD_REQUEST)
    # course
    try:
        course = Course.objects.get(pk=pk)
    except Course.DoesNotExist:
        return Response(data={"details":"Course not found"}, status=status.HTTP_404_NOT_FOUND)
    #retaking courseResult
    try:
        retaking = CourseResult.objects.get(pk=retake_for)
    except CourseResult.DoesNotExist:
        return Response(data={"details":"Course not found"}, status=status.HTTP_404_NOT_FOUND)
    # finding student
    try:
        student = StudentAccount.objects.get(registration=reg_no)
    except StudentAccount.DoesNotExist:
        return Response(data={"details":"Invalid Registration Number"}, status=status.HTTP_400_BAD_REQUEST)
    # finding enrollment of the specified semester
    try:
        enroll = SemesterEnroll.objects.get(semester__id=semester_id, semester__is_running=True, student=student)
    except SemesterEnroll.DoesNotExist:
        return Response(data={"details":"Student didn't enrolled for this semester, or the semester is not running"}, status=status.HTTP_400_BAD_REQUEST)
    # checking if this course is already in the enrollment
    if course in enroll.courses.all():
        return Response(data={"details":"Student already registered for this course"}, status=status.HTTP_400_BAD_REQUEST)
    # checking wheather this semester has included this course in the drop courses, then add it if not included
    if course not in enroll.semester.drop_courses.all():
        enroll.semester.drop_courses.add(course)
    # creating course result
    try:
        CourseResult.objects.create(
            student = student,
            course = course,
            retake_of = retaking,
            is_drop_course = True
        )
    except Exception as e:
        return Response(data={"details": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    # adding course to enrollment
    enroll.courses.add(course)
    
    return Response(data={'status': 'Course Result for the student has been created'})

@csrf_exempt
def process_course_excel(request, pk):
    try:
        course = Course.objects.get(pk=pk)
        course_results = course.courseresult_set.all()
    except Course.DoesNotExist:
        return JsonResponse({'details': "Course not found"}, status=404)
    if not course.semester.is_running:
        return JsonResponse({'details': "Semester is not running!"}, status=400)
    if request.method == "POST" and request.FILES.get('excel'):
        excel_file = request.FILES.get('excel')
        # checking filename for our course here
        filename = excel_file.name.replace(' ', '').lower()
        course_codename = course.code.replace(' ', '').lower()
        if filename.find(course_codename) == -1:
            return JsonResponse({'details': 'Filename must contain course code'}, status=400)
        # preparing workbook
        try:
            buffer = BytesIO(excel_file.read())
            wb = openpyxl.load_workbook(buffer)
            sheet = wb[wb.sheetnames[0]]
            rows = list(sheet.rows)
            header = [cell.value.lower().strip() if cell.value is not None else None for cell in rows[0]]
            data_rows = rows[1:]
        except Exception as e:
            return JsonResponse({'details': e}, status=400)
            
        try:
            reg_col_idx = header.index('reg')
        except ValueError:
            return JsonResponse({'details': "Registration no. column 'reg' not found"}, status=400)
        logs = {
            'success': 0,
            'errors': {
                'missing_cols': set(),
                'parse_errors': [],
                'save_errors': [],
                'unmatching': []
            }
        }
        # data saving
        if 'total' in header: 
            total_col_idx = header.index('total')
            for r in range(len(data_rows)):
                try:
                    reg_no = int(data_rows[r][reg_col_idx].value)
                    total = data_rows[r][total_col_idx].value
                except Exception as e:
                    logs['errors']['parse_errors'].append(f'row: {r+2}. error: {e}')
                    continue
                course_res = course_results.filter(student__registration=reg_no).first()
                if course_res:
                    if total is None:
                        logs['errors']['parse_errors'].append(f'Reg no: {reg_no} Missing value for: total. Value set to : 0')
                        total = 0
                    course_res.total_score = total
                    # setting other scores to None
                    course_res.part_A_score = None
                    course_res.part_B_score = None
                    course_res.incourse_score = None
                    try:
                        course_res.save()
                    except Exception as e:
                        logs['errors']['save_errors'].append(f"reg. no: {reg_no}. Error: {e}")
                        continue
                    logs['success'] += 1
                else:
                    logs['errors']['unmatching'].append(f'Reg: {reg_no}. Row number: {r+2}')
        else:
            course_props = {
                'code_a': 'part_A_code',
                'marks_a': 'part_A_score',
                'code_b': 'part_B_code',
                'marks_b': 'part_B_score',
                'marks_tt': 'incourse_score',
            }
            for r in range(len(data_rows)):
                try:
                    reg_no = int(data_rows[r][reg_col_idx].value)
                except Exception as e:
                    logs['errors']['parse_errors'].append(f'row: {r+2}. error: {e}')
                    continue
                course_res = course_results.filter(student__registration=reg_no).first()
                if course_res:
                    for col, prop_name in course_props.items():
                        try:
                            title_idx = header.index(col)
                        except Exception as e:
                            logs['errors']['missing_cols'].add(col)
                            continue
                        try:
                            value = data_rows[r][title_idx].value
                            if col not in ['code_a', 'code_b']:
                                if value is None:
                                    logs['errors']['parse_errors'].append(f'Reg no: {reg_no} Missing value for: {col}')
                                else:
                                    value = float(value)
                        except Exception as e:
                            logs['errors']['parse_errors'].append(f'Reg no: {reg_no}. error: {e}')
                            continue
                        setattr(course_res, prop_name, value)
                    try:
                        course_res.save()
                    except Exception as e:
                        logs['errors']['save_errors'].append(f"Reg. no: {reg_no}. Error: {e}")
                        continue
                    logs['success'] += 1
                else:
                    logs['errors']['unmatching'].append(f'Reg: {reg_no}. Row number: {r+2}')
        
        logs['has_missing_cols'] = bool(len(logs['errors']['missing_cols']))    
        logs['has_parse_errors'] = bool(len(logs['errors']['parse_errors']))    
        logs['has_save_errors'] = bool(len(logs['errors']['save_errors']))
        logs['has_unmatching_errors'] = bool(len(logs['errors']['unmatching']))  
        
        summary = render_to_string('results/components/excel_summary_list.html', context={'logs': logs})
        return JsonResponse({'status':'Complete', 'summary':summary})
    else:
        return JsonResponse({'details': 'Not allowed!'}, status=400)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_backup(request):
    try:
        dept_id = request.data['department_id']
        dept = Department.objects.get(id=dept_id)
    except KeyError:
        return Response(data={"details":"Data is missing"}, status=status.HTTP_400_BAD_REQUEST)
    except Department.DoesNotExist:
        return Response(data={"details":"Department Not Found"}, status=status.HTTP_404_NOT_FOUND)
    # cheking admin user
    if ((not hasattr(request.user, 'adminaccount')) or
        request.user.adminaccount.dept is not None and
        request.user.adminaccount.dept != dept):
        return Response(data={'details': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    # get backup data
    try:
        backup_data = utils.create_backup(dept)
    except Exception as e:
        return Response(data={"details": f"Cannot create backup. Error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    backup = Backup(
        department = dept,
        data = backup_data
    )
    backup.save()
    backups_qs = Backup.objects.filter(department=dept)
    deleted_backups = []
    if backups_qs.count() > 5:
        deleting_backups = list(backups_qs)[5:]
        for d_backup in deleting_backups:
            deleted_backups.append(d_backup.id)
            d_backup.delete()
    response = {
        'deleted_backups': deleted_backups,
        'new_backup_id': backup.id,
        'new_backup_elem': render_to_string('results/components/backup_item.html', context={'backup': backup}),
        'is_no_backup_shown': backups_qs.count() == 1,
    }
    
    return Response(data=response)


@csrf_exempt
def perform_restore(request):
    if (not request.user.is_authenticated) or (not hasattr(request.user, 'adminaccount')):
        return JsonResponse({'details': "Forbidden Action"}, status=403)
    if request.method == "POST" and request.FILES.get('backup_file'):
        backup_file = request.FILES.get('backup_file')
        decoded_file = backup_file.read().decode('utf-8')
        data = json.loads(decoded_file)
    else:
        return JsonResponse({'details': "Semester is not running!"}, status=400)
    if (request.user.adminaccount.dept is not None and 
        request.user.adminaccount.dept.name.lower() != data['dept']):
        return JsonResponse({'details': "Forbidden Action"}, status=403)
    try:
        dept = Department.objects.get(name=data['dept'])
    except Department.DoesNotExist:
        return JsonResponse({'details': "Department Not Found"}, status=404)
    try:
        obj_count = utils.get_obj_count(data['sessions'])
    except Exception as e:
        return JsonResponse({'details': "Bad data"}, status=406)

    utils.delete_all_of_dept(dept)
    result = restore_data_task.delay(dept.id, data['sessions'], obj_count)
    progress_url = reverse('celery_progress:task_status', args=(result.task_id,))
    return JsonResponse(data={'info': 'ok', 'progress_url': progress_url})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def course_result_entry_info(request):
    try:
        result_id = request.data.get('result_id')
        course_res = CourseResult.objects.get(pk=result_id)
    except CourseResult.DoesNotExist:
        return Response(data={'details': "Not found"})
    enrollment = course_res.course.enrollment.filter(student=course_res.student).first()
    context = {
        'course_res': course_res, 
        'enrollment': enrollment, 
    }
    if course_res.retake_of:
        context['retake_course'] = course_res.retake_of.course
    context['retakes'] = CourseResult.objects.filter(retake_of=course_res).order_by("course__semester__session__from_year")
    html_content= render_to_string('results/components/courseresult_info.html', context=context)
    return Response(data={"content": html_content, 'semester_running': course_res.course.semester.is_running})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def students_stats(request, session_pk):
    try:
        session = Session.objects.get(pk=session_pk)
    except Session.DoesNotExist:
        return Response(data={"details": "Session Not Found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_transcript(request):
    context = request.data
    context['admin_name'] = request.user.adminaccount.user_full_name
    try:
        transcript_pdf = get_transcript(context)
    except Exception as e:
        return Response(data={"details": f"Error during rendering: {e}"}, status=status.HTTP_400_BAD_REQUEST)
    pdf_base64 = base64.b64encode(transcript_pdf).decode('utf-8')
    redis_key = str(int(time.time())) + request.user.username
    cache.set(redis_key, pdf_base64)
    filename = "transcript-" + str(request.data['reg_num']) + ".pdf"
    return Response(data={'url': reverse('results:download_cachedpdf', args=(redis_key, filename))})


@csrf_exempt
def generate_gradesheet(request):
    if request.method == "POST" and request.FILES.get('excel'):
        excel_file = request.FILES.get('excel')
        formdata = json.loads(request.POST.get('data'))
        num_semesters = formdata['num_semesters']
        try:
            excel_data = utils.parse_gradesheet_excel(excel_file, formdata, num_semesters)
        except Exception as e:
            return JsonResponse(data={"details": f"Error while parsing the excel file: {e}"}, status=400)
        try:
            sheet_pdf = get_gradesheet(formdata, excel_data, num_semesters=num_semesters)
        except Exception as e:
            return JsonResponse(data={"details": f"Error while rendering file: {e}"}, status=400)
        pdf_base64 = base64.b64encode(sheet_pdf).decode('utf-8')
        redis_key = str(int(time.time())) + request.user.username
        cache.set(redis_key, pdf_base64)
        gradesheet_title = f"-gradesheet_{formdata['first_sem_year']}-{formdata['first_sem_number']}"
        if num_semesters == 2:
            gradesheet_title += f"_{formdata['second_sem_year']}-{formdata['second_sem_number']}"
        filename =  str(formdata['reg_num']) + gradesheet_title + ".pdf"
        return JsonResponse({'url': reverse('results:download_cachedpdf', args=(redis_key, filename))})
    else:
        return JsonResponse({'details': 'Not allowed!'}, status=400)


    
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_stats(request, registration):
    if not hasattr(request.user, 'adminaccount'):
        return Response(data={"details": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    current_student = get_object_or_404(StudentAccount, registration=registration)
    current_student_cgpa = current_student.raw_cgpa
    session_students = current_student.session.studentaccount_set.all() 
    session_students_with_cgpa = [student for student in session_students if student.raw_cgpa is not None]
    session_students_sorted = utils.rank_students(session_students_with_cgpa)
    session_students_cgpa = [student.raw_cgpa for student in session_students_sorted]
    # session_students_cgpa.sort(reverse=True)
    data = {
       'classes': {
            'A+': 0, 'A': 0, 'A-': 0,
            'B+': 0, 'B': 0, 'B-': 0,
            'C+': 0, 'C': 0, 'C-': 0,
            'F': 0,
        } 
    }
    try:
        position_in_class = session_students_cgpa.index(current_student_cgpa) + 1
        data['position_suffix'] = get_ordinal_suffix(position_in_class)
    except ValueError:
        position_in_class = "Last"
        data['position_suffix'] = ""
    data['position'] = position_in_class
    
    data['letter_grade'] = get_letter_grade(current_student_cgpa)
    for cgpa in session_students_cgpa:
        data['classes'][get_letter_grade(cgpa)] += 1
    
    return Response(data=data)
    
  
@api_view(['GET'])
def sust_student_data(request):
    registration = request.GET.get('registration', None)
    if registration is None or (not str(registration).isdigit()):
        raise BadrequestException("Required data not provided")
    student = get_object_or_404(StudentAccount, pk=registration)
    response_data = {}
    response_data['student'] = {
        'registration': registration,
        'name': student.student_name,
        'cgpa': student.student_cgpa,
        'dept': student.session.dept.fullname,
        'session': student.session.session_code,
        'avatar_url': student.avatar_url,
        'email': '[empty]',
    }
    response_data['semester_gradesheets'] = []
    response_data['year_gradesheets'] = []
    for sem_num in student.gradesheet_semesters:
        response_data['semester_gradesheets'].append(
            {
                'semester_number': sem_num,
                'semester_suffix': get_ordinal_suffix(sem_num),
                'url': reverse('results:download_semester_gradesheet', args=(registration, sem_num))
            }
        )
    for year_num in student.gradesheet_years:
        response_data['year_gradesheets'].append(
            {
                'year_number': year_num,
                'year_suffix': get_ordinal_suffix(year_num),
                'url': reverse('results:download_year_gradesheet', args=(registration, year_num))
            }
        )
    response_data['transcript_url'] = reverse('results:download_transcript', args=(registration,))
    response_data['full_document_url'] = "/"
    return Response(data=response_data) 


@csrf_exempt
def render_customdoc(request):
    st = ""
    excel_file = request.FILES.get("file", None)
    admin_name = request.user.first_name + " " + request.user.last_name
    document = utils.render_customdoc(excel_file, admin_name)
    pdf_base64 = base64.b64encode(document).decode('utf-8')
    redis_key = str(int(time.time())) + request.user.username
    cache.set(redis_key, pdf_base64)
    filename = "document-" + str(int(time.time())) +  ".pdf"
    return JsonResponse(data={'url': reverse('results:download_cachedpdf', args=(redis_key, filename))})
    # return JsonResponse(data={'type': st, 'files': str(type(request.FILES))})



@csrf_exempt
def create_session_prevpoint_via_excel(request, pk):
    try:
        semester = Semester.objects.get(pk=pk)
    except Semester.DoesNotExist:
        return JsonResponse({'details': "Semester not found"}, status=404)
    if not semester.prevpoint_applicable:
            return JsonResponse({'details': 'Not applicable!'}, status=400)
    if request.method == "POST" and request.FILES.get('excel'):
        excel_file = request.FILES.get('excel')

        if hasattr(semester.session, 'previouspoint'):
            prevPoint = semester.session.previouspoint
        else:
            prevPoint = PreviousPoint(
                session=semester.session, 
                added_by=request.user, 
                upto_semester_num=(semester.semester_no-1)
            )
            prevPoint.save()
        summary = utils.createStudentPointsFromExcel(excel_file, prevPoint, semester.session)
        return JsonResponse({'status':'Complete', 'summary':summary})
    else:
        return JsonResponse({'details': 'Not allowed!'}, status=400)

    
# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def get_transcript_data(request, registration):
#     if not hasattr(request.user, 'adminaccount'):
#         return Response(data={"details": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
#     student = get_object_or_404(StudentAccount, registration=registration)
#     data = {
#         'name': student.student_name,
#         'sesion': student.session.session_code,
#         'dept': student.session.dept.fullname,
        
#     }