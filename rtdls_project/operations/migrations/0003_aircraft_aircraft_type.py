from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0002_pilot_alter_flightlog_pilot_name_flightdata_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='aircraft',
            name='aircraft_type',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
    ]
