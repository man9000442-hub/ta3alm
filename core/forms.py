from django import forms
from django.contrib.auth import get_user_model
from teachers.models import TeacherProfile
from accounts.models import StudentProfile
from assistants.models import AssistantProfile
User = get_user_model()

# 1. فورم البيانات الأساسية (لأي مستخدم)
class OwnerUserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'national_id', 'custom_id']
        labels = {
            'first_name': 'الاسم الأول',
            'last_name': 'الاسم الأخير',
            'email': 'البريد الإلكتروني',
            'phone': 'رقم الهاتف',
            'national_id': 'الرقم القومي',
            'custom_id': 'الكود التعريفي (ID)'
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control'}),
            'custom_id': forms.TextInput(attrs={'class': 'form-control'}),
        }

# 2. فورم بيانات المعلم الإضافية
class OwnerTeacherEditForm(forms.ModelForm):
    # حقل التاريخ بتصميم HTML5 Date Picker
    subscription_end_date = forms.DateTimeField(
        label='تاريخ انتهاء الاشتراك',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    class Meta:
        model = TeacherProfile
        fields = ['subject', 'bio', 'subscription_end_date']
        labels = {
            'subject': 'المادة الدراسية',
            'bio': 'نبذة عن المعلم',
        }
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

# 3. فورم بيانات الطالب الإضافية
class OwnerStudentEditForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['parent_phone']
        labels = {
            'parent_phone': 'رقم ولي الأمر',
        }
        widgets = {
            'parent_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }



class OwnerAssistantEditForm(forms.ModelForm):
    class Meta:
        model = AssistantProfile
        fields = ['phone']
        labels = {'phone': 'رقم الهاتف'}
        widgets = {'phone': forms.TextInput(attrs={'class': 'form-control'})}