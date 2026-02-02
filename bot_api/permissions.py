from django.conf import settings
from rest_framework.permissions import BasePermission

class IsBotService(BasePermission):
    def has_permission(self, request, view):
        key = request.headers.get("X-BOT-KEY")
        return bool(key) and bool(getattr(settings, "BOT_API_KEY", "")) and key == settings.BOT_API_KEY