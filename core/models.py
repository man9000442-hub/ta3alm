from django.db import models
from django.utils.translation import gettext_lazy as _

class SiteSetting(models.Model):
    is_maintenance_mode = models.BooleanField(default=False, verbose_name=_("وضع الصيانة"))
    
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    

# core/models.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications', verbose_name=_("المستقبل"))
    title = models.CharField(max_length=255, verbose_name=_("العنوان"))
    message = models.TextField(verbose_name=_("الرسالة"))
    link = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("الرابط"))
    is_read = models.BooleanField(default=False, verbose_name=_("مقروءة"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("وقت الإنشاء"))

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient} - {self.title}"
    
# قائمة الصفوف (للاستخدام في الفلترة)
GRADE_CHOICES = (
    ('1_prep', 'أولى إعدادي'), ('2_prep', 'ثانية إعدادي'), ('3_prep', 'ثالثة إعدادي'),
    ('1_sec', 'أولى ثانوي'), ('2_sec', 'ثانية ثانوي'), ('3_sec', 'ثالثة ثانوي'),
)

class Subject(models.Model):
    name = models.CharField(max_length=50, verbose_name="اسم المادة")
    # الصفوف التي تدرس فيها هذه المادة (يمكن اختيار أكثر من صف)
    # سنستخدم حقل نصي بسيط أو JSON، لكن للأسهل سنستخدم MultiselectField (مكتبة خارجية)
    # أو ببساطة: نجعل المادة عامة، ونفلتر بالمعلم.
    # الحل الأبسط: لا نربط المادة بالصف في الداتا بيز، بل نربط المعلم بالمادة.
    
    def __str__(self):
        return self.name