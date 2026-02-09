from django.contrib import admin

from .models import Aircraft, Base, Crew, FlightData, FlightLog, Pilot


@admin.register(Base)
class BaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'location')
    search_fields = ('name', 'location')


@admin.register(Crew)
class CrewAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'rank', 'role', 'is_available')
    list_filter = ('is_available', 'role')
    search_fields = ('full_name', 'rank', 'role')


@admin.register(Pilot)
class PilotAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'rank', 'contact_info', 'is_active')
    list_filter = ('is_active', 'rank')
    search_fields = ('full_name', 'rank', 'contact_info')


@admin.register(Aircraft)
class AircraftAdmin(admin.ModelAdmin):
    list_display = ('tail_number', 'model', 'status', 'maintenance_threshold_hours', 'home_base')
    list_filter = ('status', 'home_base')
    search_fields = ('tail_number', 'model')


@admin.register(FlightLog)
class FlightLogAdmin(admin.ModelAdmin):
    list_display = ('aircraft', 'pilot', 'pilot_name', 'mission_type', 'mission_status', 'atd', 'eta', 'ata', 'flight_hours', 'logged_by')
    list_filter = ('mission_status', 'mission_type', 'atd')
    search_fields = ('pilot_name', 'mission_type', 'aircraft__tail_number')
    autocomplete_fields = ('crew_members',)


@admin.register(FlightData)
class FlightDataAdmin(admin.ModelAdmin):
    list_display = ('flight_log', 'timestamp', 'altitude', 'speed', 'engine_temp', 'fuel_level', 'heading')
    list_filter = ('timestamp',)
    search_fields = ('flight_log__aircraft__tail_number',)
