from django.urls import path

from .views import dashboard_home, opensky_feed

app_name = 'dashboard'

urlpatterns = [
    path('', dashboard_home, name='home'),
    path('api/opensky/', opensky_feed, name='opensky-feed'),
    path('api/opensky/ghana/', opensky_feed, name='opensky-ghana'),
]
