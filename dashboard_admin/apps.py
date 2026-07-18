"""
dashboard_admin/apps.py
"""
from django.apps import AppConfig


class DashboardAdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard_admin'
    verbose_name = 'لوحة الإدارة'

    def ready(self):
        pass  # مكان لربط الـ signals مستقبلاً
