from django.urls import path, include
from results import views

app_name = "results"

urlpatterns = [
    path('', views.homepage, name="dashboard"),
    path('results/api/', include("results.api.urls")),
    path('departments/', views.departments_all, name="all_departments"),
    path('sust/', views.SustAdminHome.as_view(), name="sustadminhome"),
    path('sust/<path>/', views.SustAdminHome.as_view(), name="sust_routing"),
    path('academic/', views.SecAcademicHome.as_view(), name="secacademichome"),
    path('academic/<path>/', views.SecAcademicHome.as_view(), name="secacademic_routing"),
    path('departments/<str:dept_name>/', views.DepartmentView.as_view(), name="view_department"),
    path('departments/<str:dept_name>/<int:from_year>-<int:to_year>/', views.SessionView.as_view(), name="view_session"),
    path('departments/<str:dept_name>/<int:from_year>-<int:to_year>/semester/<int:year>-<int:semester>/', views.SemesterView.as_view(), name="view_semester"),
    path('departments/<str:dept_name>/<int:from_year>-<int:to_year>/semester/<int:year>-<int:semester>/<str:course_code>/', views.CourseView.as_view(), name="view_course"),
    path('semester/<int:pk>/tabulation/download/', views.download_semester_tabulation, name="download_semester_tabulation"),
    path('student/<int:registration>/gradesheet/<int:year>/', views.download_year_gradesheet, name="download_year_gradesheet"),
    path('student/<int:registration>/semestergradesheet/<int:semester_no>/', views.download_semester_gradesheet, name="download_semester_gradesheet"),
    path('coursereport/<str:b64_id>', views.download_coruse_report, name="download_coruse_report"),
    path('coursescorelist/<str:b64_id>/', views.download_scorelist, name="download_scorelist"),
    path('student/<int:registration>/transcript/', views.download_transcript, name="download_transcript"),
    path('student/<int:registration>/fulldocument/', views.download_full_document, name="download_full_document"),
    path('student/<int:registration>/coursemediumcert/', views.download_coursemediumcert, name="download_coursemediumcert"),
    path('student/<int:registration>/appearedcert/', views.download_appeared_cert, name="download_appeared_cert"),
    path('student/<int:registration>/download_testimonial/', views.download_testimonial, name="download_testimonial"),
    path('staffs/', views.StaffsView.as_view(), name="stuffs_view"),
    path('extensions/', views.ExtensionsView.as_view(), name="extensions_view"),
    path('extensions/gradesheet/', views.GradesheetMakerView.as_view(), name="gradesheetmaker_view"),
    path('extensions/transcript/', views.TranscriptMakerView.as_view(), name="transcriptmaker_view"),
    path('extensions/customdocument/', views.CustomdocMakerView.as_view(), name="customdocmaker_view"),
    path('customdoc-temp/', views.download_customdoc_template, name="download_customdoc_template"),
    path('course-sustdocs-temp/<int:pk>/', views.download_sustdocs_template, name="download_sustdocs_template"),
    path('backup-<int:pk>/download/', views.download_backup, name="download_backup"),
    path('semesterexcel/<int:pk>/', views.get_semester_excel, name="get_semester_excel"),
    path('cachedpdf/<str:cache_key>/<str:filename>', views.download_cachedpdf, name="download_cachedpdf"),
    path('courseexcel/<str:b64_id>/', views.get_course_excel, name="get_course_excel"),
    path('studentcustomdocument/<int:reg>/<str:doctype>/', views.download_customdoc, name="download_customdoc"),
]

