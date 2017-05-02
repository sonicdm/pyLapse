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


class Camera(models.Model):

    # Fields
    camera_name = CharField(max_length=200)
    camera_web = models.TextField('web interface url', max_length=200)
    camera_url = CharField('main image url', max_length=200)
    camera_preview_url = models.TextField(max_length=200, blank=True)
    camera_user = models.TextField(max_length=200, blank=True)
    camera_pass = models.TextField(max_length=200, blank=True)
    enabled = models.BooleanField(default=True)

    # Relationship Fields
    capture = models.ManyToManyField('lapsecore.Capture', )

    class Meta:
        ordering = ('-pk',)

    def __unicode__(self):
        return u'%s' % self.pk

    def get_absolute_url(self):
        return reverse('lapsecore_camera_detail', args=(self.pk,))


    def get_update_url(self):
        return reverse('lapsecore_camera_update', args=(self.pk,))


class Capture(models.Model):

    # Fields
    capture_name = CharField(max_length=200)
    created_on = DateTimeField('capture created')
    collection_id = IntegerField()
    enabled = models.TextField(default=True)
    last_capture = models.DateTimeField()

    # Relationship Fields
    camera = models.ManyToManyField('lapsecore.Camera', )

    class Meta:
        ordering = ('-pk',)

    def __unicode__(self):
        return u'%s' % self.pk

    def get_absolute_url(self):
        return reverse('lapsecore_capture_detail', args=(self.pk,))


    def get_update_url(self):
        return reverse('lapsecore_capture_update', args=(self.pk,))


class CaptureCamera(models.Model):

    # Fields
    camera_alias = CharField(max_length=200)

    # Relationship Fields
    capture = ForeignKey('lapsecore.Capture', on_delete=models.CASCADE)
    camera = ForeignKey('lapsecore.Camera', on_delete=models.CASCADE)

    class Meta:
        ordering = ('-pk',)

    def __unicode__(self):
        return u'%s' % self.pk

    def get_absolute_url(self):
        return reverse('lapsecore_capturecamera_detail', args=(self.pk,))


    def get_update_url(self):
        return reverse('lapsecore_capturecamera_update', args=(self.pk,))


class CaptureSchedule(models.Model):

    # Fields
    range_start = models.DateTimeField()
    range_end = models.DateTimeField()
    capture_interval = models.PositiveSmallIntegerField(max_length=30)
    interval_unit = models.CharField(max_length=10)

    # Relationship Fields
    capture = ForeignKey('lapsecore.Capture', on_delete=models.CASCADE)

    class Meta:
        ordering = ('-pk',)

    def __unicode__(self):
        return u'%s' % self.pk

    def get_absolute_url(self):
        return reverse('lapsecore_captureschedule_detail', args=(self.pk,))


    def get_update_url(self):
        return reverse('lapsecore_captureschedule_update', args=(self.pk,))


class Collection(models.Model):

    # Fields
    name = models.CharField(max_length=255)
    slug = extension_fields.AutoSlugField(populate_from='name', blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    file_prefix = models.CharField(max_length=50)
    output_filename_mask = models.TextField(max_length=100)
    collection_directory = models.TextField(max_length=200)


    class Meta:
        ordering = ('-created',)

    def __unicode__(self):
        return u'%s' % self.slug

    def get_absolute_url(self):
        return reverse('lapsecore_collection_detail', args=(self.slug,))


    def get_update_url(self):
        return reverse('lapsecore_collection_update', args=(self.slug,))


class CollectionExport(models.Model):

    # Fields
    name = models.CharField(max_length=255)
    slug = extension_fields.AutoSlugField(populate_from='name', blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    export_type = models.TextField(max_length=200)
    export_path = models.TextField(max_length=300)
    export_filename = models.TextField(max_length=100)

    # Relationship Fields
    collections = models.ForeignKey('lapsecore.Collections', )

    class Meta:
        ordering = ('-created',)

    def __unicode__(self):
        return u'%s' % self.slug

    def get_absolute_url(self):
        return reverse('lapsecore_collectionexport_detail', args=(self.slug,))


    def get_update_url(self):
        return reverse('lapsecore_collectionexport_update', args=(self.slug,))


class ExportPreset(models.Model):

    # Fields
    name = models.CharField(max_length=255)
    slug = extension_fields.AutoSlugField(populate_from='name', blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    output_folder = models.TextField(max_length=150)
    timefilter_id = models.IntegerField()


    class Meta:
        ordering = ('-created',)

    def __unicode__(self):
        return u'%s' % self.slug

    def get_absolute_url(self):
        return reverse('lapsecore_exportpreset_detail', args=(self.slug,))


    def get_update_url(self):
        return reverse('lapsecore_exportpreset_update', args=(self.slug,))


class Scheduler(models.Model):

    # Fields
    name = models.CharField(max_length=255)
    slug = extension_fields.AutoSlugField(populate_from='name', blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)


    class Meta:
        ordering = ('-created',)

    def __unicode__(self):
        return u'%s' % self.slug

    def get_absolute_url(self):
        return reverse('lapsecore_scheduler_detail', args=(self.slug,))


    def get_update_url(self):
        return reverse('lapsecore_scheduler_update', args=(self.slug,))


class ExportTimeFilter(models.Model):

    # Fields
    name = models.CharField(max_length=255)
    slug = extension_fields.AutoSlugField(populate_from='name', blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)


    class Meta:
        ordering = ('-created',)

    def __unicode__(self):
        return u'%s' % self.slug

    def get_absolute_url(self):
        return reverse('lapsecore_exporttimefilter_detail', args=(self.slug,))


    def get_update_url(self):
        return reverse('lapsecore_exporttimefilter_update', args=(self.slug,))


class CollectionFile(models.Model):

    # Fields
    name = models.CharField(max_length=255)
    slug = extension_fields.AutoSlugField(populate_from='name', blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    capture_time = models.DateTimeField()
    file_path = models.CharField(max_length=200)
    resolution = models.CharField(max_length=30)
    exif_data = models.TextField(max_length=65000)

    # Relationship Fields
    collection = models.ForeignKey('lapsecore.Collection', )

    class Meta:
        ordering = ('-created',)

    def __unicode__(self):
        return u'%s' % self.slug

    def get_absolute_url(self):
        return reverse('lapsecore_collectionfile_detail', args=(self.slug,))


    def get_update_url(self):
        return reverse('lapsecore_collectionfile_update', args=(self.slug,))


class CaptureScheduleDays(models.Model):

    # Fields
    name = models.CharField(max_length=255)
    slug = extension_fields.AutoSlugField(populate_from='name', blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    monday = models.BooleanField(default=True)
    tuesday = models.BooleanField(default=True)
    wednesday = models.BooleanField(default=True)
    thursday = models.BooleanField(default=True)
    friday = models.BooleanField(default=True)
    saturday = models.BooleanField(default=True)
    sunday = models.BooleanField(default=True)

    # Relationship Fields
    captureschedule = models.ForeignKey('lapsecore.CaptureSchedule', )

    class Meta:
        ordering = ('-created',)

    def __unicode__(self):
        return u'%s' % self.slug

    def get_absolute_url(self):
        return reverse('lapsecore_capturescheduledays_detail', args=(self.slug,))


    def get_update_url(self):
        return reverse('lapsecore_capturescheduledays_update', args=(self.slug,))


class ExportTimeFilterDays(models.Model):
    # Fields
    name = models.CharField(max_length=255)
    slug = extension_fields.AutoSlugField(populate_from='name', blank=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    monday = models.BooleanField(default=True)
    tuesday = models.BooleanField(default=True)
    wednesday = models.BooleanField(default=True)
    thursday = models.BooleanField(default=True)
    friday = models.BooleanField(default=True)
    saturday = models.BooleanField(default=True)
    sunday = models.BooleanField(default=True)
