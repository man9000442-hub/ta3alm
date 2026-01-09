from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from teachers.models import TeacherProfile

class AssistantProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assistant_profile')
    phone = models.CharField(max_length=15, verbose_name=_("رقم الهاتف"))
    def __str__(self): return self.user.username

class AssistantJob(models.Model):
    assistant = models.ForeignKey(AssistantProfile, on_delete=models.CASCADE, related_name='jobs')
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='assistants_jobs')
    is_active = models.BooleanField(default=False, verbose_name=_('مقبول'))
    joined_at = models.DateTimeField(auto_now_add=True)
    
    can_manage_students = models.BooleanField(default=True, verbose_name=_('إدارة الطلاب'))
    can_manage_exams = models.BooleanField(default=False, verbose_name=_('إدارة الامتحانات'))
    can_manage_videos = models.BooleanField(default=False, verbose_name=_('إدارة الفيديوهات'))
    can_manage_packages = models.BooleanField(default=False, verbose_name=_('إدارة الحزم'))
    class Meta:
        unique_together = ('assistant', 'teacher')