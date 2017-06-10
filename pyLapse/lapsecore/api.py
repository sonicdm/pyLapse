import models
import serializers
from rest_framework import viewsets, permissions


class CameraViewSet(viewsets.ModelViewSet):
    """ViewSet for the Camera class"""

    queryset = models.Camera.objects.all()
    serializer_class = serializers.CameraSerializer
    permission_classes = [permissions.IsAuthenticated]


class CaptureViewSet(viewsets.ModelViewSet):
    """ViewSet for the Capture class"""

    queryset = models.Capture.objects.all()
    serializer_class = serializers.CaptureSerializer
    permission_classes = [permissions.IsAuthenticated]


class CaptureScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet for the CaptureSchedule class"""

    queryset = models.CaptureSchedule.objects.all()
    serializer_class = serializers.CaptureScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]


class CaptureCameraViewSet(viewsets.ModelViewSet):
    """ViewSet for the CaptureCamera class"""

    queryset = models.CaptureCamera.objects.all()
    serializer_class = serializers.CaptureCameraSerializer
    permission_classes = [permissions.IsAuthenticated]


