from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class MultiFieldAuthBackend(ModelBackend):
    """
    يتيح تسجيل الدخول باستخدام (اسم المستخدم، البريد الإلكتروني، أو رقم الهاتف).
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('email')
            
        if username is None:
            return None

        try:
            # البحث عن المستخدم بناءً على الحقول الثلاثة
            user = User.objects.get(
                Q(username__iexact=username) | 
                Q(email__iexact=username) | 
                Q(phone=username)
            )
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing difference 
            # between an existing and a non-existing user (prevents timing attacks).
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            # في حال وجود أكثر من مستخدم بنفس الرقم (نادر لكن للاحتياط)، نأخذ الأول
            user = User.objects.filter(
                Q(username__iexact=username) | 
                Q(email__iexact=username) | 
                Q(phone=username)
            ).order_by('id').first()

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
