from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.decorators import role_required
from audittrail.models import AuditLog, log_action
from operations.models import Aircraft

from .forms import MaintenanceLogForm
from .models import Alert, MaintenanceLog


@login_required
@role_required('admin', 'maintenance')
def maintenance_log_create_view(request):
    if request.method == 'POST':
        form = MaintenanceLogForm(request.POST)
        if form.is_valid():
            log_entry = form.save(commit=False)
            log_entry.logged_by = request.user
            log_entry.save()
            log_action(
                user=request.user,
                action=AuditLog.Action.CREATE,
                entity='MaintenanceLog',
                entity_id=log_entry.id,
                description=f'Created maintenance log #{log_entry.id} from web form',
                ip_address=request.META.get('REMOTE_ADDR'),
            )
            messages.success(request, 'Maintenance log submitted successfully.')
            return redirect('maintenance:log-create')
    else:
        form = MaintenanceLogForm()

    recent_logs = MaintenanceLog.objects.select_related('aircraft', 'logged_by').all()[:10]
    active_alerts = Alert.objects.select_related('aircraft').filter(is_resolved=False)[:8]
    stats = {
        'total_logs': MaintenanceLog.objects.count(),
        'open_alerts': Alert.objects.filter(is_resolved=False).count(),
        'high_alerts': Alert.objects.filter(is_resolved=False, severity=Alert.Severity.HIGH).count(),
        'aircraft_in_maintenance': Aircraft.objects.filter(status=Aircraft.Status.IN_MAINTENANCE).count(),
    }
    return render(
        request,
        'maintenance/maintenance_log_form.html',
        {'form': form, 'recent_logs': recent_logs, 'active_alerts': active_alerts, 'stats': stats},
    )
