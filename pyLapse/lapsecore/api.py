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


class CaptureCameraViewSet(viewsets.ModelViewSet):
    """ViewSet for the CaptureCamera class"""

    queryset = models.CaptureCamera.objects.all()
    serializer_class = serializers.CaptureCameraSerializer
    permission_classes = [permissions.IsAuthenticated]


class CaptureScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet for the CaptureSchedule class"""

    queryset = models.CaptureSchedule.objects.all()
    serializer_class = serializers.CaptureScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]


class CollectionViewSet(viewsets.ModelViewSet):
    """ViewSet for the Collection class"""

    queryset = models.Collection.objects.all()
    serializer_class = serializers.CollectionSerializer
    permission_classes = [permissions.IsAuthenticated]


class CollectionExportViewSet(viewsets.ModelViewSet):
    """ViewSet for the CollectionExport class"""

    queryset = models.CollectionExport.objects.all()
    serializer_class = serializers.CollectionExportSerializer
    permission_classes = [permissions.IsAuthenticated]


class ExportPresetViewSet(viewsets.ModelViewSet):
    """ViewSet for the ExportPreset class"""

    queryset = models.ExportPreset.objects.all()
    serializer_class = serializers.ExportPresetSerializer
    permission_classes = [permissions.IsAuthenticated]


class SchedulerViewSet(viewsets.ModelViewSet):
    """ViewSet for the Scheduler class"""

    queryset = models.Scheduler.objects.all()
    serializer_class = serializers.SchedulerSerializer
    permission_classes = [permissions.IsAuthenticated]


class ExportTimeFilterViewSet(viewsets.ModelViewSet):
    """ViewSet for the ExportTimeFilter class"""

    queryset = models.ExportTimeFilter.objects.all()
    serializer_class = serializers.ExportTimeFilterSerializer
    permission_classes = [permissions.IsAuthenticated]


class CollectionFileViewSet(viewsets.ModelViewSet):
    """ViewSet for the CollectionFile class"""

    queryset = models.CollectionFile.objects.all()
    serializer_class = serializers.CollectionFileSerializer
    permission_classes = [permissions.IsAuthenticated]


class ScheduleDaysViewSet(viewsets.ModelViewSet):
    """ViewSet for the ScheduleDays class"""

    queryset = models.ScheduleDays.objects.all()
    serializer_class = serializers.ScheduleDaysSerializer
    permission_classes = [permissions.IsAuthenticated]


