from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
import random

ROLE_CHOICES = (
    ('student', _('طالب')),
    ('teacher', _('معلم')),
    ('center', _('سنتر')),
    ('assistant', _('مساعد')),
    ('admin', _('مسؤول منصة')),
)

class User(AbstractUser):
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student', verbose_name=_('نوع المستخدم'))
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name=_('رقم الهاتف'))
    national_id = models.CharField(max_length=14, blank=True, null=True, unique=True, verbose_name=_('الرقم القومي'))
    custom_id = models.CharField(max_length=10, blank=True, null=True, unique=True, verbose_name=_('كود المستخدم'))
    is_banned = models.BooleanField(default=False, verbose_name=_('محظور'))

    def save(self, *args, **kwargs):
        # توليد كود تلقائي إذا لم يوجد
        if not self.custom_id and self.role in ['student', 'teacher', 'assistant']:
            # إذا كان هناك رقم قومي، نستخدمه
            if self.national_id and len(self.national_id) >= 14:
                letters = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=2))
                nums = self.national_id[-3:] 
                self.custom_id = f"{letters}{nums}"
            else:
                # توليد عشوائي كامل (للمساعد أو المعلم الجديد)
                import string
                chars = string.ascii_uppercase + string.digits
                self.custom_id = "T" + ''.join(random.choices(chars, k=6))
                
        super().save(*args, **kwargs)

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    parent_phone = models.CharField(max_length=15, verbose_name=_('رقم ولي الأمر'))
    enrolled_teachers = models.ManyToManyField('teachers.TeacherProfile', blank=True, related_name='students', verbose_name=_('المدرسين المشترك معهم'))
    
    def __str__(self):
        return self.user.username