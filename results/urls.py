from django.urls import path
from results import views

app_name = "results"

urlpatterns = [
    path('', views.DashboardView.as_view(), name="admin_dashboard"),
    path('departments/', views.departments_all, name="all_departments"),
    path('departments/<str:dept_name>', views.DepartmentView.as_view(), name="view_department"),
]

