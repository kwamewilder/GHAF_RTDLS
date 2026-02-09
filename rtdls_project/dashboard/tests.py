from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings
from unittest.mock import patch

User = get_user_model()


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class SecurityViewTests(TestCase):
    def test_dashboard_requires_authentication(self):
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_authenticated_user_can_view_dashboard(self):
        user = User.objects.create_user(username='viewer', password='StrongPass123!', role='auditor')
        self.client.force_login(user)
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_opensky_feed_requires_authentication(self):
        response = self.client.get('/dashboard/api/opensky/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    @patch('dashboard.views.get_opensky_feed')
    def test_authenticated_user_can_fetch_opensky_feed(self, mock_feed):
        user = User.objects.create_user(username='opsviewer', password='StrongPass123!', role='flight_ops')
        self.client.force_login(user)
        mock_feed.return_value = {
            'source': 'opensky',
            'generated_at': '2026-02-07T15:20:00+00:00',
            'requested_scope': 'africa',
            'requested_scope_label': 'Africa',
            'query_scope': 'africa',
            'query_scope_label': 'Africa',
            'query_bbox': {'lamin': -35.0, 'lomin': -20.0, 'lamax': 38.0, 'lomax': 55.0},
            'flights': [],
        }
        response = self.client.get('/dashboard/api/opensky/?scope=africa')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content.decode('utf-8'),
            {
                'source': 'opensky',
                'generated_at': '2026-02-07T15:20:00+00:00',
                'requested_scope': 'africa',
                'requested_scope_label': 'Africa',
                'query_scope': 'africa',
                'query_scope_label': 'Africa',
                'query_bbox': {'lamin': -35.0, 'lomin': -20.0, 'lamax': 38.0, 'lomax': 55.0},
                'flights': [],
            },
        )
