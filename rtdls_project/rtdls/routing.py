from django.urls import path
from dashboard.consumers import DashboardConsumer

websocket_urlpatterns = [
    path('ws/dashboard/', DashboardConsumer.as_asgi()),
]
