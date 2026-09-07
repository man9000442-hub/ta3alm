"""
dashboard_admin/models.py
نماذج نظام الإدارة: أدوار المسؤولين وسجل الأحداث
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


# ==========================================================
# أدوار الإدارة
# ==========================================================
class AdminRole(models.TextChoices):
    OWNER     = 'owner',     _('مالك المنصة')
    MODERATOR = 'moderator', _('مشرف')
    SUPPORT   = 'support',   _('دعم فني')
    FINANCE   = 'finance',   _('مسؤول مالي')


# ==========================================================
# بروفايل المسؤول الإداري
# ==========================================================
class AdminProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='admin_profile',
        verbose_name=_('المستخدم'),
    )
    admin_role = models.CharField(
        max_length=20,
        choices=AdminRole.choices,
        default=AdminRole.MODERATOR,
        verbose_name=_('دور الإدارة'),
    )
    is_active_admin = models.BooleanField(
        default=True,
        verbose_name=_('نشط'),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('ملاحظات'),
    )
    appointed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='appointed_admins',
        verbose_name=_('عيَّنه'),
    )
    appointed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ التعيين'),
    )

    class Meta:
        verbose_name = _('بروفايل مسؤول')
        verbose_name_plural = _('بروفايلات المسؤولين')
        ordering = ['admin_role', 'appointed_at']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email} ({self.get_admin_role_display()})"

    # --- صلاحيات مُحسَّنة ---
    @property
    def is_owner(self):
        return self.admin_role == AdminRole.OWNER or self.user.is_superuser

    @property
    def can_manage_users(self):
        return self.admin_role in (AdminRole.OWNER, AdminRole.MODERATOR)

    @property
    def can_delete_users(self):
        return self.admin_role == AdminRole.OWNER or self.user.is_superuser

    @property
    def can_view_finance(self):
        return self.admin_role in (AdminRole.OWNER, AdminRole.FINANCE)

    @property
    def can_manage_plans(self):
        return self.admin_role == AdminRole.OWNER or self.user.is_superuser

    @property
    def can_view_audit_log(self):
        return self.admin_role == AdminRole.OWNER or self.user.is_superuser


# ==========================================================
# سجل الأحداث الإدارية (Audit Log)
# ==========================================================
class AuditLog(models.Model):
    # أنواع الأحداث
    ACTION_BAN           = 'ban_user'
    ACTION_UNBAN         = 'unban_user'
    ACTION_DELETE        = 'delete_user'
    ACTION_RENEW_SUB     = 'renew_subscription'
    ACTION_EDIT_USER     = 'edit_user'
    ACTION_ADD_PLAN      = 'add_plan'
    ACTION_EDIT_PLAN     = 'edit_plan'
    ACTION_DELETE_PLAN   = 'delete_plan'
    ACTION_PAY_WITHDRAW  = 'pay_withdrawal'
    ACTION_TOGGLE_MAINT  = 'toggle_maintenance'
    ACTION_TOGGLE_AI     = 'toggle_ai'
    ACTION_APPOINT_ADMIN = 'appoint_admin'
    ACTION_REMOVE_ADMIN  = 'remove_admin'

    ACTION_CHOICES = [
        (ACTION_BAN,           _('حظر مستخدم')),
        (ACTION_UNBAN,         _('رفع حظر')),
        (ACTION_DELETE,        _('حذف مستخدم')),
        (ACTION_RENEW_SUB,     _('تجديد اشتراك')),
        (ACTION_EDIT_USER,     _('تعديل بيانات مستخدم')),
        (ACTION_ADD_PLAN,      _('إضافة باقة')),
        (ACTION_EDIT_PLAN,     _('تعديل باقة')),
        (ACTION_DELETE_PLAN,   _('حذف باقة')),
        (ACTION_PAY_WITHDRAW,  _('تسديد طلب سحب')),
        (ACTION_TOGGLE_MAINT,  _('تغيير وضع الصيانة')),
        (ACTION_TOGGLE_AI,     _('تشغيل/إيقاف الذكاء الاصطناعي')),
        (ACTION_APPOINT_ADMIN, _('تعيين مسؤول')),
        (ACTION_REMOVE_ADMIN,  _('إزالة مسؤول')),
    ]

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        verbose_name=_('المسؤول المنفِّذ'),
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        verbose_name=_('الحدث'),
    )
    target_label = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('المستهدف (وصف)'),
    )
    target_id = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('ID المستهدف'),
    )
    details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('التفاصيل'),
    )
    ip_address = models.GenericIPAddressField(
        null=True, blank=True,
        verbose_name=_('عنوان IP'),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('وقت الحدث'),
    )

    class Meta:
        verbose_name = _('سجل حدث')
        verbose_name_plural = _('سجل الأحداث الإدارية')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['admin', 'created_at'], name='auditlog_admin_time_idx'),
            models.Index(fields=['action'], name='auditlog_action_idx'),
        ]

    def __str__(self):
        admin_name = self.admin.get_full_name() if self.admin else 'محذوف'
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {admin_name} — {self.get_action_display()}"

    @classmethod
    def log(cls, request, action, target_label='', target_id=None, details=None):
        """Helper سريع لتسجيل حدث إداري."""
        ip = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR')
        )
        return cls.objects.create(
            admin=request.user,
            action=action,
            target_label=target_label,
            target_id=target_id,
            details=details or {},
            ip_address=ip or None,
        )
