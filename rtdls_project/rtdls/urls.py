from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from accounts.api import UserViewSet
from maintenance.api import MaintenanceLogViewSet, AlertViewSet
from operations.api import AircraftViewSet, BaseViewSet, CrewViewSet, FlightDataViewSet, FlightLogViewSet, PilotViewSet
from reports_app.views import (
    reports_dashboard_view,
    report_export,
    daily_flight_report,
    weekly_maintenance_report,
    aircraft_utilization_report,
)
from .views import healthz

router = DefaultRouter()
router.register('users', UserViewSet, basename='api-users')
router.register('aircraft', AircraftViewSet, basename='api-aircraft')
router.register('bases', BaseViewSet, basename='api-bases')
router.register('crew', CrewViewSet, basename='api-crew')
router.register('pilots', PilotViewSet, basename='api-pilots')
router.register('flight-logs', FlightLogViewSet, basename='api-flight-logs')
router.register('flight-data', FlightDataViewSet, basename='api-flight-data')
router.register('maintenance-logs', MaintenanceLogViewSet, basename='api-maintenance-logs')
router.register('alerts', AlertViewSet, basename='api-alerts')

urlpatterns = [
    path('healthz/', healthz, name='healthz'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('operations/', include('operations.urls')),
    path('maintenance/', include('maintenance.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/', include(router.urls)),
    path('reports/', reports_dashboard_view, name='reports-dashboard'),
    path('reports/export/', report_export, name='report-export'),
    path('reports/daily-flight/', daily_flight_report, name='daily-flight-report'),
    path('reports/weekly-maintenance/', weekly_maintenance_report, name='weekly-maintenance-report'),
    path('reports/aircraft-utilization/', aircraft_utilization_report, name='aircraft-utilization-report'),
    path('', RedirectView.as_view(pattern_name='dashboard:home', permanent=False)),
]
