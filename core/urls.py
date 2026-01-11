from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/<str:role>/', views.signup_redirect, name='signup_redirect'),
    path('redirect/', views.custom_login_redirect, name='custom_login_redirect'),
    path('owner/dashboard/', views.owner_dashboard, name='owner_dashboard'),
    path('banned/', views.banned_page, name='banned_page'),
    path('owner/payments/', views.owner_payments, name='owner_payments'),
    path('owner/edit/<int:user_id>/', views.owner_edit_user, name='owner_edit_user'),
    path('owner/edit/<int:user_id>/', views.owner_edit_user, name='owner_edit_user'),
    path('owner/plans/', views.manage_plans, name='manage_plans'),
    path('owner/withdrawals/', views.owner_withdrawals, name='owner_withdrawals'),
    path('owner/student-payments/', views.owner_student_payments, name='owner_student_payments'),
    path('notifications/read/<int:notif_id>/', views.read_notification, name='read_notification'),
    path('notifications/all/', views.all_notifications, name='all_notifications'),
    path('guide/', views.platform_guide, name='platform_guide'),
]