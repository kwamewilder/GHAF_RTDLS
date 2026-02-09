from django.contrib import admin

from .models import Alert, MaintenanceLog


@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ('aircraft', 'total_flight_hours', 'last_maintenance_date', 'component_status', 'logged_by', 'created_at')
    list_filter = ('last_maintenance_date', 'component_status')
    search_fields = ('aircraft__tail_number', 'maintenance_notes', 'component_status')


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('aircraft', 'title', 'severity', 'is_resolved', 'recipient_role', 'created_at')
    list_filter = ('severity', 'is_resolved', 'recipient_role')
    search_fields = ('aircraft__tail_number', 'title', 'message')
