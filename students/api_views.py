from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Enrollment, PackageEnrollment
from .serializers import EnrollmentSerializer, PackageEnrollmentSerializer # سننشئهم حالاً
from django.shortcuts import get_object_or_404
from teachers.models import Lecture
from exams.models import Exam
from .serializers import LectureSerializer, ExamSerializer
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_groups_api(request):
    print(f"DEBUG API: User is {request.user.username} (ID: {request.user.id})") # <---
    
    enrollments = Enrollment.objects.filter(student__user=request.user, is_active=True)
    print(f"DEBUG API: Found {enrollments.count()} enrollments") # <---
    
    serializer = EnrollmentSerializer(enrollments, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_packages_api(request):
    enrollments = PackageEnrollment.objects.filter(student__user=request.user, is_paid=True)
    serializer = PackageEnrollmentSerializer(enrollments, many=True)
    return Response(serializer.data)

from teachers.models import Lecture
from exams.models import Exam
from .serializers import LectureSerializer, ExamSerializer,PDFSerializer # سننشئهم

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def group_content_api(request, group_id):
    # التحقق من الاشتراك (مهم للأمان)
    enrollment = get_object_or_404(Enrollment, student__user=request.user, group_id=group_id, is_active=True)
    group = enrollment.group
    
    lectures = group.lectures.filter(is_active=True).order_by('-created_at')
    exams = group.exams.filter(is_active=True).order_by('-created_at')
    pdfs = group.pdfs.all().order_by('-created_at') # <--- جلب الملفات
    return Response({
        'lectures': LectureSerializer(lectures, many=True).data,
        'exams': ExamSerializer(exams, many=True).data,
        'pdfs': PDFSerializer(pdfs, many=True).data # <--- إرسالها
    })