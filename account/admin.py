from django.contrib import admin
from account import models
# Register your models here.

admin.site.register(models.AdminAccount)
admin.site.register(models.StudentAccount)
admin.site.register(models.InviteToken)