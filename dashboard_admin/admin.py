from django.contrib import admin
from .models import AdminProfile, AuditLog


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'admin_role', 'is_active_admin', 'appointed_by', 'appointed_at']
    list_filter  = ['admin_role', 'is_active_admin']
    search_fields = ['user__email', 'user__first_name']
    raw_id_fields = ['user', 'appointed_by']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display  = ['created_at', 'admin', 'action', 'target_label', 'ip_address']
    list_filter   = ['action']
    search_fields = ['admin__email', 'target_label']
    readonly_fields = ['admin', 'action', 'target_label', 'target_id',
                       'details', 'ip_address', 'created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
