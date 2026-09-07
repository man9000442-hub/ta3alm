"""
exams/models.py — نماذج نظام الامتحانات
"""
from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from teachers.models import Group
from accounts.models import StudentProfile


class Exam(models.Model):
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name='exams',
        null=True, blank=True
    )
    title = models.CharField(max_length=200, verbose_name=_('العنوان'))
    description = models.TextField(blank=True, verbose_name=_('الوصف'))
    duration_minutes = models.PositiveIntegerField(default=30, verbose_name=_('المدة (دقيقة)'))
    is_active = models.BooleanField(default=False, verbose_name=_('نشط'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['group', 'is_active'], name='exam_group_active_idx'),
        ]

    def total_marks(self):
        """
        إجمالي درجات الامتحان.
        استخدم annotate() في QuerySet لتجنب N+1:
          Exam.objects.annotate(total=Sum('questions__marks'))
        """
        # fallback لو لم يُستخدم annotate
        result = self.questions.aggregate(total=Sum('marks'))
        return result['total'] or 0

    def __str__(self):
        return self.title


class Question(models.Model):
    ANSWER_CHOICES = (('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'))

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField(verbose_name=_('نص السؤال'))
    image = models.ImageField(upload_to='questions/', blank=True, null=True, verbose_name=_('صورة توضيحية'))
    option_a = models.CharField(max_length=200, verbose_name=_('اختيار A'))
    option_b = models.CharField(max_length=200, verbose_name=_('اختيار B'))
    option_c = models.CharField(max_length=200, verbose_name=_('اختيار C'))
    option_d = models.CharField(max_length=200, verbose_name=_('اختيار D'))
    correct_answer = models.CharField(max_length=1, choices=ANSWER_CHOICES, verbose_name=_('الإجابة الصحيحة'))
    marks = models.PositiveIntegerField(default=1, verbose_name=_('الدرجة'))

    def __str__(self):
        return self.text[:50]


class ExamResult(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='exam_results')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    score = models.PositiveIntegerField(verbose_name=_('الدرجة'))
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'exam')
        indexes = [
            models.Index(fields=['student', 'exam'], name='examresult_student_exam_idx'),
        ]

    def __str__(self):
        return f"{self.student} — {self.exam.title}: {self.score}"