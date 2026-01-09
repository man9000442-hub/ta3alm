from django import forms
from django.core.exceptions import ValidationError
from .models import User, StudentProfile
from teachers.models import TeacherProfile
from assistants.models import AssistantProfile

# ==========================================
# دالة مساعدة للتحقق من رقم الهاتف (لعدم تكرار الكود)
# ==========================================
def validate_egyptian_phone(value):
    if not value:
        return value
    if not value.isdigit():
        raise ValidationError("رقم الهاتف يجب أن يحتوي على أرقام فقط.")
    if len(value) < 11:
        raise ValidationError("رقم الهاتف يجب ألا يقل عن 11 رقماً.")
    return value

# ==========================================
# 1. فورم استكمال بيانات الطالب
# ==========================================
class CompleteStudentProfileForm(forms.ModelForm):
    full_name = forms.CharField(
        label='الاسم رباعي (باللغة العربية)',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اكتب اسمك رباعياً هنا'})
    )
    
    national_id = forms.CharField(
        label='الرقم القومي',
        max_length=14,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '14 رقم'})
    )

    phone = forms.CharField(
        label='رقم هاتفك الشخصي',
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '01xxxxxxxxx'})
    )

    parent_phone = forms.CharField(
        max_length=15, 
        label='رقم ولي الأمر',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '01xxxxxxxxx'})
    )

    # +++++ حقول الباسورد الجديدة +++++
    password = forms.CharField(
        label='كلمة المرور',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '******'}),
        required=True
    )
    confirm_password = forms.CharField(
        label='تأكيد كلمة المرور',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '******'}),
        required=True
    )
    # +++++++++++++++++++++++++++++++



    class Meta:
        model = User
        fields = ['national_id', 'phone']

    # التحقق من الرقم القومي
    def clean_national_id(self):
        nid = self.cleaned_data.get('national_id')
        if not nid: return nid
        if len(nid) != 14 or not nid.isdigit():
            raise ValidationError("الرقم القومي يجب أن يكون 14 رقماً صحيحاً.")
        return nid


    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirm_password")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("كلمتا المرور غير متطابقتين.")
        return cleaned_data

    # التحقق من رقم الطالب
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        return validate_egyptian_phone(phone)

    # التحقق من رقم ولي الأمر
    def clean_parent_phone(self):
        phone = self.cleaned_data.get('parent_phone')
        return validate_egyptian_phone(phone)

from core.models import Subject
# ==========================================
# 2. فورم استكمال بيانات المعلم
# ==========================================
class CompleteTeacherProfileForm(forms.ModelForm):
    full_name = forms.CharField(
        label='الاسم ثلاثي أو رباعي',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الاسم الذي سيظهر للطلاب'})
    )

    national_id = forms.CharField(
        label='الرقم القومي',
        max_length=14,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '14 رقم'})
    )

    phone = forms.CharField(
        label='رقم الهاتف',
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '01xxxxxxxxx'})
    )

    bio = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'اكتب نبذة مختصرة...'}), 
        label='نبذة مختصرة عنك',
        required=False
    )
    
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(), # جلب كل المواد
        label='المادة التي تدرسها',
        required=True,
        empty_label="-- اختر المادة --",
        widget=forms.Select(attrs={'class': 'form-select'}) # تنسيق Bootstrap
    )


    # +++++ حقول الباسورد الجديدة +++++
    password = forms.CharField(
        label='كلمة المرور',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '******'}),
        required=True
    )
    confirm_password = forms.CharField(
        label='تأكيد كلمة المرور',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '******'}),
        required=True
    )
    # +++++++++++++++++++++++++++++++


    class Meta:
        model = User
        fields = ['national_id', 'phone']

    def clean_national_id(self):
        nid = self.cleaned_data.get('national_id')
        if not nid: return nid
        if len(nid) != 14 or not nid.isdigit():
            raise ValidationError("الرقم القومي يجب أن يكون 14 رقماً صحيحاً.")
        return nid

    # التحقق من رقم المعلم
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        return validate_egyptian_phone(phone)
    
    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirm_password")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("كلمتا المرور غير متطابقتين.")
        return cleaned_data

# ==========================================
# 3. فورم استكمال بيانات المساعد
# ==========================================
class CompleteAssistantProfileForm(forms.ModelForm):
    full_name = forms.CharField(
        label='الاسم ثلاثي أو رباعي',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسمك بالكامل'})
    )

    phone = forms.CharField(
        label='رقم الهاتف',
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '01xxxxxxxxx'})
    )

        # +++++ أضف هذا الحقل +++++
    national_id = forms.CharField(
        label='الرقم القومي',
        max_length=14,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '14 رقم'})
    )
    # +++++++++++++++++++++++++

    # +++++ حقول الباسورد الجديدة +++++
    password = forms.CharField(
        label='كلمة المرور',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '******'}),
        required=True
    )
    confirm_password = forms.CharField(
        label='تأكيد كلمة المرور',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '******'}),
        required=True
    )
    # +++++++++++++++++++++++++++++++


    class Meta:
        model = User
        fields = ['national_id', 'phone']


    def clean_national_id(self):
        nid = self.cleaned_data.get('national_id')
        if not nid: return nid
        if len(nid) != 14 or not nid.isdigit():
            raise forms.ValidationError("الرقم القومي يجب أن يكون 14 رقماً صحيحاً.")
        return nid

    # التحقق من رقم المساعد
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        return validate_egyptian_phone(phone)
    

    
    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirm_password")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("كلمتا المرور غير متطابقتين.")
        return cleaned_data