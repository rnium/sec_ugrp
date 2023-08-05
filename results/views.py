from django.contrib.auth.mixins import LoginRequiredMixin
from typing import Any, Dict
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, DetailView
from django.contrib.auth.decorators import login_required
from results.models import (Semester, Department, Session, Course)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "results/dashboard.html"
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        context['request'] = self.request
        semesters = []
        if self.request.user.adminaccount.is_super_admin:
            semesters = Semester.objects.all().order_by("is_running", "added_in")[:4]
        else:
            semesters = Semester.objects.filter(session__dept=self.request.user.adminaccount.dept).order_by("-is_running", "added_in")[:4]
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
        return context
    

@login_required 
def pending_view(request):
    return HttpResponse("<h1 style='text-align: center;margin-top:10rem'>This Section is Under Development</h1>")