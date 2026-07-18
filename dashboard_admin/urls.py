"""
dashboard_admin/urls.py
روابط لوحة الإدارة — prefix: /admin-panel/
"""
from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # الرئيسية
    path('',                    views.dashboard,          name='dashboard'),
    path('maintenance/toggle/', views.toggle_maintenance, name='toggle_maintenance'),

    # إدارة المستخدمين
    path('users/',              views.manage_users,       name='manage_users'),
    path('users/action/',       views.user_action,        name='user_action'),
    path('users/edit/<int:user_id>/', views.edit_user,   name='edit_user'),

    # المالية
    path('finance/',            views.finance_report,     name='finance_report'),
    path('finance/withdrawals/',views.withdrawals,        name='withdrawals'),
    path('finance/student-payments/', views.student_payments, name='student_payments'),
    path('finance/manual-payments/', views.manual_payments, name='manual_payments'),

    # الباقات
    path('plans/',              views.manage_plans,       name='manage_plans'),

    # سجل الأحداث
    path('audit-log/',          views.audit_log,          name='audit_log'),

    # فريق الإدارة
    path('staff/',              views.manage_staff,       name='manage_staff'),
]
