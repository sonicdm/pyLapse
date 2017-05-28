from django.contrib import admin
from django import forms
from .models import Camera, Capture, CaptureSchedule, CaptureCamera

class CameraAdminForm(forms.ModelForm):

    class Meta:
        model = Camera
        fields = '__all__'


class CameraAdmin(admin.ModelAdmin):
    form = CameraAdminForm
    list_display = ['name', 'slug', 'created', 'last_updated', 'web_interface_url', 'image_url', 'preview_url',
                    'video_url', 'enabled', 'username', 'password']
    readonly_fields = ['slug', 'created', 'last_updated']

admin.site.register(Camera, CameraAdmin)


class CaptureAdminForm(forms.ModelForm):

    class Meta:
        model = Capture
        fields = '__all__'


class CaptureAdmin(admin.ModelAdmin):
    form = CaptureAdminForm
    list_display = ['name', 'slug', 'created', 'last_updated', 'collection_id', 'capture_start', 'capture_end']
    readonly_fields = ['slug', 'created', 'last_updated']

admin.site.register(Capture, CaptureAdmin)


class CaptureScheduleAdminForm(forms.ModelForm):

    class Meta:
        model = CaptureSchedule
        fields = '__all__'


class CaptureScheduleAdmin(admin.ModelAdmin):
    form = CaptureScheduleAdminForm
    list_display = ['name', 'slug', 'created', 'last_updated', 'start_time', 'end_time', 'capture_interval',
                    'capture_days']
    readonly_fields = ['slug', 'created', 'last_updated']

admin.site.register(CaptureSchedule, CaptureScheduleAdmin)


class CaptureCameraAdminForm(forms.ModelForm):

    class Meta:
        model = CaptureCamera
        fields = '__all__'


class CaptureCameraAdmin(admin.ModelAdmin):
    form = CaptureCameraAdminForm
    list_display = ['name', 'slug', 'created', 'last_updated', 'camera_id', 'camera_alias']
    readonly_fields = ['slug', 'created', 'last_updated']


admin.site.register(CaptureCamera, CaptureCameraAdmin)
