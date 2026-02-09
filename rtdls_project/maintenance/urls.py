from django.urls import path

from .views import maintenance_log_create_view

app_name = 'maintenance'

urlpatterns = [
    path('logs/new/', maintenance_log_create_view, name='log-create'),
]
