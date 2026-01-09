from .models import Notification

def send_notification(user, title, message, link=None):
    """
    دالة لإرسال إشعار لمستخدم معين.
    """
    Notification.objects.create(
        recipient=user,
        title=title,
        message=message,
        link=link
    )