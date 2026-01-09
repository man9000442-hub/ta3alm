from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import StudentProfile
from teachers.models import Group

class Enrollment(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='enrollments')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='enrollments')
    is_active = models.BooleanField(default=False, verbose_name=_('مقبول'))
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'group')

class PerformanceLog(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='performance_logs')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='performance_logs')
    date = models.DateField(auto_now_add=True, verbose_name=_('التاريخ'))
    session_number = models.PositiveIntegerField(default=1, verbose_name=_('رقم الحصة'))
    is_present = models.BooleanField(default=True, verbose_name=_('حضور'))
    
    homework_score = models.IntegerField(null=True, blank=True, verbose_name=_('الواجب'))
    homework_max = models.IntegerField(default=10)
    
    class_exam_score = models.IntegerField(null=True, blank=True, verbose_name=_('امتحان الحصة'))
    class_exam_max = models.IntegerField(default=10)
    
    recitation_score = models.IntegerField(null=True, blank=True, verbose_name=_('التسميع'))
    recitation_max = models.IntegerField(default=10)
    
    comprehensive_exam_score = models.IntegerField(null=True, blank=True, verbose_name=_('الشامل'))
    comprehensive_exam_max = models.IntegerField(default=50)
    
    note = models.CharField(max_length=200, blank=True, verbose_name=_('ملاحظات'))

# في students/models.py
from teachers.models import CoursePackage, Lecture

# 1. جدول اشتراك الطالب في الحزمة (شراء)
class PackageEnrollment(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='package_enrollments')
    package = models.ForeignKey(CoursePackage, on_delete=models.CASCADE, related_name='enrollments')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False) # يصبح True بعد الدفع
    
    # يمكن إضافة حقل للعملية المالية لاحقاً
    
    class Meta:
        unique_together = ('student', 'package')

# 2. جدول تتبع مشاهدة الفيديو داخل الحزمة (لإعطاء الـ 10 درجات)
class VideoViewTracking(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    package = models.ForeignKey(CoursePackage, on_delete=models.CASCADE)
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE)
    
    views_count = models.PositiveIntegerField(default=0, verbose_name="عدد مرات المشاهدة")
    is_completed = models.BooleanField(default=False, verbose_name="تمت المشاهدة (أخذ الدرجة)")
    points_awarded = models.PositiveIntegerField(default=0, verbose_name="النقاط المكتسبة")

    class Meta:
        unique_together = ('student', 'package', 'lecture')


# نتيجة امتحان داخل حزمة (منفصلة عن المجموعات)
class PackageExamResult(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    package = models.ForeignKey('teachers.CoursePackage', on_delete=models.CASCADE)
    exam = models.ForeignKey('exams.Exam', on_delete=models.CASCADE)
    score = models.PositiveIntegerField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'package', 'exam') # الطالب يمتحن مرة واحدة داخل الحزمة
