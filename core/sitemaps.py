from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from teachers.models import TeacherProfile, CoursePackage

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'daily'

    def items(self):
        return ['home', 'account_login', 'account_signup', 'list_packages']

    def location(self, item):
        return reverse(item)

class TeacherSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return TeacherProfile.objects.all()

    def location(self, obj):
        # سنحتاج لعمل صفحة بروفايل عامة للمدرس لاحقاً (Public Profile)
        # حالياً سنوجه لصفحة البحث باسمه
        return f"/student/search/?q={obj.user.first_name}"

class PackageSitemap(Sitemap):
    changefreq = "weekly"
    priority = 1.0

    def items(self):
        return CoursePackage.objects.filter(is_active=True)

    def location(self, obj):
        return reverse('package_detail', args=[obj.id])