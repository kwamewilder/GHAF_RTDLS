from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from maintenance.models import Alert, MaintenanceLog
from operations.models import Aircraft, Base

User = get_user_model()


class PredictiveMaintenanceTests(TestCase):
    def setUp(self):
        self.base = Base.objects.create(name='Takoradi', location='Takoradi')
        self.aircraft = Aircraft.objects.create(
            tail_number='GAF-002',
            model='L-39',
            maintenance_threshold_hours=100,
            home_base=self.base,
        )
        self.maintainer = User.objects.create_user(username='maint', password='StrongPass123!', role='maintenance')

    def test_alert_is_generated_when_threshold_reached(self):
        MaintenanceLog.objects.create(
            aircraft=self.aircraft,
            total_flight_hours=120,
            last_maintenance_date=date.today(),
            component_status='Engine: attention required',
            maintenance_notes='Threshold exceeded',
            logged_by=self.maintainer,
        )

        self.assertEqual(Alert.objects.count(), 1)
        alert = Alert.objects.first()
        self.assertEqual(alert.recipient_role, 'maintenance')
        self.assertFalse(alert.is_resolved)
