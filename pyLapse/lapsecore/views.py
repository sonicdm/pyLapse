from django.views.generic import DetailView, ListView, UpdateView, CreateView
from .models import Camera, Capture, CaptureCamera, CaptureSchedule, Collection, CollectionExport, ExportPreset, Scheduler, ExportTimeFilter, CollectionFile, ScheduleDays
from .forms import CameraForm, CaptureForm, CaptureCameraForm, CaptureScheduleForm, CollectionForm, CollectionExportForm, ExportPresetForm, SchedulerForm, ExportTimeFilterForm, CollectionFileForm, ScheduleDaysForm


class CameraListView(ListView):
    model = Camera


class CameraCreateView(CreateView):
    model = Camera
    form_class = CameraForm


class CameraDetailView(DetailView):
    model = Camera


class CameraUpdateView(UpdateView):
    model = Camera
    form_class = CameraForm


class CaptureListView(ListView):
    model = Capture


class CaptureCreateView(CreateView):
    model = Capture
    form_class = CaptureForm


class CaptureDetailView(DetailView):
    model = Capture


class CaptureUpdateView(UpdateView):
    model = Capture
    form_class = CaptureForm


class CaptureCameraListView(ListView):
    model = CaptureCamera


class CaptureCameraCreateView(CreateView):
    model = CaptureCamera
    form_class = CaptureCameraForm


class CaptureCameraDetailView(DetailView):
    model = CaptureCamera


class CaptureCameraUpdateView(UpdateView):
    model = CaptureCamera
    form_class = CaptureCameraForm


class CaptureScheduleListView(ListView):
    model = CaptureSchedule


class CaptureScheduleCreateView(CreateView):
    model = CaptureSchedule
    form_class = CaptureScheduleForm


class CaptureScheduleDetailView(DetailView):
    model = CaptureSchedule


class CaptureScheduleUpdateView(UpdateView):
    model = CaptureSchedule
    form_class = CaptureScheduleForm


class CollectionListView(ListView):
    model = Collection


class CollectionCreateView(CreateView):
    model = Collection
    form_class = CollectionForm


class CollectionDetailView(DetailView):
    model = Collection


class CollectionUpdateView(UpdateView):
    model = Collection
    form_class = CollectionForm


class CollectionExportListView(ListView):
    model = CollectionExport


class CollectionExportCreateView(CreateView):
    model = CollectionExport
    form_class = CollectionExportForm


class CollectionExportDetailView(DetailView):
    model = CollectionExport


class CollectionExportUpdateView(UpdateView):
    model = CollectionExport
    form_class = CollectionExportForm


class ExportPresetListView(ListView):
    model = ExportPreset


class ExportPresetCreateView(CreateView):
    model = ExportPreset
    form_class = ExportPresetForm


class ExportPresetDetailView(DetailView):
    model = ExportPreset


class ExportPresetUpdateView(UpdateView):
    model = ExportPreset
    form_class = ExportPresetForm


class SchedulerListView(ListView):
    model = Scheduler


class SchedulerCreateView(CreateView):
    model = Scheduler
    form_class = SchedulerForm


class SchedulerDetailView(DetailView):
    model = Scheduler


class SchedulerUpdateView(UpdateView):
    model = Scheduler
    form_class = SchedulerForm


class ExportTimeFilterListView(ListView):
    model = ExportTimeFilter


class ExportTimeFilterCreateView(CreateView):
    model = ExportTimeFilter
    form_class = ExportTimeFilterForm


class ExportTimeFilterDetailView(DetailView):
    model = ExportTimeFilter


class ExportTimeFilterUpdateView(UpdateView):
    model = ExportTimeFilter
    form_class = ExportTimeFilterForm


class CollectionFileListView(ListView):
    model = CollectionFile


class CollectionFileCreateView(CreateView):
    model = CollectionFile
    form_class = CollectionFileForm


class CollectionFileDetailView(DetailView):
    model = CollectionFile


class CollectionFileUpdateView(UpdateView):
    model = CollectionFile
    form_class = CollectionFileForm


class ScheduleDaysListView(ListView):
    model = ScheduleDays


class ScheduleDaysCreateView(CreateView):
    model = ScheduleDays
    form_class = ScheduleDaysForm


class ScheduleDaysDetailView(DetailView):
    model = ScheduleDays


class ScheduleDaysUpdateView(UpdateView):
    model = ScheduleDays
    form_class = ScheduleDaysForm

