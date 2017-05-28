from django.views.generic import DetailView, ListView, UpdateView, CreateView
from .models import Camera, Capture, CaptureSchedule, CaptureCamera
from .forms import CameraForm, CaptureForm, CaptureScheduleForm, CaptureCameraForm


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
