from django.urls import path
from .views import ResolveUserView, VerifyNationalIdView, ChangePasswordView
from .views import ResolveByLidView, LinkLidView
urlpatterns = [
    path("resolve-user/", ResolveUserView.as_view()),
    path("verify-national-id/", VerifyNationalIdView.as_view()),
    path("change-password/", ChangePasswordView.as_view()),
    path("resolve-by-lid/", ResolveByLidView.as_view()),
    path("link-lid/", LinkLidView.as_view()),
]