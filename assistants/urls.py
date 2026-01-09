from django.urls import path
from . import views

urlpatterns = [
    # هذا هو الرابط الذي يبحث عنه جانجو ولم يجده
    path('dashboard/', views.assistant_dashboard, name='assistant_dashboard'),
    
    # باقي روابط المساعد
    path('find-teacher/', views.find_teacher, name='find_teacher'),
    path('teacher/<int:teacher_id>/groups/', views.view_teacher_groups, name='view_teacher_groups'),
    path('teacher/<int:teacher_id>/packages/', views.assistant_view_packages, name='assistant_view_packages'),
    path('teacher/<int:teacher_id>/create-group/', views.create_group_for_teacher, name='create_group_for_teacher'),
]