from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.templatetags.static import static
from results.utils import get_ordinal_number, calculate_grade_point, calculate_letter_grade
from os.path import join, basename


class Department(models.Model):
    name = models.CharField(max_length=3, unique=True)
    fullname = models.CharField(max_length=100)
    dept_logo = models.ImageField(upload_to="departments/logo/",
                                    null=True, 
                                    blank=True,
                                    validators=[FileExtensionValidator(allowed_extensions=settings.ALLOWED_IMAGE_EXTENSIONS)])
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    added = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name.upper()
    
    @property
    def dept_title_short(self):
        return f"Dept of {self.name.upper()}"
    
    @property
    def dept_title_full(self):
        return f"Department of {self.fullname}"
    
    
class Session(models.Model):
    from_year = models.IntegerField()
    to_year = models.IntegerField()
    batch_no = models.IntegerField()
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ["-from_year"]
        constraints = [
            models.UniqueConstraint(fields=["from_year", "dept"], name="unique_dept_session"),
            models.UniqueConstraint(fields=["batch_no", "dept"], name="unique_dept_batch"),
        ]
        
    def __str__(self):
        return f"{self.dept.name} {self.session_code}"
    
    @property
    def session_code(self):
        return f"{self.from_year}-{self.to_year % 2000}"

    @property
    def batch_name(self):
        return f"{self.dept.name.upper()} {get_ordinal_number(self.batch_no)} batch"
    


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
    start_month = models.CharField(max_length=15)
    is_running = models.BooleanField(default=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    drop_courses = models.ManyToManyField("Course", blank=True, related_name="drop_courses")
    added_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    added_in = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["year", "year_semester"]
        constraints = [
            models.UniqueConstraint(fields=["year", "year_semester", "session"], name="unique_session_semester")
        ]
        
        
    def __str__(self) -> str:
        return f"{self.session}, {self.semester_name}"
    
    @property
    def semester_code(self):
        return f"{self.year}-{self.year_semester} [{self.session.session_code}]"
    
    @property
    def semester_name(self):
        return f"{get_ordinal_number(self.year)} Year {get_ordinal_number(self.year_semester)} Semester"
    
    @property
    def has_courses(self):
        num_courses = self.course_set.count() + self.drop_courses.count()
        print(num_courses)
        return bool(num_courses)
    

class SemesterDocument(models.Model):
    def filepath(self, filename):
        return join(str(self.semester.session.dept.name), str(self.semester.session.session_code), str(self.semester.semester_code), filename)
    semester = models.OneToOneField(Semester, on_delete=models.CASCADE)
    tabulation_sheet = models.FileField(upload_to=filepath)
    tabulation_thumbnail = models.ImageField(upload_to="thumbnails", null=True, blank=True)


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

    class Meta:
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(fields=["semester", "code"], name="unique_course_semester")
        ]
    

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
    part_A_code = models.CharField(max_length=20, null=True, blank=True)
    part_B_code = models.CharField(max_length=20, null=True, blank=True)
    grade_point = models.FloatField(null=True, blank=True, validators=[
        MinValueValidator(0, message="Score cannot be less than 0")])
    letter_grade = models.CharField(max_length=5, null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "course"], name="unique_courseresult_student")
        ]
    
    
    def save(self, *args, **kwargs):
        if ((self.part_A_score is not None and self.part_A_score > self.course.part_A_marks) or
            (self.part_B_score is not None and self.part_B_score > self.course.part_B_marks )or
            (self.incourse_score is not None and self.incourse_score > self.course.incourse_marks) or
            (self.total_score is not None and self.total_score > self.course.total_marks)):
            raise ValidationError("Score cannot be more than defined marks")
        # Saving grade point
        if self.total_score:
            self.grade_point = calculate_grade_point(self.total_score, self.course.total_marks)
            self.letter_grade = calculate_letter_grade(self.total_score, self.course.total_marks)
            print(self.letter_grade)
        super().save(args, kwargs)
        
    
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
    
    class Meta:
        ordering = ['at']