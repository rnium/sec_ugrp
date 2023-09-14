import math
from typing import Iterable, Optional
from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.models import User
from django.templatetags.static import static
from results.utils import (get_ordinal_number, calculate_grade_point, 
                           calculate_letter_grade, round_up_point_five)
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
        return f"{self.dept.name.upper()} {self.session_code}"
    
    def count_total_credits(self):
        credits_count = 0
        for semester in self.semester_set.all():
            credits_count += semester.total_credits
        return credits_count
            
    @property
    def session_code(self):
        return f"{self.from_year}-{self.to_year % 2000}"
    
    @property
    def session_code_formal(self):
        return f"{(self.from_year % 2000) + 2000}-{(self.to_year % 2000) + 2000}"

    @property
    def batch_name(self):
        return f"{self.dept.name.upper()} {get_ordinal_number(self.batch_no)} batch"
    
    @property
    def has_semester(self):
        return bool(self.semester_set.count())
    
    
        
    

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
    start_month = models.CharField(max_length=15) # IT is the SCHEDULE time of the exam, another one is HELD IN time 
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
    
    def update_enrollments(self):
        for enroll in self.semesterenroll_set.all():
            enroll.update_stats()
    
    @property
    def semester_code(self):
        return f"{self.year}-{self.year_semester} [{self.session.session_code}]"
    
    @property
    def semester_name(self):
        return f"{get_ordinal_number(self.year)} Year {get_ordinal_number(self.year_semester)} Semester"
    
    @property
    def exam_year(self):
        exam_month_lst = self.start_month.split(" ")
        if len(exam_month_lst) == 2 and exam_month_lst[1].isdecimal():
            return int(exam_month_lst[1])
        else:
            return ""
            
    @property
    def has_courses(self):
        num_courses = self.course_set.count() + self.drop_courses.count()
        return bool(num_courses)
    
    @property
    def total_credits(self):
        credits = sum([course.course_credit for course in self.course_set.all()])
        return credits
        
    
    @property
    def is_tabulation_producible(self):
        num_course_results = CourseResult.objects.filter(course__semester=self, total_score__isnull=False).count()
        return bool(num_course_results)
    
    @property
    def has_tabulation_sheet(self):
        if self.semesterdocument and self.semesterdocument.tabulation_sheet:
            return True
    

class SemesterEnroll(models.Model):
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    student = models.ForeignKey("account.StudentAccount", on_delete=models.CASCADE)
    courses = models.ManyToManyField("Course", related_name='enrollment')
    semester_credits = models.FloatField(default=0)
    semester_points = models.FloatField(default=0)
    semester_gpa = models.FloatField(null=True, blank=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['semester', 'student'], name="one_enroll_per_semester")
        ]
    
    def update_stats(self):
        """Updates the stats field of the object.
        Dont call this function within SemesterEnroll.save()
        """
        
        credits_count = 0
        points_count = 0
        for course in self.courses.all():
            course_result = CourseResult.objects.filter(course=course, student=self.student).first()
            grade_point = course_result.grade_point
            if course_result and grade_point:
                credits_count += course_result.course.course_credit
                points_count += (grade_point * course.course_credit)
        # calculation and store values
        if points_count > 0:
            self.semester_credits = credits_count
            self.semester_points = points_count
            self.semester_gpa = round(points_count/credits_count, 2)
            self.save()
            self.student.update_stats()
        

class SemesterDocument(models.Model):
    def filepath(self, filename):
        return join(str(self.semester.session.dept.name), str(self.semester.session.session_code), str(self.semester.semester_code), filename)
    semester = models.OneToOneField(Semester, on_delete=models.CASCADE)
    tabulation_sheet = models.FileField(upload_to=filepath, null=True, blank=True)
    tabulation_thumbnail = models.ImageField(upload_to=filepath, null=True, blank=True)
    tabulation_sheet_render_time = models.DateTimeField(null=True, blank=True)
    tabulation_sheet_render_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    tabulatiobn_sheet_render_config = models.JSONField(null=True, blank=True)    
    
    @property
    def tabulation_filename(self):
        name_str = basename(self.tabulation_sheet.name)
        return name_str
    
    
class Course(models.Model):
    semester = models.ForeignKey("Semester", on_delete=models.CASCADE)
    code = models.CharField(max_length=20)
    title = models.CharField(max_length=200)
    course_credit = models.FloatField(validators=[MinValueValidator(settings.MIN_COURSE_CREDIT), MaxValueValidator(settings.MAX_COURSE_CREDIT)])
    total_marks = models.FloatField(validators=[MinValueValidator(1, "Total Marks must be greater than 0")])
    part_A_marks = models.FloatField(validators=[MinValueValidator(0, "Marks must be non negative")])
    part_B_marks = models.FloatField(validators=[MinValueValidator(0, "Marks must be non negative")])
    part_A_marks_final = models.FloatField(default=0, validators=[MinValueValidator(0, "Marks must be non negative")])
    part_B_marks_final = models.FloatField(default=0, validators=[MinValueValidator(0, "Marks must be non negative")])
    incourse_marks = models.FloatField(validators=[MinValueValidator(0, "Marks must be non negative")])  # so called TERMTEST 
    added_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    added_in = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code", "-course_credit"]
        constraints = [
            models.UniqueConstraint(fields=["semester", "code"], name="unique_course_semester")
        ]
    
    def __str__(self):
        return f"{self.semester} Course: {self.code}"
    
    def save(self, *args, **kwargs) -> None:
        if self.part_A_marks_final == 0:
            self.part_A_marks_final = self.part_A_marks
        if self.part_B_marks_final == 0:
            self.part_B_marks_final = self.part_B_marks
        super().save(*args, **kwargs)
    
    @property
    def num_nonempty_records(self):
        filled_records = self.courseresult_set.filter(
            Q(part_A_score__isnull=False) | Q(part_B_score__isnull=False) | Q(incourse_score__isnull=False)
        )
        return filled_records.count()
    
    @property
    def is_deletable(self):
        return self.num_nonempty_records == 0
    
    @property
    def num_regular_results(self):
        return self.courseresult_set.filter(is_drop_course=False).count()

    @property
    def num_pending_course(self):
        return self.courseresult_set.filter(total_score=None).count()
    
    
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
    is_drop_course = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "course"], name="unique_courseresult_student")
        ]
    
    
    def save(self, *args, **kwargs):
        ### Calculates total marks before saving
        if (self.part_A_score is not None or   # Case 1: If any component scores are provided, calculating total
            self.part_B_score is not None or
            self.incourse_score is not None):
            total = 0
            if self.part_A_score is not None:
                if self.part_A_score > self.course.part_A_marks:
                    raise ValidationError("Score cannot be more than defined marks")
                conversion_ratio = (self.course.part_A_marks_final / self.course.part_A_marks)
                part_a_actual_score = conversion_ratio * self.part_A_score
                total += part_a_actual_score
            if self.part_B_score is not None:
                if self.part_B_score > self.course.part_B_marks:
                    raise ValidationError("Score cannot be more than defined marks")
                conversion_ratio = (self.course.part_B_marks_final / self.course.part_B_marks)
                part_b_actual_score = conversion_ratio * self.part_B_score
                total += part_b_actual_score
            if self.incourse_score is not None:
                if self.incourse_score > self.course.incourse_marks:
                    raise ValidationError("Score cannot be more than defined marks")
                total += self.incourse_score
                
            self.total_score = total
                
        else:          # Case 2: If total marks are provided
            if self.total_score != None:
                if self.total_score > self.course.total_marks:
                    raise ValidationError("Score cannot be more than defined marks")
                
        # Saving grade point
        if self.total_score is not None:
            totalScore = round_up_point_five(self.total_score)
            self.grade_point = calculate_grade_point(totalScore, self.course.total_marks)
            self.letter_grade = calculate_letter_grade(totalScore, self.course.total_marks)
        super().save(*args, **kwargs)
        # updating semester enrollment
        enrollment = self.course.enrollment.filter(student=self.student).first()
        if enrollment:
            enrollment.update_stats()
        
    
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