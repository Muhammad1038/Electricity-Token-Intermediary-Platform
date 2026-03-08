"""
meters — Views: MeterProfileViewSet + MeterValidationView.
"""
import logging

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MeterProfile
from .serializers import (
    MeterProfileSerializer,
    MeterValidationRequestSerializer,
    MeterValidationResultSerializer,
)
from .services import validate_meter_with_disco

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        tags=["meters"],
        summary="List my meter profiles",
        description="Returns all active meter profiles belonging to the authenticated user. Default meter is listed first.",
        responses={200: MeterProfileSerializer(many=True)},
    ),
    create=extend_schema(
        tags=["meters"],
        summary="Add a meter profile",
        description=(
            "Save a new meter. The meter number is validated against the DISCO API before saving.\n\n"
            "**Example body:**\n"
            "```json\n"
            '{\"meter_number\": \"45811090419\", \"disco\": \"IBEDC\"}\n'
            "```"
        ),
        request=MeterProfileSerializer,
        responses={
            201: MeterProfileSerializer,
            400: OpenApiResponse(description="Validation error or meter not found at DISCO"),
            403: OpenApiResponse(description="Maximum 5 meters per account reached"),
        },
    ),
    retrieve=extend_schema(
        tags=["meters"],
        summary="Get a meter profile",
        responses={200: MeterProfileSerializer},
    ),
    partial_update=extend_schema(
        tags=["meters"],
        summary="Update a meter profile",
        description="Partial update — send only the fields to change (e.g. `nickname`).",
        request=MeterProfileSerializer,
        responses={200: MeterProfileSerializer},
    ),
    destroy=extend_schema(
        tags=["meters"],
        summary="Remove a meter profile",
        description="Soft-deletes the meter (sets `is_active=False`). The record is not permanently deleted.",
        responses={204: OpenApiResponse(description="Deleted")},
    ),
)
class MeterProfileViewSet(viewsets.ModelViewSet):
    """
    CRUD for the authenticated user's saved meter profiles.

    GET    /api/v1/meters/           — list my meters
    POST   /api/v1/meters/           — add meter (validates via DISCO API)
    GET    /api/v1/meters/{id}/      — retrieve one
    PATCH  /api/v1/meters/{id}/      — update nickname / is_default
    DELETE /api/v1/meters/{id}/      — soft-delete (sets is_active=False)
    POST   /api/v1/meters/{id}/set_default/  — set as default
    """

    serializer_class = MeterProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return MeterProfile.objects.filter(
            user=self.request.user, is_active=True
        ).order_by("-is_default", "created_at")

    def perform_destroy(self, instance):
        """Soft-delete instead of hard delete."""
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])

    @extend_schema(
        tags=["meters"],
        summary="Set as default meter",
        description="Marks this meter as the default. Clears the default flag from all other user meters automatically.",
        request=None,
        responses={
            200: OpenApiResponse(
                description="Success",
                examples=[OpenApiExample("Success", value={"detail": "'12345678901' set as default meter."})],
            )
        },
    )
    @action(detail=True, methods=["post"], url_path="set-default")
    def set_default(self, request, pk=None):
        """Mark this meter as the user's default."""
        meter = self.get_object()
        meter.is_default = True
        meter.save()  # MeterProfile.save() clears other defaults automatically
        return Response(
            {"detail": f"'{meter.nickname or meter.meter_number}' set as default meter."},
            status=status.HTTP_200_OK,
        )


class MeterValidationView(APIView):
    """
    Validate a meter number against the DISCO API without saving a profile.

    POST /api/v1/meters/validate/
    Body: { "meter_number": "...", "disco": "IBEDC" }
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["meters"],
        summary="Validate a meter number",
        description=(
            "Checks a meter number against the DISCO API in real time. Does **not** save anything.\n\n"
            "Use this before adding a meter to confirm it exists.\n\n"
            "**Available DISCO codes:** `IBEDC`, `EKEDC`, `AEDC`, `BEDC`, `EEDC`, `JEDC`, `KAEDCO`, `KEDCO`, `PHEDC`, `YEDC`"
        ),
        request=MeterValidationRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=MeterValidationResultSerializer,
                description="Meter is valid",
                examples=[OpenApiExample(
                    "Valid meter",
                    value={
                        "meter_number": "45811090419",
                        "disco": "IBEDC",
                        "meter_owner_name": "JOHN DOE",
                        "meter_address": "12 EXAMPLE STREET, IBADAN",
                        "meter_type": "PREPAID",
                        "is_valid": True,
                    },
                )],
            ),
            422: OpenApiResponse(description="Meter number not found at DISCO"),
        },
    )
    def post(self, request):
        req_serializer = MeterValidationRequestSerializer(data=request.data)
        req_serializer.is_valid(raise_exception=True)

        meter_number = req_serializer.validated_data["meter_number"]
        disco = req_serializer.validated_data["disco"]

        result = validate_meter_with_disco(meter_number, disco)

        if not result.get("is_valid"):
            return Response(
                {"is_valid": False, "error": result.get("error", "Invalid meter number.")},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        result_serializer = MeterValidationResultSerializer(
            data={
                "meter_number": meter_number,
                "disco": disco,
                "meter_owner_name": result.get("meter_owner_name", ""),
                "meter_address": result.get("meter_address", ""),
                "meter_type": result.get("meter_type", "PREPAID"),
                "is_valid": True,
            }
        )
        result_serializer.is_valid()
        return Response(result_serializer.data, status=status.HTTP_200_OK)
