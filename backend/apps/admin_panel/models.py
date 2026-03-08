"""
admin_panel — AdminUser model and AuditLog.
"""
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class AdminRole(models.TextChoices):
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
    OPERATOR = "OPERATOR", "Operator"


class AdminUserManager(BaseUserManager):
    def create_admin(self, email, password, role=AdminRole.OPERATOR, **extra_fields):
        if not email:
            raise ValueError("Email is required for admin accounts.")
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class AdminUser(models.Model):
    """
    Admin/operator accounts — separate from consumer User model.
    Created manually by Super Admin; cannot self-register.
    MFA enforced at the serializer/view layer.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    # Hashed password stored via Django's auth machinery
    password = models.CharField(max_length=128)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=AdminRole.choices, default=AdminRole.OPERATOR)
    is_active = models.BooleanField(default=True)

    # TOTP device linked via django-otp (OTPDevice FK added automatically)
    mfa_enabled = models.BooleanField(default=False)

    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_admins",
    )

    class Meta:
        db_table = "admin_users"

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def is_super_admin(self):
        return self.role == AdminRole.SUPER_ADMIN

    def check_password(self, raw_password):
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.password)

    def set_password(self, raw_password):
        from django.contrib.auth.hashers import make_password
        self.password = make_password(raw_password)


class AuditLog(models.Model):
    """
    Immutable audit trail of admin actions.
    No admin — including Super Admin — may delete entries.
    Retained minimum 2 years.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Actor: either an AdminUser or a consumer User
    admin_actor = models.ForeignKey(
        AdminUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    user_actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    actor_label = models.CharField(max_length=255, blank=True)  # display fallback

    action = models.CharField(max_length=100, db_index=True)  # e.g. "user.suspend"
    target_type = models.CharField(max_length=100, blank=True)  # e.g. "User", "Transaction"
    target_id = models.CharField(max_length=100, blank=True)

    # Arbitrary JSON metadata
    metadata = models.JSONField(default=dict, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-timestamp"]
        # Prevent accidental deletion
        default_permissions = ("add", "view")  # no change/delete permissions

    def __str__(self):
        return f"[{self.timestamp}] {self.actor_label} → {self.action} on {self.target_type}:{self.target_id}"
