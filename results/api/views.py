from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.exceptions import APIException
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializer import (SessionSerializer, SemesterSerializer, CourseSerializer)
from .permission import IsCampusAdmin
from results.models import Session, Semester, Course, CourseResult
from .utils import create_course_results
 
    
class BadrequestException(APIException):
    status_code = 403
    default_detail = 'Bad Request'
    

class SessionCreate(CreateAPIView):
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated, IsCampusAdmin]
    queryset = Session.objects.all()
    
    def perform_create(self, serializer):
        try:
            super().perform_create(serializer)
        except Exception as e:
            raise BadrequestException(str(e))

class SemesterCreate(CreateAPIView):
    serializer_class = SemesterSerializer
    permission_classes = [IsAuthenticated, IsCampusAdmin]
    
    def get_queryset(self):
        pk = self.kwargs.get("pk")
        sessions = Session.objects.filter(id=pk)
        return sessions
    
    def perform_create(self, serializer):
        try:
            super().perform_create(serializer)
        except Exception as e:
            raise BadrequestException(str(e))



class CourseCreate(CreateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsCampusAdmin]
    queryset = Course.objects.all()
    
    def create(self, request, *args, **kwargs):
        data = request.data
        data['added_by'] = request.user.id
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            self.perform_create(serializer)
            course_id = serializer.data.get('id')
            course = Course.objects.get(id=course_id)
            create_course_results(course=course)
            return Response(serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)
    
    
    def perform_create(self, serializer):
        try:
            super().perform_create(serializer)
        except Exception as e:
            raise BadrequestException(str(e))


@api_view(["POST"])
def updateDropCourses(request, pk):
    try:
        semester = Semester.objects.get(pk=pk)
    except Semester.DoesNotExist:
        return Response(data={"details": "Semester not found"}, status=status.HTTP_404_NOT_FOUND)
    if request.user.adminaccount.is_super_admin or request.user.adminaccount.dept == semester.session.dept:
        try:
            add_courses = request.data['add_courses']
            remove_courses = request.data['remove_courses']
        except Exception as e:
            return Response(data={"details": "Invalid data format"}, status=status.HTTP_400_BAD_REQUEST)
        for course_id in add_courses:
            course = get_object_or_404(Course, pk=course_id)
            if course not in semester.drop_courses.all():
                semester.drop_courses.add(course)
        for course_id in remove_courses:
            course = get_object_or_404(Course, pk=course_id)
            if course in semester.drop_courses.all():
                semester.drop_courses.remove(course)
        return Response(data={"details": "complete"})