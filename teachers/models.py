from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
import re
import random
import string
from core.models import Subject
# ==========================================
# 1. المجموعات والصفوف
# ==========================================
GRADE_CHOICES = (
    ('1_prep', _('الصف الأول الإعدادي')),
    ('2_prep', _('الصف الثاني الإعدادي')),
    ('3_prep', _('الصف الثالث الإعدادي')),
    ('1_sec', _('الصف الأول الثانوي')),
    ('2_sec', _('الصف الثاني الثانوي')),
    ('3_sec', _('الصف الثالث الثانوي')),
)

# ==========================================
# 2. خطط الأسعار (Subscription Plans)
# ==========================================
class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("اسم الباقة"))
    price = models.PositiveIntegerField(verbose_name=_("السعر (EGP)"))
    student_limit = models.PositiveIntegerField(verbose_name=_("حد الطلاب الأقصى"))
    description = models.TextField(blank=True, verbose_name=_("وصف الباقة"))
    
    # --- قيود الباقة ---
    student_limit = models.PositiveIntegerField(default=1000, verbose_name=_("حد الطلاب"))
    group_limit = models.PositiveIntegerField(default=5, verbose_name=_("حد المجموعات"))
    assistant_limit = models.PositiveIntegerField(default=2, verbose_name=_("حد المساعدين"))
    
    # --- صلاحيات (نعم/لا) ---
    allow_online_packages = models.BooleanField(default=False, verbose_name=_("مسموح بالحزم الأونلاين"))
    allow_question_images = models.BooleanField(default=False, verbose_name=_("مسموح بصور الأسئلة"))
    is_default = models.BooleanField(default=False, verbose_name=_("باقة افتراضية (مجانية)"))

    def save(self, *args, **kwargs):
        # لو اخترت دي افتراضية، الغي الافتراضي من الباقي
        if self.is_default:
            SubscriptionPlan.objects.filter(is_default=True).update(is_default=False)
            
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.name} ({self.price} EGP)"

# ==========================================
# 3. بروفايل المعلم
# ==========================================
class TeacherProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teacher_profile')
    
    bio = models.TextField(blank=True, verbose_name=_('نبذة عن المعلم'))
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, verbose_name="المادة")
    image = models.ImageField(upload_to='teachers/', blank=True, null=True, verbose_name=_('صورة المعلم'))
    
    # الاشتراك
    subscription_end_date = models.DateTimeField(null=True, blank=True, verbose_name=_('تاريخ انتهاء الاشتراك'))
    is_trial_used = models.BooleanField(default=False, verbose_name=_('هل استهلك الشهر المجاني؟'))
    current_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("الباقة الحالية"))

    def has_active_subscription(self):
        if not self.subscription_end_date: return False
        return self.subscription_end_date > timezone.now()

    def days_remaining(self):
        if not self.subscription_end_date: return 0
        return max((self.subscription_end_date - timezone.now()).days, 0)
    
    def get_student_limit(self):
        return self.current_plan.student_limit if self.current_plan else 0

    def get_total_students(self):
        from django.apps import apps
        Enrollment = apps.get_model('students', 'Enrollment')
        return Enrollment.objects.filter(group__teacher=self, is_active=True).count()
        # دالة ترجع قائمة IDs المجموعات المسموحة (الأقدم فالأحدث حسب الحد)
    def get_allowed_group_ids(self):
        limit = self.current_plan.group_limit if self.current_plan else 0
        # نأخذ أقدم N مجموعات فقط
        return self.groups.order_by('created_at').values_list('id', flat=True)[:limit]

    # هل الحزم مسموحة في الباقة الحالية؟
    def are_packages_allowed(self):
        return self.current_plan.allow_online_packages if self.current_plan else False

    def __str__(self):
        return self.user.username

# ==========================================
# 4. المجموعة (Group)
# ==========================================
class Group(models.Model):
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='groups')
    name = models.CharField(max_length=100, verbose_name=_('اسم المجموعة'))
    grade = models.CharField(max_length=20, choices=GRADE_CHOICES, verbose_name=_('الصف الدراسي'))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.get_grade_display()}"

# ==========================================
# 5. المحاضرة (Lecture)
# ==========================================
class Lecture(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='lectures', null=True, blank=True)
    title = models.CharField(max_length=200, verbose_name=_('العنوان'))
    video_link = models.URLField(verbose_name=_('رابط الفيديو'))
    description = models.TextField(blank=True, verbose_name=_('الوصف'))
    is_active = models.BooleanField(default=True, verbose_name=_("مفعلة"))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.title

    def get_video_id(self):
        if not self.video_link: return None
        clean = self.video_link.strip()
        # دعم يوتيوب فقط حالياً في هذا الفانكشن
        if 'youtube' not in clean and 'youtu.be' not in clean: return None
        patterns = [r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})', r'(?:embed\/)([0-9A-Za-z_-]{11})']
        for p in patterns:
            match = re.search(p, clean)
            if match: return match.group(1)
        return None

# ==========================================
# 6. أكواد الفيديو
# ==========================================
class VideoCode(models.Model):
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='codes')
    code = models.CharField(max_length=10, unique=True, verbose_name=_('الكود'))
    
    max_views = models.PositiveIntegerField(default=1, verbose_name=_("حد المشاهدات"))
    current_views = models.PositiveIntegerField(default=0, verbose_name=_("المشاهدات الحالية"))
    
    is_used = models.BooleanField(default=False, verbose_name=_('تم التفعيل'))
    used_by = models.ForeignKey('accounts.StudentProfile', on_delete=models.SET_NULL, null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)

    def is_expired(self):
        return self.current_views >= self.max_views

    @staticmethod
    def generate_random_code():
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


class PDFFile(models.Model):
    # يمكن أن يكون تابعاً لمجموعة (اختياري)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='pdfs', null=True, blank=True)
    
    title = models.CharField(max_length=200, verbose_name=_('عنوان الملف'))
    link = models.URLField(verbose_name=_('رابط الملف (Drive/Direct)'))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.title

    
# ==========================================
# 7. الحزم التعليمية (Online Course Packages)
# ==========================================
class CoursePackage(models.Model):
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='packages')
    title = models.CharField(max_length=200, verbose_name=_("اسم الحزمة"))
    
    # حقل الصف (الجديد) - بدون default ليجبرك على اختياره
    grade = models.CharField(max_length=20, choices=GRADE_CHOICES, verbose_name=_("الصف الدراسي"))
    pdfs = models.ManyToManyField(PDFFile, related_name='packages', verbose_name=_("الملفات المختارة"), blank=True)    
    description = models.TextField(verbose_name=_("وصف الحزمة"))
    price = models.PositiveIntegerField(verbose_name=_("سعر الحزمة (EGP)"))
    image = models.ImageField(upload_to='packages/', blank=True, null=True, verbose_name=_("صورة الغلاف"))
    
    # العلاقات (ManyToMany) - هنا نستخدم string لتجنب Circular Import مع exams
    lectures = models.ManyToManyField(Lecture, related_name='packages', verbose_name=_("المحاضرات المختارة"))
    exams = models.ManyToManyField('exams.Exam', related_name='packages', verbose_name=_("الامتحانات المختارة"))
    
    view_limit = models.PositiveIntegerField(default=3, verbose_name=_("حد المشاهدة للفيديو"))
    is_active = models.BooleanField(default=True, verbose_name=_("متاحة للشراء"))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.title

# ==========================================
# 8. سجل المدفوعات (للمعلم)
# ==========================================
class PaymentTransaction(models.Model):
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(verbose_name=_("المبلغ"))
    date = models.DateTimeField(auto_now_add=True, verbose_name=_("التاريخ"))
    transaction_id = models.CharField(max_length=100, blank=True, null=True)


# محفظة المعلم
class Wallet(models.Model):
    teacher = models.OneToOneField(TeacherProfile, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(default=0.0, max_digits=10, decimal_places=2, verbose_name="الرصيد الحالي")
    total_earnings = models.DecimalField(default=0.0, max_digits=12, decimal_places=2, verbose_name="إجمالي الأرباح")
    
    def __str__(self):
        return f"محفظة: {self.teacher.user.username} ({self.balance} EGP)"

# طلبات السحب
class WithdrawRequest(models.Model):
    METHODS = (
        ('vodafone', 'Vodafone Cash'),
        ('instapay', 'InstaPay'),
        ('bank', 'Bank Transfer'),
    )
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ المطلوب")
    method = models.CharField(max_length=20, choices=METHODS, verbose_name="طريقة السحب")
    details = models.TextField(verbose_name="بيانات التحويل (رقم/حساب)")
    is_paid = models.BooleanField(default=False, verbose_name="تم التحويل")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.amount} - {self.get_method_display()}"