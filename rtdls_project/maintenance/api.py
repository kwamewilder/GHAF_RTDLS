from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsAdminRole, IsMaintenanceOrAdmin
from audittrail.models import AuditLog, log_action
from dashboard.realtime import broadcast_dashboard_update

from .models import Alert, MaintenanceLog
from .serializers import AlertSerializer, MaintenanceLogSerializer


class BaseAuditViewSet(viewsets.ModelViewSet):
    audit_entity = ''

    def _client_ip(self):
        forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        return self.request.META.get('REMOTE_ADDR')

    def _log(self, action, obj_id, text):
        log_action(
            user=self.request.user,
            action=action,
            entity=self.audit_entity,
            entity_id=obj_id,
            description=text,
            ip_address=self._client_ip(),
        )


class MaintenanceLogViewSet(BaseAuditViewSet):
    queryset = MaintenanceLog.objects.select_related('aircraft', 'logged_by').all()
    serializer_class = MaintenanceLogSerializer
    audit_entity = 'MaintenanceLog'

    def get_permissions(self):
        if self.action in {'list', 'retrieve'}:
            return [IsAuthenticated()]
        if self.action in {'create', 'update', 'partial_update'}:
            return [IsAuthenticated(), IsMaintenanceOrAdmin()]
        return [IsAuthenticated(), IsAdminRole()]

    def perform_create(self, serializer):
        obj = serializer.save(logged_by=self.request.user)
        self._log(AuditLog.Action.CREATE, obj.id, f'Created MaintenanceLog #{obj.id}')

    def perform_update(self, serializer):
        obj = serializer.save()
        self._log(AuditLog.Action.UPDATE, obj.id, f'Updated MaintenanceLog #{obj.id}')
        broadcast_dashboard_update()

    def perform_destroy(self, instance):
        obj_id = instance.id
        instance.delete()
        self._log(AuditLog.Action.DELETE, obj_id, f'Deleted MaintenanceLog #{obj_id}')
        broadcast_dashboard_update()


class AlertViewSet(BaseAuditViewSet):
    queryset = Alert.objects.select_related('aircraft', 'maintenance_log').all()
    serializer_class = AlertSerializer
    audit_entity = 'Alert'

    def get_permissions(self):
        if self.action in {'list', 'retrieve'}:
            return [IsAuthenticated()]
        if self.action in {'update', 'partial_update'}:
            return [IsAuthenticated(), IsMaintenanceOrAdmin()]
        return [IsAuthenticated(), IsAdminRole()]

    def perform_update(self, serializer):
        obj = serializer.save()
        self._log(AuditLog.Action.UPDATE, obj.id, f'Updated Alert #{obj.id}')
        broadcast_dashboard_update()
