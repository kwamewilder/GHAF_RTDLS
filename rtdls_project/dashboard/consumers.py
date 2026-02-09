import json

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

from .services import get_dashboard_metrics


class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        await self.channel_layer.group_add('dashboard', self.channel_name)
        await self.accept()

        initial_metrics = await sync_to_async(get_dashboard_metrics)()
        await self.send(
            text_data=json.dumps(
                {
                    'event': 'initial_state',
                    'payload': {},
                    'metrics': initial_metrics,
                }
            )
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('dashboard', self.channel_name)

    async def dashboard_event(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    'event': event.get('event'),
                    'payload': event.get('payload', {}),
                    'metrics': event.get('metrics', {}),
                }
            )
        )
