import uuid
from django.core.validators import FileExtensionValidator
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.templatetags.static import static
from results.models import Department, Session, SemesterEnroll, StudentPoint
from results.utils import round_up


class InviteToken(models.Model):
    def get_uuid():
        return uuid.uuid4().hex

    id = models.CharField(
        max_length=50,
        primary_key = True,
        default = get_uuid,
        editable = False,
    )
    from_user = models.ForeignKey(User, related_name="from_user", on_delete=models.CASCADE)
    to_user_dept_id = models.IntegerField(null=True, blank=True)
    user_email = models.EmailField()
    actype = models.CharField(max_length=10, null=True, blank=True)
    expiration = models.DateTimeField()


class BaseAccount(models.Model):
    profile_picture = models.ImageField(upload_to="profiles/dp/",
                                        null=True, 
                                        blank=True,
                                        validators=[FileExtensionValidator(allowed_extensions=settings.ALLOWED_IMAGE_EXTENSIONS)])
    class Meta:
        abstract = True

    @property
    def avatar_url(self):
        if bool(self.profile_picture):
            return self.profile_picture.url
        else:
            return static('results/images/blank-dp.svg')


class AdminAccount(BaseAccount):
    limited_admin_user_types = [
        ('sust', 'Sust Admin')
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_super_admin = models.BooleanField(default=False)
    dept = models.ForeignKey(Department, null=True, blank=True, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, null=True, blank=True, choices=limited_admin_user_types)
    invited_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="inviting_user")
    
        
    def __str__(self):
        return self.user.username
    
    @property
    def user_first_name(self):
        first_name = self.user.first_name
        if first_name:
            return first_name
        else:
            return self.user.username
    
    @property
    def user_full_name(self):
        first_name = self.user.first_name
        last_name = self.user.last_name
        if first_name or last_name:
            if first_name and last_name:
                return f"{first_name} {last_name}"
            elif first_name:
                return first_name
            elif last_name:
                return last_name
        else:
            return self.user.username
    

class StudentAccount(BaseAccount):
    registration = models.IntegerField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    credits_completed = models.FloatField(default=0)
    total_points = models.FloatField(default=0)
    is_regular = models.BooleanField(default=True)
    father_name = models.CharField(max_length=100, default="")
    mother_name = models.CharField(max_length=100, default="")
    
    class Meta:
        ordering = ["-is_regular", "registration"]
    
    def __str__(self):
        return str(self.registration)
    
    def save(self, *args, **kwargs):
        session_from = str(self.session.from_year)
        if not str(self.registration).startswith(session_from):
            self.is_regular = False
        super().save(*args, **kwargs)
        
    def update_stats(self):
        enrollments = SemesterEnroll.objects.filter(student=self)
        student_prevPoint = StudentPoint.objects.filter(student=self).first()
        credits_count = 0
        points_count = 0
        if student_prevPoint:
            credits_count += student_prevPoint.total_credits
            points_count += student_prevPoint.total_points
        for enroll in enrollments:
            if (student_prevPoint and  (enroll.semester.semester_no <= student_prevPoint.prev_point.upto_semester_num)):
                continue
            credits_count += enroll.semester_credits
            points_count += enroll.semester_points
        if points_count >= 0:
            self.credits_completed = credits_count
            self.total_points = points_count
            self.save()
        
    @property
    def student_name(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.first_name
    
    @property
    def raw_cgpa(self):
        if points:= self.total_points:
            cgpa = points / self.credits_completed
            return cgpa
        else:
            return None
        
    @property
    def student_cgpa(self):
        if self.total_points:
            cgpa = self.raw_cgpa
            return "{}".format(round_up(cgpa, 2))
        else:
            return None
    
    @property
    def gradesheet_semesters(self):
        semesters = []
        for semester_no in range(1, 9):
            year_enrolls = SemesterEnroll.objects.filter(student=self, semester__semester_no=semester_no, semester__is_running=False, semester_gpa__isnull=False)
            if year_enrolls.count():
                semesters.append(semester_no)
        return semesters    
    
    @property
    def gradesheet_years(self):
        years = []
        for year in range(1, 5):
            year_enrolls = SemesterEnroll.objects.filter(student=self, semester__year=year, semester__is_running=False, semester_gpa__isnull=False)
            if year_enrolls.count() == 2:
                years.append(year)
        return years
    
    @property
    def father_name_repr(self):
        father = self.father_name
        if father == "":
            return "[empty]"
        return father    
    
    @property
    def mother_name_repr(self):
        mother = self.mother_name
        if mother == "":
            return "[empty]"
        return mother
        
        
    @property
    def is_transcript_available(self):
        semesters = 0
        for semester_no in range(1, 9):
            year_enrolls = SemesterEnroll.objects.filter(student=self, semester__semester_no=semester_no, semester__is_running=False, semester_gpa__isnull=False)
            if year_enrolls.count():
                semesters += 1
        return True if semesters == 8 else False