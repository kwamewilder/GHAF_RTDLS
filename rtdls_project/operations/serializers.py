from rest_framework import serializers

from .models import Aircraft, Base, Crew, FlightData, FlightLog, Pilot


class BaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Base
        fields = ['id', 'name', 'location']


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ['id', 'full_name', 'rank', 'role', 'is_available']


class PilotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pilot
        fields = ['id', 'full_name', 'rank', 'contact_info', 'is_active']


class AircraftSerializer(serializers.ModelSerializer):
    home_base_name = serializers.CharField(source='home_base.name', read_only=True)

    class Meta:
        model = Aircraft
        fields = [
            'id',
            'tail_number',
            'aircraft_type',
            'model',
            'maintenance_threshold_hours',
            'status',
            'home_base',
            'home_base_name',
        ]


class FlightLogSerializer(serializers.ModelSerializer):
    aircraft_tail_number = serializers.CharField(source='aircraft.tail_number', read_only=True)
    logged_by_username = serializers.CharField(source='logged_by.username', read_only=True)
    pilot_name = serializers.CharField(read_only=True)
    flight_datetime = serializers.DateTimeField(write_only=True, required=False)

    class Meta:
        model = FlightLog
        fields = [
            'id',
            'aircraft',
            'aircraft_tail_number',
            'pilot',
            'pilot_name',
            'crew_members',
            'mission_type',
            'mission_status',
            'atd',
            'eta',
            'ata',
            'flight_datetime',
            'flight_hours',
            'fuel_used',
            'departure_base',
            'arrival_base',
            'remarks',
            'logged_by',
            'logged_by_username',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['mission_status', 'logged_by', 'created_at', 'updated_at']

    def validate(self, attrs):
        legacy_departure_time = attrs.pop('flight_datetime', None)
        if legacy_departure_time and 'atd' not in attrs:
            attrs['atd'] = legacy_departure_time

        flight_hours = attrs.get('flight_hours')
        departure = attrs.get('departure_base')
        arrival = attrs.get('arrival_base')
        pilot = attrs.get('pilot')
        atd = attrs.get('atd')
        eta = attrs.get('eta')
        ata = attrs.get('ata')

        if self.instance:
            if flight_hours is None:
                flight_hours = self.instance.flight_hours
            if departure is None:
                departure = self.instance.departure_base
            if arrival is None:
                arrival = self.instance.arrival_base
            if pilot is None:
                pilot = self.instance.pilot
            if atd is None:
                atd = self.instance.atd
            if eta is None:
                eta = self.instance.eta
            if ata is None:
                ata = self.instance.ata

        if flight_hours is not None and flight_hours <= 0:
            raise serializers.ValidationError('Flight hours must be greater than zero.')
        if not atd:
            raise serializers.ValidationError('ATD is required.')
        if not eta:
            raise serializers.ValidationError('ETA is required.')
        if eta < atd:
            raise serializers.ValidationError('ETA cannot be earlier than ATD.')
        if ata and ata < atd:
            raise serializers.ValidationError('ATA cannot be earlier than ATD.')
        if departure and arrival and departure == arrival:
            raise serializers.ValidationError('Departure and arrival bases must be different.')
        existing_pilot_name = self.instance.pilot_name if self.instance else ''
        if not pilot and not existing_pilot_name:
            raise serializers.ValidationError('A pilot must be selected for the flight.')
        return attrs


class FlightDataSerializer(serializers.ModelSerializer):
    aircraft_tail_number = serializers.CharField(source='flight_log.aircraft.tail_number', read_only=True)

    class Meta:
        model = FlightData
        fields = [
            'id',
            'flight_log',
            'aircraft_tail_number',
            'timestamp',
            'altitude',
            'speed',
            'engine_temp',
            'fuel_level',
            'heading',
            'created_at',
        ]
        read_only_fields = ['created_at']
