from django.contrib import admin
from django import forms
from .models import Camera, Capture, CaptureCamera, CaptureSchedule, Collection, CollectionExport, ExportPreset, Scheduler, ExportTimeFilter, CollectionFile, ScheduleDays

class CameraAdminForm(forms.ModelForm):

    class Meta:
        model = Camera
        fields = '__all__'


class CameraAdmin(admin.ModelAdmin):
    form = CameraAdminForm
    list_display = ['name', 'camera_web', 'camera_url', 'camera_preview_url', 'camera_user', 'camera_pass', 'enabled']
    readonly_fields = ['name', 'camera_web', 'camera_url', 'camera_preview_url', 'camera_user', 'camera_pass', 'enabled']

admin.site.register(Camera, CameraAdmin)


class CaptureAdminForm(forms.ModelForm):

    class Meta:
        model = Capture
        fields = '__all__'


class CaptureAdmin(admin.ModelAdmin):
    form = CaptureAdminForm
    list_display = ['name', 'collection_id', 'enabled', 'last_capture', 'slug', 'created', 'last_updated']
    readonly_fields = ['name', 'collection_id', 'enabled', 'last_capture', 'slug', 'created', 'last_updated']

admin.site.register(Capture, CaptureAdmin)


class CaptureCameraAdminForm(forms.ModelForm):

    class Meta:
        model = CaptureCamera
        fields = '__all__'


class CaptureCameraAdmin(admin.ModelAdmin):
    form = CaptureCameraAdminForm
    list_display = ['camera_alias', 'camera_id']
    readonly_fields = ['camera_alias', 'camera_id']

admin.site.register(CaptureCamera, CaptureCameraAdmin)


class CaptureScheduleAdminForm(forms.ModelForm):

    class Meta:
        model = CaptureSchedule
        fields = '__all__'


class CaptureScheduleAdmin(admin.ModelAdmin):
    form = CaptureScheduleAdminForm
    list_display = ['range_start', 'range_end', 'capture_interval', 'interval_unit']
    readonly_fields = ['range_start', 'range_end', 'capture_interval', 'interval_unit']

admin.site.register(CaptureSchedule, CaptureScheduleAdmin)


class CollectionAdminForm(forms.ModelForm):

    class Meta:
        model = Collection
        fields = '__all__'


class CollectionAdmin(admin.ModelAdmin):
    form = CollectionAdminForm
    list_display = ['name', 'slug', 'created', 'last_updated', 'file_prefix', 'output_filename_mask', 'collection_directory']
    readonly_fields = ['name', 'slug', 'created', 'last_updated', 'file_prefix', 'output_filename_mask', 'collection_directory']

admin.site.register(Collection, CollectionAdmin)


class CollectionExportAdminForm(forms.ModelForm):

    class Meta:
        model = CollectionExport
        fields = '__all__'


class CollectionExportAdmin(admin.ModelAdmin):
    form = CollectionExportAdminForm
    list_display = ['name', 'slug', 'created', 'last_updated', 'export_type', 'export_path', 'export_filename']
    readonly_fields = ['name', 'slug', 'created', 'last_updated', 'export_type', 'export_path', 'export_filename']

admin.site.register(CollectionExport, CollectionExportAdmin)


class ExportPresetAdminForm(forms.ModelForm):

    class Meta:
        model = ExportPreset
        fields = '__all__'


class ExportPresetAdmin(admin.ModelAdmin):
    form = ExportPresetAdminForm
    list_display = ['name', 'slug', 'created', 'last_updated', 'output_folder', 'timefilter_id']
    readonly_fields = ['name', 'slug', 'created', 'last_updated', 'output_folder', 'timefilter_id']

admin.site.register(ExportPreset, ExportPresetAdmin)


class SchedulerAdminForm(forms.ModelForm):

    class Meta:
        model = Scheduler
        fields = '__all__'


class SchedulerAdmin(admin.ModelAdmin):
    form = SchedulerAdminForm
    list_display = ['name', 'slug', 'created', 'last_updated']
    readonly_fields = ['name', 'slug', 'created', 'last_updated']

admin.site.register(Scheduler, SchedulerAdmin)


class ExportTimeFilterAdminForm(forms.ModelForm):

    class Meta:
        model = ExportTimeFilter
        fields = '__all__'


class ExportTimeFilterAdmin(admin.ModelAdmin):
    form = ExportTimeFilterAdminForm
    list_display = ['name', 'slug', 'created', 'last_updated']
    readonly_fields = ['name', 'slug', 'created', 'last_updated']

admin.site.register(ExportTimeFilter, ExportTimeFilterAdmin)


class CollectionFileAdminForm(forms.ModelForm):

    class Meta:
        model = CollectionFile
        fields = '__all__'


class CollectionFileAdmin(admin.ModelAdmin):
    form = CollectionFileAdminForm
    list_display = ['name', 'slug', 'created', 'last_updated', 'capture_time', 'file_path', 'resolution', 'exif_data', 'camera_id']
    readonly_fields = ['name', 'slug', 'created', 'last_updated', 'capture_time', 'file_path', 'resolution', 'exif_data', 'camera_id']

admin.site.register(CollectionFile, CollectionFileAdmin)


class ScheduleDaysAdminForm(forms.ModelForm):

    class Meta:
        model = ScheduleDays
        fields = '__all__'


class ScheduleDaysAdmin(admin.ModelAdmin):
    form = ScheduleDaysAdminForm
    list_display = ['name', 'slug', 'created', 'last_updated', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    readonly_fields = ['name', 'slug', 'created', 'last_updated', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

admin.site.register(ScheduleDays, ScheduleDaysAdmin)


