from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone

from operations.models import Aircraft, Base, FlightLog, Pilot

User = get_user_model()


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ReportExportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='commander', password='StrongPass123!', role='commander')
        self.client.force_login(self.user)
        self.base_a = Base.objects.create(name='Accra', location='Accra')
        self.base_b = Base.objects.create(name='Tamale', location='Tamale')
        self.aircraft = Aircraft.objects.create(tail_number='GAF-003', model='CN-235', home_base=self.base_a)
        self.pilot = Pilot.objects.create(
            full_name='Sqn Ldr Addo',
            rank='Sqn Ldr',
            contact_info='+233-024-000-0002',
            is_active=True,
        )

        atd = timezone.now() - timedelta(hours=2)
        FlightLog.objects.create(
            aircraft=self.aircraft,
            pilot=self.pilot,
            mission_type='Transport',
            atd=atd,
            eta=atd + timedelta(hours=1, minutes=50),
            ata=atd + timedelta(hours=1, minutes=48),
            flight_hours=1.8,
            fuel_used=250,
            departure_base=self.base_a,
            arrival_base=self.base_b,
            remarks='Personnel transfer',
            logged_by=self.user,
        )

    def test_daily_report_pdf(self):
        response = self.client.get('/reports/daily-flight/?format=pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_reports_dashboard_page(self):
        response = self.client.get('/reports/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Report Configuration')

    def test_reports_export_csv(self):
        response = self.client.get('/reports/export/?format=csv')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')

    def test_reports_export_csv_sanitizes_formula_cells(self):
        self.pilot.full_name = '=2+2'
        self.pilot.save()
        log = FlightLog.objects.first()
        log.pilot = self.pilot
        log.save()

        response = self.client.get('/reports/export/?format=csv')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn("'=2+2", content)

    def test_utilization_report_xlsx(self):
        response = self.client.get('/reports/aircraft-utilization/?format=xlsx')
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', response['Content-Type'])
