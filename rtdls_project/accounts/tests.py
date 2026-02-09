from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from audittrail.models import AuditLog
from operations.models import Aircraft, Base

User = get_user_model()


class AccountAuditTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ops', password='StrongPass123!', role='flight_ops')

    def test_login_logout_signals_are_audited(self):
        user_logged_in.send(sender=User, request=None, user=self.user)
        user_logged_out.send(sender=User, request=None, user=self.user)

        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.LOGIN, user=self.user).exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.LOGOUT, user=self.user).exists())

    def test_role_change_generates_audit_log(self):
        self.user.role = 'commander'
        self.user.save()

        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.Action.ROLE_CHANGE,
                entity='User',
                entity_id=self.user.id,
            ).exists()
        )


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class LoginRecaptchaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='pilot_user', password='StrongPass123!', role='flight_ops')

    @override_settings(RECAPTCHA_ENABLED=True, RECAPTCHA_SITE_KEY='site-key', RECAPTCHA_SECRET_KEY='secret-key')
    def test_login_requires_recaptcha_token(self):
        response = self.client.post(
            '/accounts/login/',
            {'username': 'pilot_user', 'password': 'StrongPass123!'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please complete the reCAPTCHA challenge.')

    @override_settings(RECAPTCHA_ENABLED=True, RECAPTCHA_SITE_KEY='site-key', RECAPTCHA_SECRET_KEY='secret-key')
    @patch('accounts.forms.verify_recaptcha_token', return_value=(True, ''))
    def test_login_succeeds_with_valid_recaptcha(self, _mock_verify):
        response = self.client.post(
            '/accounts/login/',
            {
                'username': 'pilot_user',
                'password': 'StrongPass123!',
                'g-recaptcha-response': 'mock-token',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/dashboard/', response.url)

    @override_settings(RECAPTCHA_ENABLED=True, RECAPTCHA_SITE_KEY='site-key', RECAPTCHA_SECRET_KEY='secret-key')
    @patch('accounts.forms.verify_recaptcha_token', return_value=(False, 'Invalid reCAPTCHA response. Please retry.'))
    def test_login_fails_with_invalid_recaptcha(self, _mock_verify):
        response = self.client.post(
            '/accounts/login/',
            {
                'username': 'pilot_user',
                'password': 'StrongPass123!',
                'g-recaptcha-response': 'invalid-token',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid reCAPTCHA response. Please retry.')


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class SettingsPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin_user',
            password='StrongPass123!',
            role='admin',
            email='admin@example.mil',
        )
        self.flight_ops_user = User.objects.create_user(
            username='ops_user',
            password='StrongPass123!',
            role='flight_ops',
            email='ops@example.mil',
        )
        self.base = Base.objects.create(name='Accra AFB', location='Accra')

    def test_settings_page_loads_for_authenticated_user(self):
        self.client.login(username='admin_user', password='StrongPass123!')
        response = self.client.get('/accounts/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard Overview')
        self.assertContains(response, 'User Management')
        self.assertContains(response, 'Aircraft Registry')

    def test_settings_page_honors_section_query_param(self):
        self.client.login(username='admin_user', password='StrongPass123!')
        response = self.client.get('/accounts/profile/?section=system-logs')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-default-section="system-logs"')

    def test_admin_can_add_aircraft_from_registry(self):
        self.client.login(username='admin_user', password='StrongPass123!')
        response = self.client.post(
            '/accounts/profile/?section=aircraft-registry',
            data={
                'settings_action': 'add_aircraft',
                'aircraft-tail_number': '9g aaa',
                'aircraft-aircraft_type': 'Transport',
                'aircraft-model': 'CASA C295',
                'aircraft-home_base': str(self.base.id),
                'aircraft-maintenance_threshold_hours': '120',
                'aircraft-status': 'available',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Aircraft.objects.filter(tail_number='9G AAA').exists())
        aircraft = Aircraft.objects.get(tail_number='9G AAA')
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.Action.CREATE,
                entity='Aircraft',
                entity_id=aircraft.id,
            ).exists()
        )

    def test_non_admin_cannot_add_aircraft_from_registry(self):
        self.client.login(username='ops_user', password='StrongPass123!')
        response = self.client.post(
            '/accounts/profile/?section=aircraft-registry',
            data={
                'settings_action': 'add_aircraft',
                'aircraft-tail_number': '9G BBB',
                'aircraft-aircraft_type': 'Trainer',
                'aircraft-model': 'DA42',
                'aircraft-home_base': str(self.base.id),
                'aircraft-maintenance_threshold_hours': '90',
                'aircraft-status': 'available',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Aircraft.objects.filter(tail_number='9G BBB').exists())

    def test_admin_can_add_user_from_settings_modal(self):
        self.client.login(username='admin_user', password='StrongPass123!')
        response = self.client.post(
            '/accounts/profile/?section=user-management',
            data={
                'settings_action': 'add_user',
                'newuser-username': 'new_ops_user',
                'newuser-first_name': 'New',
                'newuser-last_name': 'Operator',
                'newuser-email': 'new.ops@example.mil',
                'newuser-role': 'maintenance',
                'newuser-password1': 'StrongPass123!',
                'newuser-password2': 'StrongPass123!',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='new_ops_user').exists())
        created_user = User.objects.get(username='new_ops_user')
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.Action.CREATE,
                entity='User',
                entity_id=created_user.id,
            ).exists()
        )

    def test_non_admin_cannot_add_user_from_settings_modal(self):
        self.client.login(username='ops_user', password='StrongPass123!')
        response = self.client.post(
            '/accounts/profile/?section=user-management',
            data={
                'settings_action': 'add_user',
                'newuser-username': 'blocked_user',
                'newuser-first_name': 'Blocked',
                'newuser-last_name': 'User',
                'newuser-email': 'blocked@example.mil',
                'newuser-role': 'auditor',
                'newuser-password1': 'StrongPass123!',
                'newuser-password2': 'StrongPass123!',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(username='blocked_user').exists())

    def test_admin_can_edit_user_from_settings_modal(self):
        target_user = User.objects.create_user(
            username='editable_user',
            password='StrongPass123!',
            role='auditor',
            email='editable@example.mil',
            first_name='Edit',
            last_name='Me',
        )
        self.client.login(username='admin_user', password='StrongPass123!')
        response = self.client.post(
            '/accounts/profile/?section=user-management',
            data={
                'settings_action': 'edit_user',
                'edit_user_id': str(target_user.id),
                'edituser-username': 'editable_user',
                'edituser-first_name': 'Edited',
                'edituser-last_name': 'Person',
                'edituser-email': 'edited@example.mil',
                'edituser-role': 'maintenance',
                'edituser-is_active': 'on',
            },
        )
        self.assertEqual(response.status_code, 302)
        target_user.refresh_from_db()
        self.assertEqual(target_user.first_name, 'Edited')
        self.assertEqual(target_user.last_name, 'Person')
        self.assertEqual(target_user.email, 'edited@example.mil')
        self.assertEqual(target_user.role, 'maintenance')
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.Action.UPDATE,
                entity='User',
                entity_id=target_user.id,
            ).exists()
        )
        role_changes = AuditLog.objects.filter(
            action=AuditLog.Action.ROLE_CHANGE,
            entity='User',
            entity_id=target_user.id,
        )
        self.assertEqual(role_changes.count(), 1)
        self.assertEqual(role_changes.first().user_id, self.user.id)

    def test_non_admin_cannot_edit_user_from_settings_modal(self):
        target_user = User.objects.create_user(
            username='protected_user',
            password='StrongPass123!',
            role='auditor',
            email='protected@example.mil',
        )
        self.client.login(username='ops_user', password='StrongPass123!')
        response = self.client.post(
            '/accounts/profile/?section=user-management',
            data={
                'settings_action': 'edit_user',
                'edit_user_id': str(target_user.id),
                'edituser-username': 'protected_user',
                'edituser-first_name': 'Hacked',
                'edituser-last_name': 'Attempt',
                'edituser-email': 'hacked@example.mil',
                'edituser-role': 'admin',
                'edituser-is_active': 'on',
            },
        )
        self.assertEqual(response.status_code, 302)
        target_user.refresh_from_db()
        self.assertNotEqual(target_user.first_name, 'Hacked')

    def test_admin_can_edit_aircraft_from_registry_modal(self):
        aircraft = Aircraft.objects.create(
            tail_number='9G OLD',
            aircraft_type='Transport',
            model='CASA C295',
            home_base=self.base,
            maintenance_threshold_hours=100,
            status='available',
        )
        self.client.login(username='admin_user', password='StrongPass123!')
        response = self.client.post(
            '/accounts/profile/?section=aircraft-registry',
            data={
                'settings_action': 'edit_aircraft',
                'edit_aircraft_id': str(aircraft.id),
                'editaircraft-tail_number': '9G NEW',
                'editaircraft-aircraft_type': 'Trainer',
                'editaircraft-model': 'DA42',
                'editaircraft-home_base': str(self.base.id),
                'editaircraft-maintenance_threshold_hours': '130',
                'editaircraft-status': 'in_maintenance',
            },
        )
        self.assertEqual(response.status_code, 302)
        aircraft.refresh_from_db()
        self.assertEqual(aircraft.tail_number, '9G NEW')
        self.assertEqual(aircraft.aircraft_type, 'Trainer')
        self.assertEqual(aircraft.model, 'DA42')
        self.assertEqual(aircraft.status, 'in_maintenance')
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.Action.UPDATE,
                entity='Aircraft',
                entity_id=aircraft.id,
            ).exists()
        )

    def test_non_admin_cannot_edit_aircraft_from_registry_modal(self):
        aircraft = Aircraft.objects.create(
            tail_number='9G LOCK',
            aircraft_type='Transport',
            model='CASA C295',
            home_base=self.base,
            maintenance_threshold_hours=100,
            status='available',
        )
        self.client.login(username='ops_user', password='StrongPass123!')
        response = self.client.post(
            '/accounts/profile/?section=aircraft-registry',
            data={
                'settings_action': 'edit_aircraft',
                'edit_aircraft_id': str(aircraft.id),
                'editaircraft-tail_number': '9G BAD',
                'editaircraft-aircraft_type': 'Trainer',
                'editaircraft-model': 'DA42',
                'editaircraft-home_base': str(self.base.id),
                'editaircraft-maintenance_threshold_hours': '130',
                'editaircraft-status': 'in_maintenance',
            },
        )
        self.assertEqual(response.status_code, 302)
        aircraft.refresh_from_db()
        self.assertEqual(aircraft.tail_number, '9G LOCK')


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ApiLoginThrottleTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        User.objects.create_user(username='throttle_user', password='StrongPass123!', role='auditor')

    def test_login_endpoint_is_rate_limited(self):
        payload = {'username': 'throttle_user', 'password': 'wrong'}
        last_status = None
        for _ in range(12):
            response = self.client.post('/api/users/login/', payload, format='json')
            last_status = response.status_code
        self.assertEqual(last_status, 429)
