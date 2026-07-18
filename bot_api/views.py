import re
from django.contrib.auth import get_user_model
from django.core import signing
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import IsBotService
from .utils import normalize_egypt_phone

User = get_user_model()

BOT_SALT = "bot-action-v1"
VERIFY_MAX_AGE_SECONDS = 10 * 60  # 10 دقائق
NID_MAX_ATTEMPTS = 5
NID_ATTEMPTS_TTL = 60 * 60        # ساعة

def _attempt_key(phone: str) -> str:
    return f"bot:nid_attempts:{phone}"

class ResolveUserView(APIView):
    permission_classes = [IsBotService]

    def get(self, request):
        phone = normalize_egypt_phone(request.query_params.get("phone", ""))

        if not phone:
            return Response({"exists": False, "reason": "phone_required"}, status=200)

        user = User.objects.filter(phone=phone).first()
        if not user:
            return Response({"exists": False}, status=200)

        name = f"{user.first_name} {user.last_name}".strip() or user.username

        return Response({
            "exists": True,
            "user_id": user.id,
            "role": getattr(user, "role", "student"),
            "name": name,
            "custom_id": getattr(user, "custom_id", None),
            "phone": user.phone,
        }, status=200)

class VerifyNationalIdView(APIView):
    permission_classes = [IsBotService]

    def post(self, request):
        phone = normalize_egypt_phone(request.data.get("phone", ""))
        national_id = re.sub(r"\D", "", str(request.data.get("national_id", "")))

        if not phone or not national_id:
            return Response({"verified": False, "reason": "missing_fields"}, status=400)

        attempts = cache.get(_attempt_key(phone), 0)
        if attempts >= NID_MAX_ATTEMPTS:
            return Response({"verified": False, "reason": "too_many_attempts"}, status=429)

        user = User.objects.filter(phone=phone).first()
        if not user:
            return Response({"verified": False, "reason": "user_not_found"}, status=404)

        if not getattr(user, "national_id", None) or str(user.national_id) != national_id:
            cache.set(_attempt_key(phone), attempts + 1, NID_ATTEMPTS_TTL)
            return Response({"verified": False, "reason": "invalid_national_id"}, status=401)

        cache.delete(_attempt_key(phone))

        token = signing.dumps({"uid": user.id, "phone": user.phone}, salt=BOT_SALT)

        return Response({"verified": True, "action_token": token, "expires_in": VERIFY_MAX_AGE_SECONDS}, status=200)

class ChangePasswordView(APIView):
    permission_classes = [IsBotService]

    def post(self, request):
        user_id = request.data.get("user_id")
        action_token = request.data.get("action_token")
        new_password = request.data.get("new_password", "")

        if not user_id or not action_token or not new_password:
            return Response({"success": False, "reason": "missing_fields"}, status=400)

        if len(new_password) < 8:
            return Response({"success": False, "reason": "password_too_short"}, status=400)

        try:
            data = signing.loads(action_token, salt=BOT_SALT, max_age=VERIFY_MAX_AGE_SECONDS)
        except signing.SignatureExpired:
            return Response({"success": False, "reason": "token_expired"}, status=401)
        except signing.BadSignature:
            return Response({"success": False, "reason": "bad_token"}, status=401)

        if str(data.get("uid")) != str(user_id):
            return Response({"success": False, "reason": "token_user_mismatch"}, status=403)

        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"success": False, "reason": "user_not_found"}, status=404)

        user.set_password(new_password)
        user.save(update_fields=["password"])

        return Response({"success": True}, status=200)
    


import re
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import IsBotService
from .utils import normalize_egypt_phone
from .models import WhatsAppLink

User = get_user_model()

class ResolveByLidView(APIView):
    permission_classes = [IsBotService]

    def get(self, request):
        lid_base = (request.query_params.get("lid_base") or "").strip()
        if not lid_base:
            return Response({"exists": False, "reason": "lid_required"}, status=200)

        link = WhatsAppLink.objects.select_related("user").filter(lid_base=lid_base).first()
        if not link:
            return Response({"exists": False}, status=200)

        u = link.user
        name = f"{u.first_name} {u.last_name}".strip() or u.username

        return Response({
            "exists": True,
            "user_id": u.id,
            "role": getattr(u, "role", "student"),
            "name": name,
            "phone": u.phone,
            "custom_id": getattr(u, "custom_id", None),
        }, status=200)


class LinkLidView(APIView):
    permission_classes = [IsBotService]

    def post(self, request):
        lid_base = str(request.data.get("lid_base", "")).strip()
        phone = normalize_egypt_phone(str(request.data.get("phone", "")))
        national_id = re.sub(r"\D", "", str(request.data.get("national_id", "")))

        if not lid_base or not phone or not national_id:
            return Response({"linked": False, "reason": "missing_fields"}, status=400)

        if not (phone.startswith("01") and len(phone) == 11):
            return Response({"linked": False, "reason": "invalid_phone"}, status=400)

        if len(national_id) != 14:
            return Response({"linked": False, "reason": "invalid_national_id_format"}, status=400)

        user = User.objects.filter(phone=phone).first()
        if not user:
            return Response({"linked": False, "reason": "user_not_found"}, status=404)

        if not getattr(user, "national_id", None) or str(user.national_id) != national_id:
            return Response({"linked": False, "reason": "invalid_national_id"}, status=401)

        WhatsAppLink.objects.update_or_create(
            lid_base=lid_base,
            defaults={"user": user, "phone": phone},
        )

        name = f"{user.first_name} {user.last_name}".strip() or user.username
        return Response({"linked": True, "user_id": user.id, "role": getattr(user, "role", "student"), "name": name}, status=200)