from django.contrib.auth.mixins import LoginRequiredMixin
from typing import Any, Dict
from django.shortcuts import render
from django.views.generic import TemplateView
from results.models import Semester


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
