from django.db import models
from django.conf import settings

class WhatsAppLink(models.Model):
    lid_base = models.CharField(max_length=32, unique=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wa_links")
    phone = models.CharField(max_length=15)  # snapshot 01xxxxxxxxx
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)