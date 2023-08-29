from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.base import ContentFile
from typing import Any, Dict
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, DetailView
from django.contrib.auth.decorators import login_required
from django.http.response import FileResponse
from results.models import (Semester, SemesterEnroll, Department, Session, Course)
from account.models import StudentAccount, AdminAccount
from results.gradesheet_generator import get_gradesheet
from results.utils import get_ordinal_number, render_error


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "results/dashboard.html"
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        context['request'] = self.request
        semesters = []
        if self.request.user.adminaccount.is_super_admin:
            semesters = Semester.objects.all().order_by("-is_running", "-added_in")[:4]
        else:
            semesters = Semester.objects.filter(session__dept=self.request.user.adminaccount.dept).order_by("-is_running", "-semester_no", "added_in")[:4]
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
        context['request'] = self.request
        # drop courses semester for current semester
        semester = context['semester']
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
        context['superadmins'] = AdminAccount.objects.filter(is_super_admin=True) 
        context['deptadmins'] = AdminAccount.objects.filter(is_super_admin=False).order_by('dept') 
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
    # student
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
def pending_view(request):
    return render_error(request, 'This Section is Under Development!')