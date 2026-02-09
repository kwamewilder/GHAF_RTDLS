import hashlib
from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = 'create', 'Create'
        UPDATE = 'update', 'Update'
        DELETE = 'delete', 'Delete'
        LOGIN = 'login', 'Login'
        LOGOUT = 'logout', 'Logout'
        ROLE_CHANGE = 'role_change', 'Role Change'
        VIEW = 'view', 'View'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=24, choices=Action.choices)
    entity = models.CharField(max_length=64)
    entity_id = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    previous_checksum = models.CharField(max_length=64, blank=True)
    checksum = models.CharField(max_length=64, editable=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.created_at} - {self.action} - {self.entity}'

    def save(self, *args, **kwargs):
        if not self.previous_checksum:
            latest = AuditLog.objects.exclude(pk=self.pk).order_by('-id').first()
            self.previous_checksum = latest.checksum if latest else 'GENESIS'
        payload = '|'.join(
            [
                self.action,
                self.entity,
                str(self.entity_id or ''),
                str(self.user_id or ''),
                self.description,
                self.previous_checksum,
            ]
        )
        self.checksum = hashlib.sha256(payload.encode('utf-8')).hexdigest()
        super().save(*args, **kwargs)


def log_action(*, user, action, entity, entity_id, description, ip_address=None):
    AuditLog.objects.create(
        user=user,
        action=action,
        entity=entity,
        entity_id=entity_id,
        description=description,
        ip_address=ip_address,
    )
