from rest_framework import serializers
from .models import Enrollment, PackageEnrollment
from teachers.models import Group, CoursePackage, TeacherProfile
from django.contrib.auth import get_user_model
from teachers.models import Lecture
from exams.models import Exam
User = get_user_model()

# تسلسل متداخل (Nested) لجلب بيانات المعلم والمجموعة
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone']

class TeacherSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = TeacherProfile
        fields = ['user', 'subject', 'image'] # تأكد من subject

class GroupSerializer(serializers.ModelSerializer):
    teacher = TeacherSerializer()
    grade_display = serializers.CharField(source='get_grade_display') # لجلب اسم الصف
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'teacher', 'grade_display']

class EnrollmentSerializer(serializers.ModelSerializer):
    group = GroupSerializer()
    class Meta:
        model = Enrollment
        fields = ['id', 'group', 'joined_at']

# للحزم
class PackageSerializer(serializers.ModelSerializer):
    teacher = TeacherSerializer()
    class Meta:
        model = CoursePackage
        fields = ['id', 'title', 'price', 'image', 'teacher']

class PackageEnrollmentSerializer(serializers.ModelSerializer):
    package = PackageSerializer()
    class Meta:
        model = PackageEnrollment
        fields = ['id', 'package', 'joined_at']

class LectureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lecture
        fields = ['id', 'title', 'description', 'video_link', 'created_at']

class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ['id', 'title', 'duration_minutes', 'total_marks'] # total_marks تحتاج لدالة في الموديل

from teachers.models import PDFFile

class PDFSerializer(serializers.ModelSerializer):
    class Meta:
        model = PDFFile
        fields = ['id', 'title', 'link', 'created_at']