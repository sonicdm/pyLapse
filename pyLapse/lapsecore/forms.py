from django import forms
from .models import Camera, Capture, CaptureSchedule, CaptureCamera


class CameraForm(forms.ModelForm):
    class Meta:
        model = Camera
        fields = ['name', 'web_interface_url', 'image_url', 'preview_url', 'video_url', 'enabled', 'username',
                  'password']


class CaptureForm(forms.ModelForm):
    class Meta:
        model = Capture
        fields = ['name', 'collection_id', 'capture_start', 'capture_end']


class CaptureScheduleForm(forms.ModelForm):
    class Meta:
        model = CaptureSchedule
        fields = ['name', 'start_time', 'end_time', 'capture_interval', 'capture_days', 'capture']


class CaptureCameraForm(forms.ModelForm):
    class Meta:
        model = CaptureCamera
        fields = ['name', 'camera_id', 'camera_alias', 'capture']
