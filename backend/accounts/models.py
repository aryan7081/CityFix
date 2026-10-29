from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        CITIZEN = "CITIZEN", "Citizen"
        ADMIN = "ADMIN", "Administrator"
        MAINTENANCE = "MAINTENANCE", "Maintenance Staff"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CITIZEN,
        db_index=True,
    )
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_citizen(self) -> bool:
        return self.role == self.Role.CITIZEN

    @property
    def is_admin_role(self) -> bool:
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_maintenance(self) -> bool:
        return self.role == self.Role.MAINTENANCE

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"
