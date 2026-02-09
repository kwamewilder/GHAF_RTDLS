from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import pre_save
from django.dispatch import receiver

from audittrail.models import AuditLog
from audittrail.context import get_current_user

User = get_user_model()


def _extract_ip(request):
    if not request:
        return None
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    AuditLog.objects.create(
        user=user,
        action=AuditLog.Action.LOGIN,
        entity='User',
        entity_id=user.id,
        description='User logged in',
        ip_address=_extract_ip(request),
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if not user:
        return
    AuditLog.objects.create(
        user=user,
        action=AuditLog.Action.LOGOUT,
        entity='User',
        entity_id=user.id,
        description='User logged out',
        ip_address=_extract_ip(request),
    )


@receiver(pre_save, sender=User)
def log_role_change(sender, instance, **kwargs):
    if not instance.pk:
        return
    previous = User.objects.filter(pk=instance.pk).first()
    if not previous:
        return
    if previous.role != instance.role:
        actor = get_current_user()
        if not actor or not getattr(actor, 'is_authenticated', False):
            actor = None
        AuditLog.objects.create(
            user=actor,
            action=AuditLog.Action.ROLE_CHANGE,
            entity='User',
            entity_id=instance.id,
            description=(
                f'Role changed for {instance.username} '
                f'from {previous.role} to {instance.role}'
            ),
        )
