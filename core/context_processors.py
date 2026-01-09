from .models import Notification

def notifications(request):
    if request.user.is_authenticated:
        # آخر 5 إشعارات
        notifs = Notification.objects.filter(recipient=request.user)[:5]
        # عدد غير المقروءة
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return {'notifications': notifs, 'unread_count': unread_count}
    return {}