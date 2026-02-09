from django.http import JsonResponse
from django.db import connections
from channels.layers import get_channel_layer
from django.utils import timezone


def healthz(_request):
    details = {
        'timestamp': timezone.now().isoformat(),
    }

    db_ok = True
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except Exception:
        db_ok = False
    details['database'] = 'ok' if db_ok else 'error'

    try:
        channel_layer = get_channel_layer()
        details['channels'] = 'ok' if channel_layer else 'not-configured'
    except Exception:
        details['channels'] = 'error'

    status_code = 200 if db_ok else 503
    details['status'] = 'ok' if status_code == 200 else 'degraded'
    return JsonResponse(details, status=status_code)
