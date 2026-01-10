# assistants/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from teachers.models import TeacherProfile
from .models import AssistantProfile,AssistantJob
from django.db.models import Q
from core.models import Subject

@login_required
def view_teacher_groups(request, teacher_id):
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    assistant_profile = request.user.assistant_profile
    
    # 1. التحقق من الصلاحية
    is_authorized = AssistantJob.objects.filter(
        assistant=assistant_profile, teacher=teacher, is_active=True
    ).exists()
    if not is_authorized:
        return redirect('assistant_dashboard')

    # 2. جلب المجموعات (للعرض)
    groups = teacher.groups.all().order_by('-created_at')

    # 3. حساب المسموح (Allowed IDs)
    allowed_ids = []
    
    if teacher.has_active_subscription():
        # نحدد الحد من الباقة (أو 5 افتراضي لو مفيش باقة)
        limit = teacher.current_plan.group_limit if teacher.current_plan else 5
        
        # نأخذ أقدم [limit] مجموعات
        # مثال: لو الحد 2، نأخذ أقدم مجموعتين ونعتبرهم مسموحين
        # الباقي (الأحدث) سيظهر لكنه مغلق
        allowed_ids = list(teacher.groups.all().order_by('created_at').values_list('id', flat=True)[:limit])
    
    # (لو الاشتراك منتهي، القائمة تظل فارغة [] وكله مغلق)

    return render(request, 'assistants/teacher_groups.html', {
        'teacher': teacher, 
        'groups': groups, 
        'allowed_ids': allowed_ids
    })


@login_required
def assistant_dashboard(request):
    # حماية: التأكد أن المستخدم مساعد
    if request.user.role != 'assistant':
        return redirect('home')
    
        # +++++ التحقق الصارم +++++
    # إذا لم يكن لديه بروفايل مساعد، نطرده لصفحة الإكمال
    if not hasattr(request.user, 'assistant_profile'):
        return redirect('complete_profile')
    # ++++++++++++++++++++++++
        # تحقق إضافي داخل الداشبورد نفسها
    if not hasattr(request.user, 'assistant_profile') or not request.user.assistant_profile.phone:
        return redirect('complete_profile')

    
    assistant = request.user.assistant_profile
    
    # التأكد من وجود بروفايل للمساعد (أو إنشاؤه لو مش موجود)
    assistant, created = AssistantProfile.objects.get_or_create(user=request.user)
    
    # جلب الوظائف (العلاقات مع المعلمين)
    # 1. الوظائف النشطة (تم القبول)
    active_jobs = assistant.jobs.filter(is_active=True).select_related('teacher__user')
    
    # 2. الطلبات المعلقة (قيد الانتظار)
    pending_jobs = assistant.jobs.filter(is_active=False).select_related('teacher__user')

    context = {
        'active_jobs': active_jobs,
        'pending_jobs': pending_jobs
    }
    return render(request, 'assistants/dashboard.html', context)






from .models import AssistantProfile, AssistantJob
from teachers.models import TeacherProfile

# ==========================================
# 1. لوحة تحكم المساعد (Dashboard)
# ==========================================
# @login_required
# def assistant_dashboard(request):
#     if request.user.role != 'assistant':
#         return redirect('home')
    
#     # التأكد من وجود بروفايل
#     assistant, created = AssistantProfile.objects.get_or_create(user=request.user)
    
#     # جلب الوظائف
#     active_jobs = assistant.jobs.filter(is_active=True).select_related('teacher__user')
#     pending_jobs = assistant.jobs.filter(is_active=False).select_related('teacher__user')

#     context = {
#         'active_jobs': active_jobs,
#         'pending_jobs': pending_jobs
#     }
#     return render(request, 'assistants/dashboard.html', context)


# ==========================================
# 2. البحث عن معلم وإرسال طلب (Find Teacher)
# ==========================================
@login_required
def find_teacher(request):
    if request.user.role != 'assistant':
        return redirect('home')
        
    query = request.GET.get('q')
    teachers = TeacherProfile.objects.select_related('user').all().order_by('-id')
    subjects = Subject.objects.all()    


    q_subject = request.GET.get('subject')
    if q_subject:
        teachers = teachers.filter(subject__id=q_subject)

    # منطق البحث
    if query:
        teachers = TeacherProfile.objects.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__phone__icontains=query) |
            Q(user__custom_id__icontains=query) | 
            # أضف __name
            Q(subject__name__icontains=query)
        )

    # منطق إرسال الطلب (POST)
    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        teacher = get_object_or_404(TeacherProfile, id=teacher_id)
        assistant, _ = AssistantProfile.objects.get_or_create(user=request.user)
        
        # إنشاء الطلب (مع تجنب التكرار using get_or_create)
        obj, created = AssistantJob.objects.get_or_create(
            assistant=assistant,
            teacher=teacher
        )
        
        if created:
            messages.success(request, f"تم إرسال طلب الانضمام للمستر {teacher.user.first_name} بنجاح.")
        else:
            messages.info(request, "لقد أرسلت طلباً لهذا المعلم من قبل وهو قيد الانتظار أو مقبول.")
            
        return redirect('assistant_dashboard')

    return render(request, 'assistants/find_teacher.html', {'teachers': teachers, 'query': query,'subjects': subjects})


# ==========================================
# 3. عرض مجموعات المعلم (View Teacher Groups)
# ==========================================


@login_required
def assistant_view_packages(request, teacher_id):
    if request.user.role != 'assistant': return redirect('home')
    
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    assistant = request.user.assistant_profile
    
    # التأكد من العلاقة والصلاحية
    job = AssistantJob.objects.filter(assistant=assistant, teacher=teacher, is_active=True).first()
    if not job or not job.can_manage_packages:
        messages.error(request, "ليس لديك صلاحية لإدارة الحزم.")
        return redirect('assistant_dashboard')

    packages = teacher.packages.all().order_by('-created_at')
    
    # نستخدم نفس تيمبلت المعلم ولكن نخفي بعض الأزرار إذا أردت، أو ننشئ واحداً جديداً
    # للأسهل: نستخدم تيمبلت جديد بسيط للمساعد
    return render(request, 'assistants/teacher_packages.html', {'packages': packages, 'teacher': teacher})


from teachers.forms import GroupForm # استيراد

@login_required
def create_group_for_teacher(request, teacher_id):
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    assistant = request.user.assistant_profile
    
    # التأكد من الصلاحية (هل هو مساعد؟)
    # ملاحظة: يمكن إضافة صلاحية جديدة "can_create_groups" لو أردت دقة أكثر
    if not AssistantJob.objects.filter(assistant=assistant, teacher=teacher, is_active=True).exists():
        return redirect('home')

    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            # التحقق من حد الباقة للمعلم
            if teacher.current_plan and teacher.groups.count() >= teacher.current_plan.group_limit:
                messages.error(request, "لا يمكن إنشاء مجموعة. المعلم تجاوز حد الباقة.")
                return redirect('view_teacher_groups', teacher_id=teacher.id)

            group = form.save(commit=False)
            group.teacher = teacher # ربط المجموعة بالمعلم
            group.save()
            messages.success(request, f"تم إنشاء مجموعة '{group.name}' للمعلم.")
            return redirect('view_teacher_groups', teacher_id=teacher.id)
            
    # لو GET، لا نعرض صفحة، بل نعتمد على المودال في الصفحة السابقة
    return redirect('view_teacher_groups', teacher_id=teacher.id)