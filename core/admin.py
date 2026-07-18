from django.contrib import admin
from .models import ManualPayment

@admin.register(ManualPayment)
class ManualPaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'payment_type', 'amount', 'phone_number', 'status', 'created_at')
    list_filter = ('status', 'payment_type', 'created_at')
    search_fields = ('user__username', 'phone_number')
    readonly_fields = ('created_at',)
    list_editable = ('status',)
