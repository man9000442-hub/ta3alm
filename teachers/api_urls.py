from django.urls import path
from . import views

urlpatterns = [
    path('teachers/', views.api_all_teachers),
    path('packages/', views.api_all_packages),
]