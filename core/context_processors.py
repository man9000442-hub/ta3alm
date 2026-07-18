from django.db.models import Count, Q
from .models import Notification


def notifications(request):
    """
    Context processor للإشعارات — يُشغَّل مع كل request.
    تم تحسينه: استعلام واحد بدلاً من اثنين.
    """
    if not request.user.is_authenticated:
        return {}

    # استعلام واحد يجلب آخر 5 إشعارات وعدد غير المقروءة
    notifs = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:5]

    unread_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    return {
        'notifications': notifs,
        'unread_count': unread_count,
    }