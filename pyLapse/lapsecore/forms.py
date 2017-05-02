from django import forms
from .models import Camera, Capture, CaptureCamera, CaptureSchedule, Collection, CollectionExport, ExportPreset, Scheduler, ExportTimeFilter, CollectionFile, ScheduleDays


class CameraForm(forms.ModelForm):
    class Meta:
        model = Camera
        fields = ['name', 'camera_web', 'camera_url', 'camera_preview_url', 'camera_user', 'camera_pass', 'enabled']


class CaptureForm(forms.ModelForm):
    class Meta:
        model = Capture
        fields = ['name', 'collection_id', 'enabled', 'last_capture', 'camera', 'collection']


class CaptureCameraForm(forms.ModelForm):
    class Meta:
        model = CaptureCamera
        fields = ['camera_alias', 'camera_id', 'capture']


class CaptureScheduleForm(forms.ModelForm):
    class Meta:
        model = CaptureSchedule
        fields = ['range_start', 'range_end', 'capture_interval', 'interval_unit', 'capture']


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ['name', 'file_prefix', 'output_filename_mask', 'collection_directory']


class CollectionExportForm(forms.ModelForm):
    class Meta:
        model = CollectionExport
        fields = ['name', 'export_type', 'export_path', 'export_filename', 'collection']


class ExportPresetForm(forms.ModelForm):
    class Meta:
        model = ExportPreset
        fields = ['name', 'output_folder', 'timefilter_id']


class SchedulerForm(forms.ModelForm):
    class Meta:
        model = Scheduler
        fields = ['name']


class ExportTimeFilterForm(forms.ModelForm):
    class Meta:
        model = ExportTimeFilter
        fields = ['name']


class CollectionFileForm(forms.ModelForm):
    class Meta:
        model = CollectionFile
        fields = ['name', 'capture_time', 'file_path', 'resolution', 'exif_data', 'camera_id', 'collection']


class ScheduleDaysForm(forms.ModelForm):
    class Meta:
        model = ScheduleDays
        fields = ['name', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'captureschedule', 'exporttimefilter']


