from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError, PermissionDenied
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
from .serializer import (SessionSerializer, SemesterSerializer, CourseSerializer,
                         CourseResultSerializer, StudentStatsSerializer, DocHistorySerializer)
from .permission import IsCampusAdmin, IsSuperAdmin, IsSuperOrDeptAdmin, IsSuperAdminOrDeptHead, IsSECAcademic
from results.models import (Department, Session, Semester, Course, PreviousPoint, StudentPoint,
                            CourseResult, SemesterDocument, SemesterEnroll, Backup, StudentCustomDocument,
                            SupplementaryDocument, StudentAcademicData, DocHistory)
from account.models import StudentAccount
from . import utils
from . import excel_parsers
from results.utils import get_ordinal_number, get_letter_grade, get_ordinal_suffix, has_semester_access
from results.pdf_generators.tabulation_generator import get_tabulation_files
from results.pdf_generators.gradesheet_generator_manual import get_gradesheet
from results.pdf_generators.transcript_generator_manual import get_transcript
from results.pdf_generators.topsheet_generator import render_topsheet
from results.pdf_generators.scorelist_generator import render_scorelist
from results.pdf_generators.utils import merge_pdfs_from_buffers
from results.tasks import restore_dept_data_task, restore_session_data_task
from results.decorators_and_mixins import superadmin_required, superadmin_or_deptadmin_required
from results import copiers
from django.conf import settings
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
    status_code = 400
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
    permission_classes = [IsAuthenticated, IsSuperOrDeptAdmin]
    
    def get_queryset(self):
        pk = self.kwargs.get("pk")
        sessions = Session.objects.filter(id=pk)
        return sessions
    
    def perform_create(self, serializer):
        try:
            repeat_no = serializer.validated_data.get('repeat_number', 0)
            part_no = serializer.validated_data.get('part_no', 0)
            super().perform_create(serializer)
            pk = serializer.data.get('id')
            semester = Semester.objects.get(pk=pk)
            if repeat_no == 0 and part_no == 0:
                utils.create_course_enrollments(semester)
            else:
                copiers.copyCoursesAndSemesters(semester, self.request.user)
        except Exception as e:
            raise BadrequestException(str(e))


class SemesterUpdate(UpdateAPIView):
    serializer_class = SemesterSerializer
    permission_classes = [IsAuthenticated, IsSuperOrDeptAdmin]
    
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
    permission_classes = [IsAuthenticated, IsSuperOrDeptAdmin]
    queryset = Course.objects.all()
    
    def create(self, request, *args, **kwargs):
        data = request.data
        data['added_by'] = request.user.id
        serializer = self.get_serializer(data=data)
        semester = get_object_or_404(Semester, pk=data['semester'])
        if serializer.is_valid() and has_semester_access(semester, request.user.adminaccount):
            self.perform_create(serializer)
            course_id = serializer.data.get('id')
            course = Course.objects.get(id=course_id)
            utils.add_course_to_enrollments(course=course)
            if not request.data.get('is_carry_course', False):
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
    permission_classes = [IsAuthenticated, IsSuperOrDeptAdmin]
    
    def get_queryset(self):
        pk = self.kwargs.get("pk")
        courses = Course.objects.filter(id=pk)
        if courses.first() and (not has_semester_access(courses.first().semester, self.request.user.adminaccount)):
            raise PermissionDenied
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
@permission_classes([IsAuthenticated, IsSuperOrDeptAdmin])
def updateDropCourses(request, pk):
    try:
        semester = Semester.objects.get(pk=pk)
    except Semester.DoesNotExist:
        return Response(data={"details": "Semester not found"}, status=status.HTTP_404_NOT_FOUND)
    if has_semester_access(semester, request.user.adminaccount):
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
    else:
        return Response(data={"detail": "Access Denied"}, status=status.HTTP_403_FORBIDDEN)


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
    permission_classes = [IsAuthenticated, IsSuperOrDeptAdmin]
    def get_object(self):
        # get the course object first before getting queryset
        pk = self.kwargs.get('pk')
        course = get_object_or_404(Course, pk=pk)
        from_semester = self.request.GET.get('sem')
        if from_semester:
            semester = get_object_or_404(Semester, id=from_semester)
            if not has_semester_access(semester, self.request.user.adminaccount):
                raise PermissionDenied
        elif not has_semester_access(course.semester, self.request.user.adminaccount):
            raise PermissionDenied
        return course
    
    def get_queryset(self):
        course = self.get_object()
        from_semester = self.request.GET.get('sem')
        if from_semester:
            semester = get_object_or_404(Semester, id=from_semester)
            students = [enrollment.student for enrollment in semester.semesterenroll_set.all()]
            course_results = CourseResult.objects.filter(is_drop_course=True, course=course, student__in=students).order_by('-student__is_regular', 'student__registration')
        else:
            course_results = CourseResult.objects.filter(course=course).order_by('is_drop_course', '-student__is_regular', 'student__registration')
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
@permission_classes([IsAuthenticated, IsSuperOrDeptAdmin])
def generate_missing_entries(request, pk):
    try:
        course = Course.objects.get(pk=pk)
    except Course.DoesNotExist:
        return Response(data={"details": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    if not has_semester_access(course.semester, request.user.adminaccount):
        return Response(data={'details': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    course_results = course.courseresult_set.all()
    existing_students = set([course_res.student for course_res in course_results if course_res.student.session == course.semester.session])
    enrolled_students = set([enroll.student for enroll in course.semester.semesterenroll_set.all()])
    missing_students = list(enrolled_students.symmetric_difference(existing_students))
    for student in missing_students:
        semester_enroll = SemesterEnroll.objects.filter(semester=course.semester, student=student).first()
        if (semester_enroll is None):
                continue
        try:
            course_res = CourseResult(student=student, course=course)
            course_res.save()
        except Exception as e:
            continue
        semester_enroll.courses.add(course)
            
    return Response(data={"info": f"{len(missing_students)} entry generated"})
      
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsSuperOrDeptAdmin])
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
@permission_classes([IsAuthenticated, IsSuperOrDeptAdmin])
def session_retake_list(request, pk):
    if not user_is_super_OR_dept_admin(request):
        return Response(data={'info': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
    session = get_object_or_404(Session, pk=pk)
    students = session.studentaccount_set.all()
    session_retake_data = {}
    for student in students:
        student_record = {
            "avatar_url": student.avatar_url,
            "credits_completed": student.credits_completed,
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
                'course_url': reverse('results:view_course', args=(student.session.dept.name, retaking.course.b64_id)),
                'completed': is_retake_complete
            })
        session_retake_data[student.registration] = student_record
    return Response(data=session_retake_data)
    

@api_view(["POST"])
@permission_classes([IsAuthenticated, IsSuperOrDeptAdmin])
def update_course_results(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if not has_semester_access(course.semester, request.user.adminaccount):
        return Response(data={'details': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    for registration in request.data:
        course_result = get_object_or_404(CourseResult, course=course, student__registration=registration)
        for attr, value in request.data[registration].items():
            setattr(course_result, attr, value)
        try:
            course_result.save()
        except Exception as e:
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
    if not has_semester_access(semester, request.user.adminaccount):
        return Response(data={'details': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    try:
        render_config = request.data['render_config']
        footer_data_raw = request.data['footer_data_raw']
    except KeyError:
        return Response(data={"necessary data missing"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        files = get_tabulation_files(semester, render_config, footer_data_raw)
    except Exception as e:
        print(e, flush=1)
        return Response(data={'details': f"cannot generate tabulation, Error: {e}"}, status=status.HTTP_400_BAD_REQUEST)
    if hasattr(semester, 'semesterdocument'):
        semesterdoc = semester.semesterdocument
    else:
        semesterdoc = SemesterDocument.objects.create(semester=semester)
    filename = f"{get_ordinal_number(semester.semester_no)} semester ({semester.session.dept.name.upper()} {semester.session.session_code})"
    if semester.part_no:
        filename += f"_p{semester.part_no}"
    if semester.repeat_number:
        filename += f"_r{semester.repeat_number}"
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
@permission_classes([IsAuthenticated, IsSuperOrDeptAdmin])
def toggle_semester_is_running(request, pk):
    try:
        semester = Semester.objects.get(pk=pk)
    except Semester.DoesNotExist:
        return Response(data={"details": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    # cheking admin user
    if (not request.user.adminaccount.is_super_admin and
        (request.user.adminaccount != semester.session.dept.head)):
        return Response(data={'details': 'forbidden'}, status=status.HTTP_403_FORBIDDEN)
    # checking password
    if not utils.is_confirmed_user(request, username=request.user.username):
        return Response(data={"details": "Incorrect password"}, status=status.HTTP_403_FORBIDDEN)
    semester.is_running = not semester.is_running
    semester.updated_by = request.user
    semester.save()
    return Response(data={"status": "ok"})    
    
    
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSuperOrDeptAdmin])
def delete_semester(request, pk):
    try:
        semester = Semester.objects.get(pk=pk)
    except Semester.DoesNotExist:
        return Response(data={"details": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    # cheking admin user
    if (not request.user.adminaccount.is_super_admin and
        (request.user.adminaccount != semester.session.dept.head)):
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
@permission_classes([IsAuthenticated, IsSuperOrDeptAdmin])
def delete_session(request, pk):
    try:
        session = Session.objects.get(pk=pk)
    except Session.DoesNotExist:
        return Response(data={"details": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    # cheking admin user
    if not (request.user.adminaccount.is_super_admin or (session.dept.head == request.user.adminaccount)):
        return Response(data={'details': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    # checking password
    if not utils.is_confirmed_user(request, username=request.user.username):
        return Response(data={"details": "Incorrect password"}, status=status.HTTP_403_FORBIDDEN)
    # url to be redirected after deletion
    dept_url = reverse('results:view_department', kwargs={
        'dept_name': session.dept.name
    })
    # delete
    session.delete()
    return Response(data={"dept_url": dept_url})    


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSuperOrDeptAdmin])
def delete_course(request, pk):
    try:
        course = Course.objects.get(pk=pk)
    except Course.DoesNotExist:
        return Response(data={"details": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    if not has_semester_access(course.semester, request.user.adminaccount):
        return Response(data={'details': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
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
        'b64_id': course.semester.b64_id,
    })
    # delete
    course.delete()
    return Response(data={"semester_url": semester_url})


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSuperOrDeptAdmin])
def toggle_enrollment_is_publishable(request):
    enrollid = request.data.get('enrollment_id')
    if enrollid is None:
        return Response(data={'details': 'no enroll id provided'}, status=status.HTTP_400_BAD_REQUEST)
    enroll = get_object_or_404(SemesterEnroll, pk=enrollid)
    if not has_semester_access(enroll.semester, request.user.adminaccount):
        return Response(data={'details': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    enroll.is_publishable = not enroll.is_publishable
    enroll.save()
    enroll.student.update_stats()
    return Response(data={'is_publishable': enroll.is_publishable})
    
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_enrollment(request, pk):
    try:
        semester = Semester.objects.get(pk=pk)
    except Semester.DoesNotExist:
        return Response(data={"details": "Semester Not Found"}, status=status.HTTP_404_NOT_FOUND)
    if not has_semester_access(semester, request.user.adminaccount):
        return Response(data={'details': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    try:
        reg_num = int(request.data['registration_no'])
    except Exception as e:
        return Response(data={"details": "Invalid registration number"}, status=status.HTTP_400_BAD_REQUEST)
    student = StudentAccount.objects.filter(registration=reg_num, session=semester.session).first()
    if student == None:
        return Response(data={"details": "Student not found in this session"}, status=status.HTTP_404_NOT_FOUND)
    enroll = SemesterEnroll(semester=semester, student=student)
    try:
        enroll.save()
    except Exception as e:
        return Response(data={"details": e}, status=status.HTTP_400_BAD_REQUEST)
    utils.add_course_and_create_courseresults(enroll)
    return Response(data={'info': f'{reg_num} Added'})
    
        
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_enrollment(request):
    try:
        enrollment_id = request.data.get('enrollment_id')
        enrollment = SemesterEnroll.objects.get(pk=enrollment_id)
    except SemesterEnroll.DoesNotExist:
        return Response(data={"details": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    if not has_semester_access(enrollment.semester, request.user.adminaccount):
        return Response(data={'details': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    # cheking admin user
    if not user_is_super_OR_dept_admin(request):
        return Response(data={'details': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    # checking of semester running
    if not enrollment.semester.is_running:
        return Response(data={'details': "Semester is offline"}, status=status.HTTP_400_BAD_REQUEST)
    # delete
    semester = enrollment.semester
    student = enrollment.student
    enrollment.delete()
    return Response(data={"info": "deleted", "id": enrollment_id, "current_enroll_count": semester.semesterenroll_set.count()})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_course_result(request):
    try:
        course_res_id = request.data.get('courseres_id')
        course_res = CourseResult.objects.get(pk=course_res_id)
    except CourseResult.DoesNotExist:
        return Response(data={"details": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    # access
    if not has_semester_access(course_res.course.semester, request.user.adminaccount):
        return Response(data={'details': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
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
    course = get_object_or_404(Course, pk=pk)
    if not has_semester_access(course.semester, request.user.adminaccount):
        return Response(data={'details': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    reg_no = request.data.get('registration')
    student = get_object_or_404(StudentAccount, registration=reg_no)
    try:
        utils.add_student_to_course(student, course)
    except Exception as e:
        return Response(data={"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(data={'status': 'Course Result for the student has been created'})

@csrf_exempt
def process_course_excel(request, pk):
    try:
        course = Course.objects.get(pk=pk)
        course_results = course.courseresult_set.all()
    except Course.DoesNotExist:
        return JsonResponse({'details': "Course not found"}, status=404)
     # access
    if request.user.adminaccount not in course.semester.editor_members:
        return JsonResponse(data={'details': 'Access denied'}, status=403)
    from_semester_pk = str(request.POST.get('semester_from')).strip()
    from_semester = None # For Carry Course Type
    if from_semester_pk.isdigit():
        from_semester = get_object_or_404(Semester, pk=from_semester_pk)
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
                student = StudentAccount.objects.filter(registration=reg_no).first()
                if student == None:
                    logs['errors']['unmatching'].append(f'Reg: {reg_no} -  student not found. Row number: {r+2}')
                    continue
                if student.session != course.semester.session:
                    course_res = utils.get_or_create_entry_for_carryCourse(student, course)
                else:
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
                    # binding carry courseresult
                    retaking = utils.try_get_carrycourse_retake_of(course_res)
                    if retaking and course_res.retake_of is None:
                        course_res.retake_of = retaking
                        course_res.save()
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
                student = StudentAccount.objects.filter(registration=reg_no).first()
                if student == None:
                    logs['errors']['unmatching'].append(f'Reg: {reg_no} -  student not found. Row number: {r+2}')
                    continue
                if student.session != course.semester.session:
                    course_res = utils.get_or_create_entry_for_carryCourse(student, course)
                else:
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
                    # binding carry courseresult
                    retaking = utils.try_get_carrycourse_retake_of(course_res)
                    if retaking and course_res.retake_of is None:
                        course_res.retake_of = retaking
                        course_res.save()
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
    session_id = request.data.get('session_id')
    backup_data = utils.create_backup(dept, session_id)
    backup_kwargs = {
        'department': dept,
        'data': backup_data,
    }
    if session_id:
        backup_kwargs['session'] = Session.objects.get(id=session_id)
    backup = Backup(**backup_kwargs)
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
    if (data.get('single_batch_type') == True):
        clear, message = utils.check_session_dependancy(data['sessions'][0])
        if not clear:
            return JsonResponse({'details': message}, status=400)
        session = Session.objects.filter(dept=dept, batch_no=data['sessions'][0]['session_meta']['batch_no']).first()
        if session:
            session.delete()
        result = restore_session_data_task.delay(dept.id, data['sessions'][0], obj_count)
    else:
        utils.delete_all_of_dept(dept)
        result = restore_dept_data_task.delay(dept.id, data['sessions'], obj_count)
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
    dept_name = request.GET.get('dept', None)
    if registration is None or dept_name is None or (not str(registration).isdigit()):
        raise BadrequestException("Required data not provided")
    student = get_object_or_404(StudentAccount, pk=registration, session__dept__name=dept_name)
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
    response_data['full_document_url'] = reverse('results:download_full_document', args=(registration,))
    response_data['transcript_url'] = reverse('results:download_transcript', args=(registration,))
    custom_transcript = StudentCustomDocument.objects.filter(student=student, doc_type="transcript").first()
    if custom_transcript and (not student.is_transcript_available):
        response_data['transcript_url'] = reverse('results:download_customdoc', args=(registration,'transcript'))
    response_data['custom_transcript_url'] = reverse('results:download_transcript', args=(registration,))
    response_data['customdoc_url'] = False
    response_data['custom_semester_gradesheets'] = []
    response_data['custom_yearly_gradesheets'] = []
    custom_sem_gradesheets = StudentCustomDocument.objects.filter(student=student, doc_type="sem_gs").order_by('sem_or_year_num')
    custom_y_gradesheets = StudentCustomDocument.objects.filter(student=student, doc_type="y_gs").order_by('sem_or_year_num')
    for sem_gs in custom_sem_gradesheets:
        response_data['custom_semester_gradesheets'].append(
            {
                'url': reverse('results:download_customdoc', args=(registration,'sem_gs')) + f"?num={sem_gs.sem_or_year_num}",
                'semester_number': sem_gs.sem_or_year_num,
                'semester_suffix': get_ordinal_suffix(sem_gs.sem_or_year_num,),
            }
        )
    for y_gs in custom_y_gradesheets:
        response_data['custom_yearly_gradesheets'].append(
            {
                'url': reverse('results:download_customdoc', args=(registration,'y_gs')) + f"?num={y_gs.sem_or_year_num}",
                'year_number': y_gs.sem_or_year_num,
                'year_suffix': get_ordinal_suffix(y_gs.sem_or_year_num,),
            }
        )
    return Response(data=response_data)


@api_view(['GET'])
def academic_studentcerts_data(request):
    registration = request.GET.get('registration', None)
    dept_name = request.GET.get('dept', None)
    if registration is None or dept_name is None or (not str(registration).isdigit()):
        raise BadrequestException("Required data not provided")
    student, response_data = utils.academic_student_data(registration, dept_name)
    semesters = []
    if student:
        for enrollment in student.semesterenroll_set.all():
            semester = enrollment.semester
            if not hasattr(semester, 'semesterdocument'):
                continue
            semesters.append({
                'semester_no': semester.semester_no,
                'semester_name': semester.semester_name,
                'tabulation_thumb_img': semester.semesterdocument.tabulation_thumbnail.url, 
                'tabulation_url': semester.semesterdocument.tabulation_sheet.url
            })
    response_data['semesters'] = semesters
    return Response(data=response_data)

   
@csrf_exempt
@login_required
def render_customdoc(request):
    excel_file = request.FILES.get("file", None)
    admin_name = request.user.first_name + " " + request.user.last_name
    doc = utils.parse_and_save_customdoc(excel_file, admin_name, request.user)
    return JsonResponse(data={'info': f'Documents Data Saved for: {doc.student.registration}', 'reg': doc.student.registration})

@csrf_exempt
@login_required
def render_course_sustdocs(request, pk):
    course = get_object_or_404(Course, pk=pk)
    excel_file = request.FILES.get("excel", None)
    if excel_file is None:
        return JsonResponse(data={'details': 'No excel file provided'}, status=400)
    try:
        data = excel_parsers.parse_course_sustdocs_excel(excel_file)
    except Exception as e:
        print(e, flush=1)
        return JsonResponse(data={'details': 'Cannot parse excel file'}, status=400)
    try:
        topsheet = render_topsheet(course, data)
        scorelist = render_scorelist(course, data)
    except Exception as e:
        print(e, flush=1)
        return JsonResponse(data={'details': 'Rendering failed. Check for missing data in Excel file'}, status=400)
    document = merge_pdfs_from_buffers([topsheet, scorelist])
    filename = f"{course.b64_id}_supplemetaryDocument"+'.pdf'
    if hasattr(course, 'supplementarydocument'):
        s_doc = course.supplementarydocument
        s_doc.document.delete()
        s_doc.added_at = timezone.now()
    else:
        s_doc = SupplementaryDocument(course=course)
    s_doc.document.save(filename, ContentFile(document.getvalue()))
    s_doc.save()
    return JsonResponse(data={'url': reverse('results:download_supplementarydoc', args=(s_doc.course.b64_id,))})
    # return JsonResponse(data={'type': st, 'files': str(type(request.FILES))})



@csrf_exempt
def create_session_prevpoint_via_excel(request, pk):
    try:
        semester = Semester.objects.get(pk=pk)
    except Semester.DoesNotExist:
        return JsonResponse({'details': "Semester not found"}, status=404)
    if not (request.user.adminaccount.is_super_admin or (semester.session.dept.head == request.user.adminaccount)):
        return Response(data={'details': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
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


@api_view(['GET'])
@permission_classes([IsSuperAdminOrDeptHead])
def get_customdoc_list(request):
    depts_qs = Department.objects.all()
    all_dept_context = []
    for dept in depts_qs:
        dept_context = []
        for session in dept.session_set.all():
            students = session.studentaccount_set.all()
            session_students_with_customdoc = []
            for student in students:
                if student.studentcustomdocument_set.count():
                    session_students_with_customdoc.append(student)
            if session_students_with_customdoc:
                dept_context.append(
                    {
                        'name': f"{session.batch_name} ({session.session_code})",
                        'students': session_students_with_customdoc
                    }
                )
        if dept_context:
            all_dept_context.append(dept_context)
    list_html = render_to_string('results/components/customdoc_listing.html', context={'departments': all_dept_context})
    return Response(data={'html': list_html})
    
@api_view()
@permission_classes([IsSuperAdminOrDeptHead])
def get_student_customdocs(request):
    reg = request.GET.get('reg')
    if not reg:
        return Response(data={'details': "Registration not provided"}, status=status.HTTP_400_BAD_REQUEST)
    student = get_object_or_404(StudentAccount, registration=reg)
    context = {
        'title': f"Generated Documents of {reg}",
        'documents': student.studentcustomdocument_set.all().order_by('sem_or_year_num', '-doc_type')
    }
    html_text = render_to_string('results/components/student_customdocs.html', context=context)
    return Response(data={'html': html_text})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def export_student_academic_data(request):
    excel_file = request.FILES.get('file')
    data = excel_parsers.parse_student_academic_docs(excel_file)
    try:
        utils.save_academic_studentdata(data)
    except Exception as e:
        return Response({'details': f"Error, Cannot Save Data error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'info': "Saved data"})


@api_view()
@permission_classes([IsAuthenticated])
def view_saved_student_academic_data(request):
    qs = StudentAcademicData.objects.all()
    sessions = list(set([q.session_code for q in qs]))
    data = []
    for session in sessions:
        data.append({
            'session': session,
            'students': [s.registration for s in qs.filter(session_code=session)],
        })
    return Response(data)


@api_view(['POST'])
@permission_classes([IsSuperAdminOrDeptHead])
def update_student_prev_record(request, registration):
    try:
        utils.update_student_prevrecord(registration, request.data)
    except Exception as e:
        return Response({'details': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"info": "Updated"})


class DocHistoryList(ListAPIView):
    serializer_class = DocHistorySerializer

    def get_queryset(self):
        return DocHistory.objects.all().order_by('-added')