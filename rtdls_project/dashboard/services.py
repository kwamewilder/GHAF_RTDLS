import json
import os
import base64
import random
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.cache import cache
from django.db.models import Q, Sum
from django.utils import timezone

from maintenance.models import Alert
from operations.models import Aircraft, Crew, FlightData, FlightLog

GHANA_BBOX = {
    'lamin': 4.5,
    'lomin': -3.5,
    'lamax': 11.5,
    'lomax': 1.5,
}

WEST_AFRICA_BBOX = {
    'lamin': 2.0,
    'lomin': -8.0,
    'lamax': 14.0,
    'lomax': 4.0,
}

AFRICA_BBOX = {
    'lamin': -35.0,
    'lomin': -20.0,
    'lamax': 38.0,
    'lomax': 55.0,
}

DEFAULT_OPENSKY_SCOPES = {
    'ghana': {
        'label': 'Ghana',
        'bbox': GHANA_BBOX,
    },
    'west_africa': {
        'label': 'West Africa',
        'bbox': WEST_AFRICA_BBOX,
    },
    'africa': {
        'label': 'Africa',
        'bbox': AFRICA_BBOX,
    },
    'global': {
        'label': 'Global',
        'bbox': None,
    },
}


def _coerce_bbox(raw_bbox):
    if raw_bbox is None:
        return None
    if not isinstance(raw_bbox, dict):
        return None
    required = ('lamin', 'lomin', 'lamax', 'lomax')
    try:
        bbox = {key: float(raw_bbox[key]) for key in required}
    except (KeyError, TypeError, ValueError):
        return None
    return bbox


def _load_opensky_scopes():
    raw = os.getenv('OPENSKY_SCOPES_JSON', '').strip()
    if not raw:
        return DEFAULT_OPENSKY_SCOPES
    try:
        payload = json.loads(raw)
    except ValueError:
        return DEFAULT_OPENSKY_SCOPES
    if not isinstance(payload, dict):
        return DEFAULT_OPENSKY_SCOPES

    parsed_scopes = {}
    for key, value in payload.items():
        if not isinstance(key, str) or not isinstance(value, dict):
            continue
        scope_key = key.strip().lower().replace(' ', '_')
        if not scope_key:
            continue
        label = str(value.get('label') or scope_key.replace('_', ' ').title())
        bbox = _coerce_bbox(value.get('bbox'))
        if value.get('bbox') is not None and bbox is None:
            continue
        parsed_scopes[scope_key] = {'label': label, 'bbox': bbox}

    return parsed_scopes or DEFAULT_OPENSKY_SCOPES


OPENSKY_SCOPES = _load_opensky_scopes()

DEFAULT_OPENSKY_SCOPE = os.getenv('OPENSKY_DEFAULT_SCOPE', 'africa').strip().lower()
if DEFAULT_OPENSKY_SCOPE not in OPENSKY_SCOPES:
    DEFAULT_OPENSKY_SCOPE = 'africa'


def _env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def _in_bbox(latitude, longitude, bbox):
    if bbox is None:
        return True
    return (
        bbox['lamin'] <= latitude <= bbox['lamax']
        and bbox['lomin'] <= longitude <= bbox['lomax']
    )


def _state_in_bbox(state, bbox):
    if bbox is None:
        return True
    longitude = state[5]
    latitude = state[6]
    if longitude is None or latitude is None:
        return False
    return _in_bbox(float(latitude), float(longitude), bbox)


def _build_demo_flights(scope_key, bbox):
    random.seed(f'ghaf-rtdls-{scope_key}')
    seed_points = [
        ('GH101', 'Ghana', 5.6037, -0.1870),
        ('GH223', 'Ghana', 6.6885, -1.6244),
        ('NG402', 'Nigeria', 6.5244, 3.3792),
        ('CI551', "Cote d'Ivoire", 5.3600, -4.0083),
        ('SN310', 'Senegal', 14.7167, -17.4677),
        ('DZ808', 'Algeria', 36.7538, 3.0588),
        ('EG972', 'Egypt', 30.0444, 31.2357),
        ('KE117', 'Kenya', -1.2921, 36.8219),
        ('ZA440', 'South Africa', -26.2041, 28.0473),
        ('MA266', 'Morocco', 33.5731, -7.5898),
        ('ET759', 'Ethiopia', 8.9806, 38.7578),
        ('TN620', 'Tunisia', 36.8065, 10.1815),
    ]
    if scope_key == 'global':
        seed_points.extend(
            [
                ('US001', 'United States', 40.7128, -74.0060),
                ('GB241', 'United Kingdom', 51.5072, -0.1276),
                ('IN780', 'India', 28.6139, 77.2090),
            ]
        )

    flights = []
    for idx, (callsign, country, lat, lon) in enumerate(seed_points):
        if not _in_bbox(lat, lon, bbox):
            continue
        flights.append(
            {
                'icao24': f'demo{idx:02d}',
                'callsign': callsign,
                'origin_country': country,
                'latitude': round(lat + random.uniform(-0.18, 0.18), 5),
                'longitude': round(lon + random.uniform(-0.22, 0.22), 5),
                'altitude_ft': random.randrange(14000, 36000, 500),
                'speed_knots': random.randrange(260, 490, 10),
                'heading': round(random.uniform(0, 359.9), 1),
                'on_ground': False,
                'is_demo': True,
            }
        )

    return flights[:20]


def _fetch_opensky_states(bbox, timeout):
    endpoint = os.getenv('OPENSKY_STATES_URL', 'https://opensky-network.org/api/states/all')
    if bbox:
        params = urlencode(bbox)
        url = f'{endpoint}?{params}'
    else:
        url = endpoint
    request = Request(url, headers={'User-Agent': 'GAF-RTDLS-Dashboard/1.0'})

    username = os.getenv('OPENSKY_USERNAME', '').strip()
    password = os.getenv('OPENSKY_PASSWORD', '').strip()
    if username and password:
        token = base64.b64encode(f'{username}:{password}'.encode('utf-8')).decode('ascii')
        request.add_header('Authorization', f'Basic {token}')

    with urlopen(request, timeout=timeout) as response:
        content = response.read().decode('utf-8')
        raw = json.loads(content)
    return raw.get('states') or []


def _normalize_opensky_state(state):
    longitude = state[5]
    latitude = state[6]
    if longitude is None or latitude is None:
        return None

    callsign = (state[1] or '').strip() or (state[0] or '').upper()
    speed_ms = float(state[9] or 0.0)
    altitude_m = float((state[13] if state[13] is not None else state[7]) or 0.0)
    return {
        'icao24': state[0],
        'callsign': callsign,
        'origin_country': state[2],
        'longitude': round(float(longitude), 5),
        'latitude': round(float(latitude), 5),
        'altitude_ft': int(round(altitude_m * 3.28084)),
        'speed_knots': int(round(speed_ms * 1.94384)),
        'heading': round(float(state[10] or 0.0), 1),
        'on_ground': bool(state[8]),
    }


def get_opensky_feed(scope='africa'):
    normalized_scope = (scope or '').strip().lower() or DEFAULT_OPENSKY_SCOPE
    if normalized_scope not in OPENSKY_SCOPES:
        normalized_scope = DEFAULT_OPENSKY_SCOPE

    cache_key = f'dashboard:opensky:{normalized_scope}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    timeout = int(os.getenv('OPENSKY_TIMEOUT_SECONDS', '8'))
    scope_config = OPENSKY_SCOPES[normalized_scope]
    query_bbox = scope_config['bbox']

    payload = {
        'source': 'opensky',
        'generated_at': timezone.now().isoformat(),
        'requested_scope': normalized_scope,
        'requested_scope_label': scope_config['label'],
        'query_scope': normalized_scope,
        'query_scope_label': scope_config['label'],
        'query_bbox': query_bbox,
        'simulated': False,
        'flights': [],
    }

    try:
        states = _fetch_opensky_states(query_bbox, timeout)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        states = []

    # If scoped query is empty, try global and filter back into the requested region.
    if not states and query_bbox is not None:
        try:
            global_states = _fetch_opensky_states(None, timeout)
            states = [state for state in global_states if _state_in_bbox(state, query_bbox)]
            if states:
                payload['source'] = 'opensky_global_filtered'
        except (HTTPError, URLError, TimeoutError, OSError, ValueError):
            states = []

    flights = []
    for state in states:
        normalized = _normalize_opensky_state(state)
        if normalized is not None:
            flights.append(normalized)

    flights.sort(key=lambda row: row['callsign'])
    payload['flights'] = flights[:250]

    if not payload['flights'] and _env_bool('OPENSKY_DEMO_FALLBACK', True):
        payload['simulated'] = True
        payload['source'] = 'simulated'
        payload['flights'] = _build_demo_flights(normalized_scope, query_bbox)
        payload['note'] = 'Live OpenSky traffic unavailable. Showing simulated demo flights.'

    cache.set(cache_key, payload, 20)
    return payload


def get_ghana_opensky_feed():
    return get_opensky_feed('ghana')


def get_dashboard_metrics():
    now = timezone.now()
    today = timezone.localdate()
    flights_today_qs = FlightLog.objects.filter(flight_datetime__date=today)
    flights_today = flights_today_qs.count()
    active_missions = flights_today_qs.filter(mission_status=FlightLog.MissionStatus.ACTIVE).count()
    delayed_arrivals = flights_today_qs.filter(
        Q(remarks__icontains='delay') | Q(remarks__icontains='late')
    ).count()
    cancelled_flights = flights_today_qs.filter(remarks__icontains='cancel').count()
    completed_flights = flights_today_qs.filter(mission_status=FlightLog.MissionStatus.COMPLETED).count()
    landed_flights = max(completed_flights - cancelled_flights, 0)
    scheduled_flights = flights_today_qs.filter(flight_datetime__gt=now).exclude(remarks__icontains='cancel').count()
    on_time_departure_rate = (
        round((max(flights_today - delayed_arrivals - cancelled_flights, 0) / flights_today) * 100, 1)
        if flights_today
        else 100.0
    )

    maintenance_alerts = Alert.objects.filter(is_resolved=False).count()
    crew_available = Crew.objects.filter(is_available=True).count()
    aircraft_available = Aircraft.objects.filter(status=Aircraft.Status.AVAILABLE).count()

    utilization_data = (
        FlightLog.objects.values('aircraft__tail_number')
        .annotate(total_hours=Sum('flight_hours'))
        .order_by('-total_hours')[:5]
    )
    utilization = [
        {
            'aircraft': row['aircraft__tail_number'],
            'hours': float(row['total_hours'] or 0.0),
        }
        for row in utilization_data
    ]

    status_distribution = {
        'airborne': active_missions,
        'landed': landed_flights,
        'scheduled': scheduled_flights,
        'delayed': delayed_arrivals,
        'cancelled': cancelled_flights,
    }

    latest_telemetry = FlightData.objects.select_related('flight_log').order_by('-timestamp').first()
    live_feed = {
        'speed_knots': 0,
        'altitude_feet': 0,
        'flight_level': 'FL000',
        'mach': 0.0,
        'updated_time': timezone.localtime().strftime('%I:%M:%S %p'),
    }
    if latest_telemetry:
        speed_knots = float(latest_telemetry.speed)
        altitude_feet = float(latest_telemetry.altitude)
        live_feed = {
            'speed_knots': int(round(speed_knots)),
            'altitude_feet': int(round(altitude_feet)),
            'flight_level': f'FL{int(round(altitude_feet / 100)):03d}',
            'mach': round(speed_knots / 661.0, 2),
            'updated_time': timezone.localtime(latest_telemetry.timestamp).strftime('%I:%M:%S %p'),
        }

    trend_qs = FlightData.objects.none()
    if latest_telemetry:
        trend_qs = FlightData.objects.filter(flight_log_id=latest_telemetry.flight_log_id).order_by('timestamp')[:18]

    altitude_trend = [
        {
            'time': timezone.localtime(item.timestamp).strftime('%H:%M'),
            'altitude': float(item.altitude),
        }
        for item in trend_qs
    ]
    if not altitude_trend:
        altitude_trend = [
            {'time': '08:10', 'altitude': 0},
            {'time': '08:20', 'altitude': 1300},
            {'time': '08:30', 'altitude': 3200},
            {'time': '08:40', 'altitude': 3800},
            {'time': '08:50', 'altitude': 3900},
            {'time': '09:00', 'altitude': 3800},
            {'time': '09:10', 'altitude': 3600},
            {'time': '09:20', 'altitude': 2500},
            {'time': '09:30', 'altitude': 900},
            {'time': '09:40', 'altitude': 300},
            {'time': '09:50', 'altitude': 0},
        ]

    return {
        'aircraft_available': aircraft_available,
        'flights_today': flights_today,
        'active_missions': active_missions,
        'on_time_departure_rate': on_time_departure_rate,
        'delayed_arrivals': delayed_arrivals,
        'maintenance_alerts': maintenance_alerts,
        'crew_availability': crew_available,
        'aircraft_utilization': utilization,
        'status_distribution': status_distribution,
        'live_feed': live_feed,
        'altitude_trend': altitude_trend,
        'last_updated': timezone.now().isoformat(),
    }
