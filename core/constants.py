"""
core/constants.py — ثوابت المنصة المشتركة بين جميع التطبيقات
"""
from django.utils.translation import gettext_lazy as _

# ==========================================================
# الصفوف الدراسية — مصدر واحد للجميع
# لا تعرّف GRADE_CHOICES في أي app أخرى، استورد من هنا دائماً
# ==========================================================
GRADE_CHOICES = (
    ('1_prep', _('الصف الأول الإعدادي')),
    ('2_prep', _('الصف الثاني الإعدادي')),
    ('3_prep', _('الصف الثالث الإعدادي')),
    ('1_sec', _('الصف الأول الثانوي')),
    ('2_sec', _('الصف الثاني الثانوي')),
    ('3_sec', _('الصف الثالث الثانوي')),
)

GRADE_MAP = dict(GRADE_CHOICES)

# ==========================================================
# أدوار المستخدمين
# ==========================================================
ROLE_STUDENT = 'student'
ROLE_TEACHER = 'teacher'
ROLE_ASSISTANT = 'assistant'
ROLE_CENTER = 'center'
ROLE_ADMIN = 'admin'

ROLE_CHOICES = (
    (ROLE_STUDENT, _('طالب')),
    (ROLE_TEACHER, _('معلم')),
    (ROLE_CENTER, _('سنتر')),
    (ROLE_ASSISTANT, _('مساعد')),
    (ROLE_ADMIN, _('مسؤول منصة')),
)
