from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Max, Sum
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from audittrail.models import AuditLog
from maintenance.models import Alert, MaintenanceLog
from operations.models import Aircraft, FlightLog
from operations.forms import AircraftRegistryForm
from .models import User
from .forms import LoginForm, SettingsUserCreateForm, SettingsUserEditForm


class SecureLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recaptcha_enabled'] = getattr(settings, 'RECAPTCHA_ENABLED', False)
        context['recaptcha_site_key'] = getattr(settings, 'RECAPTCHA_SITE_KEY', '')
        return context


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    def section_redirect(section):
        return redirect(f"{reverse('profile')}?section={section}#{section}")

    section_order = [
        ('overview', 'Overview'),
        ('user-management', 'User Management'),
        ('aircraft-registry', 'Aircraft Registry'),
        ('system-logs', 'System Logs'),
        ('analytics-report', 'Analytics Report'),
        ('configuration', 'Configuration'),
    ]
    selected_section = request.GET.get('section', 'overview')
    section_role_map = {
        'overview': {role for role in User.Role.values},
        'user-management': {User.Role.ADMIN},
        'aircraft-registry': {User.Role.ADMIN},
        'system-logs': {User.Role.ADMIN, User.Role.AUDITOR},
        'analytics-report': {User.Role.ADMIN, User.Role.COMMANDER, User.Role.AUDITOR},
        'configuration': {User.Role.ADMIN},
    }

    allowed_section_ids = {item[0] for item in section_order}
    if selected_section not in allowed_section_ids:
        selected_section = 'overview'

    user_allowed_sections = [
        section_id for section_id, _label in section_order if request.user.role in section_role_map.get(section_id, set())
    ]
    if selected_section not in user_allowed_sections:
        selected_section = user_allowed_sections[0] if user_allowed_sections else 'overview'
    settings_sections = [
        {
            'id': section_id,
            'label': label,
            'allowed': request.user.role in section_role_map.get(section_id, set()),
        }
        for section_id, label in section_order
    ]

    aircraft_form = AircraftRegistryForm(prefix='aircraft')
    aircraft_edit_form = AircraftRegistryForm(prefix='editaircraft')
    user_form = SettingsUserCreateForm(prefix='newuser')
    user_edit_form = SettingsUserEditForm(prefix='edituser')
    edit_target_user_id = ''
    edit_target_aircraft_id = ''
    if request.method == 'POST':
        action = request.POST.get('settings_action')
        if action == 'add_aircraft':
            selected_section = 'aircraft-registry'
            if request.user.role != User.Role.ADMIN:
                messages.error(request, 'Only Admin can register new aircraft.')
                return section_redirect('aircraft-registry')

            aircraft_form = AircraftRegistryForm(request.POST, prefix='aircraft')
            if aircraft_form.is_valid():
                aircraft = aircraft_form.save()
                AuditLog.objects.create(
                    user=request.user,
                    action=AuditLog.Action.CREATE,
                    entity='Aircraft',
                    entity_id=aircraft.id,
                    description=f'Registered aircraft {aircraft.tail_number} ({aircraft.model})',
                    ip_address=request.META.get('REMOTE_ADDR'),
                )
                messages.success(request, f'Aircraft {aircraft.tail_number} added successfully.')
                return section_redirect('aircraft-registry')
            messages.error(request, 'Please fix the highlighted aircraft form errors.')
        elif action == 'edit_aircraft':
            selected_section = 'aircraft-registry'
            if request.user.role != User.Role.ADMIN:
                messages.error(request, 'Only Admin can edit aircraft.')
                return section_redirect('aircraft-registry')

            edit_target_aircraft_id = (request.POST.get('edit_aircraft_id') or '').strip()
            target_aircraft = Aircraft.objects.filter(pk=edit_target_aircraft_id).first() if edit_target_aircraft_id.isdigit() else None
            if not target_aircraft:
                messages.error(request, 'Selected aircraft was not found.')
                return section_redirect('aircraft-registry')

            previous_status = target_aircraft.status
            aircraft_edit_form = AircraftRegistryForm(request.POST, instance=target_aircraft, prefix='editaircraft')
            if aircraft_edit_form.is_valid():
                updated_aircraft = aircraft_edit_form.save()
                AuditLog.objects.create(
                    user=request.user,
                    action=AuditLog.Action.UPDATE,
                    entity='Aircraft',
                    entity_id=updated_aircraft.id,
                    description=f'Updated aircraft {updated_aircraft.tail_number}',
                    ip_address=request.META.get('REMOTE_ADDR'),
                )
                if previous_status != updated_aircraft.status:
                    AuditLog.objects.create(
                        user=request.user,
                        action=AuditLog.Action.UPDATE,
                        entity='Aircraft',
                        entity_id=updated_aircraft.id,
                        description=f'Changed status from {previous_status} to {updated_aircraft.status}',
                        ip_address=request.META.get('REMOTE_ADDR'),
                    )
                messages.success(request, f'Aircraft {updated_aircraft.tail_number} updated successfully.')
                return section_redirect('aircraft-registry')
            messages.error(request, 'Please fix the highlighted aircraft edit form errors.')
        elif action == 'add_user':
            selected_section = 'user-management'
            if request.user.role != User.Role.ADMIN:
                messages.error(request, 'Only Admin can add users.')
                return section_redirect('user-management')

            user_form = SettingsUserCreateForm(request.POST, prefix='newuser')
            if user_form.is_valid():
                created_user = user_form.save()
                AuditLog.objects.create(
                    user=request.user,
                    action=AuditLog.Action.CREATE,
                    entity='User',
                    entity_id=created_user.id,
                    description=f'Created user {created_user.username} with role {created_user.role}',
                    ip_address=request.META.get('REMOTE_ADDR'),
                )
                messages.success(request, f'User {created_user.username} added successfully.')
                return section_redirect('user-management')
            messages.error(request, 'Please fix the highlighted user form errors.')
        elif action == 'edit_user':
            selected_section = 'user-management'
            if request.user.role != User.Role.ADMIN:
                messages.error(request, 'Only Admin can edit users.')
                return section_redirect('user-management')

            edit_target_user_id = (request.POST.get('edit_user_id') or '').strip()
            target_user = User.objects.filter(pk=edit_target_user_id).first() if edit_target_user_id.isdigit() else None
            if not target_user:
                messages.error(request, 'Selected user was not found.')
                return section_redirect('user-management')

            previous_active = target_user.is_active
            user_edit_form = SettingsUserEditForm(request.POST, instance=target_user, prefix='edituser')
            if user_edit_form.is_valid():
                updated_user = user_edit_form.save()
                AuditLog.objects.create(
                    user=request.user,
                    action=AuditLog.Action.UPDATE,
                    entity='User',
                    entity_id=updated_user.id,
                    description=f'Updated user {updated_user.username}',
                    ip_address=request.META.get('REMOTE_ADDR'),
                )
                if previous_active != updated_user.is_active:
                    state = 'active' if updated_user.is_active else 'inactive'
                    AuditLog.objects.create(
                        user=request.user,
                        action=AuditLog.Action.UPDATE,
                        entity='User',
                        entity_id=updated_user.id,
                        description=f'Updated account status to {state}',
                        ip_address=request.META.get('REMOTE_ADDR'),
                    )
                messages.success(request, f'User {updated_user.username} updated successfully.')
                return section_redirect('user-management')
            messages.error(request, 'Please fix the highlighted edit-user form errors.')

    now = timezone.now()
    users_qs = User.objects.order_by('id')
    user_page = Paginator(users_qs, 10).get_page(request.GET.get('user_page', 1))
    role_label_map = {
        User.Role.ADMIN: 'Admin',
        User.Role.FLIGHT_OPS: 'Flight Operations Officer',
        User.Role.MAINTENANCE: 'Maintenance Officer',
        User.Role.COMMANDER: 'Commander',
        User.Role.AUDITOR: 'Auditor',
    }
    user_rows = []
    for account in user_page.object_list:
        if not account.is_active:
            status_key = 'inactive'
            status_label = 'Inactive'
        elif account.last_login:
            status_key = 'active'
            status_label = 'Active'
        else:
            status_key = 'pending'
            status_label = 'Pending'
        user_rows.append(
            {
                'code': f'us{account.id:03d}',
                'id': account.id,
                'username': account.username,
                'first_name': account.first_name,
                'last_name': account.last_name,
                'name': account.get_full_name() or account.username,
                'email_raw': account.email or '',
                'email': account.email or '-',
                'role_value': account.role,
                'role': role_label_map.get(account.role, account.get_role_display()),
                'status_key': status_key,
                'status_label': status_label,
                'is_active': account.is_active,
            }
        )

    active_users = users_qs.filter(is_active=True).count()
    inactive_users = users_qs.filter(is_active=False).count()
    recent_window_start = now - timedelta(days=30)
    prior_window_start = now - timedelta(days=60)
    recent_users = users_qs.filter(date_joined__gte=recent_window_start).count()
    prior_users = users_qs.filter(
        date_joined__gte=prior_window_start,
        date_joined__lt=recent_window_start,
    ).count()
    if prior_users:
        user_growth = round(((recent_users - prior_users) / prior_users) * 100)
    else:
        user_growth = 100 if recent_users else 0

    aircraft_qs = Aircraft.objects.select_related('home_base').annotate(
        last_maintenance_date=Max('maintenance_logs__last_maintenance_date')
    ).order_by('tail_number')
    aircraft_rows = list(aircraft_qs[:12])
    total_aircraft = aircraft_qs.count()
    in_maintenance_count = aircraft_qs.filter(status=Aircraft.Status.IN_MAINTENANCE).count()
    active_aircraft = aircraft_qs.exclude(status=Aircraft.Status.IN_MAINTENANCE).count()

    unresolved_alerts = Alert.objects.filter(is_resolved=False).count()
    if total_aircraft:
        maintenance_load_pct = (in_maintenance_count / total_aircraft) * 30
        alert_load_pct = min(unresolved_alerts * 2, 20)
        system_health = max(60, min(99, round(100 - maintenance_load_pct - alert_load_pct)))
    else:
        system_health = 92
    if system_health >= 90:
        system_health_label = 'Optimized'
    elif system_health >= 75:
        system_health_label = 'Stable'
    else:
        system_health_label = 'At Risk'

    flights_qs = FlightLog.objects.select_related('aircraft', 'departure_base', 'arrival_base')
    flight_stats = flights_qs.aggregate(
        total_flights=Count('id'),
        avg_duration=Avg('flight_hours'),
        total_fuel=Sum('fuel_used'),
    )
    mission_active = flights_qs.filter(mission_status=FlightLog.MissionStatus.ACTIVE).count()
    role_breakdown = users_qs.values('role').annotate(total=Count('id')).order_by('role')
    role_breakdown_rows = [
        {
            'name': role_label_map.get(row['role'], row['role'].replace('_', ' ').title()),
            'count': row['total'],
        }
        for row in role_breakdown
    ]

    system_logs = AuditLog.objects.select_related('user').all()[:30]
    maintenance_count = MaintenanceLog.objects.count()

    context = {
        'user': request.user,
        'settings_sections': settings_sections,
        'selected_section': selected_section,
        'show_add_user': request.user.role == User.Role.ADMIN,
        'can_manage_users': request.user.role == User.Role.ADMIN,
        'can_manage_aircraft': request.user.role == User.Role.ADMIN,
        'user_rows': user_rows,
        'users_page': user_page,
        'user_form': user_form,
        'user_edit_form': user_edit_form,
        'edit_target_user_id': edit_target_user_id,
        'aircraft_rows': aircraft_rows,
        'aircraft_form': aircraft_form,
        'aircraft_edit_form': aircraft_edit_form,
        'edit_target_aircraft_id': edit_target_aircraft_id,
        'system_logs': system_logs,
        'overview': {
            'total_users': users_qs.count(),
            'active_users': active_users,
            'inactive_users': inactive_users,
            'user_growth': user_growth,
            'active_aircraft': active_aircraft,
            'in_maintenance_count': in_maintenance_count,
            'system_health': system_health,
            'system_health_label': system_health_label,
        },
        'analytics': {
            'total_flights': int(flight_stats.get('total_flights') or 0),
            'avg_duration': float(flight_stats.get('avg_duration') or 0),
            'total_fuel': float(flight_stats.get('total_fuel') or 0),
            'active_missions': mission_active,
            'maintenance_records': maintenance_count,
            'role_breakdown': role_breakdown_rows,
        },
        'config': {
            'recaptcha_enabled': getattr(settings, 'RECAPTCHA_ENABLED', False),
            'database_engine': settings.DATABASES['default']['ENGINE'],
            'channels_backend': settings.CHANNEL_LAYERS['default']['BACKEND'],
            'debug': settings.DEBUG,
        },
    }
    return render(request, 'accounts/profile.html', context)
