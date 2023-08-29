from django.urls import path, include
from results import views

app_name = "results"

urlpatterns = [
    path('', views.DashboardView.as_view(), name="dashboard"),
    path('results/api/', include("results.api.urls")),
    path('departments/', views.departments_all, name="all_departments"),
    path('departments/<str:dept_name>', views.DepartmentView.as_view(), name="view_department"),
    path('departments/<str:dept_name>/<int:from_year>-<int:to_year>', views.SessionView.as_view(), name="view_session"),
    path('departments/<str:dept_name>/<int:from_year>-<int:to_year>/semester/<int:year>-<int:semester>', views.SemesterView.as_view(), name="view_semester"),
    path('departments/<str:dept_name>/<int:from_year>-<int:to_year>/semester/<int:year>-<int:semester>/<str:course_code>', views.CourseView.as_view(), name="view_course"),
    path('semester/<int:pk>/tabulation/download', views.download_semester_tabulation, name="download_semester_tabulation"),
    path('student/<int:registration>/gradesheet/<int:year>', views.download_year_gradesheet, name="download_year_gradesheet"),
    path('student/<int:registration>/transcript', views.download_transcript, name="download_transcript"),
    path('staffs', views.StaffsView.as_view(), name="stuffs_view"),
]

