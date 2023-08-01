from django.contrib.auth.mixins import LoginRequiredMixin
from typing import Any, Dict
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, DetailView
from django.contrib.auth.decorators import login_required
from results.models import (Semester, Department, Session)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "results/dashboard.html"
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        context['request'] = self.request
        semesters = []
        if self.request.user.adminaccount.is_super_admin:
            semesters = Semester.objects.all()[:4]
        else:
            semesters = Semester.objects.filter(session__dept=self.request.user.adminaccount.dept)[:4]
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
        print(context)
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


@login_required 
def pending_view(request):
    return HttpResponse("<h1 style='text-align: center;margin-top:10rem'>This Section is Under Development</h1>")