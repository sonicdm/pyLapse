from django.core.urlresolvers import reverse
from django_extensions.db.fields import AutoSlugField
from django.db.models import *
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.contrib.auth import models as auth_models
from django.db import models as models
from django_extensions.db import fields as extension_fields
from django.utils import timezone


class Camera(models.Model):
    # Fields
    name = models.CharField(max_length=255)
    slug = extension_fields.AutoSlugField(populate_from='name', blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    web_interface_url = models.CharField(max_length=500, blank=True)
    image_url = models.CharField(max_length=100, blank=True)
    preview_url = models.CharField(max_length=100, blank=True)
    video_url = models.CharField(max_length=100, blank=True)
    enabled = models.BooleanField(default=True)
    username = models.CharField(max_length=30, blank=True)
    password = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ('-created',)

    def __unicode__(self):
        return u'%d: %s' % (self.pk, self.slug)

    def get_absolute_url(self):
        return reverse('lapsecore_camera_detail', args=(self.slug,))

    def get_update_url(self):
        return reverse('lapsecore_camera_update', args=(self.slug,))


class Capture(models.Model):
    # Fields
    name = models.CharField(max_length=255)
    slug = extension_fields.AutoSlugField(populate_from='name', blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    collection_id = models.IntegerField()
    capture_start = models.DateTimeField()
    capture_end = models.DateTimeField()
    capture_prefix = models.CharField(max_length=40, blank=True)

    class Meta:
        ordering = ('-created',)

    def __unicode__(self):
        return u'%s' % self.slug

    def get_absolute_url(self):
        return reverse('lapsecore_capture_detail', args=(self.slug,))

    def get_update_url(self):
        return reverse('lapsecore_capture_update', args=(self.slug,))


class CaptureSchedule(models.Model):
    # Fields
    name = models.CharField(max_length=255)
    slug = extension_fields.AutoSlugField(populate_from='name', blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    start_time = models.IntegerField()
    end_time = models.IntegerField()
    capture_interval = models.IntegerField()
    last_capture = models.DateTimeField(blank=True)
    capture_days = models.CharField(max_length=15, default='1,1,1,1,1,1,1')

    # Relationship Fields
    capture = models.ForeignKey('lapsecore.Capture', )

    class Meta:
        ordering = ('-created',)

    def __unicode__(self):
        return u'%s' % self.slug

    def get_absolute_url(self):
        return reverse('lapsecore_captureschedule_detail', args=(self.slug,))

    def get_update_url(self):
        return reverse('lapsecore_captureschedule_update', args=(self.slug,))


class CaptureCamera(models.Model):
    # Fields
    name = models.CharField(max_length=255)
    slug = extension_fields.AutoSlugField(populate_from='name', blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    camera_id = models.IntegerField()
    camera_alias = models.CharField(blank=True, max_length=30)

    # Relationship Fields
    capture = models.ForeignKey('lapsecore.Capture', )

    class Meta:
        ordering = ('-created',)

    def __unicode__(self):
        return u'%s' % self.slug

    def get_absolute_url(self):
        return reverse('lapsecore_capturecamera_detail', args=(self.slug,))

    def get_update_url(self):
        return reverse('lapsecore_capturecamera_update', args=(self.slug,))

    def save(self, *args, **kwargs):
        if not self.camera_alias:
            self.camera_alias = self.slug
        super(CaptureCamera, self).save(*args, **kwargs)


class Collection(models.Model):
    # Fields
    name = models.CharField(max_length=255)
    slug = extension_fields.AutoSlugField(populate_from='name', blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    collection_dir = models.CharField(max_length=255)

    class Meta:
        ordering = ('-last_updated',)

    def __unicode__(self):
        return u'%s' % self.slug


class CollectionOptions(models.Model):
    name = models.CharField(max_length=255)
    slug = extension_fields.AutoSlugField(populate_from='name', blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    auto_resize = models.BooleanField(default=False)
    resize_x = models.IntegerField(blank=True)
    resize_y = models.IntegerField(blank=True)
    quality = models.IntegerField(blank=True)
    optimize = models.BooleanField(default=True)


class CaptureImage(models.Model):
    # Fields
    name = models.CharField(max_length=255)
    slug = extension_fields.AutoSlugField(populate_from='name', blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    capture = models.ForeignKey('lapsecore.Capture', )
    collection = models.ForeignKey('lapsecore.Collection', )

    collection_dir = models.CharField(max_length=255)

    class Meta:
        ordering = ('created',)

    def __unicode__(self):
        return u'%s' % self.slug

    def get_absolute_url(self):
        return reverse('lapsecore_capture_detail', args=(self.slug,))

    def get_update_url(self):
        return reverse('lapsecore_capture_update', args=(self.slug,))
