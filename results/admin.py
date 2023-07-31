from django.contrib import admin
from results import models
# Register your models here.

admin.site.register(models.Department)
admin.site.register(models.Session)
admin.site.register(models.Semester)
admin.site.register(models.Course)
admin.site.register(models.CourseResult)
admin.site.register(models.Activity)