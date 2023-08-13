from django.urls import path
from results.api import views


urlpatterns = [
    path('createsession/', views.SessionCreate.as_view(), name="create_session"),
    path('session/<int:pk>/createsemester/', views.SemesterCreate.as_view(), name="create_semester"),
    path('createcourse/', views.CourseCreate.as_view(), name="create_course"),
    path('semester<int:pk>/dropcourseupdate/', views.updateDropCourses, name="drop_course_update"),
    path('semester<int:pk>/rendertabulation/', views.render_tabulation, name="render_tabulation"),
    path('semester<int:pk>/changerunningstatus/', views.toggle_semester_is_running, name="change_running_status"),
    path('semester<int:pk>/deletesemester/', views.delete_semester, name="delete_semester"),
    path('course/<int:pk>/courseresults/', views.CourseResultList.as_view(), name="course_results"),
    path('course/<int:pk>/courseresults/update/', views.update_course_results, name="update_course_results"),
    path('course/<int:pk>/delete', views.delete_course, name="delete_course"),
]

