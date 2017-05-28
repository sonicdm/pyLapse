import unittest
from django.core.urlresolvers import reverse
from django.test import Client
from .models import Camera, Capture, CaptureSchedule, CaptureCamera, Collection, CollectionOptions, CaptureImage
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
    defaults["slug"] = "slug"
    defaults["web_interface_url"] = "web_interface_url"
    defaults["image_url"] = "image_url"
    defaults["preview_url"] = "preview_url"
    defaults["video_url"] = "video_url"
    defaults["enabled"] = "enabled"
    defaults["username"] = "username"
    defaults["password"] = "password"
    defaults.update(**kwargs)
    return Camera.objects.create(**defaults)


def create_capture(**kwargs):
    defaults = {}
    defaults["name"] = "name"
    defaults["slug"] = "slug"
    defaults["collection_id"] = "collection_id"
    defaults["capture_start"] = "capture_start"
    defaults["capture_end"] = "capture_end"
    defaults["capture_prefix"] = "capture_prefix"
    defaults.update(**kwargs)
    return Capture.objects.create(**defaults)


def create_captureschedule(**kwargs):
    defaults = {}
    defaults["name"] = "name"
    defaults["slug"] = "slug"
    defaults["start_time"] = "start_time"
    defaults["end_time"] = "end_time"
    defaults["capture_interval"] = "capture_interval"
    defaults["last_capture"] = "last_capture"
    defaults["capture_days"] = "capture_days"
    defaults.update(**kwargs)
    if "capture" not in defaults:
        defaults["capture"] = create_
        'lapsecore_capture'()
    return CaptureSchedule.objects.create(**defaults)


def create_capturecamera(**kwargs):
    defaults = {}
    defaults["name"] = "name"
    defaults["slug"] = "slug"
    defaults["camera_id"] = "camera_id"
    defaults["camera_alias"] = "camera_alias"
    defaults.update(**kwargs)
    if "capture" not in defaults:
        defaults["capture"] = create_
        'lapsecore_capture'()
    return CaptureCamera.objects.create(**defaults)


def create_collection(**kwargs):
    defaults = {}
    defaults["name"] = "name"
    defaults["slug"] = "slug"
    defaults["collection_dir"] = "collection_dir"
    defaults.update(**kwargs)
    return Collection.objects.create(**defaults)


def create_collectionoptions(**kwargs):
    defaults = {}
    defaults["name"] = "name"
    defaults["slug"] = "slug"
    defaults["auto_resize"] = "auto_resize"
    defaults["resize_x"] = "resize_x"
    defaults["resize_y"] = "resize_y"
    defaults["quality"] = "quality"
    defaults["optimize"] = "optimize"
    defaults.update(**kwargs)
    return CollectionOptions.objects.create(**defaults)


def create_captureimage(**kwargs):
    defaults = {}
    defaults["name"] = "name"
    defaults["slug"] = "slug"
    defaults["file_path"] = "file_path"
    defaults.update(**kwargs)
    if "capture" not in defaults:
        defaults["capture"] = create_
        'lapsecore_capture'()
    if "collection" not in defaults:
        defaults["collection"] = create_
        'lapsecore_collection'()
    return CaptureImage.objects.create(**defaults)


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
            "slug": "slug",
            "web_interface_url": "web_interface_url",
            "image_url": "image_url",
            "preview_url": "preview_url",
            "video_url": "video_url",
            "enabled": "enabled",
            "username": "username",
            "password": "password",
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_camera(self):
        camera = create_camera()
        url = reverse('lapsecore_camera_detail', args=[camera.slug, ])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_camera(self):
        camera = create_camera()
        data = {
            "name": "name",
            "slug": "slug",
            "web_interface_url": "web_interface_url",
            "image_url": "image_url",
            "preview_url": "preview_url",
            "video_url": "video_url",
            "enabled": "enabled",
            "username": "username",
            "password": "password",
        }
        url = reverse('lapsecore_camera_update', args=[camera.slug, ])
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
            "slug": "slug",
            "collection_id": "collection_id",
            "capture_start": "capture_start",
            "capture_end": "capture_end",
            "capture_prefix": "capture_prefix",
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
            "slug": "slug",
            "collection_id": "collection_id",
            "capture_start": "capture_start",
            "capture_end": "capture_end",
            "capture_prefix": "capture_prefix",
        }
        url = reverse('lapsecore_capture_update', args=[capture.slug,])
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
                   "name": "name",
                   "slug": "slug",
                   "start_time": "start_time",
                   "end_time": "end_time",
            "capture_interval": "capture_interval",
                   "last_capture": "last_capture",
                   "capture_days": "capture_days",
                   "capture": create_'lapsecore_capture'().pk,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_captureschedule(self):
        captureschedule = create_captureschedule()
        url = reverse('lapsecore_captureschedule_detail', args=[captureschedule.slug, ])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_captureschedule(self):
        captureschedule = create_captureschedule()
        data = {
                   "name": "name",
                   "slug": "slug",
                   "start_time": "start_time",
                   "end_time": "end_time",
            "capture_interval": "capture_interval",
                   "last_capture": "last_capture",
                   "capture_days": "capture_days",
                   "capture": create_'lapsecore_capture'().pk,
        }
        url = reverse('lapsecore_captureschedule_update', args=[captureschedule.slug, ])
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
            "name": "name",
                   "slug": "slug",
                   "camera_id": "camera_id",
                   "camera_alias": "camera_alias",
                   "capture": create_'lapsecore_capture'().pk,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_capturecamera(self):
        capturecamera = create_capturecamera()
        url = reverse('lapsecore_capturecamera_detail', args=[capturecamera.slug, ])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_capturecamera(self):
        capturecamera = create_capturecamera()
        data = {
            "name": "name",
                   "slug": "slug",
                   "camera_id": "camera_id",
                   "camera_alias": "camera_alias",
                   "capture": create_'lapsecore_capture'().pk,
        }
        url = reverse('lapsecore_capturecamera_update', args=[capturecamera.slug, ])
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
            "slug": "slug",
            "collection_dir": "collection_dir",
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_collection(self):
        collection = create_collection()
        url = reverse('lapsecore_collection_detail', args=[collection.slug, ])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_collection(self):
        collection = create_collection()
        data = {
            "name": "name",
            "slug": "slug",
            "collection_dir": "collection_dir",
        }
        url = reverse('lapsecore_collection_update', args=[collection.slug, ])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


class CollectionOptionsViewTest(unittest.TestCase):
    '''
    Tests for CollectionOptions
    '''
    def setUp(self):
        self.client = Client()

    def test_list_collectionoptions(self):
        url = reverse('lapsecore_collectionoptions_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_collectionoptions(self):
        url = reverse('lapsecore_collectionoptions_create')
        data = {
            "name": "name",
            "slug": "slug",
            "auto_resize": "auto_resize",
            "resize_x": "resize_x",
            "resize_y": "resize_y",
            "quality": "quality",
            "optimize": "optimize",
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_collectionoptions(self):
        collectionoptions = create_collectionoptions()
        url = reverse('lapsecore_collectionoptions_detail', args=[collectionoptions.slug, ])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_collectionoptions(self):
        collectionoptions = create_collectionoptions()
        data = {
            "name": "name",
            "slug": "slug",
            "auto_resize": "auto_resize",
            "resize_x": "resize_x",
            "resize_y": "resize_y",
            "quality": "quality",
            "optimize": "optimize",
        }
        url = reverse('lapsecore_collectionoptions_update', args=[collectionoptions.slug, ])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


class CaptureImageViewTest(unittest.TestCase):
    '''
    Tests for CaptureImage
    '''
    def setUp(self):
        self.client = Client()

    def test_list_captureimage(self):
        url = reverse('lapsecore_captureimage_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_captureimage(self):
        url = reverse('lapsecore_captureimage_create')
        data = {
            "name": "name",
                   "slug": "slug",
            "file_path": "file_path",
                   "capture": create_'lapsecore_capture'().pk,
               "collection": create_
        'lapsecore_collection'().pk,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_detail_captureimage(self):
        captureimage = create_captureimage()
        url = reverse('lapsecore_captureimage_detail', args=[captureimage.slug, ])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_update_captureimage(self):
        captureimage = create_captureimage()
        data = {
            "name": "name",
                   "slug": "slug",
            "file_path": "file_path",
                   "capture": create_'lapsecore_capture'().pk,
               "collection": create_
        'lapsecore_collection'().pk,
        }
        url = reverse('lapsecore_captureimage_update', args=[captureimage.slug, ])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)


