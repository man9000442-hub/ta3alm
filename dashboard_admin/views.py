"""
dashboard_admin/views.py
لوحة تحكم الإدارة — منقولة من core وموسَّعة
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta

from teachers.models import TeacherProfile, PaymentTransaction, SubscriptionPlan, WithdrawRequest
from accounts.models import StudentProfile
from assistants.models import AssistantProfile
from students.models import PackageEnrollment
from core.models import SiteSetting

from .models import AdminProfile, AdminRole, AuditLog
from .decorators import admin_required, owner_required, finance_required, moderator_required
from .forms import (
    AdminUserEditForm, AdminTeacherEditForm,
    AdminStudentEditForm, AdminAssistantEditForm,
    AppointAdminForm,
)

User = get_user_model()


# ----------------------------------------------------------
# مساعد: يُعيد context الـ sidebar الموحَّد
# ----------------------------------------------------------
def _base_context(request):
    """Context مشترك لكل صفحات الإدارة (sidebar + صلاحيات)."""
    user = request.user
    profile = getattr(user, 'admin_profile', None)

    # جلب عدد الإشعارات غير المقروءة
    from core.models import Notification
    unread_count = Notification.objects.filter(recipient=user, is_read=False).count()

    from core.models import SiteSetting
    site_settings = SiteSetting.load()

    return {
        'admin_user':       user,
        'admin_profile':    profile,
        'is_owner':         user.is_superuser or (profile and profile.is_owner),
        'can_manage_users': user.is_superuser or (profile and profile.can_manage_users),
        'can_delete_users': user.is_superuser or (profile and profile.can_delete_users),
        'can_view_finance': user.is_superuser or (profile and profile.can_view_finance),
        'can_manage_plans': user.is_superuser or (profile and profile.can_manage_plans),
        'can_view_audit':   user.is_superuser or (profile and profile.can_view_audit_log),
        'unread_count':     unread_count,
        'site_settings':    site_settings,
    }



# ==========================================================
# 1. لوحة الإحصاءات الرئيسية (Dashboard)
# ==========================================================
@admin_required
def dashboard(request):
    ctx = _base_context(request)

    # إحصاءات
    ctx['total_teachers']   = TeacherProfile.objects.count()
    ctx['total_students']   = StudentProfile.objects.count()
    ctx['total_assistants'] = AssistantProfile.objects.count()

    # ✅ إصلاح N+1: استعلام واحد يستخدم filter بدلاً من Python loop
    ctx['active_teachers_count'] = TeacherProfile.objects.filter(
        subscription_end_date__gt=timezone.now()
    ).count()

    # آخر الأحداث
    ctx['recent_logs'] = AuditLog.objects.select_related('admin').order_by('-created_at')[:10]

    return render(request, 'admin_panel/dashboard.html', ctx)



# ==========================================================
# 2. تبديل وضع الصيانة
# ==========================================================
@owner_required
def toggle_maintenance(request):
    if request.method == 'POST':
        settings = SiteSetting.load()
        settings.is_maintenance_mode = not settings.is_maintenance_mode
        settings.save()
        status = "تفعيل" if settings.is_maintenance_mode else "إلغاء"
        AuditLog.log(request, AuditLog.ACTION_TOGGLE_MAINT,
                     details={'maintenance': settings.is_maintenance_mode})
        messages.warning(request, f"تم {status} وضع الصيانة.")
    return redirect('admin_panel:dashboard')


# ==========================================================
# 3. إدارة المستخدمين
# ==========================================================
@moderator_required
def manage_users(request):
    ctx = _base_context(request)

    query = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '')

    teachers   = TeacherProfile.objects.select_related('user', 'current_plan').order_by('-id')
    students   = StudentProfile.objects.select_related('user').order_by('-id')
    assistants = AssistantProfile.objects.select_related('user').order_by('-id')

    if query:
        q_filter = (
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)  |
            Q(user__email__icontains=query)       |
            Q(user__phone__icontains=query)
        )
        teachers   = teachers.filter(q_filter)
        students   = students.filter(q_filter | Q(parent_phone__icontains=query))
        assistants = assistants.filter(q_filter | Q(phone__icontains=query))

    ctx.update({
        'teachers':    teachers,
        'students':    students,
        'assistants':  assistants,
        'all_plans':   SubscriptionPlan.objects.all(),
        'query':       query,
        'role_filter': role_filter,
    })
    return render(request, 'admin_panel/manage_users.html', ctx)


# ==========================================================
# 4. إجراءات على المستخدم (حظر / رفع / حذف / تجديد)
# ==========================================================
@moderator_required
def user_action(request):
    if request.method != 'POST':
        return redirect('admin_panel:manage_users')

    user_id = request.POST.get('user_id')
    action  = request.POST.get('action')

    try:
        target = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "المستخدم غير موجود.")
        return redirect('admin_panel:manage_users')

    # حماية: لا يُمسّ المالك أو الـ superuser
    if target.is_superuser:
        messages.error(request, "لا يمكن التأثير على حساب المالك.")
        return redirect('admin_panel:manage_users')

    # حماية: المشرف لا يستطيع حذف مستخدمين
    requester_profile = getattr(request.user, 'admin_profile', None)
    can_delete = request.user.is_superuser or (requester_profile and requester_profile.can_delete_users)

    if action == 'ban':
        target.is_banned = True
        target.save(update_fields=['is_banned'])
        AuditLog.log(request, AuditLog.ACTION_BAN,
                     target_label=f"{target.get_full_name()} ({target.email})",
                     target_id=target.id)
        messages.warning(request, f"تم حظر {target.get_full_name() or target.email}.")

    elif action == 'unban':
        target.is_banned = False
        target.save(update_fields=['is_banned'])
        AuditLog.log(request, AuditLog.ACTION_UNBAN,
                     target_label=f"{target.get_full_name()} ({target.email})",
                     target_id=target.id)
        messages.success(request, f"تم رفع الحظر عن {target.get_full_name() or target.email}.")

    elif action == 'delete':
        if not can_delete:
            messages.error(request, "ليس لديك صلاحية حذف المستخدمين.")
        else:
            name = target.get_full_name() or target.email
            AuditLog.log(request, AuditLog.ACTION_DELETE,
                         target_label=name, target_id=target.id,
                         details={'role': target.role, 'email': target.email})
            target.delete()
            messages.error(request, f"تم حذف المستخدم «{name}» وجميع بياناته نهائياً.")

    elif action == 'renew_free':
        if not hasattr(target, 'teacher_profile'):
            messages.error(request, "هذا المستخدم ليس معلماً.")
        else:
            teacher  = target.teacher_profile
            plan_id  = request.POST.get('plan_id')
            if plan_id:
                plan = get_object_or_404(SubscriptionPlan, id=plan_id)
                teacher.current_plan = plan

            teacher.subscription_end_date = (
                teacher.subscription_end_date + timedelta(days=30)
                if teacher.has_active_subscription()
                else timezone.now() + timedelta(days=30)
            )
            teacher.save()
            AuditLog.log(request, AuditLog.ACTION_RENEW_SUB,
                         target_label=target.get_full_name(),
                         target_id=target.id,
                         details={'plan': teacher.current_plan.name if teacher.current_plan else '-'})
            messages.success(request, f"تم تجديد اشتراك {target.get_full_name()}.")

    return redirect('admin_panel:manage_users')


# ==========================================================
# 5. تعديل بيانات مستخدم
# ==========================================================
@moderator_required
def edit_user(request, user_id):
    ctx = _base_context(request)
    target = get_object_or_404(User, id=user_id)

    teacher_form = student_form = assistant_form = None

    if request.method == 'POST':
        user_form = AdminUserEditForm(request.POST, instance=target)

        if target.role == 'teacher' and hasattr(target, 'teacher_profile'):
            teacher_form = AdminTeacherEditForm(request.POST, instance=target.teacher_profile)
            if user_form.is_valid() and teacher_form.is_valid():
                user_form.save()
                teacher_form.save()
                AuditLog.log(request, AuditLog.ACTION_EDIT_USER,
                             target_label=target.get_full_name(), target_id=target.id)
                messages.success(request, "تم تعديل بيانات المعلم.")
                return redirect('admin_panel:manage_users')

        elif target.role == 'student' and hasattr(target, 'student_profile'):
            student_form = AdminStudentEditForm(request.POST, instance=target.student_profile)
            if user_form.is_valid() and student_form.is_valid():
                user_form.save()
                student_form.save()
                AuditLog.log(request, AuditLog.ACTION_EDIT_USER,
                             target_label=target.get_full_name(), target_id=target.id)
                messages.success(request, "تم تعديل بيانات الطالب.")
                return redirect('admin_panel:manage_users')

        elif target.role == 'assistant' and hasattr(target, 'assistant_profile'):
            assistant_form = AdminAssistantEditForm(request.POST, instance=target.assistant_profile)
            if user_form.is_valid() and assistant_form.is_valid():
                user_form.save()
                assistant_form.save()
                AuditLog.log(request, AuditLog.ACTION_EDIT_USER,
                             target_label=target.get_full_name(), target_id=target.id)
                messages.success(request, "تم تعديل بيانات المساعد.")
                return redirect('admin_panel:manage_users')
        else:
            if user_form.is_valid():
                user_form.save()
                messages.success(request, "تم التعديل.")
                return redirect('admin_panel:manage_users')
    else:
        user_form = AdminUserEditForm(instance=target)
        if target.role == 'teacher' and hasattr(target, 'teacher_profile'):
            teacher_form = AdminTeacherEditForm(instance=target.teacher_profile)
        elif target.role == 'student' and hasattr(target, 'student_profile'):
            student_form = AdminStudentEditForm(instance=target.student_profile)
        elif target.role == 'assistant' and hasattr(target, 'assistant_profile'):
            assistant_form = AdminAssistantEditForm(instance=target.assistant_profile)

    ctx.update({
        'target_user':    target,
        'user_form':      user_form,
        'teacher_form':   teacher_form,
        'student_form':   student_form,
        'assistant_form': assistant_form,
    })
    return render(request, 'admin_panel/edit_user.html', ctx)


# ==========================================================
# 6. التقارير المالية
# ==========================================================
@finance_required
def finance_report(request):
    ctx = _base_context(request)

    query = request.GET.get('q', '').strip()
    transactions = PaymentTransaction.objects.select_related('teacher__user').order_by('-date')

    if query:
        transactions = transactions.filter(
            Q(teacher__user__first_name__icontains=query) |
            Q(teacher__user__phone__icontains=query)       |
            Q(transaction_id__icontains=query)
        )

    total_revenue = transactions.aggregate(total=Sum('amount'))['total'] or 0

    ctx.update({
        'transactions': transactions,
        'total_revenue': total_revenue,
        'query': query,
    })
    return render(request, 'admin_panel/finance_report.html', ctx)


# ==========================================================
# 7. طلبات السحب
# ==========================================================
@finance_required
def withdrawals(request):
    ctx = _base_context(request)

    withdraw_requests = WithdrawRequest.objects.select_related(
        'wallet__teacher__user'
    ).order_by('-created_at')

    if request.method == 'POST':
        req_id = request.POST.get('req_id')
        req = get_object_or_404(WithdrawRequest, id=req_id)
        req.is_paid = True
        req.save()
        AuditLog.log(request, AuditLog.ACTION_PAY_WITHDRAW,
                     target_label=str(req), target_id=req.id,
                     details={'amount': str(req.amount)})
        messages.success(request, f"تم تسجيل تحويل {req.amount} EGP.")
        return redirect('admin_panel:withdrawals')

    ctx['requests'] = withdraw_requests
    return render(request, 'admin_panel/withdrawals.html', ctx)


# ==========================================================
# 8. مدفوعات الطلاب على الحزم
# ==========================================================
@finance_required
def student_payments(request):
    ctx = _base_context(request)

    payments = PackageEnrollment.objects.filter(
        is_paid=True
    ).select_related('student__user', 'package__teacher__user').order_by('-joined_at')

    # ✅ إصلاح N+1: aggregate بدلاً من sum في Python
    total_revenue = payments.aggregate(total=Sum('package__price'))['total'] or 0

    ctx.update({'payments': payments, 'total_revenue': total_revenue})
    return render(request, 'admin_panel/student_payments.html', ctx)


# ==========================================================
# 9. إدارة باقات الاشتراك
# ==========================================================
@owner_required
def manage_plans(request):
    ctx = _base_context(request)
    plans = SubscriptionPlan.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')

        def clean_int(val, default=0):
            try:
                return int(val)
            except (ValueError, TypeError):
                return default

        if action == 'add':
            plan = SubscriptionPlan.objects.create(
                name=request.POST.get('name', ''),
                price=clean_int(request.POST.get('price')),
                description=request.POST.get('desc', ''),
                student_limit=clean_int(request.POST.get('student_limit'), 1000),
                group_limit=clean_int(request.POST.get('group_limit'), 5),
                assistant_limit=clean_int(request.POST.get('assistant_limit'), 2),
                allow_online_packages=(request.POST.get('allow_online') == 'on'),
                allow_question_images=(request.POST.get('allow_images') == 'on'),
                is_default=(request.POST.get('is_default') == 'on'),
            )
            AuditLog.log(request, AuditLog.ACTION_ADD_PLAN,
                         target_label=plan.name, target_id=plan.id)
            messages.success(request, "تم إضافة الباقة.")

        elif action == 'edit':
            plan = get_object_or_404(SubscriptionPlan, id=request.POST.get('plan_id'))
            plan.name           = request.POST.get('name', '')
            plan.price          = clean_int(request.POST.get('price'))
            plan.description    = request.POST.get('desc', '')
            plan.student_limit  = clean_int(request.POST.get('student_limit'), 1000)
            plan.group_limit    = clean_int(request.POST.get('group_limit'), 5)
            plan.assistant_limit = clean_int(request.POST.get('assistant_limit'), 2)
            plan.allow_online_packages = (request.POST.get('allow_online') == 'on')
            plan.allow_question_images = (request.POST.get('allow_images') == 'on')
            plan.is_default     = (request.POST.get('is_default') == 'on')
            plan.save()
            AuditLog.log(request, AuditLog.ACTION_EDIT_PLAN,
                         target_label=plan.name, target_id=plan.id)
            messages.success(request, "تم تعديل الباقة.")

        elif action == 'delete':
            plan = get_object_or_404(SubscriptionPlan, id=request.POST.get('plan_id'))
            name = plan.name
            AuditLog.log(request, AuditLog.ACTION_DELETE_PLAN,
                         target_label=name, target_id=plan.id)
            plan.delete()
            messages.warning(request, f"تم حذف الباقة «{name}».")

        return redirect('admin_panel:manage_plans')

    ctx['plans'] = plans
    return render(request, 'admin_panel/manage_plans.html', ctx)


# ==========================================================
# 10. سجل الأحداث (Audit Log)
# ==========================================================
@owner_required
def audit_log(request):
    ctx = _base_context(request)

    logs = AuditLog.objects.select_related('admin').order_by('-created_at')

    action_filter = request.GET.get('action', '')
    if action_filter:
        logs = logs.filter(action=action_filter)

    ctx.update({
        'logs':           logs[:200],
        'action_choices': AuditLog.ACTION_CHOICES,
        'action_filter':  action_filter,
    })
    return render(request, 'admin_panel/audit_log.html', ctx)


# ==========================================================
# 11. إدارة فريق الإدارة (Staff Management)
# ==========================================================
@owner_required
def manage_staff(request):
    ctx = _base_context(request)

    staff_list = AdminProfile.objects.select_related('user', 'appointed_by').order_by('admin_role')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'appoint':
            form = AppointAdminForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data['user_email']
                try:
                    target = User.objects.get(email=email)
                    if target.is_superuser:
                        messages.error(request, "المالك لا يحتاج لبروفايل إداري.")
                    else:
                        target.role = 'admin'
                        target.save(update_fields=['role'])
                        AdminProfile.objects.update_or_create(
                            user=target,
                            defaults={
                                'admin_role':      form.cleaned_data['admin_role'],
                                'notes':           form.cleaned_data.get('notes', ''),
                                'is_active_admin': True,
                                'appointed_by':    request.user,
                            }
                        )
                        AuditLog.log(request, AuditLog.ACTION_APPOINT_ADMIN,
                                     target_label=target.get_full_name() or email,
                                     target_id=target.id,
                                     details={'role': form.cleaned_data['admin_role']})
                        messages.success(request, f"تم تعيين {target.get_full_name() or email} كمسؤول.")
                except User.DoesNotExist:
                    messages.error(request, "لا يوجد مستخدم بهذا البريد الإلكتروني.")
            else:
                messages.error(request, "بيانات غير صحيحة.")

        elif action == 'remove':
            profile_id = request.POST.get('profile_id')
            profile = get_object_or_404(AdminProfile, id=profile_id)
            name = profile.user.get_full_name() or profile.user.email
            profile.user.role = 'student'   # إعادة لدور افتراضي محايد
            profile.user.save(update_fields=['role'])
            AuditLog.log(request, AuditLog.ACTION_REMOVE_ADMIN,
                         target_label=name, target_id=profile.user.id)
            profile.delete()
            messages.warning(request, f"تم إزالة {name} من الفريق الإداري.")

        return redirect('admin_panel:manage_staff')

    ctx.update({
        'staff_list':    staff_list,
        'appoint_form':  AppointAdminForm(),
        'admin_roles':   AdminRole.choices,
    })
    return render(request, 'admin_panel/manage_staff.html', ctx)
