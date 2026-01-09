from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import random
import string
from django.contrib.auth import update_session_auth_hash

from .forms import CompleteStudentProfileForm, CompleteTeacherProfileForm, CompleteAssistantProfileForm
from .models import StudentProfile
from teachers.models import TeacherProfile, SubscriptionPlan
from assistants.models import AssistantProfile

@login_required
def complete_profile(request):
    user = request.user
    print(f"--- VIEW: Entering complete_profile. Role: {user.role}, Code: {user.custom_id} ---")

    # 1. التحقق الصارم (هل البيانات مكتملة فعلاً؟)
    is_complete = False
    
    if user.role == 'student':
        if hasattr(user, 'student_profile') and user.student_profile.parent_phone: is_complete = True
    elif user.role == 'teacher':
        if hasattr(user, 'teacher_profile') and user.teacher_profile.subject: is_complete = True
    elif user.role == 'assistant':
        # المساعد: يجب أن يكون لديه بروفايل + رقم هاتف
        if hasattr(user, 'assistant_profile') and user.assistant_profile.phone: 
            is_complete = True
            
    # لو مكتمل ولديه كود -> يخرج
    if is_complete and user.custom_id:
        print("--- VIEW: Profile is complete. Redirecting... ---")
        return redirect('custom_login_redirect')

    # 2. تحديد الفورم
    if user.role == 'student': FormClass = CompleteStudentProfileForm
    elif user.role == 'teacher': FormClass = CompleteTeacherProfileForm
    elif user.role == 'assistant': FormClass = CompleteAssistantProfileForm
    else: return redirect('home')

    # 3. معالجة الحفظ
    if request.method == 'POST':
        form = FormClass(request.POST, instance=user)
        if form.is_valid():
            saved_user = form.save(commit=False)
            
            # الاسم
            full_name = form.cleaned_data.get('full_name', '')
            if full_name:
                name_parts = full_name.split(' ', 1)
                saved_user.first_name = name_parts[0]
                saved_user.last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            # الكود (لو مش موجود)
            if not saved_user.custom_id:
                chars = string.ascii_uppercase + string.digits
                prefix = "A" if user.role == 'assistant' else "T" if user.role == 'teacher' else "S"
                saved_user.custom_id = prefix + ''.join(random.choices(chars, k=6))

            # الباسورد (للمعلم والمساعد)
            if user.role in ['teacher', 'assistant','student']:
                password = form.cleaned_data.get('password')
                if password: saved_user.set_password(password)

            saved_user.save()
            
            # تحديث الجلسة
            if user.role in ['teacher', 'assistant']:
                update_session_auth_hash(request, saved_user)

            # ب) حفظ البروفايل الفرعي
            if user.role == 'student':
                StudentProfile.objects.update_or_create(
                    user=saved_user,
                    defaults={'parent_phone': form.cleaned_data['parent_phone']}
                )
            
            elif user.role == 'teacher':
                default_plan = SubscriptionPlan.objects.filter(is_default=True).first()
                if not default_plan: # لو مفيش، ناخد الأرخص كاحتياطي
                    default_plan = SubscriptionPlan.objects.order_by('price').first()
                TeacherProfile.objects.update_or_create(
                    user=saved_user,
                    defaults={
                        'bio': form.cleaned_data.get('bio', ''),
                        'subject': form.cleaned_data['subject'],
                        'subscription_end_date': timezone.now() + timedelta(days=30),
                        'is_trial_used': True,
                        'current_plan': default_plan
                    }
                )

            elif user.role == 'assistant':
                # نأخذ الهاتف يدوياً من POST لضمان وصوله
                phone_val = request.POST.get('phone')
                print(f"--- VIEW: Saving Assistant Phone: {phone_val} ---")
                
                if phone_val:
                    AssistantProfile.objects.update_or_create(
                        user=saved_user,
                        defaults={'phone': phone_val}
                    )
            
            messages.success(request, f"تم التسجيل بنجاح! أهلاً بك يا {saved_user.first_name}")
            return redirect('custom_login_redirect')
            
    else:
        form = FormClass(instance=user)

    return render(request, 'accounts/complete_profile.html', {'form': form})