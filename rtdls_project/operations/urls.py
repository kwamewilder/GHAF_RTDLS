from django.urls import path

from .views import flight_log_create_view, flight_log_update_view

app_name = 'operations'

urlpatterns = [
    path('flight-logs/new/', flight_log_create_view, name='flight-log-create'),
    path('flight-logs/<int:pk>/edit/', flight_log_update_view, name='flight-log-update'),
]
