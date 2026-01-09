from django.db import models
from django.conf import settings

class CenterProfile(models.Model):
    # ربط السنتر بالمستخدم الأساسي
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='center_profile')
    
    # بيانات السنتر
    center_name = models.CharField(max_length=150, verbose_name='اسم السنتر')
    address = models.TextField(verbose_name='العنوان بالتفصيل')
    contact_phone = models.CharField(max_length=15, verbose_name='رقم تواصل السنتر')

    def __str__(self):
        return self.center_name