from django import forms
from .models import Exam, Question

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['title', 'description', 'duration_minutes', 'is_active']
        labels = {
            'title': 'عنوان الامتحان',
            'description': 'تعليمات للطالب',
            'duration_minutes': 'المدة (دقائق)',
            'is_active': 'نشر الامتحان فوراً؟'
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        # +++++ تأكد من وجود 'image' في هذه القائمة +++++
        fields = ['text', 'image', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'marks']
        # +++++++++++++++++++++++++++++++++++++++++++++++
        
        labels = {
            'text': 'نص السؤال',
            'image': 'صورة توضيحية (اختياري)', # <--- العنوان
            'correct_answer': 'الإجابة الصحيحة',
            'marks': 'الدرجة'
        }
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'image': forms.FileInput(attrs={'class': 'form-control'}), # <--- أداة رفع الملفات
            'option_a': forms.TextInput(attrs={'class': 'form-control bg-light', 'placeholder': 'الإجابة A'}),
            'option_b': forms.TextInput(attrs={'class': 'form-control bg-light', 'placeholder': 'الإجابة B'}),
            'option_c': forms.TextInput(attrs={'class': 'form-control bg-light', 'placeholder': 'الإجابة C'}),
            'option_d': forms.TextInput(attrs={'class': 'form-control bg-light', 'placeholder': 'الإجابة D'}),
            'correct_answer': forms.Select(attrs={'class': 'form-select'}),
            'marks': forms.NumberInput(attrs={'class': 'form-control'}),
        }