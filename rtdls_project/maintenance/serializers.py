from rest_framework import serializers

from .models import Alert, MaintenanceLog


class MaintenanceLogSerializer(serializers.ModelSerializer):
    aircraft_tail_number = serializers.CharField(source='aircraft.tail_number', read_only=True)
    logged_by_username = serializers.CharField(source='logged_by.username', read_only=True)

    class Meta:
        model = MaintenanceLog
        fields = [
            'id',
            'aircraft',
            'aircraft_tail_number',
            'total_flight_hours',
            'last_maintenance_date',
            'component_status',
            'maintenance_notes',
            'logged_by',
            'logged_by_username',
            'created_at',
        ]
        read_only_fields = ['logged_by', 'created_at']


class AlertSerializer(serializers.ModelSerializer):
    aircraft_tail_number = serializers.CharField(source='aircraft.tail_number', read_only=True)

    class Meta:
        model = Alert
        fields = [
            'id',
            'aircraft',
            'aircraft_tail_number',
            'maintenance_log',
            'title',
            'message',
            'severity',
            'is_resolved',
            'recipient_role',
            'created_at',
        ]
        read_only_fields = ['created_at']
