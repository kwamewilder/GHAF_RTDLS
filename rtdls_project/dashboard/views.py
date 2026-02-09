from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.urls import reverse

from audittrail.models import AuditLog, log_action
from maintenance.models import Alert
from operations.models import FlightLog

from .services import (
    DEFAULT_OPENSKY_SCOPE,
    GHANA_BBOX,
    OPENSKY_SCOPES,
    get_dashboard_metrics,
    get_opensky_feed,
)


@login_required
def dashboard_home(request):
    metrics = get_dashboard_metrics()
    latest_flights = FlightLog.objects.select_related('aircraft', 'departure_base', 'arrival_base', 'logged_by').all()[:10]
    latest_alerts = Alert.objects.select_related('aircraft').filter(is_resolved=False)[:8]

    log_action(
        user=request.user,
        action=AuditLog.Action.VIEW,
        entity='Dashboard',
        entity_id=None,
        description='Viewed dashboard',
        ip_address=request.META.get('REMOTE_ADDR'),
    )

    return render(
        request,
        'dashboard/home.html',
        {
            'metrics': metrics,
            'latest_flights': latest_flights,
            'latest_alerts': latest_alerts,
            'ghana_bbox': GHANA_BBOX,
            'opensky_scopes': [
                {'key': key, 'label': value['label']} for key, value in OPENSKY_SCOPES.items()
            ],
            'opensky_default_scope': DEFAULT_OPENSKY_SCOPE,
            'opensky_feed_url': reverse('dashboard:opensky-feed'),
            'opensky_legacy_feed_url': reverse('dashboard:opensky-ghana'),
        },
    )


@login_required
def opensky_feed(request):
    requested_scope = request.GET.get('scope')
    if not requested_scope and request.path.endswith('/ghana/'):
        requested_scope = 'ghana'
    if not requested_scope:
        requested_scope = DEFAULT_OPENSKY_SCOPE

    try:
        payload = get_opensky_feed(requested_scope)
    except Exception:
        payload = {
            'source': 'opensky',
            'generated_at': timezone.now().isoformat(),
            'requested_scope': requested_scope,
            'requested_scope_label': requested_scope.replace('_', ' ').title(),
            'query_scope': requested_scope,
            'query_scope_label': requested_scope.replace('_', ' ').title(),
            'query_bbox': None,
            'flights': [],
            'error': 'Feed unavailable',
        }
    return JsonResponse(payload)
