import six
from apscheduler.triggers.cron import CronTrigger
from os.path import basename, join
from image import imageset_load, prepare_output_dir, ImageIO
from lapsetime import cron_image_filter
from settings import outside

CRON_ARG_NAMES = ('year', 'month', 'day', 'week', 'day_of_week', 'hour', 'minute', 'second')
WRITER_OPTIONS = (
    'resize', 'quality', 'optimize', 'resolution', 'drawtimestamp', 'timestampformat', 'timestampfont',
    'timestampfontsize', 'timestampcolor', 'timestamppos', 'prefix', 'zeropadding'
)


class Collection:
    def __init__(self, name, export_dir, collection_dir, export_configs=None, ext='jpg', mask='*', filematch=None):
        config_dict = outside
        self.name = config_dict['name']
        self.sequence_storage = config_dict['sequence_storage']
        self.collection_dir = config_dict['inputdir']
        self.export_dir = export_dir
        if export_configs:
            self._exports_from_config(export_configs)
        self.exports = dict()
        self.captures = dict()
        self.images = imageset_load(self.collection_dir, ext, mask, filematch)

    def __str__(self):
        print "Image Collection: %s - Location: %s" % (self.name, self.collection_dir)

    def get_meta_file(self):
        """
        get metadata from .pyLapse file in the main collection directory
        :return:
        """
        pass

    def update_meta_file(self):
        pass

    def add_export(self, name, subdir, prefix="", desc="", **kwargs):
        cron_args = dict((key, value) for (key, value) in six.iteritems(kwargs)
                         if key in CRON_ARG_NAMES and value is not None)
        self.exports[name] = Export(name, subdir, self.images, **cron_args)

    def get_exports(self):
        yield self.exports

    def export(self, exportname, **writer_args):
        self.exports[exportname].run(self.export_dir, **writer_args)

    def export_all(self, **writer_args):
        for exportname in self.exports.keys():
            self.exports[exportname].run(self.export_dir, **writer_args)

    def add_capture(self):
        pass

    def _exports_from_config(self, exports):
        if not exports:
            pass
        for name, config in exports.iteritems():
            subdir = config.pop('subdir', name)
            desc = config.pop('span', '')
            prefix = config.pop('prefix', '')
            self.add_export(name, subdir, prefix, desc, **config)


class Export(CronTrigger):
    CRON_ARG_NAMES = ('year', 'month', 'day', 'week', 'day_of_week', 'hour', 'minute', 'second')
    WRITER_OPTIONS = (
        'resize', 'quality', 'optimize', 'resolution', 'drawtimestamp', 'timestampformat', 'timestampfont',
        'timestampfontsize', 'timestampcolor', 'timestamppos', 'prefix', 'zeropadding'
    )

    def __init__(self, name, subdir, imageset, desc=None, year=None, month=None, day=None, week=None, day_of_week=None,
                 hour=None, minute=None, second=None, start_date=None, end_date=None, timezone=None, **kwargs):
        self.cron_args = dict((key, value) for (key, value) in six.iteritems(locals())
                              if key in self.CRON_ARG_NAMES and value is not None)
        self.writer_args = dict((key, value) for (key, value) in six.iteritems(kwargs)
                                if key in self.WRITER_OPTIONS and value is not None)
        self.imageset = imageset
        self.name = name
        self.subdir = subdir
        self.desc = desc
        super(Export, self).__init__(**self.cron_args)

    def run(self, outputdir, **kwargs):
        writer_args = dict((key, value) for (key, value) in six.iteritems(kwargs)
                           if key in self.WRITER_OPTIONS and value is not None)
        io = ImageIO()
        imageindex = self.imageset.imageindex
        imagelist = cron_image_filter(imageindex, self, fuzzy=5)
        ext = basename(imageindex.keys()[0]).split('.')[-1]
        prepare_output_dir(outputdir, ext='jpg')
        outindex = self.imageset.index_files(imagelist)
        outputdir = join(outputdir, self.subdir)
        io.write_imageset(outindex, outputdir, **writer_args)

    def __str__(self):
        value = super(Export, self).__str__()
        return "Export: {name} - {desc} - {cron}".format(name=self.name, desc=self.desc, cron=value)

    def schedule(self, scheduler, **kwargs):
        pass
