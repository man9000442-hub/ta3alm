from django.dispatch import receiver
from allauth.account.signals import user_signed_up, user_logged_in
from django.shortcuts import redirect
from django.contrib import messages
from teachers.models import TeacherProfile
from django.utils import timezone
from datetime import timedelta

@receiver(user_signed_up)
def set_role_on_signup(request, user, **kwargs):
    # جلب الدور من الجلسة
    role = request.session.get('selected_role')
    print(f"--- SIGNAL: New Signup. Role in Session: {role} ---")
    
    if role:
        user.role = role
        user.save()
        print(f"--- SIGNAL: User {user.email} saved as {role} ---")
        
        # لا ننشئ البروفايلات هنا للمساعد والطالب، نتركها لصفحة complete_profile
        # فقط المعلم نمنحه الشهر المجاني لو أكمل (أو نتركه أيضاً هناك)
        # الأفضل ترك كل شيء لصفحة الإكمال لضمان النظام
        
        # تنظيف الجلسة
        if 'selected_role' in request.session:
            del request.session['selected_role']

@receiver(user_logged_in)
def check_role_on_login(request, user, **kwargs):
    selected_role = request.session.get('selected_role')
    
    if selected_role and user.role and user.role != selected_role:
        messages.warning(request, f"حسابك مسجل بالفعل كـ '{user.get_role_display()}'، تم توجيهك للوحتك.")
        if 'selected_role' in request.session:
            del request.session['selected_role']