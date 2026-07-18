"""
core/views.py — الصفحات العامة للمنصة
(تم نقل كل views الإدارة إلى dashboard_admin/views.py)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from teachers.models import TeacherProfile
from core.models import Subject, Notification


# ==========================================================
# 1. الصفحة الرئيسية
# ==========================================================
def home(request):
    teachers = (
        TeacherProfile.objects
        .select_related('user', 'subject')
        .filter(user__is_banned=False)
        .order_by('-id')
    )
    subjects = Subject.objects.all()

    q_grade   = request.GET.get('grade', '')
    q_subject = request.GET.get('subject', '')

    if q_subject:
        teachers = teachers.filter(subject__id=q_subject)
    if q_grade:
        teachers = teachers.filter(groups__grade=q_grade).distinct()

    return render(request, 'home.html', {
        'teachers': teachers[:6],
        'subjects': subjects,
    })


# ==========================================================
# 2. توجيه صفحة التسجيل (اختيار الدور)
# ==========================================================
def signup_redirect(request, role):
    VALID_ROLES = {'student', 'teacher', 'assistant'}
    if role in VALID_ROLES:
        request.session['selected_role'] = role

    role_names = {
        'student':   'طالب',
        'teacher':   'معلم',
        'assistant': 'مساعد',
    }
    return render(request, 'account/role_signup.html', {
        'role':      role,
        'role_name': role_names.get(role, 'مستخدم'),
    })


# ==========================================================
# 3. التوجيه الذكي بعد تسجيل الدخول
# ==========================================================
@login_required
def custom_login_redirect(request):
    user = request.user

    # ✅ المالك والأدمن → لوحة الإدارة
    if user.is_superuser or user.role == 'admin':
        return redirect('admin_panel:dashboard')

    # لو ما عندوش كود → يكمل بياناته
    if not user.custom_id:
        return redirect('complete_profile')

    # ✅ التوجيه حسب الدور
    ROLE_REDIRECTS = {
        'student':   'student_dashboard',
        'teacher':   'teacher_dashboard',
        'assistant': 'assistant_dashboard',
    }

    if user.role == 'assistant':
        if not hasattr(user, 'assistant_profile') or not user.assistant_profile.phone:
            return redirect('complete_profile')

    target = ROLE_REDIRECTS.get(user.role)
    if target:
        return redirect(target)

    # دور 'center' أو دور غير معروف → الرئيسية مع رسالة توضيح
    from django.contrib import messages
    messages.info(request, "لوحة التحكم الخاصة بك قيد التطوير.")
    return redirect('home')


# ==========================================================
# 4. صفحة الحظر
# ==========================================================
def banned_page(request):
    return render(request, 'core/banned.html')


# ==========================================================
# 5. الإشعارات
# ==========================================================
@login_required
def read_notification(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notif.is_read = True
    notif.save(update_fields=['is_read'])

    if notif.link:
        return redirect(notif.link)
    return redirect('all_notifications')


@login_required
def all_notifications(request):
    notifs = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'core/notifications.html', {'notifs': notifs})


# ==========================================================
# 6. دليل المنصة
# ==========================================================
def platform_guide(request):
    return render(request, 'core/guide.html')