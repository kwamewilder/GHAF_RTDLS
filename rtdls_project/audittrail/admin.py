from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'action', 'entity', 'entity_id')
    search_fields = ('description', 'entity', 'user__username')
    list_filter = ('action', 'entity', 'created_at')
    readonly_fields = (
        'user',
        'action',
        'entity',
        'entity_id',
        'description',
        'ip_address',
        'created_at',
        'previous_checksum',
        'checksum',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
