"""
meters — URL configuration.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MeterProfileViewSet, MeterValidationView

router = DefaultRouter()
router.register(r"", MeterProfileViewSet, basename="meter-profile")

urlpatterns = [
    path("validate/", MeterValidationView.as_view(), name="meter-validate"),
    path("", include(router.urls)),
]
