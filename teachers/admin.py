from django.contrib import admin
from .models import TeacherProfile, Group, Lecture, VideoCode, PaymentTransaction

admin.site.register(TeacherProfile)
# ...
admin.site.register(PaymentTransaction) # <--- أضف هذا السطر
admin.site.register(Group)
admin.site.register(Lecture)
admin.site.register(VideoCode)