from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER   = 'owner',   'Egasi'
        MANAGER = 'manager', 'Menejer'
        CLIENT  = 'client',  'Mijoz'

    role  = models.CharField(max_length=20, choices=Role.choices, default=Role.MANAGER)
    phone = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    @property
    def is_owner(self):
        return self.role == self.Role.OWNER

    @property
    def is_manager(self):
        return self.role == self.Role.MANAGER

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT