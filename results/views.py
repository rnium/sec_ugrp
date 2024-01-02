from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.base import ContentFile
from django.core.cache import cache
import base64
from typing import Any, Dict
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, DetailView
from django.contrib.auth.decorators import login_required
from django.http.response import FileResponse
from results.models import (Semester, SemesterEnroll, Department, Session, Course, Backup)
from account.models import StudentAccount, AdminAccount
from results.pdf_generators.gradesheet_generator import get_gradesheet
from results.pdf_generators.transcript_generator import get_transcript
from results.utils import get_ordinal_number, render_error
from results.api.utils import sort_courses
from datetime import datetime
from results.pdf_generators.course_report_generator import render_coursereport
import json


def user_is_super_OR_dept_admin(request):
    if hasattr(request.user, 'adminaccount'):
        return request.user.adminaccount.is_super_admin or (request.user.adminaccount.dept is not None)
    else:
        return False
    

def user_is_superAdmin(user):
    return hasattr(user, 'adminaccount') and user.adminaccount.is_super_admin
    

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "results/dashboard.html"
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        context['request'] = self.request
        semesters = []
        if self.request.user.adminaccount.is_super_admin:
            semesters = Semester.objects.all().order_by("-is_running", 'session__from_year', "-added_in")[:4]
        else:
            semesters = Semester.objects.filter(session__dept=self.request.user.adminaccount.dept).order_by("-is_running", "session__from_year", "-semester_no", "added_in")[:4]
        if (len(semesters) > 0):
            context['semesters'] = semesters
        return context
    


class DepartmentView(LoginRequiredMixin, DetailView):
    template_name = "results/view_department.html"
    
    def get_object(self):
        department = get_object_or_404(Department, name=self.kwargs.get("dept_name", ""))
        return department
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        context['request'] = self.request
        return context
    
class ExtensionsView(LoginRequiredMixin, TemplateView):
    template_name = "results/extensions.html"   
     
class GradesheetMakerView(LoginRequiredMixin, TemplateView):
    template_name = "results/gradesheetmaker.html"     

class TranscriptMakerView(LoginRequiredMixin, TemplateView):
    template_name = "results/transcriptmaker.html"
    

@login_required 
def departments_all(request):
    if request.user.adminaccount.is_super_admin:
        context = {
            "departments": Department.objects.all(),
            "request": request
        }
        return render(request, "results/departments_all.html", context=context)
    else:
        return redirect('results:view_department', dept_name=request.user.adminaccount.dept.name)


class SessionView(LoginRequiredMixin, DetailView):
    template_name = "results/view_session.html"
    
    def get_object(self):
        session = get_object_or_404(
            Session, 
            dept__name = self.kwargs.get("dept_name", ""),
            from_year = self.kwargs.get("from_year", ""),
            to_year = self.kwargs.get("to_year", ""),
        )
        return session
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        context['request'] = self.request
        return context


class SemesterView(LoginRequiredMixin, DetailView):
    template_name = "results/view_semester.html"
    def get_object(self):
        semester = get_object_or_404(
            Semester, 
            session__dept__name = self.kwargs.get("dept_name", ""),
            session__from_year = self.kwargs.get("from_year", ""),
            session__to_year = self.kwargs.get("to_year", ""),
            year = self.kwargs.get("year", ""),
            year_semester = self.kwargs.get("semester", ""),
        )
        return semester
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        semester = context['semester']
        context['request'] = self.request
        context['courses_regular'] = semester.course_set.all().order_by('id')
        context['courses_drop'] = semester.drop_courses.all().order_by('id')
        # drop courses semester for current semester
        
        if semester.is_running:
            drop_semesters = Semester.objects.filter(is_running = True, 
                                                     year__lt = semester.year, 
                                                     session__from_year__gt = semester.session.from_year, 
                                                     session__dept = semester.session.dept).order_by("session__from_year")
            if len(drop_semesters) > 0:
                context["drop_semesters"] = drop_semesters
            
        return context
    

class CourseView(LoginRequiredMixin, DetailView):
    template_name = "results/view_course.html"
    def get_object(self):
        course = get_object_or_404(
            Course, 
            semester__session__dept__name = self.kwargs.get("dept_name", ""),
            semester__session__from_year = self.kwargs.get("from_year", ""),
            semester__session__to_year = self.kwargs.get("to_year", ""),
            semester__year = self.kwargs.get("year", ""),
            semester__year_semester = self.kwargs.get("semester", ""),
            code = self.kwargs.get("course_code", ""),
        )
        return course
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        context['request'] = self.request
        course = context['course']
        dept_running_semesters = Semester.objects.filter(
            is_running = True,
            session__dept = course.semester.session.dept,
        ).order_by('session__from_year')
        context['running_semesters'] = dept_running_semesters.exclude(pk=course.semester.id)
        return context
    

class StaffsView(LoginRequiredMixin, TemplateView):
    template_name = "results/view_staffs.html"
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['superadmins'] = AdminAccount.objects.filter(is_super_admin=True, user__is_staff=False) 
        context['deptadmins'] = AdminAccount.objects.filter(is_super_admin=False).order_by('dept') 
        context['sysadmins'] = AdminAccount.objects.filter(user__is_staff=True) 
        context['request'] = self.request
        context['departments'] = Department.objects.all()
        return context
    

@login_required
def download_semester_tabulation(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    if semester.has_tabulation_sheet:
        filepath = semester.semesterdocument.tabulation_sheet.path
        filename = semester.semesterdocument.tabulation_filename
        return FileResponse(open(filepath, 'rb'), filename=filename)
    else:
        return render_error(request, 'No Tabulation sheet')


@login_required
def download_year_gradesheet(request, registration, year):
    has_permission = user_is_super_OR_dept_admin(request)
    if not has_permission:
        return render_error(request, 'Forbidden')
    student = get_object_or_404(StudentAccount, registration=registration)
    # semester enrolls
    try:
        year_first_semester = SemesterEnroll.objects.get(student=student, semester__year=year, semester__year_semester=1, semester__is_running=False, semester_gpa__isnull=False)
        year_second_semester = SemesterEnroll.objects.get(student=student, semester__year=year, semester__year_semester=2, semester__is_running=False, semester_gpa__isnull=False)
    except:
        return render_error(request, 'GradeSheet not available!')
    sheet_pdf = get_gradesheet(
        student = student,
        year_first_sem_enroll = year_first_semester,
        year_second_sem_enroll = year_second_semester
    )
    filename = f"{get_ordinal_number(year)} year gradesheet - {student.registration}.pdf"
    return FileResponse(ContentFile(sheet_pdf), filename=filename)


@login_required
def download_semester_gradesheet(request, registration, semester_no):
    has_permission = user_is_super_OR_dept_admin(request)
    if not has_permission:
        return render_error(request, 'Forbidden')
    student = get_object_or_404(StudentAccount, registration=registration)
    # semester enrolls
    try:
        semester_enroll = SemesterEnroll.objects.get(student=student, 
                                                        semester__semester_no=semester_no, 
                                                        semester__is_running=False, semester_gpa__isnull=False)
    except:
        return render_error(request, 'GradeSheet not available!')
    sheet_pdf = get_gradesheet(
        student = student,
        year_first_sem_enroll = semester_enroll,
    )
    filename = f"{get_ordinal_number(semester_no)} semester gradesheet - {student.registration}.pdf"
    return FileResponse(ContentFile(sheet_pdf), filename=filename)

@login_required
def download_transcript(request, registration):
    has_permission = user_is_superAdmin(request.user)
    if not has_permission:
        return render_error(request, 'Forbidden')
    student = get_object_or_404(StudentAccount, registration=registration)
    last_enroll = student.semesterenroll_set.all().order_by('-semester__semester_no').first()
    if last_enroll is not None:
        context = {
            'admin_name': request.user.adminaccount.user_full_name,
            'student': student,
            'last_semester': last_enroll.semester
        }
        sheet_pdf = get_transcript(context=context)
        filename = f"Transcript - {student.registration}.pdf"
        return FileResponse(ContentFile(sheet_pdf), filename=filename)
    else:
        return render_error(request, 'Transcript not available!')

@login_required
def download_backup(request, pk):
    has_permission = user_is_super_OR_dept_admin(request)
    if not has_permission:
        return render_error(request, 'Forbidden')
    backup = get_object_or_404(Backup, pk=pk) 
    if request.user.adminaccount.dept is not None and backup.department != request.user.adminaccount.dept:
        return render_error(request, 'Forbidden')
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%d-%m-%Y")
    filename = f"RDB Backup-{backup.id} {backup.department.name.upper()} {formatted_datetime}"
    response = JsonResponse(backup.data)
    response['Content-Disposition'] = f'attachment; filename="{filename}.json"'
    return response


@login_required
def download_coruse_report(request, b64_id):
    try:
        str_pk = base64.b64decode(b64_id.encode('utf-8')).decode()
        pk = int(str(str_pk))
    except Exception as e:
        return render_error(request, "Invalid Course ID")
    course = get_object_or_404(Course, pk=pk)
    report_pdf = render_coursereport(course)
    filename = f"{str(course)} Report.pdf"
    return FileResponse(ContentFile(report_pdf), filename=filename)
    
@login_required
def download_cachedpdf(request, cache_key, filename):
    pdf_base64 = cache.get(cache_key)
    if pdf_base64:
        pdf_data = base64.b64decode(pdf_base64.encode('utf-8'))
        return FileResponse(ContentFile(pdf_data), filename=filename)
    else:
        return render_error(request, "File not found in Cache")
        
    
    
@login_required 
def pending_view(request):
    return render_error(request, 'This Section is Under Development!')

