from django.db.models.signals import post_save
from django.dispatch import receiver

from dashboard.realtime import broadcast_dashboard_update

from .models import FlightData, FlightLog


@receiver(post_save, sender=FlightLog)
def flight_log_realtime_update(sender, instance, created, **kwargs):
    if created:
        broadcast_dashboard_update(event='flight_log_created', payload={'flight_log_id': instance.id})


@receiver(post_save, sender=FlightData)
def flight_data_realtime_update(sender, instance, created, **kwargs):
    if created:
        broadcast_dashboard_update(event='flight_data_logged', payload={'flight_data_id': instance.id})
