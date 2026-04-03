"""
meters — Serializers for MeterProfile CRUD and DISCO validation.
"""
from django.conf import settings
from rest_framework import serializers

from .models import DISCOProvider, MeterProfile, MeterType


class MeterValidationResultSerializer(serializers.Serializer):
    """Read-only: what the DISCO API returns after validation."""

    meter_number = serializers.CharField()
    disco = serializers.CharField()
    meter_owner_name = serializers.CharField()
    meter_address = serializers.CharField()
    meter_type = serializers.CharField()
    is_valid = serializers.BooleanField()


class MeterValidationRequestSerializer(serializers.Serializer):
    """Used for the standalone /validate/ endpoint (no save)."""

    meter_number = serializers.CharField(max_length=20)
    disco = serializers.ChoiceField(choices=DISCOProvider.choices)

    def validate_meter_number(self, value):
        if len(value) not in [11, 13] or not value.isdigit():
            raise serializers.ValidationError("Meter number must be exactly 11 or 13 digits and contain only numbers.")
        return value


class MeterProfileSerializer(serializers.ModelSerializer):
    disco_display = serializers.CharField(source="get_disco_display", read_only=True)
    meter_type_display = serializers.CharField(source="get_meter_type_display", read_only=True)

    class Meta:
        model = MeterProfile
        fields = [
            "id",
            "nickname",
            "meter_number",
            "disco",
            "disco_display",
            "meter_type",
            "meter_type_display",
            "meter_owner_name",
            "meter_address",
            "is_default",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "meter_owner_name",
            "meter_address",
            "meter_type",
            "created_at",
            "updated_at",
            "disco_display",
            "meter_type_display",
        ]

    def validate_meter_number(self, value):
        if len(value) not in [11, 13] or not value.isdigit():
            raise serializers.ValidationError("Meter number must be exactly 11 or 13 digits and contain only numbers.")
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        max_meters = getattr(settings, "MAX_METER_PROFILES_PER_USER", 5)

        # On create: enforce max limit and duplicate check
        if self.instance is None:
            existing_count = MeterProfile.objects.filter(
                user=user, is_active=True
            ).count()
            if existing_count >= max_meters:
                raise serializers.ValidationError(
                    f"You can save a maximum of {max_meters} meter profiles."
                )

            # Check for active duplicate only — a previously removed meter can be re-added
            meter_number = attrs.get("meter_number", "")
            disco = attrs.get("disco", "")
            if MeterProfile.objects.filter(
                user=user, meter_number=meter_number, disco=disco, is_active=True
            ).exists():
                raise serializers.ValidationError(
                    {"meter_number": "This meter is already saved to your account."}
                )

        return attrs

    def create(self, validated_data):
        from .services import validate_meter_with_disco

        user = self.context["request"].user
        meter_number = validated_data["meter_number"]
        disco = validated_data["disco"]

        # Validate against DISCO API and enrich the profile
        result = validate_meter_with_disco(meter_number, disco)
        if not result["is_valid"]:
            raise serializers.ValidationError(
                {"meter_number": result.get("error", "Meter validation failed.")}
            )

        validated_data["user"] = user
        validated_data["meter_owner_name"] = result.get("meter_owner_name", "")
        validated_data["meter_address"] = result.get("meter_address", "")
        validated_data["meter_type"] = result.get("meter_type", "PREPAID")

        # Auto-fill nickname with the registered account name from the DISCO
        # so the meter card title always shows a meaningful name.
        # Users can still rename it later via PATCH /meters/{id}/.
        if not validated_data.get("nickname") and validated_data["meter_owner_name"]:
            validated_data["nickname"] = validated_data["meter_owner_name"]

        # If a soft-deleted record exists for this user+meter+disco, reactivate it
        # instead of creating a duplicate (which would violate unique_together).
        existing = MeterProfile.objects.filter(
            user=user, meter_number=meter_number, disco=disco, is_active=False
        ).first()
        if existing:
            for field, value in validated_data.items():
                if field != "user":
                    setattr(existing, field, value)
            existing.is_active = True
            existing.save()
            return existing

        return MeterProfile.objects.create(**validated_data)
