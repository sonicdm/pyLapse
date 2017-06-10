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
    def __init__(self, name, export_dir, collection_dir, ext='jpg', mask='*', filematch=None):
        self.name = name
        self.collection_dir = collection_dir
        self.export_dir = export_dir
        self.exports = dict()
        self.captures = dict()
        self.images = imageset_load(self.collection_dir, ext, mask, filematch)

    def __str__(self):
        return "Image Collection: %s, Location: %s, Image Count: %s" % (self.name, self.collection_dir,
                                                                        self.images.imagecount)

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
        self.exports[name] = Export(name, subdir, self.images, prefix=prefix, desc=desc, **cron_args)

    def get_exports(self):
        yield self.exports

    def export(self, exportname, **writer_args):
        self.exports[exportname].run(self.export_dir, **writer_args)

    def export_all(self, **writer_args):
        for exportname in self.exports.keys():
            print self.exports.get(exportname)
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
        'timestampfontsize', 'timestampcolor', 'timestamppos', 'zeropadding'
    )

    def __init__(self, name, subdir, imageset, prefix=None, desc=None, year=None, month=None, day=None, week=None,
                 day_of_week=None,
                 hour=None, minute=None, second=None, start_date=None, end_date=None, timezone=None):
        cron_args = dict((key, value) for (key, value) in six.iteritems(locals())
                         if key in self.CRON_ARG_NAMES and value is not None)
        self.imageset = imageset
        self.name = name
        self.subdir = subdir
        self.desc = desc
        self.prefix = prefix
        super(Export, self).__init__(**cron_args)

    def run(self, outputdir, **kwargs):
        writer_args = dict((key, value) for (key, value) in six.iteritems(kwargs)
                           if key in self.WRITER_OPTIONS and value is not None)
        io = ImageIO()
        imageindex = self.imageset.imageindex
        imagelist = cron_image_filter(imageindex, self, fuzzy=5)
        ext = basename(imageindex.keys()[0]).split('.')[-1]
        outputdir = join(outputdir, self.subdir)
        prepare_output_dir(outputdir, ext='jpg')
        outindex = self.imageset.index_files(imagelist)

        io.write_imageset(outindex, outputdir, prefix=self.prefix, **writer_args)

    def __str__(self):
        cron_str = super(Export, self).__str__()
        return "Export: {name} - Subdir: {subdir} - Desc: {desc} - Prefix: {prefix} - {cron}".format(
            name=self.name, desc=self.desc,
            prefix=self.prefix, cron=cron_str, subdir=self.subdir)

    def schedule(self, scheduler, **kwargs):
        pass
