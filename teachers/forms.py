from django import forms
# from .models import Group
from .models import Group, Lecture # <--- تأكد من استيراد Lecture
from django import forms
from .models import Group, Lecture, CoursePackage, TeacherProfile # <--- تأكد من وجود Lecture
from exams.models import Exam # <--- هذا هو السطر الناقص
from .models import TeacherProfile
from accounts.models import User
from core.models import Subject
from .models import PDFFile

class PDFForm(forms.ModelForm):
    class Meta:
        model = PDFFile
        fields = ['title', 'link']
        labels = {'title': 'اسم الملف', 'link': 'رابط التحميل'}
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Google Drive / MediaFire'}),
        }

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'grade']
        labels = {
            'name': 'اسم المجموعة (مثال: سبت وثلاثاء 2 ظهراً)',
            'grade': 'الصف الدراسي',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اكتب اسماً مميزاً للمجموعة'}),
            'grade': forms.Select(attrs={'class': 'form-select'}),
        }





# ... (GroupForm القديم) ...

class LectureForm(forms.ModelForm):
    class Meta:
        model = Lecture
        fields = ['title', 'video_link', 'description']
        labels = {
            'title': 'عنوان المحاضرة',
            'video_link': 'رابط الفيديو (Youtube)',
            'description': 'وصف أو ملاحظات',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: شرح الدرس الأول - النحو'}),
            'video_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://youtube.com/...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            
        }



class TeacherSettingsForm(forms.ModelForm):
    # حقول من جدول User
    first_name = forms.CharField(label='الاسم الأول', widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label='الاسم الأخير', widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    # حقول من جدول TeacherProfile
    bio = forms.CharField(label='نبذة عنك', widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=False)
    # +++++ تعريف الحقل صراحة +++++
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        label='المادة الدراسية',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    # +++++++++++++++++++++++++++++

    class Meta:
        model = TeacherProfile
        # الحقول التي سنعدلها في البروفايل
        fields = ['image', 'bio', 'subject'] 
        
        labels = {
            'image': 'صورة البروفايل',
            'bio': 'نبذة عنك',
            'subject': 'المادة الدراسية'
        }
        
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            # المادة كقائمة منسدلة
            'subject': forms.Select(attrs={'class': 'form-select'}), 
        }


from .models import CoursePackage

class CoursePackageForm(forms.ModelForm):
    class Meta:
        model = CoursePackage
        fields = ['title', 'grade','description', 'price', 'view_limit', 'image', 'lectures', 'exams']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'view_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            # سنستخدم CheckboxSelectMultiple للاختيار المتعدد
            'lectures': forms.CheckboxSelectMultiple(),
            'exams': forms.CheckboxSelectMultiple(),
            'grade': forms.Select(attrs={'class': 'form-select', 'id': 'packageGrade'}), # id للسكربت
        }

    def __init__(self, user, *args, **kwargs):
        super(CoursePackageForm, self).__init__(*args, **kwargs)

        self.fields['lectures'].required = False
        self.fields['exams'].required = False
        # فلترة المحتوى ليظهر فقط محتوى المعلم الحالي
        if user:
            self.fields['lectures'].queryset = Lecture.objects.filter(group__teacher__user=user)
            self.fields['exams'].queryset = Exam.objects.filter(group__teacher__user=user)