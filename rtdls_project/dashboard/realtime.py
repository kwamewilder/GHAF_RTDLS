from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .services import get_dashboard_metrics


def broadcast_dashboard_update(event='dashboard_refresh', payload=None):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    data = get_dashboard_metrics()
    async_to_sync(channel_layer.group_send)(
        'dashboard',
        {
            'type': 'dashboard.event',
            'event': event,
            'payload': payload or {},
            'metrics': data,
        },
    )
