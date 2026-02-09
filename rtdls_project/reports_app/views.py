from datetime import timedelta
import csv
from datetime import datetime
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from accounts.decorators import role_required
from audittrail.models import AuditLog
from maintenance.models import MaintenanceLog
from operations.models import Aircraft, FlightLog, Pilot


def _sanitize_spreadsheet_cell(value):
    if isinstance(value, str):
        stripped = value.lstrip()
        if stripped.startswith(('=', '+', '-', '@')):
            return "'" + value
    return value


def _render_pdf(filename, title, rows):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    y = height - 40
    pdf.setFont('Helvetica-Bold', 14)
    pdf.drawString(40, y, title)
    y -= 30

    pdf.setFont('Helvetica', 10)
    for row in rows:
        if y < 40:
            pdf.showPage()
            y = height - 40
            pdf.setFont('Helvetica', 10)
        pdf.drawString(40, y, row)
        y -= 18

    pdf.save()
    return response


def _render_xlsx(filename, sheet_name, headers, rows):
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'

    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    ws.append([_sanitize_spreadsheet_cell(value) for value in headers])
    for row in rows:
        ws.append([_sanitize_spreadsheet_cell(value) for value in row])

    wb.save(response)
    return response


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


def _format_duration_hours(hours):
    if not hours:
        return '0h 00m'
    whole_hours = int(hours)
    minutes = int(round((float(hours) - whole_hours) * 60))
    if minutes == 60:
        whole_hours += 1
        minutes = 0
    return f'{whole_hours}h {minutes:02d}m'


def _flight_status(log):
    remarks = (log.remarks or '').lower()
    if 'cancel' in remarks:
        return 'Cancelled'
    if 'delay' in remarks or 'late' in remarks:
        return 'Delayed'
    if log.mission_status == FlightLog.MissionStatus.ACTIVE:
        return 'Active'
    return 'Completed'


def _build_filtered_queryset(request):
    today = timezone.localdate()
    default_from = today - timedelta(days=30)

    date_from = _parse_date(request.GET.get('date_from')) or default_from
    date_to = _parse_date(request.GET.get('date_to')) or today

    pilot_id = request.GET.get('pilot')
    aircraft_id = request.GET.get('aircraft')
    flight_id = request.GET.get('flight_id')
    search_query = (request.GET.get('q') or '').strip()
    granularity = request.GET.get('granularity', 'daily').lower()
    if granularity not in {'daily', 'weekly', 'monthly', 'custom'}:
        granularity = 'daily'

    qs = FlightLog.objects.select_related(
        'aircraft',
        'pilot',
        'departure_base',
        'arrival_base',
        'logged_by',
    ).filter(
        flight_datetime__date__gte=date_from,
        flight_datetime__date__lte=date_to,
    )

    if pilot_id and pilot_id.isdigit():
        qs = qs.filter(pilot_id=int(pilot_id))
    if aircraft_id and aircraft_id.isdigit():
        qs = qs.filter(aircraft_id=int(aircraft_id))
    if flight_id and flight_id.isdigit():
        qs = qs.filter(id=int(flight_id))
    if search_query:
        qs = qs.filter(
            Q(aircraft__tail_number__icontains=search_query)
            | Q(aircraft__model__icontains=search_query)
            | Q(pilot_name__icontains=search_query)
            | Q(mission_type__icontains=search_query)
            | Q(remarks__icontains=search_query)
            | Q(departure_base__name__icontains=search_query)
            | Q(arrival_base__name__icontains=search_query)
        )

    return qs, {
        'date_from': date_from,
        'date_to': date_to,
        'pilot': pilot_id or '',
        'aircraft': aircraft_id or '',
        'flight_id': flight_id or '',
        'q': search_query,
        'granularity': granularity,
    }


@login_required
@role_required('admin', 'flight_ops', 'commander', 'auditor', 'maintenance')
def reports_dashboard_view(request):
    qs, filters = _build_filtered_queryset(request)
    summary = qs.aggregate(
        avg_duration=Avg('flight_hours'),
        total_fuel=Sum('fuel_used'),
    )
    total_flights = qs.count()
    delayed_or_late = qs.filter(Q(remarks__icontains='delay') | Q(remarks__icontains='late')).count()
    cancelled = qs.filter(remarks__icontains='cancel').count()
    on_time = ((max(total_flights - delayed_or_late - cancelled, 0) / total_flights) * 100) if total_flights else 100

    recent_logs = qs[:8]
    preview_rows = [
        {
            'flight_id': log.id,
            'code': log.aircraft.tail_number,
            'pilot': log.pilot_name or (log.pilot.full_name if log.pilot else 'Pilot not set'),
            'aircraft': log.aircraft.model,
            'route': f'{log.departure_base.name[:3].upper()} -> {log.arrival_base.name[:3].upper()}',
            'date': timezone.localtime(log.flight_datetime).strftime('%Y-%m-%d'),
            'duration': _format_duration_hours(log.flight_hours),
            'status': _flight_status(log),
        }
        for log in recent_logs
    ]

    filter_query = urlencode(
        {
            'date_from': filters['date_from'].isoformat(),
            'date_to': filters['date_to'].isoformat(),
            'pilot': filters['pilot'],
            'aircraft': filters['aircraft'],
            'flight_id': filters['flight_id'],
            'q': filters['q'],
            'granularity': filters['granularity'],
        }
    )

    recent_activities = AuditLog.objects.select_related('user').filter(
        entity__in=['FlightLog', 'MaintenanceLog', 'Dashboard']
    )[:8]

    context = {
        'filters': filters,
        'pilots': Pilot.objects.filter(is_active=True).order_by('full_name'),
        'aircraft_options': Aircraft.objects.order_by('tail_number'),
        'flight_id_options': FlightLog.objects.order_by('-id')[: settings.REPORTS_FLIGHT_ID_OPTIONS_LIMIT],
        'stats': {
            'total_flights': total_flights,
            'avg_duration': _format_duration_hours(summary.get('avg_duration') or 0),
            'fuel_consumed': float(summary.get('total_fuel') or 0.0),
            'on_time_perf': round(on_time, 1),
        },
        'recent_logs': preview_rows,
        'recent_activities': recent_activities,
        'filter_query': filter_query,
    }
    return render(request, 'reports_app/reports_dashboard.html', context)


@login_required
@role_required('admin', 'flight_ops', 'commander', 'auditor', 'maintenance')
def report_export(request):
    qs, filters = _build_filtered_queryset(request)
    export_format = request.GET.get('format', 'pdf').lower()
    filename_suffix = f"{filters['date_from'].isoformat()}_{filters['date_to'].isoformat()}"

    rows = [
        [
            log.id,
            log.aircraft.tail_number,
            log.pilot_name or (log.pilot.full_name if log.pilot else ''),
            f'{log.departure_base.name} -> {log.arrival_base.name}',
            log.flight_datetime.strftime('%Y-%m-%d %H:%M'),
            log.flight_hours,
            log.fuel_used,
            _flight_status(log),
        ]
        for log in qs
    ]

    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="flight-report-{filename_suffix}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Flight ID', 'Aircraft', 'Pilot', 'Route', 'Date', 'Duration (h)', 'Fuel', 'Status'])
        for row in rows:
            writer.writerow([_sanitize_spreadsheet_cell(value) for value in row])
        return response

    pdf_rows = [
        (
            f"#{row[0]} | {row[1]} | {row[2]} | {row[3]} | "
            f"{row[4]} | {row[5]}h | Fuel {row[6]} | {row[7]}"
        )
        for row in rows
    ]
    return _render_pdf(
        filename=f'flight-report-{filename_suffix}',
        title=f'Flight Report ({filters["date_from"].isoformat()} to {filters["date_to"].isoformat()})',
        rows=pdf_rows or ['No records for the selected filters.'],
    )


@login_required
@role_required('admin', 'flight_ops', 'commander', 'auditor')
def daily_flight_report(request):
    report_format = request.GET.get('format', 'pdf').lower()
    date = timezone.localdate()
    flights = FlightLog.objects.select_related('aircraft', 'departure_base', 'arrival_base', 'logged_by').filter(flight_datetime__date=date)

    if report_format == 'xlsx':
        rows = [
            [
                f.aircraft.tail_number,
                f.pilot_name,
                f.mission_type,
                f.flight_datetime.isoformat(),
                f.flight_hours,
                f.fuel_used,
                f.departure_base.name,
                f.arrival_base.name,
                f.logged_by.username if f.logged_by else '-',
            ]
            for f in flights
        ]
        return _render_xlsx(
            filename=f'daily-flight-report-{date.isoformat()}',
            sheet_name='Daily Flights',
            headers=['Aircraft', 'Pilot', 'Mission', 'DateTime', 'Hours', 'Fuel', 'Departure', 'Arrival', 'Logged By'],
            rows=rows,
        )

    rows = [
        (
            f'{f.aircraft.tail_number} | Pilot: {f.pilot_name} | Mission: {f.mission_type} | '
            f'Hours: {f.flight_hours} | Fuel: {f.fuel_used} | {f.departure_base.name}->{f.arrival_base.name}'
        )
        for f in flights
    ]
    return _render_pdf(
        filename=f'daily-flight-report-{date.isoformat()}',
        title=f'Daily Flight Report - {date.isoformat()}',
        rows=rows or ['No flights logged for today.'],
    )


@login_required
@role_required('admin', 'maintenance', 'commander', 'auditor')
def weekly_maintenance_report(request):
    report_format = request.GET.get('format', 'pdf').lower()
    end_date = timezone.localdate()
    start_date = end_date - timedelta(days=7)
    logs = MaintenanceLog.objects.select_related('aircraft', 'logged_by').filter(created_at__date__gte=start_date, created_at__date__lte=end_date)

    if report_format == 'xlsx':
        rows = [
            [
                m.aircraft.tail_number,
                m.total_flight_hours,
                m.last_maintenance_date.isoformat(),
                m.component_status,
                m.logged_by.username if m.logged_by else '-',
                m.created_at.isoformat(),
            ]
            for m in logs
        ]
        return _render_xlsx(
            filename=f'weekly-maintenance-report-{end_date.isoformat()}',
            sheet_name='Maintenance',
            headers=['Aircraft', 'Total Flight Hours', 'Last Maintenance Date', 'Status', 'Logged By', 'Created At'],
            rows=rows,
        )

    rows = [
        (
            f'{m.aircraft.tail_number} | Total Hours: {m.total_flight_hours} | Last Maint: '
            f'{m.last_maintenance_date.isoformat()} | Status: {m.component_status}'
        )
        for m in logs
    ]
    return _render_pdf(
        filename=f'weekly-maintenance-report-{end_date.isoformat()}',
        title=f'Weekly Maintenance Report ({start_date.isoformat()} to {end_date.isoformat()})',
        rows=rows or ['No maintenance logs for selected period.'],
    )


@login_required
@role_required('admin', 'commander', 'auditor', 'maintenance', 'flight_ops')
def aircraft_utilization_report(request):
    report_format = request.GET.get('format', 'pdf').lower()
    utilization = (
        FlightLog.objects.values('aircraft__tail_number')
        .annotate(total_hours=Sum('flight_hours'), total_fuel=Sum('fuel_used'))
        .order_by('-total_hours')
    )

    if report_format == 'json':
        return JsonResponse({'utilization': list(utilization)})

    if report_format == 'xlsx':
        rows = [[u['aircraft__tail_number'], float(u['total_hours'] or 0), float(u['total_fuel'] or 0)] for u in utilization]
        return _render_xlsx(
            filename='aircraft-utilization-report',
            sheet_name='Utilization',
            headers=['Aircraft', 'Total Flight Hours', 'Total Fuel Used'],
            rows=rows,
        )

    rows = [
        f"{u['aircraft__tail_number']} | Total Hours: {float(u['total_hours'] or 0):.1f} | Total Fuel: {float(u['total_fuel'] or 0):.1f}"
        for u in utilization
    ]
    return _render_pdf(
        filename='aircraft-utilization-report',
        title='Aircraft Utilization Report',
        rows=rows or ['No utilization data available.'],
    )
