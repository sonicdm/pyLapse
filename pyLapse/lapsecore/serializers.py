import models

from rest_framework import serializers


class CameraSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Camera
        fields = (
            'slug', 
            'name',
            'created',
            'last_updated',
            'web_interface_url',
            'image_url',
            'preview_url',
            'video_url', 
            'enabled',
            'username',
            'password', 
        )


class CaptureSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Capture
        fields = (
            'slug', 
            'name', 
            'created', 
            'last_updated',
            'collection_id',
            'capture_start',
            'capture_end', 
        )


class CaptureScheduleSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CaptureSchedule
        fields = (
            'slug', 
            'name', 
            'created', 
            'last_updated',
            'start_time',
            'end_time',
            'capture_interval',
            'capture_days', 
        )


class CaptureCameraSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CaptureCamera
        fields = (
            'slug', 
            'name', 
            'created', 
            'last_updated', 
            'camera_id',
            'camera_alias', 
        )


