from django.urls import reverse
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from results.models import Department, Session, Semester, Course, CourseResult

class SessionSerializer(ModelSerializer):
    view_url = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = Session
        fields = "__all__"
        
    def get_view_url(self, obj):
        return reverse(
            "results:view_session",
            kwargs = {
                'dept_name':obj.dept.name,
                'from_year':obj.from_year,
                'to_year':obj.to_year
            }
        )