"""
ta3alm_project/middleware.py — Middleware المخصص للمنصة
"""
from django.shortcuts import render, redirect
from django.urls import reverse, resolve, Resolver404
from django.http import Http404
from rest_framework.authtoken.models import Token
from django.contrib.auth import login
from core.models import SiteSetting


class SubdomainAdminMiddleware:
    """
    يعترض الطلبات القادمة على النطاق الفرعي admin.* ويُعيد
    توجيهها لـ dashboard_admin URLs دون أي تغيير في الرابط الظاهر.

    محلياً  : admin.localhost:8000  أو  admin.127.0.0.1
    إنتاج   : admin.ta3alm.online
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def _is_admin_subdomain(self, host):
        """True إذا كان الـ host يبدأ بـ admin."""
        # أزِل رقم المنفذ لو موجود  (admin.localhost:8000 → admin.localhost)
        hostname = host.split(':')[0].lower()
        return hostname.startswith('admin.')

    def __call__(self, request):
        host = request.META.get('HTTP_HOST', '')

        if self._is_admin_subdomain(host):
            # أعِد كتابة المسار ليصل لـ dashboard_admin عبر prefix /admin-panel/
            original_path = request.path_info

            # تجنُّب إعادة الكتابة لو المسار أصلاً يحمل الـ prefix
            if not original_path.startswith('/admin-panel/'):
                # الصفحة الجذر → لوحة التحكم مباشرة
                if original_path in ('/', ''):
                    new_path = '/admin-panel/'
                else:
                    new_path = '/admin-panel' + original_path

                request.path_info = new_path
                request.path = new_path
                request.META['PATH_INFO'] = new_path

        return self.get_response(request)


class TokenAuthMiddleware:
    """
    يسمح بتسجيل الدخول عبر Token في Header أو Query Parameter.
    
    ⚠️ تحذير أمني: Auth Token في URL يُحفظ في Logs وBrowser History.
    الاستخدام المُفضَّل: Authorization: Token <key> في الـ Header.
    القيم في URL للتوافق مع Flutter Mobile App فقط.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            # أولاً: ابحث في Authorization Header (الأكثر أماناً)
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            token_key = None

            if auth_header.startswith('Token '):
                token_key = auth_header.split(' ', 1)[1].strip()
            else:
                # ثانياً: fallback لـ Query Parameter (للتوافق مع المحتوى القديم)
                token_key = request.GET.get('auth_token')

            if token_key:
                try:
                    token = Token.objects.select_related('user').get(key=token_key)
                    login(request, token.user,
                          backend='django.contrib.auth.backends.ModelBackend')
                except Token.DoesNotExist:
                    pass

        return self.get_response(request)


class BanMiddleware:
    """
    يمنع المستخدمين المحظورين من الوصول لأي صفحة.
    """
    EXEMPT_PATHS = None  # سيُحسب عند أول استخدام

    def __init__(self, get_response):
        self.get_response = get_response

    def _get_exempt_paths(self):
        if self.EXEMPT_PATHS is None:
            BanMiddleware.EXEMPT_PATHS = {
                reverse('account_logout'),
                reverse('banned_page'),
            }
        return self.EXEMPT_PATHS

    def __call__(self, request):
        # استثناء الـ API endpoints
        if request.path.startswith(('/api/', '/teacher/api/')):
            return self.get_response(request)

        if request.user.is_authenticated and request.user.is_banned:
            exempt = self._get_exempt_paths()
            if request.path not in exempt:
                return redirect('banned_page')

        return self.get_response(request)


class MaintenanceMiddleware:
    """
    يُظهر صفحة الصيانة لغير المشرفين عند تفعيل وضع الصيانة.
    """
    ALLOWED_PREFIXES = ('/admin/', '/admin-panel/', '/accounts/', '/static/', '/media/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # استثناء الـ API endpoints
        if request.path.startswith(('/api/', '/teacher/api/')):
            return self.get_response(request)

        # التعامل مع بادئة اللغة (مثال: /ar/admin/)
        path = request.path
        if path.startswith('/ar/') or path.startswith('/en/'):
            path = path[3:]

        # الصفحات المسموح بها دائماً
        if any(path.startswith(p) for p in self.ALLOWED_PREFIXES):
            return self.get_response(request)

        try:
            settings = SiteSetting.load()
            is_maintenance = settings.is_maintenance_mode
        except Exception:
            is_maintenance = False

        if is_maintenance and not (request.user.is_authenticated and request.user.is_superuser):
            return render(request, 'core/maintenance.html', status=503)

        return self.get_response(request)