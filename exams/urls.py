from django.urls import path
from . import views

urlpatterns = [
    path('manage/<int:exam_id>/', views.exam_manage, name='exam_manage'),
    
    # الروابط الجديدة
    path('toggle/<int:exam_id>/', views.toggle_exam_status, name='toggle_exam'),
    path('delete/<int:exam_id>/', views.delete_exam, name='delete_exam'),
    
    path('question/delete/<int:question_id>/', views.delete_question, name='delete_question'),
    #path('question/edit/<int:question_id>/', views.edit_question, name='edit_question'),
    path('exam/<int:exam_id>/add/', views.add_question_page, name='add_question_page'),
    path('question/<int:question_id>/edit/', views.edit_question_page, name='edit_question_page'),
]