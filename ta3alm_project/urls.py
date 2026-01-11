"""
URL configuration for ta3alm_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from accounts import views as account_views # استيراد فيوز الحسابات
from django.conf import settings # <--- جديد
from django.conf.urls.static import static # <--- جديد
from django.conf.urls.i18n import i18n_patterns # <--- استيراد
from django.contrib.sitemaps.views import sitemap
# استيراد الكلاسات التي أنشأناها في sitemaps.py
from core.sitemaps import StaticViewSitemap, TeacherSitemap, PackageSitemap
from core.sitemaps import StaticViewSitemap, TeacherSitemap, PackageSitemap
from django.contrib.sitemaps.views import sitemap
from django.views.generic.base import TemplateView
sitemaps = {
    'static': StaticViewSitemap,
    'teachers': TeacherSitemap,
    'packages': PackageSitemap,
}
urlpatterns = [
    path('admin/', admin.site.urls),
    
    # روابط مكتبة allauth (تسجيل الدخول والخروج)
    path('accounts/', include('allauth.urls')),
    
    # رابط صفحة إكمال البيانات (التي أنشأناها قبل قليل)
    path('complete-profile/', account_views.complete_profile, name='complete_profile'),
            # --- أضف هذه السطور ---
    path('student/', include('students.urls')), # روابط الطالب
    path('teacher/', include('teachers.urls')), # روابط المعلم
    # روابط الصفحة الرئيسية (تطبيق core)
    # نجعلها فارغة '' لكي تفتح عند زيارة الموقع مباشرة
    path('exams/', include('exams.urls')),
    path('assistants/', include('assistants.urls')),    
    path('', include('core.urls')), 
    path('i18n/', include('django.conf.urls.i18n')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")), # سننشئه الآن




]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    
    # روابط مكتبة allauth (تسجيل الدخول والخروج)
    path('accounts/', include('allauth.urls')),
    
    # رابط صفحة إكمال البيانات (التي أنشأناها قبل قليل)
    path('complete-profile/', account_views.complete_profile, name='complete_profile'),
            # --- أضف هذه السطور ---
    path('student/', include('students.urls')), # روابط الطالب
    path('teacher/', include('teachers.urls')), # روابط المعلم
    # روابط الصفحة الرئيسية (تطبيق core)
    # نجعلها فارغة '' لكي تفتح عند زيارة الموقع مباشرة
    path('exams/', include('exams.urls')),
    path('assistants/', include('assistants.urls')),    
    path('', include('core.urls')),     
)

