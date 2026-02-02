from rest_framework import serializers
from .models import TeacherProfile, Group, CoursePackage

# 1. مترجم بيانات المعلم
class TeacherSerializer(serializers.ModelSerializer):
    # نجيب الاسم من اليوزر المرتبط
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    subject_name = serializers.CharField(source='subject.name', default="") 

    class Meta:
        model = TeacherProfile
        fields = ['id', 'first_name', 'last_name', 'bio', 'subject_name', 'image']

# 2. مترجم الحزم
class PackageSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.user.first_name')
    
    class Meta:
        model = CoursePackage
        fields = ['id', 'title', 'description', 'price', 'image', 'teacher_name']