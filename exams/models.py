from django.db import models
from django.utils.translation import gettext_lazy as _
from teachers.models import Group
from accounts.models import StudentProfile

class Exam(models.Model):
    # السطر الأول
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='exams', null=True, blank=True)    
    # السطر الثاني (يجب أن يكون في سطر جديد)
    title = models.CharField(max_length=200, verbose_name=_('العنوان'))    
    description = models.TextField(blank=True, verbose_name=_('الوصف'))
    duration_minutes = models.PositiveIntegerField(default=30, verbose_name=_('المدة (دقيقة)'))
    is_active = models.BooleanField(default=False, verbose_name=_('نشط'))
    created_at = models.DateTimeField(auto_now_add=True)

    def total_marks(self):
        return sum(q.marks for q in self.questions.all())

class Question(models.Model):
    ANSWER_CHOICES = (('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'))
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField(verbose_name=_('نص السؤال'))
    image = models.ImageField(upload_to='questions/', blank=True, null=True, verbose_name=_('صورة توضيحية'))
    option_a = models.CharField(max_length=200, verbose_name=_('اختار A'))
    option_b = models.CharField(max_length=200, verbose_name=_('اختار B'))
    option_c = models.CharField(max_length=200, verbose_name=_('اختار C'))
    option_d = models.CharField(max_length=200, verbose_name=_('اختار D'))
    correct_answer = models.CharField(max_length=1, choices=ANSWER_CHOICES, verbose_name=_('الإجابة الصحيحة'))
    marks = models.PositiveIntegerField(default=1, verbose_name=_('الدرجة'))

class ExamResult(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='exam_results')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    score = models.PositiveIntegerField(verbose_name=_('الدرجة'))
    submitted_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('student', 'exam')