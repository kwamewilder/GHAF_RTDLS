from datetime import timedelta

from django.db import migrations, models


def backfill_flight_timing(apps, schema_editor):
    FlightLog = apps.get_model('operations', 'FlightLog')

    for log in FlightLog.objects.all().iterator():
        atd_value = log.atd or log.flight_datetime
        eta_value = log.eta
        if eta_value is None:
            hours = float(log.flight_hours or 0.0)
            eta_value = atd_value + timedelta(hours=hours)

        ata_value = log.ata
        if ata_value is None and log.mission_status == 'completed':
            ata_value = eta_value

        mission_status = 'completed' if ata_value else 'active'

        FlightLog.objects.filter(pk=log.pk).update(
            atd=atd_value,
            eta=eta_value,
            ata=ata_value,
            mission_status=mission_status,
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0003_aircraft_aircraft_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='flightlog',
            name='atd',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='flightlog',
            name='eta',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='flightlog',
            name='ata',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='flightlog',
            name='mission_status',
            field=models.CharField(choices=[('active', 'Active'), ('completed', 'Completed')], default='active', max_length=16),
        ),
        migrations.RunPython(backfill_flight_timing, noop_reverse),
        migrations.AlterField(
            model_name='flightlog',
            name='atd',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='flightlog',
            name='eta',
            field=models.DateTimeField(),
        ),
    ]
