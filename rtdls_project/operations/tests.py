from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from operations.models import Aircraft, Base, FlightData, FlightLog, Pilot

User = get_user_model()


class FlightLogAccessTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.base_a = Base.objects.create(name='Accra', location='Accra')
        self.base_b = Base.objects.create(name='Tamale', location='Tamale')
        self.aircraft = Aircraft.objects.create(
            tail_number='GAF-001',
            model='C-295',
            maintenance_threshold_hours=120,
            home_base=self.base_a,
        )
        self.pilot = Pilot.objects.create(
            full_name='Wing Cdr Mensah',
            rank='Wing Cdr',
            contact_info='+233-024-000-0001',
            is_active=True,
        )
        self.admin = User.objects.create_user(username='admin', password='StrongPass123!', role='admin')
        self.ops = User.objects.create_user(username='ops', password='StrongPass123!', role='flight_ops')
        self.auditor = User.objects.create_user(username='auditor', password='StrongPass123!', role='auditor')

    def test_flight_ops_can_create_flight_log(self):
        self.client.force_authenticate(self.ops)
        response = self.client.post(
            '/api/flight-logs/',
            {
                'aircraft': self.aircraft.id,
                'pilot': self.pilot.id,
                'mission_type': 'Recon',
                'atd': (timezone.now() - timedelta(hours=1)).isoformat(),
                'eta': (timezone.now() + timedelta(hours=1)).isoformat(),
                'flight_hours': 2.5,
                'fuel_used': 400,
                'departure_base': self.base_a.id,
                'arrival_base': self.base_b.id,
                'remarks': 'Routine patrol',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(FlightLog.objects.count(), 1)
        self.assertEqual(FlightLog.objects.first().pilot_id, self.pilot.id)
        self.assertEqual(FlightLog.objects.first().mission_status, FlightLog.MissionStatus.ACTIVE)

    def test_auditor_cannot_create_flight_log(self):
        self.client.force_authenticate(self.auditor)
        response = self.client.post(
            '/api/flight-logs/',
            {
                'aircraft': self.aircraft.id,
                'pilot': self.pilot.id,
                'mission_type': 'Recon',
                'atd': timezone.now().isoformat(),
                'eta': (timezone.now() + timedelta(hours=2)).isoformat(),
                'flight_hours': 2.5,
                'fuel_used': 400,
                'departure_base': self.base_a.id,
                'arrival_base': self.base_b.id,
                'remarks': 'Routine patrol',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_flight_ops_can_log_flight_telemetry(self):
        flight_log = FlightLog.objects.create(
            aircraft=self.aircraft,
            pilot=self.pilot,
            mission_type='Training',
            atd=timezone.now() - timedelta(minutes=30),
            eta=timezone.now() + timedelta(minutes=30),
            flight_hours=1.2,
            fuel_used=180,
            departure_base=self.base_a,
            arrival_base=self.base_b,
            remarks='Telemetry test',
            logged_by=self.ops,
        )
        self.client.force_authenticate(self.ops)
        response = self.client.post(
            '/api/flight-data/',
            {
                'flight_log': flight_log.id,
                'timestamp': timezone.now().isoformat(),
                'altitude': 5200,
                'speed': 310,
                'engine_temp': 88,
                'fuel_level': 65,
                'heading': 147,
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(FlightData.objects.count(), 1)

    def test_add_ata_marks_flight_completed(self):
        flight_log = FlightLog.objects.create(
            aircraft=self.aircraft,
            pilot=self.pilot,
            mission_type='Recon',
            atd=timezone.now() - timedelta(hours=2),
            eta=timezone.now() - timedelta(minutes=30),
            flight_hours=1.5,
            fuel_used=210,
            departure_base=self.base_a,
            arrival_base=self.base_b,
            remarks='Awaiting arrival confirmation',
            logged_by=self.ops,
        )
        self.assertEqual(flight_log.mission_status, FlightLog.MissionStatus.ACTIVE)

        self.client.force_authenticate(self.ops)
        ata_time = timezone.now() - timedelta(minutes=20)
        response = self.client.patch(
            f'/api/flight-logs/{flight_log.id}/',
            {'ata': ata_time.isoformat()},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        flight_log.refresh_from_db()
        self.assertEqual(flight_log.mission_status, FlightLog.MissionStatus.COMPLETED)
        self.assertIsNotNone(flight_log.ata)
