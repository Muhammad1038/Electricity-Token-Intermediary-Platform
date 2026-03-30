from rest_framework import serializers
from .models_inquiry import MeterInquiry

class MeterInquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = MeterInquiry
        fields = [
            "id",
            "user",
            "description",
            "image1",
            "image2",
            "status",
            "feedback",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "feedback", "created_at", "updated_at", "user"]