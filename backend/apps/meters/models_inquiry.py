from django.db import models
from django.conf import settings

class MeterInquiry(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="meter_inquiries")
    description = models.TextField()
    image1 = models.ImageField(upload_to="meter_inquiries/")
    image2 = models.ImageField(upload_to="meter_inquiries/")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    feedback = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Inquiry #{self.id} by {self.user}"  