"""
services/zoho_mail_service.py
خدمة الربط المتكاملة مع Zoho Mail REST API باستخدام بروتوكول OAuth 2.0.
تتيح قراءة واستعراض الرسائل الواردة إلى support@ta3alm.online والرد عليها مباشرة من لوحة الإدارة.
"""
import logging
import requests
from datetime import timedelta
from urllib.parse import urlencode

from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


class ZohoMailService:
    """
    خدمة التفاعل مع Zoho Mail REST API
    """
    DEFAULT_SCOPES = "ZohoMail.messages.ALL,ZohoMail.accounts.READ"

    def __init__(self, config=None):
        if config is None:
            try:
                from dashboard_admin.models import ZohoMailConfig
                self.config = ZohoMailConfig.load()
            except Exception as e:
                logger.warning("Failed to load ZohoMailConfig from DB: %s", e)
                self.config = None
        else:
            self.config = config

    # ------------------------------------------------------------------
    # 1. خاصيات وإعدادات التهيئة
    # ------------------------------------------------------------------
    @property
    def client_id(self):
        if self.config:
            return self.config.get_effective_client_id()
        import os
        return os.environ.get('ZOHO_CLIENT_ID', '').strip()

    @property
    def client_secret(self):
        if self.config:
            return self.config.get_effective_client_secret()
        import os
        return os.environ.get('ZOHO_CLIENT_SECRET', '').strip()

    @property
    def refresh_token(self):
        if self.config:
            return self.config.get_effective_refresh_token()
        import os
        return os.environ.get('ZOHO_REFRESH_TOKEN', '').strip()

    @property
    def support_email(self):
        if self.config:
            return self.config.get_effective_support_email()
        import os
        return os.environ.get('ZOHO_SUPPORT_EMAIL', 'support@ta3alm.online').strip()

    @property
    def accounts_url(self):
        if self.config and self.config.zoho_accounts_url:
            return self.config.zoho_accounts_url.rstrip('/')
        return "https://accounts.zoho.com"

    @property
    def api_url(self):
        if self.config and self.config.zoho_api_url and "zohoapis.com" not in self.config.zoho_api_url:
            return self.config.zoho_api_url.rstrip('/')
        return "https://mail.zoho.com/api"

    def is_configured(self):
        return bool(self.client_id and self.client_secret)

    def is_connected(self):
        return bool(self.is_configured() and self.refresh_token)

    # ------------------------------------------------------------------
    # 2. بروتوكول OAuth 2.0
    # ------------------------------------------------------------------
    def get_authorization_url(self, redirect_uri: str, state: str = "zoho_auth") -> str:
        """
        يُولِّد رابط التخويل (Consent Page) في Zoho للموافقة على الصلاحيات والحصول على الكود.
        """
        if not self.client_id:
            raise ValueError("ZOHO_CLIENT_ID غير مضبوط في الإعدادات.")

        params = {
            'scope': self.DEFAULT_SCOPES,
            'client_id': self.client_id,
            'response_type': 'code',
            'access_type': 'offline',
            'prompt': 'consent',
            'redirect_uri': redirect_uri,
            'state': state,
        }
        return f"{self.accounts_url}/oauth/v2/auth?{urlencode(params)}"

    def exchange_code(self, code: str, redirect_uri: str) -> dict:
        """
        استبدال كود التفويض (Authorization Code) بـ Access Token و Refresh Token.
        """
        token_url = f"{self.accounts_url}/oauth/v2/token"
        payload = {
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
        }

        response = requests.post(token_url, data=payload, timeout=20)
        data = response.json()

        if response.status_code != 200 or 'error' in data:
            error_msg = data.get('error_description') or data.get('error') or f"HTTP {response.status_code}"
            logger.error("Zoho OAuth exchange error: %s", error_msg)
            raise ValueError(f"فشل الحصول على الرمز المميز من Zoho: {error_msg}")

        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')
        expires_in = int(data.get('expires_in', 3600))
        api_domain = data.get('api_domain', '')

        # تحديد دومين الـ Mail API المناسب حسب الـ data center
        mail_domain = "https://mail.zoho.com/api"
        if api_domain:
            if "zohoapis.eu" in api_domain:
                mail_domain = "https://mail.zoho.eu/api"
            elif "zohoapis.in" in api_domain:
                mail_domain = "https://mail.zoho.in/api"
            elif "zohoapis.com.au" in api_domain:
                mail_domain = "https://mail.zoho.com.au/api"
            elif "zohoapis.sa" in api_domain:
                mail_domain = "https://mail.zoho.sa/api"
            else:
                mail_domain = "https://mail.zoho.com/api"

        # حفظ التوكنات في قاعدة البيانات
        if self.config:
            self.config.access_token = access_token
            if refresh_token:
                self.config.refresh_token = refresh_token
            self.config.token_expires_at = timezone.now() + timedelta(seconds=expires_in - 120)
            self.config.zoho_api_url = mail_domain
            self.config.save()

            # جلب معرف الحساب فورياً وحفظه
            try:
                self.get_account_id(force_refresh=True)
            except Exception as e:
                logger.warning("Could not auto-fetch account_id: %s", e)

        return data

    def refresh_access_token(self) -> str:
        """
        تجديد الـ Access Token باستخدام الـ Refresh Token الدائم.
        """
        if not self.refresh_token:
            raise ValueError("لا يوجد Refresh Token مسجل للاتصال بـ Zoho Mail.")

        token_url = f"{self.accounts_url}/oauth/v2/token"
        payload = {
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
        }

        response = requests.post(token_url, data=payload, timeout=20)
        data = response.json()

        if response.status_code != 200 or 'error' in data:
            error_msg = data.get('error_description') or data.get('error') or f"HTTP {response.status_code}"
            logger.error("Zoho Token Refresh error: %s", error_msg)
            raise ValueError(f"فشل تجديد توكن Zoho Mail: {error_msg}")

        new_access_token = data.get('access_token')
        expires_in = int(data.get('expires_in', 3600))

        if self.config:
            self.config.access_token = new_access_token
            self.config.token_expires_at = timezone.now() + timedelta(seconds=expires_in - 120)
            self.config.save(update_fields=['access_token', 'token_expires_at', 'updated_at'])

        return new_access_token

    def get_valid_access_token(self) -> str:
        """
        يُعيد Access Token صالحاً، ويقوم بتجديده تلقائياً إذا انتهت مدة صلاحيته أو أوشكت على الانتهاء.
        """
        if self.config and self.config.access_token and self.config.token_expires_at:
            if self.config.token_expires_at > timezone.now():
                return self.config.access_token

        return self.refresh_access_token()

    # ------------------------------------------------------------------
    # 3. إدارة الحساب (Accounts API)
    # ------------------------------------------------------------------
    def get_account_id(self, force_refresh: bool = False) -> str:
        """
        يجلب معرف حساب Zoho Mail المرتبط بـ support@ta3alm.online أو الحساب الأساسي.
        """
        if not force_refresh and self.config:
            cached_id = self.config.get_effective_account_id()
            if cached_id:
                return cached_id

        token = self.get_valid_access_token()
        headers = {
            'Authorization': f'Zoho-oauthtoken {token}',
            'Accept': 'application/json',
        }
        url = f"{self.api_url}/accounts"
        response = requests.get(url, headers=headers, timeout=20)

        if response.status_code != 200:
            logger.error("Failed to fetch Zoho accounts: %s %s", response.status_code, response.text)
            raise ValueError(f"فشل جلب بيانات حسابات Zoho: {response.text}")

        res_data = response.json()
        accounts = res_data.get('data', [])
        if not accounts:
            raise ValueError("لم يتم العثور على أي حسابات بريد إلكتروني في حساب Zoho المربوط.")

        # البحث عن الحساب المطابق للإيميل الرسمي support@ta3alm.online
        target_email = self.support_email.lower()
        selected_account = None
        for acc in accounts:
            primary_email = (acc.get('primaryEmailAddress') or acc.get('incomingUserName') or '').lower()
            if primary_email == target_email:
                selected_account = acc
                break

        if not selected_account:
            selected_account = accounts[0]  # استخدام أول حساب متوفر

        account_id = str(selected_account.get('accountId'))
        if self.config:
            self.config.account_id = account_id
            self.config.save(update_fields=['account_id', 'updated_at'])

        return account_id

    # ------------------------------------------------------------------
    # 4. قراءة البريد الوارد (Messages API)
    # ------------------------------------------------------------------
    def list_messages(self, folder_id: str = None, limit: int = 25, start: int = 1, search_key: str = None) -> dict:
        """
        استعراض قائمة الرسائل في صندوق البريد الوارد.
        """
        account_id = self.get_account_id()
        token = self.get_valid_access_token()
        headers = {
            'Authorization': f'Zoho-oauthtoken {token}',
            'Accept': 'application/json',
        }

        # الـ endpoint لعرض الرسائل
        url = f"{self.api_url}/accounts/{account_id}/messages/view"
        params = {
            'limit': limit,
            'start': start,
        }
        if folder_id:
            params['folderId'] = folder_id
        if search_key:
            params['searchKey'] = search_key

        response = requests.get(url, headers=headers, params=params, timeout=25)
        if response.status_code != 200:
            logger.error("Zoho list messages failed: %s %s", response.status_code, response.text)
            raise ValueError(f"فشل استعراض الرسائل من Zoho Mail: {response.text}")

        if self.config:
            self.config.last_synced_at = timezone.now()
            self.config.save(update_fields=['last_synced_at'])

        return response.json()

    def get_message_content(self, message_id: str, folder_id: str = None) -> dict:
        """
        جلب محتوى رسالة محددة بالكامل (النص وتفاصيل المرسل والمرفقات).
        """
        account_id = self.get_account_id()
        token = self.get_valid_access_token()
        headers = {
            'Authorization': f'Zoho-oauthtoken {token}',
            'Accept': 'application/json',
        }

        # إذا لم يتم تمرير folder_id، نبحث عنه تلقائياً في قائمة الرسائل
        if not folder_id:
            try:
                res_msgs = self.list_messages(limit=50).get('data', [])
                for m in res_msgs:
                    if str(m.get('messageId')) == str(message_id):
                        folder_id = m.get('folderId')
                        break
            except Exception as e:
                logger.warning("Could not auto-resolve folderId for message %s: %s", message_id, e)

        if folder_id:
            url = f"{self.api_url}/accounts/{account_id}/folders/{folder_id}/messages/{message_id}/content"
            response = requests.get(url, headers=headers, timeout=25)
            if response.status_code == 200:
                return response.json()

        # بديل تفاصيل الرسالة إذا لم يرجع الـ endpoint الأول
        detail_url = f"{self.api_url}/accounts/{account_id}/messages/{message_id}/details"
        detail_res = requests.get(detail_url, headers=headers, timeout=25)
        if detail_res.status_code == 200:
            return detail_res.json()

        raise ValueError(f"تعذر جلب تفاصيل الرسالة {message_id}")

    # ------------------------------------------------------------------
    # 5. الرد وإرسال الرسائل (Send / Reply API)
    # ------------------------------------------------------------------
    def send_reply(self, to_email: str, subject: str, content: str, message_id: str = None) -> dict:
        """
        إرسال رد على رسالة محددة أو رسالة مرتبطة بسلسلة المحادثة.
        """
        account_id = self.get_account_id()
        token = self.get_valid_access_token()
        headers = {
            'Authorization': f'Zoho-oauthtoken {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        url = f"{self.api_url}/accounts/{account_id}/messages"

        # تنسيق الرد بما يتوافق مع Zoho REST API
        payload = {
            'fromAddress': self.support_email,
            'toAddress': to_email.strip(),
            'subject': subject.strip(),
            'content': content,
            'mailFormat': 'html',
        }
        if message_id:
            payload['action'] = 'reply'
            payload['mailId'] = str(message_id)

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        res_data = response.json()

        if response.status_code not in (200, 201):
            error_desc = res_data.get('status', {}).get('description') or res_data.get('data', {}).get('moreInfo') or response.text
            logger.error("Zoho send reply failed: %s %s", response.status_code, error_desc)
            raise ValueError(f"فشل إرسال الرد عبر Zoho Mail: {error_desc}")

        return res_data

    def compose_new_message(self, to_email: str, subject: str, content: str) -> dict:
        """
        إنشاء وإرسال رسالة جديدة تماماً من بريد الدعم support@ta3alm.online
        """
        return self.send_reply(to_email=to_email, subject=subject, content=content, message_id=None)
