from django.db import models
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.templatetags.static import static
from results.utils import get_ordinal_number


class Department(models.Model):
    name = models.CharField(max_length=3)
    fullname = models.CharField(max_length=100)
    dept_logo = models.ImageField(upload_to="departments/logo/",
                                    null=True, 
                                    blank=True,
                                    validators=[FileExtensionValidator(allowed_extensions=settings.ALLOWED_IMAGE_EXTENSIONS)])
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    added = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    
class Session(models.Model):
    from_year = models.IntegerField()
    to_year = models.IntegerField()
    batch_no = models.IntegerField()
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.dept.name} {self.from_year}-{self.to_year % 2000}"
    
    @property
    def session_name(self):
        return str(self)
    
    class Meta:
        ordering = ["-from_year"]


class Semester(models.Model):
    year = models.IntegerField(
        validators = [
            MinValueValidator(1, message="Year must be atleast 1"),
            MaxValueValidator(4, message="Year cannot be more than 4"),
        ]
    )
    year_semester = models.IntegerField(
        validators = [
            MinValueValidator(1, message="Year semester must be atleast 1"),
            MaxValueValidator(2, message="Year semester cannot be more than 2"),
        ]
    )
    semester_no = models.IntegerField(
        validators = [
            MinValueValidator(1, message="Semester number must be atleast 1"),
            MaxValueValidator(8, message="Semester number cannot be more than 8"),
        ]
    )
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    drop_courses = models.ManyToManyField("Course", blank=True, related_name="drop_courses")
    added_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    added_in = models.DateTimeField(auto_now_add=True)
    
    def __str__(self) -> str:
        return f"{self.session}, {self.semester_name}"
    
    @property
    def semester_name(self):
        return f"{get_ordinal_number(self.year)} Year {get_ordinal_number(self.year_semester)} Semester"
    
    
class Course(models.Model):
    semester = models.ForeignKey("Semester", on_delete=models.CASCADE)
    code = models.CharField(max_length=20)
    title = models.CharField(max_length=200)
    course_credit = models.FloatField(validators=[MinValueValidator(settings.MIN_COURSE_CREDIT), MaxValueValidator(settings.MAX_COURSE_CREDIT)])
    total_marks = models.FloatField(validators=[MinValueValidator(1, "Total Marks must be greater than 0")])
    part_A_marks = models.FloatField(validators=[MinValueValidator(1, "Marks must be greater than 0")])
    part_B_marks = models.FloatField(validators=[MinValueValidator(1, "Marks must be greater than 0")])
    incourse_marks = models.FloatField(validators=[MinValueValidator(1, "Marks must be greater than 0")])
    added_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    added_in = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.semester} Course: {self.code}"
    

class CourseResult(models.Model):
    student = models.ForeignKey("account.StudentAccount", on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    part_A_score = models.FloatField(null=True, blank=True, validators=[
        MinValueValidator(0, message="Score cannot be less than 0")])
    part_B_score = models.FloatField(null=True, blank=True, validators=[
        MinValueValidator(0, message="Score cannot be less than 0")])
    incourse_score = models.FloatField(null=True, blank=True, validators=[
        MinValueValidator(0, message="Score cannot be less than 0")])
    total_score = models.FloatField(null=True, blank=True, validators=[
        MinValueValidator(0, message="Score cannot be less than 0")])
    part_A_code = models.CharField(max_length=20, null=True)
    part_B_code = models.CharField(max_length=20, null=True)
    grade_point = models.FloatField(null=True, blank=True, validators=[
        MinValueValidator(0, message="Score cannot be less than 0")])
    letter_grade = models.CharField(max_length=2, null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)
    
    
    @property
    def course_points(self):
        return (self.grade_point * self.course.course_credit)
    
    
class Activity(models.Model):
    ACTIVITY_TYPES = [
        ("add", "Addition"),
        ("update", "Modification"),
        ("delete", "Deletion"),
    ]
    by = models.ForeignKey(User, on_delete=models.CASCADE)
    at = models.DateTimeField(auto_now_add=True)
    target_url = models.URLField(null=True, blank=True)
    type = models.CharField(max_length=10, choices=ACTIVITY_TYPES)
    message = models.CharField(max_length=200)