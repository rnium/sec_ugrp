from django.db import models
from django.core.validators import FileExtensionValidator
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.models import User
from django.templatetags.static import static


class Department(models.Model):
    name = models.CharField(max_length=3)
    fullname = models.CharField(max_length=100)
    dept_logo = models.ImageField(upload_to="departments/logo/",
                                    null=True, 
                                    blank=True,
                                    validators=[FileExtensionValidator(allowed_extensions=settings.ALLOWED_IMAGE_EXTENSIONS)])
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    added = models.DateTimeField(auto_now_add=True)
    
    
class Session(models.Model):
    from_year = models.IntegerField()
    to_year = models.IntegerField()
    batch_no = models.IntegerField()
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"EEE {self.from_year}-{self.to_year % 2000}"
    
    class Meta:
        ordering = ["from_year"]
