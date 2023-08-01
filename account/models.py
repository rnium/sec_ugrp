from django.core.validators import FileExtensionValidator
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.templatetags.static import static
from results.models import Department, Session


class InviteToken(models.Model):
    from_user = models.ForeignKey(User, null=True, blank=True, related_name="from_user", on_delete=models.SET_NULL)
    to_user = models.ForeignKey(User, related_name="to_user", on_delete=models.CASCADE)
    user_email = models.EmailField()
    expiration = models.DateTimeField()


class BaseAccount(models.Model):
    profile_picture = models.ImageField(upload_to="profiles/dp/",
                                        null=True, 
                                        blank=True,
                                        validators=[FileExtensionValidator(allowed_extensions=settings.ALLOWED_IMAGE_EXTENSIONS)])
    class Meta:
        abstract = True
    
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

    @property
    def avatar_url(self):
        if bool(self.profile_picture):
            return self.profile_picture.url
        else:
            return static('results/images/blank-dp.svg')


class AdminAccount(BaseAccount):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_super_admin = models.BooleanField(default=False)
    dept = models.ForeignKey(Department, null=True, blank=True, on_delete=models.CASCADE)
    invitation = models.ForeignKey(InviteToken, on_delete=models.CASCADE)
    

class StudentAccount(BaseAccount):
    registration = models.IntegerField(primary_key=True)
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    cgpa = models.FloatField(default=0)

    class Meta:
        ordering = ["registration"]