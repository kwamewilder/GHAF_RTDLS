from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Base(models.Model):
    name = models.CharField(max_length=64, unique=True)
    location = models.CharField(max_length=128)

    class Meta:
        verbose_name_plural = 'Bases'

    def __str__(self):
        return self.name


class Crew(models.Model):
    full_name = models.CharField(max_length=128)
    rank = models.CharField(max_length=64)
    role = models.CharField(max_length=64)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.full_name


class Pilot(models.Model):
    full_name = models.CharField(max_length=128)
    rank = models.CharField(max_length=64)
    contact_info = models.CharField(max_length=128, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['full_name']

    def __str__(self):
        return self.full_name


class Aircraft(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        IN_MISSION = 'in_mission', 'In Mission'
        IN_MAINTENANCE = 'in_maintenance', 'In Maintenance'

    tail_number = models.CharField(max_length=32, unique=True)
    aircraft_type = models.CharField(max_length=64, blank=True, default='')
    model = models.CharField(max_length=64)
    maintenance_threshold_hours = models.FloatField(default=100.0, validators=[MinValueValidator(1)])
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.AVAILABLE)
    home_base = models.ForeignKey(Base, on_delete=models.PROTECT, related_name='aircraft')

    def __str__(self):
        return f'{self.tail_number} ({self.model})'


class FlightLog(models.Model):
    class MissionStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'

    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE, related_name='flight_logs')
    pilot = models.ForeignKey(Pilot, on_delete=models.SET_NULL, null=True, blank=True, related_name='flight_logs')
    pilot_name = models.CharField(max_length=128, blank=True)
    crew_members = models.ManyToManyField(Crew, blank=True, related_name='flight_logs')
    mission_type = models.CharField(max_length=128)
    mission_status = models.CharField(max_length=16, choices=MissionStatus.choices, default=MissionStatus.ACTIVE)
    flight_datetime = models.DateTimeField()
    atd = models.DateTimeField()
    eta = models.DateTimeField()
    ata = models.DateTimeField(null=True, blank=True)
    flight_hours = models.FloatField(validators=[MinValueValidator(0.1)])
    fuel_used = models.FloatField(validators=[MinValueValidator(0.0)])
    departure_base = models.ForeignKey(Base, on_delete=models.PROTECT, related_name='departures')
    arrival_base = models.ForeignKey(Base, on_delete=models.PROTECT, related_name='arrivals')
    remarks = models.TextField(blank=True)
    logged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='flight_logs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-flight_datetime']

    def save(self, *args, **kwargs):
        if self.pilot:
            self.pilot_name = self.pilot.full_name
        if not self.atd and self.flight_datetime:
            self.atd = self.flight_datetime
        if self.atd:
            self.flight_datetime = self.atd
        if self.ata:
            self.mission_status = self.MissionStatus.COMPLETED
        else:
            self.mission_status = self.MissionStatus.ACTIVE
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.aircraft.tail_number} - {self.atd:%Y-%m-%d %H:%M}'


class FlightData(models.Model):
    flight_log = models.ForeignKey(FlightLog, on_delete=models.CASCADE, related_name='telemetry')
    timestamp = models.DateTimeField(default=timezone.now)
    altitude = models.FloatField(validators=[MinValueValidator(0.0)])
    speed = models.FloatField(validators=[MinValueValidator(0.0)])
    engine_temp = models.FloatField(validators=[MinValueValidator(0.0)])
    fuel_level = models.FloatField(validators=[MinValueValidator(0.0)])
    heading = models.FloatField(validators=[MinValueValidator(0.0)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'FD#{self.id} - Flight {self.flight_log_id} @ {self.timestamp:%Y-%m-%d %H:%M:%S}'
