import unittest
from django.core.urlresolvers import reverse
from django.test import Client
from .models import Camera, Capture, CaptureCamera, CaptureSchedule, Collection, CollectionExport, ExportPreset, Scheduler, ExportTimeFilter, CollectionFile, ScheduleDays
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType


def create_django_contrib_auth_models_user(**kwargs):
    defaults = {}
    defaults["username"] = "username"
    defaults["email"] = "username@tempurl.com"
    defaults.update(**kwargs)
    return User.objects.create(**defaults)


def create_django_contrib_auth_models_group(**kwargs):
    defaults = {}
    defaults["name"] = "group"
    defaults.update(**kwargs)
    return Group.objects.create(**defaults)


def create_django_contrib_contenttypes_models_contenttype(**kwargs):
    defaults = {}
    defaults.update(**kwargs)
    return ContentType.objects.create(**defaults)


def create_camera(**kwargs):
    defaults = {}
    defaults["name"] = "name"
    defaults["camera_web"] = "camera_web"
    defaults["camera_url"] = "camera_url"
    defaults["camera_preview_url"] = "camera_preview_url"
    defaults["camera_user"] = "camera_user"
    defaults["camera_pass"] = "camera_pass"
    defaults["enabled"] = "enabled"
    defaults.update(**kwargs)
    return Camera.objects.create(**defaults)


def create_capture(**kwargs):
    defaults = {}
    defaults["name"] = "name"
    defaults["collection_id"] = "collection_id"
    defaults["enabled"] = "enabled"
    defaults["last_capture"] = "last_capture"
    defaults.update(**kwargs)
    if "camera" not in defaults:
        defaults["camera"] = create_camera()
    if "collection" not in defaults:
        defaults["collection"] = create_collection()
    return Capture.objects.create(**defaults)


def create_capturecamera(**kwargs):
    defaults = {}
    defaults["camera_alias"] = "camera_alias"
    defaults["camera_id"] = "camera_id"
    defaults.update(**kwargs)
    if "capture" not in defaults:
        defaults["capture"] = create_capture()
    return CaptureCamera.objects.create(**defaults)


def create_captureschedule(**kwargs):
    defaults = {}
    defaults["range_start"] = "range_start"
    defaults["range_end"] = "range_end"
    defaults["capture_interval"] = "capture_interval"
    defaults["interval_unit"] = "interval_unit"
    defaults.update(**kwargs)
    if "capture" not in defaults:
        defaults["capture"] = create_capture()
    return CaptureSchedule.objects.create(**defaults)


def create_collection(**kwargs):
    defaults = {}
    defaults["name"] = "name"
    defaults["file_prefix"] = "file_prefix"
    defaults["output_filename_mask"] = "output_filename_mask"
    defaults["collection_directory"] = "collection_directory"
    defaults.update(**kwargs)
    return Collection.objects.create(**defaults)


def create_collectionexport(**kwargs):
    defaults = {}
    defaults["name"] = "name"
    defaults["export_type"] = "export_type"
    defaults["export_path"] = "export_path"
    defaults["export_filename"] = "export_filename"
    defaults.update(**kwargs)
    if "collection" not in defaults:
        defaults["collection"] = create_collection()
    return CollectionExport.objects.create(**defaults)


def create_exportpreset(**kwargs):
    defaults = {}
    defaults["name"] = "name"
    defaults["output_folder"] = "output_folder"
    defaults["timefilter_id"] = "timefilter_id"
    defaults.update(**kwargs)
    return ExportPreset.objects.create(**defaults)


def create_scheduler(**kwargs):
    defaults = {}
    defaults["name"] = "name"
    defaults.update(**kwargs)
    return Scheduler.objects.create(**defaults)


def create_exporttimefilter(**kwargs):
    defaults = {}
    defaults["name"] = "name"
    defaults.update(**kwargs)
    return ExportTimeFilter.objects.create(**defaults)


def create_collectionfile(**kwargs):
    defaults = {}
    defaults["name"] = "name"
    defaults["capture_time"] = "capture_time"
    defaults["file_path"] = "file_path"
    defaults["resolution"] = "resolution"
    defaults["exif_data"] = "exif_data"
    defaults["camera_id"] = "camera_id"
    defaults.update(**kwargs)
    if "collection" not in defaults:
        defaults["collection"] = create_collection()
    return CollectionFile.objects.create(**defaults)


def create_scheduledays(**kwargs):
    defaults = {}
    defaults["name"] = "name"
    defaults["monday"] = "monday"
    defaults["tuesday"] = "tuesday"
    defaults["wednesday"] = "wednesday"
    defaults["thursday"] = "thursday"
    defaults["friday"] = "friday"
    defaults["saturday"] = "saturday"
    defaults["sunday"] = "sunday"
    defaults.update(**kwargs)
    if "captureschedule" not in defaults:
        defaults["captureschedule"] = create_captureschedule()
    if "exporttimefilter" not in defaults:
        defaults["exporttimefilter"] = create_exporttimefilter()
    return ScheduleDays.objects.create(**defaults)


class CameraViewTest(unittest.TestCase):
    '''
    Tests for Camera
    '''
    def setUp(self):
        self.client = Client()

    def test_list_camera(self):
        url = reverse('lapsecore_camera_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_camera(self):
        url = reverse('lapsecore_camera_create')
        data = {
            "name": "name",
            "camera_web": "camera_web",
            "camera_url": "camera_url",
            "camera_preview_url": "camera_preview_url",
            "camera_user": "camera_user",
            "camera_pass": "camera_pass",
            "enabled": "enabled",
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_camera(self):
        camera = create_camera()
        url = reverse('lapsecore_camera_detail', args=[camera.pk,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_camera(self):
        camera = create_camera()
        data = {
            "name": "name",
            "camera_web": "camera_web",
            "camera_url": "camera_url",
            "camera_preview_url": "camera_preview_url",
            "camera_user": "camera_user",
            "camera_pass": "camera_pass",
            "enabled": "enabled",
        }
        url = reverse('lapsecore_camera_update', args=[camera.pk,])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


class CaptureViewTest(unittest.TestCase):
    '''
    Tests for Capture
    '''
    def setUp(self):
        self.client = Client()

    def test_list_capture(self):
        url = reverse('lapsecore_capture_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_capture(self):
        url = reverse('lapsecore_capture_create')
        data = {
            "name": "name",
            "collection_id": "collection_id",
            "enabled": "enabled",
            "last_capture": "last_capture",
            "camera": create_camera().pk,
            "collection": create_collection().pk,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_capture(self):
        capture = create_capture()
        url = reverse('lapsecore_capture_detail', args=[capture.slug,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_capture(self):
        capture = create_capture()
        data = {
            "name": "name",
            "collection_id": "collection_id",
            "enabled": "enabled",
            "last_capture": "last_capture",
            "camera": create_camera().pk,
            "collection": create_collection().pk,
        }
        url = reverse('lapsecore_capture_update', args=[capture.slug,])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


class CaptureCameraViewTest(unittest.TestCase):
    '''
    Tests for CaptureCamera
    '''
    def setUp(self):
        self.client = Client()

    def test_list_capturecamera(self):
        url = reverse('lapsecore_capturecamera_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_capturecamera(self):
        url = reverse('lapsecore_capturecamera_create')
        data = {
            "camera_alias": "camera_alias",
            "camera_id": "camera_id",
            "capture": create_capture().pk,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_capturecamera(self):
        capturecamera = create_capturecamera()
        url = reverse('lapsecore_capturecamera_detail', args=[capturecamera.pk,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_capturecamera(self):
        capturecamera = create_capturecamera()
        data = {
            "camera_alias": "camera_alias",
            "camera_id": "camera_id",
            "capture": create_capture().pk,
        }
        url = reverse('lapsecore_capturecamera_update', args=[capturecamera.pk,])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


class CaptureScheduleViewTest(unittest.TestCase):
    '''
    Tests for CaptureSchedule
    '''
    def setUp(self):
        self.client = Client()

    def test_list_captureschedule(self):
        url = reverse('lapsecore_captureschedule_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_captureschedule(self):
        url = reverse('lapsecore_captureschedule_create')
        data = {
            "range_start": "range_start",
            "range_end": "range_end",
            "capture_interval": "capture_interval",
            "interval_unit": "interval_unit",
            "capture": create_capture().pk,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_captureschedule(self):
        captureschedule = create_captureschedule()
        url = reverse('lapsecore_captureschedule_detail', args=[captureschedule.pk,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_captureschedule(self):
        captureschedule = create_captureschedule()
        data = {
            "range_start": "range_start",
            "range_end": "range_end",
            "capture_interval": "capture_interval",
            "interval_unit": "interval_unit",
            "capture": create_capture().pk,
        }
        url = reverse('lapsecore_captureschedule_update', args=[captureschedule.pk,])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


class CollectionViewTest(unittest.TestCase):
    '''
    Tests for Collection
    '''
    def setUp(self):
        self.client = Client()

    def test_list_collection(self):
        url = reverse('lapsecore_collection_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_collection(self):
        url = reverse('lapsecore_collection_create')
        data = {
            "name": "name",
            "file_prefix": "file_prefix",
            "output_filename_mask": "output_filename_mask",
            "collection_directory": "collection_directory",
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_collection(self):
        collection = create_collection()
        url = reverse('lapsecore_collection_detail', args=[collection.slug,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_collection(self):
        collection = create_collection()
        data = {
            "name": "name",
            "file_prefix": "file_prefix",
            "output_filename_mask": "output_filename_mask",
            "collection_directory": "collection_directory",
        }
        url = reverse('lapsecore_collection_update', args=[collection.slug,])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


class CollectionExportViewTest(unittest.TestCase):
    '''
    Tests for CollectionExport
    '''
    def setUp(self):
        self.client = Client()

    def test_list_collectionexport(self):
        url = reverse('lapsecore_collectionexport_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_collectionexport(self):
        url = reverse('lapsecore_collectionexport_create')
        data = {
            "name": "name",
            "export_type": "export_type",
            "export_path": "export_path",
            "export_filename": "export_filename",
            "collection": create_collection().pk,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_collectionexport(self):
        collectionexport = create_collectionexport()
        url = reverse('lapsecore_collectionexport_detail', args=[collectionexport.slug,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_collectionexport(self):
        collectionexport = create_collectionexport()
        data = {
            "name": "name",
            "export_type": "export_type",
            "export_path": "export_path",
            "export_filename": "export_filename",
            "collection": create_collection().pk,
        }
        url = reverse('lapsecore_collectionexport_update', args=[collectionexport.slug,])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


class ExportPresetViewTest(unittest.TestCase):
    '''
    Tests for ExportPreset
    '''
    def setUp(self):
        self.client = Client()

    def test_list_exportpreset(self):
        url = reverse('lapsecore_exportpreset_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_exportpreset(self):
        url = reverse('lapsecore_exportpreset_create')
        data = {
            "name": "name",
            "output_folder": "output_folder",
            "timefilter_id": "timefilter_id",
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_exportpreset(self):
        exportpreset = create_exportpreset()
        url = reverse('lapsecore_exportpreset_detail', args=[exportpreset.slug,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_exportpreset(self):
        exportpreset = create_exportpreset()
        data = {
            "name": "name",
            "output_folder": "output_folder",
            "timefilter_id": "timefilter_id",
        }
        url = reverse('lapsecore_exportpreset_update', args=[exportpreset.slug,])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


class SchedulerViewTest(unittest.TestCase):
    '''
    Tests for Scheduler
    '''
    def setUp(self):
        self.client = Client()

    def test_list_scheduler(self):
        url = reverse('lapsecore_scheduler_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_scheduler(self):
        url = reverse('lapsecore_scheduler_create')
        data = {
            "name": "name",
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_scheduler(self):
        scheduler = create_scheduler()
        url = reverse('lapsecore_scheduler_detail', args=[scheduler.slug,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_scheduler(self):
        scheduler = create_scheduler()
        data = {
            "name": "name",
        }
        url = reverse('lapsecore_scheduler_update', args=[scheduler.slug,])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


class ExportTimeFilterViewTest(unittest.TestCase):
    '''
    Tests for ExportTimeFilter
    '''
    def setUp(self):
        self.client = Client()

    def test_list_exporttimefilter(self):
        url = reverse('lapsecore_exporttimefilter_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_exporttimefilter(self):
        url = reverse('lapsecore_exporttimefilter_create')
        data = {
            "name": "name",
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_exporttimefilter(self):
        exporttimefilter = create_exporttimefilter()
        url = reverse('lapsecore_exporttimefilter_detail', args=[exporttimefilter.slug,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_exporttimefilter(self):
        exporttimefilter = create_exporttimefilter()
        data = {
            "name": "name",
        }
        url = reverse('lapsecore_exporttimefilter_update', args=[exporttimefilter.slug,])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


class CollectionFileViewTest(unittest.TestCase):
    '''
    Tests for CollectionFile
    '''
    def setUp(self):
        self.client = Client()

    def test_list_collectionfile(self):
        url = reverse('lapsecore_collectionfile_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_collectionfile(self):
        url = reverse('lapsecore_collectionfile_create')
        data = {
            "name": "name",
            "capture_time": "capture_time",
            "file_path": "file_path",
            "resolution": "resolution",
            "exif_data": "exif_data",
            "camera_id": "camera_id",
            "collection": create_collection().pk,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_collectionfile(self):
        collectionfile = create_collectionfile()
        url = reverse('lapsecore_collectionfile_detail', args=[collectionfile.slug,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_collectionfile(self):
        collectionfile = create_collectionfile()
        data = {
            "name": "name",
            "capture_time": "capture_time",
            "file_path": "file_path",
            "resolution": "resolution",
            "exif_data": "exif_data",
            "camera_id": "camera_id",
            "collection": create_collection().pk,
        }
        url = reverse('lapsecore_collectionfile_update', args=[collectionfile.slug,])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


class ScheduleDaysViewTest(unittest.TestCase):
    '''
    Tests for ScheduleDays
    '''
    def setUp(self):
        self.client = Client()

    def test_list_scheduledays(self):
        url = reverse('lapsecore_scheduledays_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_scheduledays(self):
        url = reverse('lapsecore_scheduledays_create')
        data = {
            "name": "name",
            "monday": "monday",
            "tuesday": "tuesday",
            "wednesday": "wednesday",
            "thursday": "thursday",
            "friday": "friday",
            "saturday": "saturday",
            "sunday": "sunday",
            "captureschedule": create_captureschedule().pk,
            "exporttimefilter": create_exporttimefilter().pk,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_scheduledays(self):
        scheduledays = create_scheduledays()
        url = reverse('lapsecore_scheduledays_detail', args=[scheduledays.slug,])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_scheduledays(self):
        scheduledays = create_scheduledays()
        data = {
            "name": "name",
            "monday": "monday",
            "tuesday": "tuesday",
            "wednesday": "wednesday",
            "thursday": "thursday",
            "friday": "friday",
            "saturday": "saturday",
            "sunday": "sunday",
            "captureschedule": create_captureschedule().pk,
            "exporttimefilter": create_exporttimefilter().pk,
        }
        url = reverse('lapsecore_scheduledays_update', args=[scheduledays.slug,])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


