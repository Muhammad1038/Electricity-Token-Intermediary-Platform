"""
meters — Meter profile model and DISCO provider registry.
"""
import uuid

from django.conf import settings
from django.db import models


class DISCOProvider(models.TextChoices):
    # South-West
    IBEDC  = "IBEDC",  "Ibadan Electricity Distribution Company"   # Oyo, Ogun, Ondo, Osun, Kwara
    EKEDC  = "EKEDC",  "Eko Electricity Distribution Company"       # Lagos Island, Badagry, Epe
    IKEDC  = "IKEDC",  "Ikeja Electric"                            # Lagos Mainland, Ikeja, Ikorodu
    # South-South
    PHED   = "PHED",   "Port Harcourt Electricity Distribution Company"  # Rivers, Bayelsa, Akwa Ibom, Cross River
    BEDC   = "BEDC",   "Benin Electricity Distribution Company"    # Edo, Delta, Ekiti, Ondo (parts)
    # South-East
    EEDC   = "EEDC",   "Enugu Electricity Distribution Company"    # Enugu, Anambra, Imo, Abia, Ebonyi
    ABA    = "ABA",    "Aba Electricity Distribution Company"       # Abia (Aba zone)
    # North-Central
    AEDC   = "AEDC",   "Abuja Electricity Distribution Company"    # FCT, Kogi, Niger, Nassarawa
    JED    = "JED",    "Jos Electricity Distribution Company"       # Plateau, Benue, Gombe, Bauchi (parts)
    # North-West
    KAEDCO = "KAEDCO", "Kaduna Electric"                           # Kaduna, Kebbi, Sokoto, Zamfara
    KEDCO  = "KEDCO",  "Kano Electricity Distribution Company"     # Kano, Jigawa, Katsina
    # North-East
    YEDC   = "YEDC",   "Yola Electricity Distribution Company"     # Adamawa, Taraba


class MeterType(models.TextChoices):
    PREPAID = "PREPAID", "Prepaid"
    POSTPAID = "POSTPAID", "Postpaid"


class MeterProfile(models.Model):
    """
    A saved meter profile belonging to a user.
    Users can save up to MAX_METER_PROFILES_PER_USER (5) profiles.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="meter_profiles",
    )
    nickname = models.CharField(max_length=50, blank=True, help_text='e.g. "Home", "Office"')
    meter_number = models.CharField(max_length=20, db_index=True)
    disco = models.CharField(max_length=20, choices=DISCOProvider.choices)
    meter_type = models.CharField(
        max_length=10, choices=MeterType.choices, default=MeterType.PREPAID
    )

    # Populated from DISCO API at validation time
    meter_owner_name = models.CharField(max_length=255, blank=True)
    meter_address = models.TextField(blank=True)

    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "meter_profiles"
        unique_together = [("user", "meter_number", "disco")]
        indexes = [
            models.Index(fields=["user", "is_default"]),
        ]

    def __str__(self):
        return f"{self.nickname or self.meter_number} ({self.disco})"

    def save(self, *args, **kwargs):
        # If setting this as default, unset all other defaults for this user
        if self.is_default:
            MeterProfile.objects.filter(user=self.user, is_default=True).exclude(
                pk=self.pk
            ).update(is_default=False)
        super().save(*args, **kwargs)
