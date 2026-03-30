from rest_framework import generics, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from .models_inquiry import MeterInquiry
from .serializers_inquiry import MeterInquirySerializer

class MeterInquiryListCreateView(generics.ListCreateAPIView):
    queryset = MeterInquiry.objects.all()
    serializer_class = MeterInquirySerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        # Users see their own, admins see all
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return MeterInquiry.objects.all().order_by('-created_at')
        return MeterInquiry.objects.filter(user=user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)