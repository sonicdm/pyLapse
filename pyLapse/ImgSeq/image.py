import glob
import os
import re
import urllib2
from StringIO import StringIO
from datetime import datetime

import psutil
from PIL import Image, ImageDraw, ImageFont

from lapsetime import cron_image_filter, dayslice
import utils

formats = {
    'jpg': 'JPEG',
    'jpeg': 'JPEG',
    'png': 'PNG'
}

WRITER_OPTIONS = ('resize'' quality'' optimize'' resolution'
                  'drawtimestamp'' timestampformat'' timestampfont'
                  'timestampfontsize'' timestampcolor'' timestamppos'
                  'prefix', 'zeropadding')


def imageset_load(inputdir, ext='jpg', mask='*', filematch=None):
    ih = ImageSet()
    obj = ih.import_folder(inputdir, ext, mask, filematch)
    return obj


def imageset_from_names(filelist, ext='jpg', mask='*', filematch=None):
    ih = ImageSet()
    obj = ih.import_from_list(filelist, ext, mask, filematch)
    return obj


def download_image(url, outputdir, ext='jpg', resize=False,
                   quality=50, optimize=False, resolution=(1920, 1080),
                   drawtimestamp=False, timestampformat=None, filenameformat=None,
                   timestampfontsize=36, timestampcolor=(255, 255, 255), timestamppos=(0, 0), timestampfont=None,
                   prefix="", zeropadding=5):
    writer_args = dict(
        ext=ext, filenameformat=filenameformat,
        resize=resize, quality=quality, optimize=optimize, resolution=resolution,
        drawtimestamp=drawtimestamp, timestampformat=timestampformat, timestampfontsize=timestampfontsize,
        timestampcolor=timestampcolor, timestamppos=timestamppos, timestampfont=timestampfont,
        prefix=prefix, zeropadding=zeropadding,
    )
    timestamp = datetime.now()
    image = ImageIO().fetch_image_from_url(url)
    return save_image(image, outputdir, **writer_args)


def save_image(image, outputdir, timestamp, ext='jpg', resize=False,
               quality=50, optimize=False, resolution=(1920, 1080),
               drawtimestamp=False, timestampformat=None, filenameformat=None,
               timestampfontsize=36, timestampcolor=(255, 255, 255), timestamppos=(0, 0), timestampfont=None,
               prefix="", zeropadding=5):
    if not timestampformat:
        timestampformat = '%Y-%m-%d %I:%M:%S %p'
    if not filenameformat:
        filenameformat = "{prefix}{timestamp:%Y-%m-%d-%H%M%S}.{ext}"
    imgformat = formats.get(ext, 'JPEG')
    if resize:
        image.thumbnail(resolution)
    if drawtimestamp:
        image = ImageIO().timestamp_image(image, timestamp,
                                          timestampformat=timestampformat,
                                          color=timestampcolor, size=timestampfontsize, font=timestampfont
                                          )
    outputfile = outputdir + r'\\' + filenameformat.format(prefix=prefix,
                                                           timestamp=timestamp,
                                                           ext=ext)

    if not os.path.isdir(outputdir):
        os.makedirs(outputfile)

    image.save("{}".format(outputfile), imgformat, quality=quality, optimize=optimize)
    return "Saved {outputfile}".format(outputfile=outputfile)


class ImageIO:
    def __init__(self, outputdir=None, cpu_count=psutil.cpu_count, debug=False):
        self.cpu_count = cpu_count
        self.debug = debug

    def write_imageset(
            self, imageset, outputdir, resize=True,
            quality=50, optimize=False, resolution=(1920, 1080),
            drawtimestamp=False, timestampformat=None,
            timestampfontsize=36, timestampcolor=(255, 255, 255), timestamppos=(0, 0), timestampfont=None,
            prefix="", zeropadding=5
    ):
        """
        :param timestampfont: 
        :param timestampcolor: 
        :param timestampfontsize: 
        :param timestamppos: 
        :param prefix: 
        :param imageset: 
        :type imageset: dict    
        :param outputdir: 
        :param resize: 
        :param resolution: 
        :param drawtimestamp: 
        :param quality:
        :param timestampformat: 
        :param zeropadding: 
        :return: 
        """
        writerargs = dict(
            resize=resize, quality=quality, optimize=optimize, resolution=resolution,
            drawtimestamp=drawtimestamp, timestampformat=timestampformat, timestampfont=timestampfont,
            timestampfontsize=timestampfontsize, timestampcolor=timestampcolor, timestamppos=timestamppos,
            prefix=prefix, zeropadding=zeropadding
        )
        if not os.path.isdir(outputdir):
            print 'Creating output directory: %s' % outputdir
            os.makedirs(outputdir)
        if not timestampformat:
            timestampformat = r'%Y-%m-%d %I:%M:%S %p'
        if not prefix:
            prefix = os.path.basename(outputdir)
        files = []
        # print imageset
        for day, images in imageset.iteritems():
            # print day
            for image, timestamp in images.iteritems():
                files.append((os.path.normpath(image), timestamp))
                # print timestamp

        outputfiles = sorted(files, key=lambda x: x[1])
        io_threading = utils.Threading(debug=self.debug)
        if drawtimestamp:
            # threader = io_threading.multiprocess_with_progressbar
            threader = io_threading.thread_with_progressbar
        else:
            threader = io_threading.thread_with_progressbar

        do_threads = threader(self.image_writer, outputfiles, outputdir, sendarg_i_idx=True, **writerargs)

    def image_writer(self, imageinput, idx, outputdir, resize=False, quality=50, optimize=False,
                     resolution=(1920, 1080),
                     drawtimestamp=False, timestampformat=None, timestampfontsize=36,
                     timestampcolor=(255, 255, 255), timestamppos=(0, 0), timestampfont=None,
                     prefix=None,
                     zeropadding=5):

        inputimage, timestamp = imageinput
        im = Image.open(inputimage)
        if resize:
            im.thumbnail(resolution)
        if drawtimestamp:
            im = self.timestamp_image(im, timestamp,
                                      timestampformat=timestampformat,
                                      color=timestampcolor, size=timestampfontsize, font=timestampfont
                                      )
        outputfile = outputdir + r'\{prefix} {seqence_idx}'.format(prefix=prefix,
                                                                   seqence_idx=str(idx + 1).zfill(zeropadding)
                                                                   )
        im.save(outputfile + ".jpg", 'JPEG', quality=quality, optimize=optimize)
        return "saved {outputfile}.jpg".format(outputfile=outputfile)

    def fetch_image_from_url(self, url):
        request = urllib2.Request(url)
        imgdata = urllib2.urlopen(request).read()
        image = Image.open(StringIO(imgdata))
        return image

    def timestamp_image(self, imageobj, datetimestamp, font=None,
                        timestampformat=None, pos=(0, 0), color=(255, 255, 255), size=72):
        """
        Take a PIL.Image object and overlay a timestamp and return the image object
        :param size: Font Size
        :param imageobj: PIL.Image object
        :param datetimestamp: datetime.datetime object
        :param font: path to font 
        :param timestampformat: strftime
        :param pos: (x,y) coordinates for timestamp 
        :param color: (R,G,B) values for color
        :return: PIL.Image
        """
        if not font:
            font = 'COPRGTL.TTF'

        if datetimestamp and not timestampformat:
            timestampformat = r'%Y-%m-%d %I:%M:%S %p'
        if timestampformat and not datetimestamp:
            raise AttributeError('You must supply a datetime object if you want a timestamp')
        overlaytext = datetimestamp.strftime(timestampformat)
        draw = ImageDraw.Draw(imageobj)
        timestampfont = ImageFont.truetype(font, size)
        draw.text(pos, overlaytext, color, font=timestampfont)
        return imageobj


class ImageSet:
    def __init__(self):
        self.imageindex = None
        self.filematch = None
        self.images = None
        self.inputdir = None
        self.filtered_images = None
        self.filtered_images_index = None
        self.setslug = None
        self.inputmask = None
        self.imagecount = 0

    def __unicode__(self):
        return u"ImgSet %s" % self.inputdir

    def __repr__(self):
        return "<Image Handler Image Set: \'%s\'>" % (self.setslug,)

    def import_folder(self, inputdir, ext, mask, filematch):
        self.inputmask = '\\'.join((inputdir, (mask or "") + "." + ext))
        self.inputdir = inputdir
        self.setslug = self.inputmask
        self.images = glob.glob(self.inputmask)
        self.images.sort()
        self.filematch = filematch
        self.imageindex = self.index_files(self.images, self.filematch)
        return self

    def refresh_folder(self):
        self.images = glob.glob(self.inputmask)
        self.images.sort()
        self.imageindex = self.index_files(self.images, self.filematch)

    def import_from_list(self, imagelist, ext, mask, filematch):
        self.images = imagelist
        self.images.sort()
        self.setslug = "from list"
        self.filematch = filematch
        self.imageindex = self.index_files(self.images, filematch)
        return self

    def index_files(self, files, filematch=None):
        lastday = None
        self.imagecount = 0
        self.filematch = filematch

        if not self.filematch:
            self.filematch = re.compile(
                r'.*?(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})-'
                r'(?P<hour>\d{2})(?P<minute>\d{2})(?P<seconds>\d{0,2})'
            )

        days = {}
        for f in files:
            image = os.path.basename(f)
            match = self.filematch.match(image)
            if not match:
                continue
            dateargs = list(match.groups())
            if not match.group('seconds'):
                dateargs[5] = '00'

            timestamp = datetime(*[int(arg) for arg in dateargs])
            day = timestamp.strftime('%Y-%m-%d')
            if day != lastday:
                days[day] = {f: timestamp}
            elif day == lastday:
                days[day].update({f: timestamp})

            lastday = day
            self.imagecount += 1
        return days

    def filter_images(self, hourlist=[i for i in xrange(0, 24)],
                      minutelist=None, verbose=False, fuzzy=5):

        self.filtered_images = dayslice(self.imageindex, hourlist=hourlist, minutelist=minutelist,
                                        verbose=verbose, fuzzy=fuzzy)
        self.filtered_images_index = self.index_files(self.filtered_images, self.filematch)

    @property
    def days(self):
        return sorted([i for i in self.imageindex.keys()])

    def get_day_files(self, day):
        if isinstance(day, str):
            try:
                return self.imageindex[day]
            except KeyError:
                raise KeyError("Day '{}' not found in image index: {}".format(day, self.days))
        elif isinstance(day, int):
            return self.imageindex[self.days[day]]
        else:
            raise AttributeError('day must be a string or int')

    def export(self, outputdir, **kwargs):
        self.filtered_images_index = cron_image_filter(self.imageindex, **kwargs)


def run_all(collections):
    # collections = (seed_closet, outside)
    for collection in collections:
        name = collection['name']
        inputdir = collection['inputdir']
        sequence_storage = collection['sequence_storage']
        exports = collection['exports']
        for export, config in exports.iteritems():
            print 'Running Export: {} with parameters {}'.format(export, config)
            start = datetime.now()
            enabled = config.pop('enabled', False)
            if not enabled:
                continue
            span = config.pop('span', None)
            subdir = config.pop('subdir')
            outputdir = os.path.join(sequence_storage, subdir)
            print welcome_string(span, start, outputdir, inputdir)
            make_image_sequence(inputdir, outputdir, **config)
            end = datetime.now()
            print "Elapsed Time: %s" % (end - start)


def run_one(collection, span):
    name = collection['name']
    inputdir = collection['inputdir']
    sequence_storage = collection['sequence_storage']
    exports = collection['exports']
    config = exports.get(span, None)
    tempconfig = config.copy()
    tempconfig.pop('enabled', None)
    if tempconfig:
        start = datetime.now()
        span = tempconfig.pop('span', None)
        subdir = tempconfig.pop('subdir', None)
        outputdir = os.path.join(sequence_storage, subdir)
        print welcome_string(span, start, outputdir, inputdir)
        make_image_sequence(inputdir, outputdir, **tempconfig)
        end = datetime.now()
        print "Elapsed Time: %s" % (end - start)


def welcome_string(span, start, outputdir, inputdir):
    # type: (str, datetime, str, str) -> str
    welcomestring = "#######################\n" \
                    "Image Sequencing Script: {span}\n" \
                    "{time}\n" \
                    "Output to: {outdir}\n" \
                    "From: {indir}\n" \
                    "#######################\n".format(span=span, time=start, outdir=outputdir, indir=inputdir)
    return welcomestring


def make_image_sequence(inputdir, outputdir,
                        ext='jpg', mask='*', filematch=None, allframes=False,
                        hourlist=[i for i in xrange(0, 24)], minutelist=None, verbose=False, fuzzy=5,
                        resize=True,
                        quality=50, optimize=False, resolution=(1920, 1080),
                        drawtimestamp=False, timestampformat=None,
                        timestampfontsize=36, timestampcolor=(255, 255, 255), timestamppos=(0, 0), timestampfont=None,
                        prefix="", zeropadding=5
                        ):
    imageset = imageset_load(inputdir, ext, mask, filematch)
    io = ImageIO(outputdir)
    prepare_output_dir(outputdir, ext)
    if allframes:
        fileindex = imageset.imageindex
    else:
        imageset.filter_images(hourlist, minutelist, verbose, fuzzy)
        fileindex = imageset.filtered_images_index
    print "Writing files to %s from %s" % (inputdir, outputdir)
    io.write_imageset(fileindex, outputdir,
                      resize, quality, optimize, resolution,
                      drawtimestamp, timestampformat, timestampfontsize, timestampcolor, timestamppos,
                      timestampfont,
                      prefix, zeropadding)


def prepare_output_dir(outputdir, ext, mask='*'):
    if os.path.isdir(outputdir):
        print "Clearing out files from %s" % outputdir
        pattern = "{mask}.{ext}".format(mask=mask, ext=ext)
        utils.clear_target(outputdir, pattern)
    else:
        print "Creating %s" % outputdir
        os.makedirs(outputdir)
