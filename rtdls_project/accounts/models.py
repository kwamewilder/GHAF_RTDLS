from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        FLIGHT_OPS = 'flight_ops', 'Flight Operations Officer'
        MAINTENANCE = 'maintenance', 'Maintenance Officer'
        COMMANDER = 'commander', 'Commander'
        AUDITOR = 'auditor', 'Auditor'

    role = models.CharField(max_length=32, choices=Role.choices, default=Role.AUDITOR)

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'
