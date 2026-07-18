from .models import AssistantJob
from django import forms

class AssistantPermissionsForm(forms.ModelForm):
    class Meta:
        model = AssistantJob
        fields = ['can_manage_students', 'can_manage_exams', 'can_manage_videos','can_manage_packages']
        labels = {
            'can_manage_students': 'إدارة الطلاب والغياب',
            'can_manage_exams': 'إدارة الامتحانات والأسئلة',
            'can_manage_videos': 'إدارة المحاضرات والفيديوهات',
            'can_manage_packages': 'إدارة الحزم والكورسات (Online)'
        }
        widgets = {
            'can_manage_students': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_exams': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_videos': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_packages': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }