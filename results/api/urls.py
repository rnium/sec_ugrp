from django.urls import path
from results.api import views


urlpatterns = [
    path('createsession/', views.SessionCreate.as_view(), name="create_session"),
    path('session/<int:pk>/createsemester/', views.SemesterCreate.as_view(), name="create_semester"),
    path('session/<int:pk>/studentstats/', views.SessionStudentStats.as_view(), name="session_student_stats"),
    path('session/<int:pk>/delete/', views.delete_session, name="delete_session"),
    path('session/<int:pk>/retakes/', views.session_retake_list, name="session_retake_list"),
    path('student-retakings/', views.student_retakings, name="student_retaking_list"),
    path('createcourse/', views.CourseCreate.as_view(), name="create_course"),
    path('semester<int:pk>/dropcourseupdate/', views.updateDropCourses, name="drop_course_update"),
    path('semester<int:pk>/update/', views.SemesterUpdate.as_view(), name="semester_update"),
    path('semester<int:pk>/rendertabulation/', views.render_tabulation, name="render_tabulation"),
    path('semester<int:pk>/changerunningstatus/', views.toggle_semester_is_running, name="change_running_status"),
    path('semester<int:pk>/deletesemester/', views.delete_semester, name="delete_semester"),
    path('course/<int:pk>/courseresults/', views.CourseResultList.as_view(), name="course_results"),
    path('course/<int:pk>/courseresults/update/', views.update_course_results, name="update_course_results"),
    path('course/<int:pk>/update/', views.CourseUpdate.as_view(), name="update_course"),
    path('course/<int:pk>/delete/', views.delete_course, name="delete_course"),
    path('course/<int:pk>/addnewentry/', views.add_new_entry_to_course, name="add_new_entry_to_course"),
    path('course/<int:pk>/processexcel/', views.process_course_excel, name="process_course_excel"),
    path('createbackup/', views.generate_backup, name="generate_backup"),
    path('restorebackup/', views.perform_restore, name="perform_restore"),
    path('courseresult-entry-info/', views.course_result_entry_info, name="course_result_entry_info"),
    path('courseresult-delete/', views.delete_course_result, name="delete_course_result"),
    path('semesterenroll-delete/', views.delete_enrollment, name="delete_enrollment"),
    path('course/<int:pk>/generate-missing', views.generate_missing_entries, name="generate_missing_entries"),
    path('generate-gradesheet', views.generate_gradesheet, name="generate_gradesheet_api"),
    path('generate-transcript', views.generate_transcript, name="generate_transcript_api"),
    path('studentstats/<int:registration>', views.student_stats, name="student_stats_api"),
]

