from django.urls import path, include
from results import views

app_name = "results"

urlpatterns = [
    path('', views.DashboardView.as_view(), name="dashboard"),
    path('results/api/', include("results.api.urls")),
    path('departments/', views.departments_all, name="all_departments"),
    path('sust/', views.SustAdminHome.as_view(), name="sustadminhome"),
    path('sust/<path>/', views.SustAdminHome.as_view(), name="sust_routing"),
    path('departments/<str:dept_name>/', views.DepartmentView.as_view(), name="view_department"),
    path('departments/<str:dept_name>/<int:from_year>-<int:to_year>/', views.SessionView.as_view(), name="view_session"),
    path('departments/<str:dept_name>/<int:from_year>-<int:to_year>/semester/<int:year>-<int:semester>/', views.SemesterView.as_view(), name="view_semester"),
    path('departments/<str:dept_name>/<int:from_year>-<int:to_year>/semester/<int:year>-<int:semester>/<str:course_code>/', views.CourseView.as_view(), name="view_course"),
    path('semester/<int:pk>/tabulation/download/', views.download_semester_tabulation, name="download_semester_tabulation"),
    path('student/<int:registration>/gradesheet/<int:year>/', views.download_year_gradesheet, name="download_year_gradesheet"),
    path('student/<int:registration>/semestergradesheet/<int:semester_no>/', views.download_semester_gradesheet, name="download_semester_gradesheet"),
    path('coursereport/<str:b64_id>', views.download_coruse_report, name="download_coruse_report"),
    path('student/<int:registration>/transcript/', views.download_transcript, name="download_transcript"),
    path('staffs/', views.StaffsView.as_view(), name="stuffs_view"),
    path('extensions/', views.ExtensionsView.as_view(), name="extensions_view"),
    path('extensions/gradesheet/', views.GradesheetMakerView.as_view(), name="gradesheetmaker_view"),
    path('extensions/transcript/', views.TranscriptMakerView.as_view(), name="transcriptmaker_view"),
    path('backup-<int:pk>/download/', views.download_backup, name="download_backup"),
    path('cachedpdf/<str:cache_key>/<str:filename>', views.download_cachedpdf, name="download_cachedpdf"),
    path('customdoc/downloadtemplate/', views.download_customdoc_template, name="download_customdoc_template"),
]

