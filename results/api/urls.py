from django.urls import path
from results.api import views


urlpatterns = [
    path('createsession/', views.SessionCreate.as_view(), name="create_session"),
    path('session/<int:pk>/createsemester/', views.SemesterCreate.as_view(), name="create_semester"),
    path('createcourse/', views.CourseCreate.as_view(), name="create_course"),
]

