from django.shortcuts import render, redirect
from django.urls import reverse

class BanMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.is_banned:
            # لو المستخدم محظور، نمنعه من الوصول لأي صفحة ما عدا صفحة "الخروج" وصفحة "الحظر"
            if request.path not in [reverse('account_logout'), reverse('banned_page')]:
                return redirect('banned_page')
        
        response = self.get_response(request)
        return response
    
from django.shortcuts import render
from core.models import SiteSetting

class MaintenanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # محاولة جلب الإعدادات (مع معالجة الخطأ لو الجدول فاضي)
        try:
            settings = SiteSetting.load()
            is_maintenance = settings.is_maintenance_mode
        except:
            is_maintenance = False

        if is_maintenance and not request.user.is_superuser:
            # الصفحات المسموحة (Login, Admin, Static)
            allowed_prefixes = ['/admin/', '/accounts/', '/static/', '/media/']
            if not any(request.path.startswith(p) for p in allowed_prefixes):
                return render(request, 'core/maintenance.html')

        return self.get_response(request)