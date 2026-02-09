from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from audittrail.models import AuditLog, log_action
from dashboard.realtime import broadcast_dashboard_update
from maintenance.models import Alert

from .forms import FlightLogForm
from .models import FlightData, FlightLog


def _flight_log_context(form, editing_log=None):
    recent_logs = FlightLog.objects.select_related('aircraft', 'pilot', 'departure_base', 'arrival_base').all()[:8]
    alert_items = Alert.objects.select_related('aircraft').filter(is_resolved=False)[:4]
    flight_totals = FlightLog.objects.aggregate(total_hours=Sum('flight_hours'))
    telemetry_averages = FlightData.objects.aggregate(
        average_altitude=Avg('altitude'),
        average_speed=Avg('speed'),
    )
    stats = {
        'total_flights': FlightLog.objects.count(),
        'average_altitude': telemetry_averages.get('average_altitude') or 0,
        'average_speed': telemetry_averages.get('average_speed') or 0,
        'total_hours': flight_totals.get('total_hours') or 0,
    }
    return {
        'form': form,
        'recent_logs': recent_logs,
        'alert_items': alert_items,
        'stats': stats,
        'editing_log': editing_log,
    }


@login_required
@role_required('admin', 'flight_ops')
def flight_log_create_view(request):
    if request.method == 'POST':
        form = FlightLogForm(request.POST)
        if form.is_valid():
            flight_log = form.save(commit=False)
            flight_log.logged_by = request.user
            flight_log.save()
            form.save_m2m()

            altitude_ft = form.cleaned_data.get('altitude_ft')
            speed_knots = form.cleaned_data.get('speed_knots')
            if altitude_ft is not None or speed_knots is not None:
                FlightData.objects.create(
                    flight_log=flight_log,
                    timestamp=flight_log.atd,
                    altitude=altitude_ft or 0.0,
                    speed=speed_knots or 0.0,
                    engine_temp=0.0,
                    fuel_level=0.0,
                    heading=0.0,
                )

            log_action(
                user=request.user,
                action=AuditLog.Action.CREATE,
                entity='FlightLog',
                entity_id=flight_log.id,
                description=f'Created flight log #{flight_log.id} from web form',
                ip_address=request.META.get('REMOTE_ADDR'),
            )
            broadcast_dashboard_update()
            messages.success(request, 'Flight log submitted successfully.')
            return redirect('operations:flight-log-create')
    else:
        form = FlightLogForm()

    return render(request, 'operations/flight_log_form.html', _flight_log_context(form))


@login_required
@role_required('admin', 'flight_ops')
def flight_log_update_view(request, pk):
    flight_log = get_object_or_404(FlightLog.objects.select_related('aircraft'), pk=pk)
    if flight_log.ata:
        messages.info(request, 'This flight is already completed and cannot be edited.')
        return redirect('operations:flight-log-create')

    if request.method == 'POST':
        form = FlightLogForm(request.POST, instance=flight_log)
        if form.is_valid():
            updated_flight = form.save()

            altitude_ft = form.cleaned_data.get('altitude_ft')
            speed_knots = form.cleaned_data.get('speed_knots')
            if altitude_ft is not None or speed_knots is not None:
                FlightData.objects.create(
                    flight_log=updated_flight,
                    timestamp=updated_flight.atd,
                    altitude=altitude_ft or 0.0,
                    speed=speed_knots or 0.0,
                    engine_temp=0.0,
                    fuel_level=0.0,
                    heading=0.0,
                )

            log_action(
                user=request.user,
                action=AuditLog.Action.UPDATE,
                entity='FlightLog',
                entity_id=updated_flight.id,
                description=f'Updated flight log #{updated_flight.id} from web form',
                ip_address=request.META.get('REMOTE_ADDR'),
            )
            broadcast_dashboard_update()
            messages.success(request, 'Flight log updated successfully.')
            return redirect('operations:flight-log-create')
    else:
        form = FlightLogForm(instance=flight_log)

    return render(request, 'operations/flight_log_form.html', _flight_log_context(form, editing_log=flight_log))
