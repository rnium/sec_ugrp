from django.contrib import admin
from results import models
# Register your models here.

admin.site.register(models.Department)
admin.site.register(models.Session)
admin.site.register(models.Semester)
admin.site.register(models.SemesterEnroll)
admin.site.register(models.SemesterDocument)
admin.site.register(models.Course)
admin.site.register(models.CourseResult)
admin.site.register(models.Backup)
admin.site.register(models.PreviousPoint)
admin.site.register(models.StudentPoint)
admin.site.register(models.StudentCustomDocument)
admin.site.register(models.ExamCommittee)
admin.site.register(models.StudentAcademicData)
admin.site.register(models.DocHistory)