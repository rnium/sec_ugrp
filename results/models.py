import base64
from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from django.templatetags.static import static
from results.utils import (get_ordinal_number, calculate_grade_point, calculate_letter_grade,
                           get_letter_grade, round_up_point_five, round_up)
from os.path import join, basename


class Department(models.Model):
    name = models.CharField(max_length=3, unique=True)
    fullname = models.CharField(max_length=100)
    dept_logo_name = models.CharField(max_length=50, null=True, blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    head = models.ForeignKey('account.AdminAccount', blank=True, null=True, on_delete=models.SET_NULL)
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
    total_credits = models.FloatField(default=0)
    
    class Meta:
        ordering = ["-from_year"]
        constraints = [
            models.UniqueConstraint(fields=["from_year", "dept"], name="unique_dept_session"),
            models.UniqueConstraint(fields=["batch_no", "dept"], name="unique_dept_batch"),
        ]
        
    def __str__(self):
        return f"{self.dept.name.upper()} {self.session_code}"
    
    def __gt__(self, other):
        return self.from_year > other.from_year
    
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
    
    @property
    def num_students(self):
        return self.studentaccount_set.count()
    
    @property
    def course_identifier_prefix(self):
        return self.dept.name.lower() + str(self.batch_no)
    
    @property
    def has_final_semester(self):
        semesters = self.semester_set.filter(year=4, year_semester=2)
        if semesters.count():
            return True
        return False
    
    @property
    def repeat_count(self):
        semesters = self.semester_set.filter(year=4, year_semester=2)
        return semesters.count()
    
       
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
    repeat_number = models.IntegerField(default=0)
    part_no = models.IntegerField(default=0)
    start_month = models.CharField(max_length=50) # IT is the SCHEDULE time of the exam, another one is HELD IN time 
    held_in = models.CharField(max_length=50, default='')
    exam_duration = models.CharField(max_length=50, null=True, blank=True)
    is_running = models.BooleanField(default=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    drop_courses = models.ManyToManyField("Course", blank=True, related_name="drop_courses")
    added_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='added_by')
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='updated_by')
    added_in = models.DateTimeField(auto_now_add=True)
    updated_in = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    class Meta:
        ordering = ["semester_no", 'part_no', 'repeat_number']
        constraints = [
            models.UniqueConstraint(fields=["year", "year_semester", "session", "part_no", "repeat_number"], name="unique_session_per_semester")
        ]
        
        
    def __str__(self) -> str:
        name = f"{self.session}, {self.semester_name}"
        if self.part_no:
            name += f", part: {self.part_no}"
        if self.repeat_number:
            name += f", repeat: {self.repeat_number}"
        return name
    
    def update_enrollments(self):
        for enroll in self.semesterenroll_set.all():
            enroll.update_stats()
    
    @property
    def b64_id(self):
        id_str_bytes = str(self.id).encode('utf-8')
        id_b64_bytes = base64.b64encode(id_str_bytes)
        return id_b64_bytes.decode('utf-8')
    
    @property
    def semester_code(self):
        codename = f"{self.year}-{self.year_semester} [{self.session.session_code}]"
        if self.part_no:
            codename += f" P-{self.part_no}"
        if self.repeat_number:
            codename += f" R-{self.repeat_number}"
        return codename
    
    @property
    def semester_name(self):
        name = f"{get_ordinal_number(self.year)} Year {get_ordinal_number(self.year_semester)} Semester"
        return name
    
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
        return bool(self.course_set.count() + self.drop_courses.count())
    
    @property
    def has_tabulation_sheet(self):
        if self.semesterdocument and self.semesterdocument.tabulation_sheet:
            return True
        
    @property
    def prevpoint_applicable(self):
        prev_semesters = self.session.semester_set.filter(semester_no__lt=self.semester_no)
        if prev_semesters.count() or self.semester_no == 1:
            return False
        else:
            return True
    
    @property
    def has_prevpoint_from_here(self):
        ppoint = PreviousPoint.objects.filter(session=self.session, upto_semester_num=self.semester_no-1).first()
        return bool(ppoint)
    
    @property
    def duration_info(self):
        if duration:= self.exam_duration:
            return duration
        return "<DURATION UNSPECIFIED>"
    
    @property
    def committee_members(self):
        members = []
        if hasattr(self, 'examcommittee'):
            committee = self.examcommittee
            if committee.chairman:
                members.append({
                    'admin': committee.chairman,
                    'title': 'Chairman',
                    'codename': 'chair'
                })
            for member in committee.members.all():
                members.append({
                    'admin': member,
                    'title': 'Member',
                    'codename': 'c-member'
                })
            for tabulator in committee.tabulators.all():
                members.append({
                    'admin': tabulator,
                    'title': 'Tabulator',
                    'codename': 'tabulator'
                })
        return members
    
    @property
    def editor_members(self):
        members = []
        if hasattr(self, 'examcommittee'):
            committee = self.examcommittee
            if committee.chairman:
                members.append(committee.chairman)
            for tabulator in committee.tabulators.all():
                members.append(tabulator)
        return members


class ExamCommittee(models.Model):
    semester = models.OneToOneField(Semester, on_delete=models.CASCADE)
    chairman = models.ForeignKey('account.AdminAccount', null=True, blank=True, on_delete=models.SET_NULL)
    members = models.ManyToManyField('account.AdminAccount', related_name='committee_member')
    tabulators = models.ManyToManyField('account.AdminAccount', related_name='committee_tabulator')
    last_updated = models.DateTimeField(auto_now=True)


class SemesterEnroll(models.Model):
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    student = models.ForeignKey("account.StudentAccount", on_delete=models.CASCADE)
    courses = models.ManyToManyField("Course", related_name='enrollment')
    semester_credits = models.FloatField(default=0)
    semester_points = models.FloatField(default=0)
    semester_gpa = models.FloatField(null=True, blank=True)
    is_publishable = models.BooleanField(default=True)
    
    class Meta:
        ordering = ["-student__is_regular", "student__registration"]
        constraints = [
            models.UniqueConstraint(fields=['semester', 'student'], name="one_enroll_per_semester")
        ]
    
    def save(self, *args, **kwargs):
        enrolls = SemesterEnroll.objects.filter(semester__semester_no=self.semester.semester_no, semester__repeat_number=self.semester.repeat_number, student=self.student).exclude(id=self.id)
        if enrolls.count():
            raise ValidationError(f"Student already enrolled for the semester no: {self.semester.semester_no}")
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        for course in self.courses.all():
            course_res = CourseResult.objects.filter(course=course, student=self.student).first()
            if course_res:
                course_res.delete()
        super().delete(*args, **kwargs)
        self.student.update_stats()
    
    
    def update_stats(self):
        """Updates the stats field of the object.
        Dont call this function within SemesterEnroll.save()
        """
        credits_count = 0
        points_count = 0
        for course in self.courses.all():
            course_result = CourseResult.objects.filter(course=course, student=self.student).first()
            if course_result and course_result.grade_point:
                grade_point = course_result.grade_point
                credits_count += course_result.course.course_credit
                points_count += (grade_point * course.course_credit)
        # calculation and store values
        if points_count > 0:
            self.semester_credits = credits_count
            self.semester_points = points_count
            self.semester_gpa = round(points_count/credits_count, 2)
            self.save()
            self.student.update_stats()


class PreviousPoint(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE)
    upto_semester_num = models.IntegerField()
    added_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    added_in = models.DateTimeField(auto_now_add=True)


class StudentPoint(models.Model):
    prev_point = models.ForeignKey(PreviousPoint, on_delete=models.CASCADE)
    student = models.ForeignKey("account.StudentAccount", on_delete=models.CASCADE)
    total_credits = models.FloatField(default=0)
    total_points = models.FloatField(default=0)
    
    @property
    def cgpa_raw(self):
        if self.total_credits:
            return (self.total_points / self.total_credits)
        return 0
    
    @property
    def cgpa(self):
        if self.total_points < 1:
            return 0
        return "{}".format(round_up(self.cgpa_raw, 2))
    
    @property
    def letter_grade(self):
        return get_letter_grade(self.cgpa_raw)
    
    @property
    def semester_range_str(self):
        return f"1st Semester to {get_ordinal_number(self.prev_point.upto_semester_num)} Semester"
      

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
    
    @property 
    def thumb_url(self):
        if thumb:= self.tabulation_thumbnail:
            return thumb.url
        else:
            return ""
    
    
class Course(models.Model):
    semester = models.ForeignKey("Semester", on_delete=models.CASCADE)
    code = models.CharField(max_length=20)
    title = models.CharField(max_length=200)
    course_credit = models.FloatField(validators=[MinValueValidator(settings.MIN_COURSE_CREDIT), MaxValueValidator(settings.MAX_COURSE_CREDIT)])
    identifier = models.CharField(max_length=20, unique=True, null=True, blank=True)
    total_marks = models.FloatField(validators=[MinValueValidator(1, "Total Marks must be greater than 0")])
    part_A_marks = models.FloatField(validators=[MinValueValidator(0, "Marks must be non negative")])
    part_B_marks = models.FloatField(validators=[MinValueValidator(0, "Marks must be non negative")])
    part_A_marks_final = models.FloatField(default=0, validators=[MinValueValidator(0, "Marks must be non negative")])
    part_B_marks_final = models.FloatField(default=0, validators=[MinValueValidator(0, "Marks must be non negative")])
    incourse_marks = models.FloatField(validators=[MinValueValidator(0, "Marks must be non negative")])  # so called TERMTEST 
    is_theory_course = models.BooleanField(default=True)
    is_carry_course = models.BooleanField(default=False)
    added_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    added_in = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["semester", "code"], name="unique_course_semester")
        ]
    
    def __str__(self):
        return f"{self.semester} {self.code}"
    
    def get_identifier_code(self):
        c = self.code.lower().replace(" ", "")
        return  self.semester.session.course_identifier_prefix + str(self.semester.repeat_number) + str(self.semester.part_no) + c
    
    def save(self, *args, **kwargs) -> None:
        if self.part_A_marks_final == 0:
            self.part_A_marks_final = self.part_A_marks
        if self.part_B_marks_final == 0:
            self.part_B_marks_final = self.part_B_marks
        self.identifier = self.get_identifier_code()
        super().save(*args, **kwargs)
        
    @property
    def b64_id(self):
        id_str_bytes = str(self.id).encode('utf-8')
        id_b64_bytes = base64.b64encode(id_str_bytes)
        return id_b64_bytes.decode('utf-8')
    
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
        return self.courseresult_set.filter(total_score=None, is_drop_course=False).count()
    
    @property
    def num_missing_entries_for_semesterenrolls(self):
        if self.is_carry_course or self.semester.repeat_number or self.semester.part_no:
            return 0
        # num_enrolled_regular = self.courseresult_set.filter(student__session=self.semester.session).count()
        num_enrolled_regular = CourseResult.objects.filter(
            student__session = self.semester.session, 
            course__code = self.code,
            course__semester__semester_no = self.semester.semester_no,
            course__semester__repeat_number = self.semester.repeat_number
        ).count()
        return (self.semester.semesterenroll_set.count() - num_enrolled_regular)
    
    
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
    retake_of = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ["is_drop_course", "student__registration"]
        constraints = [
            models.UniqueConstraint(fields=["student", "course"], name="unique_courseresult_student")
        ]
    
    
    def save(self, *args, **kwargs):
        ### Calculates total marks before saving
        if (self.part_A_score is not None or   # Case 1: If any component scores are provided, calculating total
            self.part_B_score is not None):
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
            if self.course.is_theory_course:
                self.total_score = None
            elif self.total_score != None:
                if self.total_score > self.course.total_marks:
                    raise ValidationError("Score cannot be more than defined marks")
                
        # Saving grade point
        if self.total_score is not None:
            totalScore = round_up_point_five(self.total_score)
            is_carry = self.is_drop_course
            self.grade_point = calculate_grade_point(totalScore, self.course.total_marks, is_carry)
            self.letter_grade = calculate_letter_grade(totalScore, self.course.total_marks, is_carry)
        else:
            self.grade_point = None
            self.letter_grade = None
        super().save(*args, **kwargs)
        # updating semester enrollment
        enrollment = self.course.enrollment.filter(student=self.student).first()
        if enrollment:
            enrollment.update_stats()
        
    def delete(self, *args, **kwargs):
        enrolls = SemesterEnroll.objects.filter(student=self.student, courses=self.course)
        for e in enrolls:
            e.courses.remove(self.course)
        super().delete()
        
    @property
    def course_points(self):
        return (self.grade_point * self.course.course_credit)
    
    @property
    def total_round_up(self):
        score = self.total_score
        if score is None:
            return 'Ab'
        int_score = int(score)
        if score == int_score:
            return int_score
        return round_up(score, 2)
    
    
class Backup(models.Model):
    def filepath(self, filename):
        return join(str(self.semester.session.dept.name), "Backups", filename)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    data = models.JSONField(null=True)
    session = models.ForeignKey(Session, null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-created_at"]
    
    @property
    def backup_name(self):
        if self.session:
            return f"Session Backup: {self.session.batch_name}"
        else:
            return f"Department Backup"


class StudentCustomDocument(models.Model):
    type_choices = [
        ('transcript', 'Transcript'),
        ('sem_gs', 'Semester Gradesheet'),
        ('y_gs', 'Yearly Gradesheet'),
        ('all_gss', 'All Gradesheets'),
    ]
    def filepath(self, filename):
        return join(str(self.student.session.dept.name), str(self.student.session.session_code), str(self.student.registration), filename)
    doc_type = models.CharField(choices=type_choices, max_length=20, default='all_gss')
    sem_or_year_num = models.IntegerField(null=True, blank=True)
    student = models.ForeignKey("account.StudentAccount", on_delete=models.CASCADE)
    document_data = models.JSONField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def url(self):
        if self.sem_or_year_num:
            return reverse('results:download_customdoc', args=(self.student.registration, self.doc_type)) + f"?num={self.sem_or_year_num}"
        else:
            return reverse('results:download_customdoc', args=(self.student.registration, self.doc_type))
    
    @property
    def title(self):
        if self.doc_type == 'transcript':
            return 'Academic Transcript'
        elif self.doc_type == 'sem_gs':
            if num:=self.sem_or_year_num:
                return f"{get_ordinal_number(num)} Semester Gradesheet"
            return "Semester Gradesheet"
        elif self.doc_type == 'y_gs':
            if num:=self.sem_or_year_num:
                return f"{get_ordinal_number(num)} Year Gradesheet"
            return "Year Gradesheet"
        elif self.doc_type == 'all_gss':
            return "All Gradesheets"
        else:
            return "Unknown type document"
    
    @property
    def filename(self):
        title = self.title.replace(' ', '_')
        return f"{self.student.registration}_{title}.pdf"

    
class SupplementaryDocument(models.Model):
    def filepath(self, filename):
        return join(str(self.course.semester.session.dept.name), str(self.course.semester.session.session_code), str(self.course.semester.semester_no), str(self.course.code.replace(' ', '')), filename)
    course = models.OneToOneField(Course, on_delete=models.CASCADE)
    document = models.FileField(upload_to=filepath, null=True, blank=True)
    added_at = models.DateTimeField(default=timezone.now)
    
    @property
    def document_filename(self):
        name_str = basename(self.document.name)
        return name_str


class StudentAcademicData(models.Model):
    registration = models.IntegerField(unique=True)
    session_code = models.CharField(max_length=20, null=True, blank=True)
    data = models.JSONField()


class DocHistory(models.Model):
    doc_type_choices = (
        ('t', 'Testimonial'),
        ('c', 'Coursemedium Certificate'),
        ('a', 'Appeared Certificate'),
    )
    doc_type = models.CharField(max_length=20, choices=doc_type_choices)
    registration = models.CharField(max_length=50)
    reference = models.CharField(max_length=200)
    added = models.DateTimeField(auto_now_add=True)