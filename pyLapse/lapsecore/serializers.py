import models

from rest_framework import serializers


class CameraSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Camera
        fields = (
            'pk', 
            'name', 
            'camera_web', 
            'camera_url', 
            'camera_preview_url', 
            'camera_user', 
            'camera_pass', 
            'enabled', 
        )


class CaptureSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Capture
        fields = (
            'slug', 
            'name', 
            'collection_id', 
            'enabled', 
            'last_capture', 
            'created', 
            'last_updated', 
        )


class CaptureCameraSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CaptureCamera
        fields = (
            'pk', 
            'camera_alias', 
            'camera_id', 
        )


class CaptureScheduleSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CaptureSchedule
        fields = (
            'pk', 
            'range_start', 
            'range_end', 
            'capture_interval', 
            'interval_unit', 
        )


class CollectionSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Collection
        fields = (
            'slug', 
            'name', 
            'created', 
            'last_updated', 
            'file_prefix', 
            'output_filename_mask', 
            'collection_directory', 
        )


class CollectionExportSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CollectionExport
        fields = (
            'slug', 
            'name', 
            'created', 
            'last_updated', 
            'export_type', 
            'export_path', 
            'export_filename', 
        )


class ExportPresetSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ExportPreset
        fields = (
            'slug', 
            'name', 
            'created', 
            'last_updated', 
            'output_folder', 
            'timefilter_id', 
        )


class SchedulerSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Scheduler
        fields = (
            'slug', 
            'name', 
            'created', 
            'last_updated', 
        )


class ExportTimeFilterSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ExportTimeFilter
        fields = (
            'slug', 
            'name', 
            'created', 
            'last_updated', 
        )


class CollectionFileSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CollectionFile
        fields = (
            'slug', 
            'name', 
            'created', 
            'last_updated', 
            'capture_time', 
            'file_path', 
            'resolution', 
            'exif_data', 
            'camera_id', 
        )


class ScheduleDaysSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ScheduleDays
        fields = (
            'slug', 
            'name', 
            'created', 
            'last_updated', 
            'monday', 
            'tuesday', 
            'wednesday', 
            'thursday', 
            'friday', 
            'saturday', 
            'sunday', 
        )


