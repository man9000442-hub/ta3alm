from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.db.models import Q
from assistants.models import AssistantProfile
from teachers.models import TeacherProfile, PaymentTransaction
from accounts.models import StudentProfile
from teachers.models import SubscriptionPlan
# تعريف موديل المستخدم
User = get_user_model()

# ==========================================
# 1. الصفحات العامة
# ==========================================

from core.models import Subject

def home(request):
    teachers = TeacherProfile.objects.select_related('user', 'subject').all().order_by('-id')
    subjects = Subject.objects.all() # للقائمة المنسدلة
    
    # الفلترة
    q_grade = request.GET.get('grade')
    q_subject = request.GET.get('subject')
    
    if q_subject:
        teachers = teachers.filter(subject__id=q_subject)
    
    if q_grade:
        # نفلتر المعلمين الذين لديهم مجموعات في هذا الصف
        teachers = teachers.filter(groups__grade=q_grade).distinct()

    return render(request, 'home.html', {
        'teachers': teachers[:6], # عرض أول 6 فقط
        'subjects': subjects
    })


def signup_redirect(request, role):
    if role in ['student', 'teacher', 'assistant']:
        request.session['selected_role'] = role
    
    role_names = {'student': 'طالب', 'teacher': 'معلم', 'assistant': 'مساعد'}
    role_arabic = role_names.get(role, 'مستخدم')

    return render(request, 'account/role_signup.html', {
        'role': role, 
        'role_name': role_arabic
    })

def banned_page(request):
    return render(request, 'core/banned.html')

# ==========================================
# 2. التوجيه الذكي بعد الدخول
# ==========================================
@login_required
def custom_login_redirect(request):
    user = request.user
    
    if user.is_superuser:
        return redirect('owner_dashboard')

    # +++++ التحقق الصارم قبل التوجيه +++++
    # لو ما عندوش كود، يروح يكمل
    if not user.custom_id:
        return redirect('complete_profile')

    # لو مساعد وما عندوش رقم تليفون، يروح يكمل (حتى لو عنده كود)
    if user.role == 'assistant':
        if not hasattr(user, 'assistant_profile') or not user.assistant_profile.phone:
            return redirect('complete_profile')
        return redirect('assistant_dashboard')
    # ++++++++++++++++++++++++++++++++++++
    
    if user.role == 'student':
        return redirect('student_dashboard')
    elif user.role == 'teacher':
        return redirect('teacher_dashboard')
    
    return redirect('home')

# ==========================================
# 3. لوحة المالك (Owner Dashboard)
# ==========================================
@login_required
def owner_dashboard(request):
    from .models import SiteSetting
    settings = SiteSetting.load()
    if request.method == 'POST' and request.POST.get('action') == 'toggle_maintenance':
        settings.is_maintenance_mode = not settings.is_maintenance_mode
        settings.save()
        status = "تفعيل" if settings.is_maintenance_mode else "إلغاء"
        messages.warning(request, f"تم {status} وضع الصيانة.")


    from django.utils import timezone
    from datetime import timedelta
    # حماية: فقط السوبر يوزر يدخل هنا
    if not request.user.is_superuser:
        return redirect('home')
    
    # أ) الإحصائيات العامة
    total_teachers = TeacherProfile.objects.count()
    total_students = StudentProfile.objects.count()
    total_assistants = AssistantProfile.objects.count() # <--- جديد
    # عدد الاشتراكات السارية (Active Subscription)
    active_teachers_count = len([t for t in TeacherProfile.objects.all() if t.has_active_subscription()])
    all_plans = SubscriptionPlan.objects.all()
    
    # ب) جلب القوائم
    teachers = TeacherProfile.objects.select_related('user').all().order_by('-id')
    students = StudentProfile.objects.select_related('user').all().order_by('-id')
    assistants = AssistantProfile.objects.select_related('user').all().order_by('-id')
    
    # ج) معالجة أزرار التحكم (حظر / فك حظر / حذف)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action') 
        
        try:
            target_user = User.objects.get(id=user_id)
            
            # حماية: لا يمكن للمالك حذف نفسه
            if target_user.is_superuser:
                messages.error(request, "لا يمكن حذف أو حظر المالك!")
            else:
                if action == 'ban':
                    target_user.is_banned = True
                    target_user.save()
                    messages.warning(request, f"تم حظر {target_user.first_name}")
                
                elif action == 'unban':
                    target_user.is_banned = False
                    target_user.save()
                    messages.success(request, f"تم رفع الحظر عن {target_user.first_name}")
                
                elif action == 'delete':
                    username = target_user.first_name
                    target_user.delete() # حذف نهائي من قاعدة البيانات
                    messages.error(request, f"تم حذف المستخدم {username} وجميع بياناته نهائياً.")
                # ++++++ كود التجديد المجاني (الجديد) ++++++
                elif action == 'renew_free':
                    if hasattr(target_user, 'teacher_profile'):
                        teacher = target_user.teacher_profile
                        
                        # استلام الباقة المختارة من المودال
                        plan_id = request.POST.get('plan_id')
                        if plan_id:
                            plan = get_object_or_404(SubscriptionPlan, id=plan_id)
                            teacher.current_plan = plan # تعيين الباقة
                        
                        # تمديد التاريخ
                        if teacher.has_active_subscription():
                            teacher.subscription_end_date += timedelta(days=30)
                        else:
                            teacher.subscription_end_date = timezone.now() + timedelta(days=30)
                        
                        teacher.save()
                        messages.success(request, f"تم تجديد اشتراك {target_user.first_name} على باقة {teacher.current_plan.name}.")                    
                    else:
                        messages.error(request, "هذا المستخدم ليس معلماً.")
                # ++++++++++++++++++++++++++++++++++++++++++        
        except User.DoesNotExist:
            messages.error(request, "مستخدم غير موجود.")
            
        return redirect('owner_dashboard')
    


    # 1. استقبال كلمة البحث
    query = request.GET.get('q')

    # 2. جلب القوائم الأساسية
    teachers = TeacherProfile.objects.select_related('user').all().order_by('-id')
    students = StudentProfile.objects.select_related('user').all().order_by('-id')
    assistants = AssistantProfile.objects.select_related('user').all().order_by('-id')
    # 3. تطبيق الفلتر إذا وجد بحث
    if query:
        # بحث في المعلمين (الاسم، الايميل، التليفون)
        teachers = teachers.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__phone__icontains=query)
        )
        
        # بحث في الطلاب (الاسم، الايميل، التليفون، ولي الأمر)
        students = students.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__phone__icontains=query) |
            Q(parent_phone__icontains=query)
        )

        assistants = assistants.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__phone__icontains=query) |
            Q(user__email__icontains=query) |
            Q(phone__icontains=query)
        )



    context = {
        'total_teachers': total_teachers,
        'total_students': total_students,
        'total_assistants':total_assistants,
        'active_teachers_count': active_teachers_count,
        'teachers': teachers,
        'students': students,
        'assistants': assistants,
        'query': query,
        'all_plans': all_plans,
        'site_settings':settings,
    }
    return render(request, 'core/owner_dashboard.html', context)


# ==========================================
# 4. صفحة التقارير المالية (Owner Payments)
# ==========================================
@login_required
def owner_payments(request):
    if not request.user.is_superuser:
        return redirect('home')
    
    # جلب جميع عمليات الدفع (الأحدث أولاً)
    transactions = PaymentTransaction.objects.select_related('teacher__user').all().order_by('-date')
    # ++++++ البحث ++++++
    query = request.GET.get('q')
    if query:
        transactions = transactions.filter(
            Q(teacher__user__first_name__icontains=query) |
            Q(teacher__user__phone__icontains=query) |
            Q(transaction_id__icontains=query) |
            Q(amount__icontains=query) # بحث بالمبلغ
        )
    # +++++++++++++++++++
    
    # حساب مجموع الإيرادات
    total_revenue = transactions.aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        'transactions': transactions,
        'total_revenue': total_revenue
    }
    return render(request, 'core/owner_payments.html', context)



from .forms import OwnerUserEditForm, OwnerTeacherEditForm, OwnerStudentEditForm, OwnerAssistantEditForm # <--- استيراد الفورمز

# ==========================================
# تعديل بيانات مستخدم (من لوحة المالك)
# ==========================================
# ==========================================
# تعديل بيانات مستخدم (من لوحة المالك)
# ==========================================
@login_required
def owner_edit_user(request, user_id):
    if not request.user.is_superuser:
        return redirect('home')
    
    target_user = get_object_or_404(User, id=user_id)
    
    # 1. تهيئة المتغيرات بـ None لتجنب خطأ UnboundLocalError
    teacher_form = None
    student_form = None
    assistant_form = None # <--- هذا هو المتغير الذي كان يسبب المشكلة

    if request.method == 'POST':
        # أ) حفظ البيانات الأساسية
        user_form = OwnerUserEditForm(request.POST, instance=target_user)
        
        # ب) حفظ البيانات الفرعية حسب الدور
        if target_user.role == 'teacher':
            teacher_form = OwnerTeacherEditForm(request.POST, instance=target_user.teacher_profile)
            if user_form.is_valid() and teacher_form.is_valid():
                user_form.save()
                teacher_form.save()
                messages.success(request, f"تم تعديل بيانات المعلم {target_user.first_name} بنجاح.")
                return redirect('owner_dashboard')
                
        elif target_user.role == 'student':
            student_form = OwnerStudentEditForm(request.POST, instance=target_user.student_profile)
            if user_form.is_valid() and student_form.is_valid():
                user_form.save()
                student_form.save()
                messages.success(request, f"تم تعديل بيانات الطالب {target_user.first_name} بنجاح.")
                return redirect('owner_dashboard')

        elif target_user.role == 'assistant':
            assistant_form = OwnerAssistantEditForm(request.POST, instance=target_user.assistant_profile)
            if user_form.is_valid() and assistant_form.is_valid():
                user_form.save()
                assistant_form.save()
                messages.success(request, f"تم تعديل بيانات المساعد {target_user.first_name} بنجاح.")
                return redirect('owner_dashboard')
        
        else:
            # لو أدمن أو دور آخر
            if user_form.is_valid():
                user_form.save()
                messages.success(request, "تم التعديل بنجاح.")
                return redirect('owner_dashboard')

    else:
        # GET Request: عرض الفورمز
        user_form = OwnerUserEditForm(instance=target_user)
        
        # نملأ الفورم المناسب فقط، والباقي يظل None
        if target_user.role == 'teacher':
            teacher_form = OwnerTeacherEditForm(instance=target_user.teacher_profile)
        elif target_user.role == 'student':
            student_form = OwnerStudentEditForm(instance=target_user.student_profile)
        elif target_user.role == 'assistant':
            assistant_form = OwnerAssistantEditForm(instance=target_user.assistant_profile)

    context = {
        'target_user': target_user,
        'user_form': user_form,
        'teacher_form': teacher_form,
        'student_form': student_form,
        'assistant_form': assistant_form # الآن هذا المتغير موجود دائماً (إما فورم أو None)
    }
    return render(request, 'core/owner_edit_user.html', context)




# في core/views.py

@login_required
def manage_plans(request):
    if not request.user.is_superuser: return redirect('home')
    
    plans = SubscriptionPlan.objects.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # دالة صغيرة لتنظيف الأرقام (تمنع الخطأ لو الحقل فارغ)
        def clean_int(val, default=0):
            try: return int(val)
            except (ValueError, TypeError): return default

        if action == 'add':
            SubscriptionPlan.objects.create(
                name=request.POST.get('name'),
                price=clean_int(request.POST.get('price')),
                description=request.POST.get('desc'),
                
                # القيم الجديدة
                student_limit=clean_int(request.POST.get('student_limit'), 1000),
                group_limit=clean_int(request.POST.get('group_limit'), 5),
                assistant_limit=clean_int(request.POST.get('assistant_limit'), 2),
                
                # Checkboxes
                allow_online_packages=(request.POST.get('allow_online') == 'on'),
                allow_question_images=(request.POST.get('allow_images') == 'on'),
                
                # الحقل الجديد
                is_default=(request.POST.get('is_default') == 'on')
            )
            messages.success(request, "تم إضافة الباقة بنجاح.")
            
        elif action == 'edit':
            p_id = request.POST.get('plan_id')
            plan = SubscriptionPlan.objects.get(id=p_id)
            
            plan.name = request.POST.get('name')
            plan.price = clean_int(request.POST.get('price'))
            plan.description = request.POST.get('desc')
            
            # تحديث القيم
            plan.student_limit = clean_int(request.POST.get('student_limit'), 1000)
            plan.group_limit = clean_int(request.POST.get('group_limit'), 5)
            plan.assistant_limit = clean_int(request.POST.get('assistant_limit'), 2)
            
            plan.allow_online_packages = (request.POST.get('allow_online') == 'on')
            plan.allow_question_images = (request.POST.get('allow_images') == 'on')
            plan.is_default = (request.POST.get('is_default') == 'on') # <--- الحقل الجديد
            
            plan.save()
            messages.success(request, "تم تعديل الباقة.")            
        elif action == 'delete':
            p_id = request.POST.get('plan_id')
            SubscriptionPlan.objects.get(id=p_id).delete()
            messages.warning(request, "تم حذف الباقة.")
            
        return redirect('manage_plans')
        
    return render(request, 'core/manage_plans.html', {'plans': plans})

from teachers.models import WithdrawRequest

@login_required
def owner_withdrawals(request):
    if not request.user.is_superuser: return redirect('home')
    
    requests = WithdrawRequest.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        req_id = request.POST.get('req_id')
        req = get_object_or_404(WithdrawRequest, id=req_id)
        
        # تعليم الطلب كمدفوع
        req.is_paid = True
        req.save()
        messages.success(request, f"تم تسجيل تحويل {req.amount} للمعلم.")
        return redirect('owner_withdrawals')

    return render(request, 'core/owner_withdrawals.html', {'requests': requests})


from students.models import PackageEnrollment # استيراد

@login_required
def owner_student_payments(request):
    if not request.user.is_superuser: return redirect('home')
    
    # المدفوعات فقط
    payments = PackageEnrollment.objects.filter(is_paid=True).select_related('student__user', 'package__teacher__user').order_by('-joined_at')
    
    total_revenue = sum(p.package.price for p in payments)

    return render(request, 'core/owner_student_payments.html', {
        'payments': payments,
        'total_revenue': total_revenue
    })

from .models import Notification
@login_required
def read_notification(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notif.is_read = True
    notif.save()
    
    if notif.link:
        return redirect(notif.link)
    return redirect('all_notifications')

@login_required
def all_notifications(request):
    notifs = Notification.objects.filter(recipient=request.user)
    # تصفير العداد عند دخول الصفحة
    notifs.filter(is_read=False).update(is_read=True)
    
    return render(request, 'core/notifications.html', {'notifs': notifs})