"""
core/forms.py
ملاحظة: فورمز تعديل المستخدمين من الإدارة انتقلت إلى dashboard_admin/forms.py
هذا الملف يبقى فارغاً للتوافق مع أي imports قديمة.
"""

# للتوافق مع أي كود قديم يستورد من هنا
from dashboard_admin.forms import (
    AdminUserEditForm      as OwnerUserEditForm,
    AdminTeacherEditForm   as OwnerTeacherEditForm,
    AdminStudentEditForm   as OwnerStudentEditForm,
    AdminAssistantEditForm as OwnerAssistantEditForm,
)

__all__ = [
    'OwnerUserEditForm',
    'OwnerTeacherEditForm',
    'OwnerStudentEditForm',
    'OwnerAssistantEditForm',
]