from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsAdminRole, IsCommanderAuditorOrAdmin, IsFlightOpsOrAdmin
from audittrail.models import AuditLog, log_action
from dashboard.realtime import broadcast_dashboard_update

from .models import Aircraft, Base, Crew, FlightData, FlightLog, Pilot
from .serializers import (
    AircraftSerializer,
    BaseSerializer,
    CrewSerializer,
    FlightDataSerializer,
    FlightLogSerializer,
    PilotSerializer,
)


class BaseAuditViewSet(viewsets.ModelViewSet):
    audit_entity = ''

    def _client_ip(self):
        forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        return self.request.META.get('REMOTE_ADDR')

    def perform_create(self, serializer):
        obj = serializer.save()
        log_action(
            user=self.request.user,
            action=AuditLog.Action.CREATE,
            entity=self.audit_entity,
            entity_id=obj.id,
            description=f'Created {self.audit_entity} #{obj.id}',
            ip_address=self._client_ip(),
        )

    def perform_update(self, serializer):
        obj = serializer.save()
        log_action(
            user=self.request.user,
            action=AuditLog.Action.UPDATE,
            entity=self.audit_entity,
            entity_id=obj.id,
            description=f'Updated {self.audit_entity} #{obj.id}',
            ip_address=self._client_ip(),
        )

    def perform_destroy(self, instance):
        obj_id = instance.id
        instance.delete()
        log_action(
            user=self.request.user,
            action=AuditLog.Action.DELETE,
            entity=self.audit_entity,
            entity_id=obj_id,
            description=f'Deleted {self.audit_entity} #{obj_id}',
            ip_address=self._client_ip(),
        )


class AircraftViewSet(BaseAuditViewSet):
    queryset = Aircraft.objects.select_related('home_base').all().order_by('tail_number')
    serializer_class = AircraftSerializer
    audit_entity = 'Aircraft'

    def get_permissions(self):
        if self.action in {'list', 'retrieve'}:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminRole()]


class BaseViewSet(BaseAuditViewSet):
    queryset = Base.objects.all().order_by('name')
    serializer_class = BaseSerializer
    audit_entity = 'Base'

    def get_permissions(self):
        if self.action in {'list', 'retrieve'}:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminRole()]


class CrewViewSet(BaseAuditViewSet):
    queryset = Crew.objects.all().order_by('full_name')
    serializer_class = CrewSerializer
    audit_entity = 'Crew'

    def get_permissions(self):
        if self.action in {'list', 'retrieve'}:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminRole()]


class PilotViewSet(BaseAuditViewSet):
    queryset = Pilot.objects.all().order_by('full_name')
    serializer_class = PilotSerializer
    audit_entity = 'Pilot'

    def get_permissions(self):
        if self.action in {'list', 'retrieve'}:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminRole()]


class FlightLogViewSet(BaseAuditViewSet):
    queryset = (
        FlightLog.objects.select_related('aircraft', 'pilot', 'departure_base', 'arrival_base', 'logged_by')
        .prefetch_related('crew_members')
        .all()
    )
    serializer_class = FlightLogSerializer
    audit_entity = 'FlightLog'
    filterset_fields = ['aircraft', 'pilot', 'mission_status', 'mission_type', 'departure_base', 'arrival_base', 'atd', 'eta', 'ata']

    def get_permissions(self):
        if self.action in {'list', 'retrieve'}:
            return [IsAuthenticated()]
        if self.action in {'create', 'update', 'partial_update'}:
            return [IsAuthenticated(), IsFlightOpsOrAdmin()]
        if self.action == 'destroy':
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated(), IsCommanderAuditorOrAdmin()]

    def perform_create(self, serializer):
        flight = serializer.save(logged_by=self.request.user)
        log_action(
            user=self.request.user,
            action=AuditLog.Action.CREATE,
            entity=self.audit_entity,
            entity_id=flight.id,
            description=f'Created FlightLog #{flight.id}',
            ip_address=self._client_ip(),
        )

    def perform_update(self, serializer):
        flight = serializer.save()
        log_action(
            user=self.request.user,
            action=AuditLog.Action.UPDATE,
            entity=self.audit_entity,
            entity_id=flight.id,
            description=f'Updated FlightLog #{flight.id}',
            ip_address=self._client_ip(),
        )
        broadcast_dashboard_update()

    def perform_destroy(self, instance):
        flight_id = instance.id
        instance.delete()
        log_action(
            user=self.request.user,
            action=AuditLog.Action.DELETE,
            entity=self.audit_entity,
            entity_id=flight_id,
            description=f'Deleted FlightLog #{flight_id}',
            ip_address=self._client_ip(),
        )
        broadcast_dashboard_update()


class FlightDataViewSet(BaseAuditViewSet):
    queryset = FlightData.objects.select_related('flight_log__aircraft').all()
    serializer_class = FlightDataSerializer
    audit_entity = 'FlightData'
    filterset_fields = ['flight_log', 'timestamp']

    def get_permissions(self):
        if self.action in {'list', 'retrieve'}:
            return [IsAuthenticated()]
        if self.action in {'create', 'update', 'partial_update'}:
            return [IsAuthenticated(), IsFlightOpsOrAdmin()]
        return [IsAuthenticated(), IsAdminRole()]

    def perform_create(self, serializer):
        telemetry = serializer.save()
        log_action(
            user=self.request.user,
            action=AuditLog.Action.CREATE,
            entity=self.audit_entity,
            entity_id=telemetry.id,
            description=f'Created FlightData #{telemetry.id}',
            ip_address=self._client_ip(),
        )

    def perform_update(self, serializer):
        telemetry = serializer.save()
        log_action(
            user=self.request.user,
            action=AuditLog.Action.UPDATE,
            entity=self.audit_entity,
            entity_id=telemetry.id,
            description=f'Updated FlightData #{telemetry.id}',
            ip_address=self._client_ip(),
        )
        broadcast_dashboard_update()

    def perform_destroy(self, instance):
        telemetry_id = instance.id
        instance.delete()
        log_action(
            user=self.request.user,
            action=AuditLog.Action.DELETE,
            entity=self.audit_entity,
            entity_id=telemetry_id,
            description=f'Deleted FlightData #{telemetry_id}',
            ip_address=self._client_ip(),
        )
        broadcast_dashboard_update()
