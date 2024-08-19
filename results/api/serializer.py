from django.urls import reverse
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from results.models import Department, Session, Semester, Course, CourseResult, DocHistory
from account.models import StudentAccount

class SessionSerializer(ModelSerializer):
    view_url = serializers.SerializerMethodField(read_only=True)
    session_code = serializers.SerializerMethodField(read_only=True)
    batch_name = serializers.SerializerMethodField(read_only=True)
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
        
    def get_session_code(self, obj):
        return obj.session_code
        
    def get_batch_name(self, obj):
        return obj.batch_name


class SemesterSerializer(ModelSerializer):
    view_url = serializers.SerializerMethodField(read_only=True)
    semester_name = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = Semester
        fields = "__all__"
        
    def get_view_url(self, obj):
        return reverse(
            "results:view_semester",
            kwargs = {
                'dept_name':obj.session.dept.name,
                'b64_id':obj.b64_id,
            }
        )
        
    def get_semester_name(self, obj):
        return obj.semester_name
        

class CourseSerializer(ModelSerializer):
    view_url = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = Course
        fields = "__all__"
        
    def get_view_url(self, obj):
        return reverse(
            "results:view_course",
            kwargs = {
                'dept_name':obj.semester.session.dept.name,
                'b64_id':obj.b64_id,
            }
        )


class StudentSerializer(ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)
    profile_picture_url = serializers.SerializerMethodField(read_only=True)
    dept = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = StudentAccount
        fields = '__all__'
        read_only_fields = ['registration']
   
    def get_name(self, obj):
        return obj.student_name
    def get_profile_picture_url(self, obj):
        return obj.avatar_url
    def get_dept(self, obj):
        return {"dept": str(obj.session.dept), "session_code":obj.session.session_code}
   
class CourseResultSerializer(ModelSerializer):
    student = StudentSerializer(read_only=True)
    is_theory_course = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = CourseResult
        exclude = ['updated', 'course']
    
    def get_is_theory_course(self, obj):
        return obj.course.is_theory_course

class StudentStatsSerializer(ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)
    cgpa = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = StudentAccount
        fields = ['registration', 'credits_completed', 'cgpa', 'name']
        read_only_fields = ['registration', 'cgpa']
        
    def get_name(self, obj):
        return obj.student_name
    def get_cgpa(self, obj):
        if cgpa := obj.student_cgpa:
            return float(cgpa)
        else:
            return 0
        
class DocHistorySerializer(ModelSerializer):
    doc_type = serializers.SerializerMethodField()
    class Meta:
        model = DocHistory
        fields = '__all__'
    
    def get_doc_type(self, obj):
        return obj.get_doc_type_display()
