from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import UUIDModel
from .managers import CustomUserManager


class CustomUser(UUIDModel, AbstractBaseUser, PermissionsMixin):
    """
    Production custom user model.
    AUTH_USER_MODEL = 'users.CustomUser' in settings.
    """

    class Role(models.TextChoices):
        USER       = "user",       _("User")
        ADMIN      = "admin",      _("Admin")
        SUPERADMIN = "superadmin", _("Super Admin")

    # ── Core fields ───────────────────────────────────────────
    email      = models.EmailField(_("email address"), unique=True, db_index=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name  = models.CharField(_("last name"),  max_length=150, blank=True)
    avatar     = models.ImageField(
        upload_to="avatars/%Y/%m/",
        null=True, blank=True
    )

    # ── Role & status ─────────────────────────────────────────
    role     = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
        db_index=True,
    )
    is_staff   = models.BooleanField(default=False)
    is_active  = models.BooleanField(default=True)

    # ── Timestamps ────────────────────────────────────────────
    date_joined = models.DateTimeField(default=timezone.now)
    last_login  = models.DateTimeField(null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name        = _("user")
        verbose_name_plural = _("users")
        ordering            = ["-date_joined"]
        indexes = [
            models.Index(fields=["email", "is_active"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return self.email

    # ── Computed properties ───────────────────────────────────
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    @property
    def is_admin(self):
        return self.role in (self.Role.ADMIN, self.Role.SUPERADMIN)

    @property
    def is_superadmin(self):
        return self.role == self.Role.SUPERADMIN