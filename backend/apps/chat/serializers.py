from rest_framework import serializers
from .models import Message


class SendMessageSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000, trim_whitespace=True)


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "role", "content", "created_at"]
        read_only_fields = fields
