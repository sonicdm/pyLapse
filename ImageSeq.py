import os
import glob
import re
import sys
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import as_completed, ProcessPoolExecutor, ThreadPoolExecutor
import tqdm
from datetime import datetime
import time

threadcount = 8
fuzzyness = 5
drawtimestamp = False
font = 'COPRGTL.TTF'
timestampformat = '%Y-%m-%d %I:%M:%S %p'
outputsize = (1920, 1080)
inputdir = "F:\pics\seedlings"
outputdir = r'M:\Plants\2016\Seedlings\Image Sequence'
filematch = re.compile(
    r'[ \w]*?(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})-(?P<hour>\d{2})(?P<minute>\d{2})(?P<seconds>\d{2})'
)


def __init__(self, verbose=False):
    self.verbose = verbose
    self.font = overlayfont
    print 'End Init'
    pass


class ImageHandler:
    def __init__(self):
        self.fileindex = None
        self.images = None
        pass

    def load(self, inputdir, outputdir, ext='jpg', mask='*'):
        inputmask = '\\'.join((inputdir, (mask or "") + "." + ext))
        self.images = glob.glob(inputmask)
        self.images.sort()
        self.fileindex = self.index_files(self.images)
        return self

    def index_files(self, files):
        lastday = None
        days = {}
        for f in files:
            match = filematch.match(f)
            if not match:
                continue
            timestamp = datetime(*[int(arg) for arg in match.groups()])
            day = timestamp.strftime('%Y-%m-%d')
            if day != lastday:
                days[day] = {f: timestamp}
            elif day == lastday:
                days[day].update({f: timestamp})

            lastday = day
        return days
        # do copying and thumbnailing


def main():
    setpriority()
    if len(sys.argv) > 1:
        span = sys.argv[1]
    else:
        span = raw_input('Enter timeframe. (day, all, full, night, noon):')

    start = datetime.today()
    welcomestring = "#######################\n" \
                    "Image Sequencing Script: {span}\n" \
                    "{time}\n" \
                    "Output to: {outdir}\n" \
                    "From: {indir}\n" \
                    "#######################\n".format(span=span, time=start, outdir=outputdir, indir=inputdir)
    print welcomestring
    fileindex = index_files(images)
    # every 10 minutes
    everytenmins = [minute for minute in xrange(0, 51, 10)]
    everytwohours = [hour for hour in xrange(0, 25, 2)]
    everyfivemins = [minute for minute in xrange(0, 56, 5)]
    everytwomins = [minute for minute in xrange(0, 59, 2)]
    halfhour = [0, 30]
    if span == "day":
        subdir = 'day'
        # day hours 5am to 8pm
        day = [hour for hour in xrange(6, 20, 1)]
        # 3 hours per day 8 12 20
        sixperday = [8, 10, 12, 14, 16, 20]
        imageset = dayslice(fileindex, minutelist=halfhour, hourlist=everytwohours)
        copy_images(imageset, subdir)

    if span == "night":
        subdir = "night"
        # night hours 8pm to 5am
        night = [21, 22, 23, 0, 1, 2, 3, 4, 5]
        imageset = dayslice(fileindex, minutelist=halfhour, hourlist=night)
        copy_images(imageset, subdir)

    if span == "full":
        subdir = 'full'
        imageset = dayslice(fileindex, minutelist=everyfivemins)
        copy_images(imageset, subdir)

    if span == "noon":
        subdir = 'noon'
        imageset = dayslice(fileindex, hourlist=[12])
        copy_images(imageset, subdir)

    if span == "all":
        subdir = 'all'
        copy_images(images, subdir)

    end = datetime.today()
    print "Elapsed time: {0}".format(end - start)


def clear_target(subdir):
    outputpath = os.path.join(outputdir, subdir)
    taggedfordeath = glob.glob(outputpath + r'\*.jpg')
    print "\rClearing out the old files from %s" % outputpath
    with ThreadPoolExecutor(max_workers=threadcount * 5) as executor:
        futures = [executor.submit(os.remove, victim) for idx, victim in enumerate(taggedfordeath)]
        kwargs = {
            'total': len(futures),
            'unit': ' images',
            'unit_scale': True,
            'leave': True,
            'ascii': True
        }
        tbar = tqdm.tqdm(as_completed(futures), **kwargs)

        for f in tbar:
            pass
        executor.shutdown(wait=True)


def thumbnail(inputfile, idx, subdir):
    newname = r'\\' + subdir + str(idx + 1).zfill(5) + '.jpg'
    outputfile = os.path.join(outputdir, subdir) + newname
    try:
        im = Image.open(inputfile)
        im.thumbnail(outputsize)
        if drawtimestamp:
            filename = os.path.basename(inputfile)
            match = filematch.match(filename)
            if match:
                timestamp = datetime(*[int(arg) for arg in match.groups()])
                overlaytext = timestamp.strftime(timestampformat)
                draw = ImageDraw.Draw(im)
                timestampfont = ImageFont.truetype(font, 16)
                draw.text((0, 0), overlaytext, (255, 255, 255), font=timestampfont)
        im.save(outputfile, 'JPEG')
        outstr = "{input} ==> {output}".format(input=inputfile, output=newname)
        return outstr
    except IOError:
        print "Unable to open file: {} for reading.".format(inputfile)


def copy_images(files, subdir):
    clear_target(subdir)
    print "\nCopying New files into \{}".format(subdir)
    if drawtimestamp:
        with ProcessPoolExecutor(max_workers=threadcount) as executor:
            futures = [executor.submit(thumbnail, f, idx, subdir) for idx, f in enumerate(files)]
            kwargs = {
                'total': len(futures),
                'unit': ' images',
                'unit_scale': True,
                'leave': True,
                'ascii': True
            }
            tbar = tqdm.tqdm(as_completed(futures), **kwargs)

            for f in tbar:
                pass

                # executor.shutdown(wait=True)
    else:
        with ThreadPoolExecutor(max_workers=threadcount * 5) as executor:
            futures = [executor.submit(thumbnail, f, idx, subdir) for idx, f in enumerate(files)]
            kwargs = {
                'total': len(futures),
                'unit': ' images',
                'unit_scale': True,
                'leave': True,
                'ascii': True
            }
            tbar = tqdm.tqdm(as_completed(futures), **kwargs)

            for f in tbar:
                # print f.result()
                pass

                # executor.shutdown(wait=True)

        print "{} Pictures Copied".format(len(files))
    return True


def dayslice(fileindex,
             hourlist=[i for i in xrange(0, 24)],
             minutelist=None):
    """
    Select source images based on a selection of hours and minute ranges.
    Defaults to 1 image at the beginning of the hour for 24 hours a day.
    :param fileindex: Dict of {str: {str: datetime}
    :type  fileindex: dict
    :param hourlist: list of hours to pull images from
    :type hourlist: list of int
    :param minutelist: sub list of minutes to pull from each hour
    :type minutelist: list of int
    :return:
    """

    imageset = []
    hourlist.sort()
    if not minutelist:
        minutelist = [0]
    minutelist.sort()
    for day, files in fileindex.iteritems():
        files = {key: value for key, value in sorted(files.iteritems(), key=lambda (k, v): (v, k))}
        for targethour in hourlist:
            hourminutes = []
            hourfilenames = []
            hrdbg = "Looking for targethour:{targethour}".format(targethour=targethour)
            if verbose:
                print hrdbg
            for filename, timestamp in sorted(files.iteritems()):

                if timestamp.hour == targethour:
                    # print "Found hour #{targethour} in {filename}: {timestamp}".format(targethour=targethour,
                    #                                                                 filename=filename,
                    #                                                                 timestamp=timestamp)
                    hourminutes.append(timestamp.minute)
                    hourfilenames.append(filename)
            if verbose:
                print "hourfilenames: %s" % hourfilenames
                print "hourminutes: %s" % hourminutes
            if len(hourminutes) < 1:
                # print "No hours matching {hour} for day: {day}".format(day=day, hour=targethour)
                continue

            for targetminute in minutelist:
                mindbg = "Looking for targetminute:{targetminute} in hourminutes:{hourminutes}".format(
                    targetminute=targetminute,
                    hourminutes=hourminutes
                )
                if verbose:
                    print mindbg
                match = find_nearest(hourminutes, targetminute)
                if match:
                    minute, idx = match
                    filename = hourfilenames[idx]
                    fuzzdbg = '{filename}: {minute} is close enough to {target}'.format(minute=minute,
                                                                                        target=targetminute,
                                                                                        filename=filename)
                    if verbose:
                        print fuzzdbg

                    imageset.append(filename)
                    # print "Day:{day} Imageset:{imageset}".format(day=day, imageset=imageset)
    imageset.sort()
    return imageset


def find_nearest(array, value):
    """Find nearest number to value in array
    :param value: number to find
    :param array: iterable to find number in
    :type value: int
    :type array: list
    :returns minute, minuteidx: Minute closest to value and its index.
    :rtype tuple: int,int
    """
    minuteidx, minute = min(enumerate(array), key=lambda x: abs(x[1] - value))
    if abs(value - minute) <= fuzzyness:
        return minute, minuteidx


def setpriority():
    import psutil
    ps = psutil.Process(os.getpid())
    ps.nice(16384)


if __name__ == '__main__':
    main()
