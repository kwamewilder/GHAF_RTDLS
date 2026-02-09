from django.db.models.signals import post_save
from django.dispatch import receiver

from dashboard.realtime import broadcast_dashboard_update

from .models import Alert, MaintenanceLog


@receiver(post_save, sender=MaintenanceLog)
def predictive_alert_logic(sender, instance, created, **kwargs):
    threshold = instance.aircraft.maintenance_threshold_hours
    if instance.total_flight_hours >= threshold:
        alert, alert_created = Alert.objects.get_or_create(
            aircraft=instance.aircraft,
            maintenance_log=instance,
            defaults={
                'title': 'Maintenance Threshold Reached',
                'message': (
                    f'Aircraft {instance.aircraft.tail_number} recorded {instance.total_flight_hours} '
                    f'flight hours (threshold: {threshold}). Maintenance officer action required.'
                ),
                'severity': Alert.Severity.HIGH,
                'recipient_role': 'maintenance',
            },
        )
        if not alert_created:
            alert.title = 'Maintenance Threshold Reached'
            alert.message = (
                f'Aircraft {instance.aircraft.tail_number} recorded {instance.total_flight_hours} '
                f'flight hours (threshold: {threshold}). Maintenance officer action required.'
            )
            alert.severity = Alert.Severity.HIGH
            alert.recipient_role = 'maintenance'
            alert.is_resolved = False
            alert.save(update_fields=['title', 'message', 'severity', 'recipient_role', 'is_resolved'])
    else:
        Alert.objects.filter(
            aircraft=instance.aircraft,
            maintenance_log=instance,
            is_resolved=False,
        ).update(is_resolved=True)

    if created:
        broadcast_dashboard_update(event='maintenance_log_created', payload={'maintenance_log_id': instance.id})


@receiver(post_save, sender=Alert)
def alert_realtime_update(sender, instance, created, **kwargs):
    if created:
        broadcast_dashboard_update(event='maintenance_alert', payload={'alert_id': instance.id})
