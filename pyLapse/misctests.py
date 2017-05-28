import os, sys

os.chdir('J:\TOOL KIT\scripts\pyLapse\pyLapse')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pyLapseweb.settings")
sys.path.extend(
    ['J:\\TOOL KIT\\scripts\\pyLapse', 'J:\\TOOL KIT\\scripts\\CatalogBoss', 'J:/TOOL KIT/scripts/pyLapse/pyLapse'])
import django

django.setup()
from ImgSeq import utils, image, lapsetime
import datetime
from background_task import background
from lapsecore.models import Capture, Camera

# Some useful test variables
inputdir = r"M:\Plants\2016\Filbert Window"
outputdir = r'M:\Plants\2016\Filbert Window\Seq'
testdir = r'F:\test'


# initialize django in the shell


def test_import_folder_to_collection():
    """
    Import Files from a folder into a collection.
    """
    pass


def get_capture_schedule(id):
    capture = Capture.objects.get(pk=id)
    schedule = capture.captureschedule_set
    print schedule.values()
    return schedule


def get_camera(id):
    camera = Camera.objects.get(pk=id)
    return camera


from threading import Timer


def schedule_capture(func, interval, *args, **kwargs):
    timer = Timer(interval, func, *args, **kwargs)


def full_set_process():
    inputdir = r'F:\Timelapse\2016\Outside 1'
    outputdir = r'F:\Timelapse\Image Sequences\Outside 1\Day'
    utils.clear_target(outputdir)
    imageset = image.imageset_load(inputdir)
    io = image.ImageIO()
    io.write_imageset(imageset.imageindex, outputdir, resize=True, timestampfontsize=24)


def test_process_imageset():
    reload(image)
    quality = 90
    fontsize = 18
    drawtimestamp = True
    prefix = "Outside 1"
    resize = True
    inputdir = r'F:\Timelapse\2016\Outside 1'
    outputdir = r'F:\Timelapse\Image Sequences\Outside 1\Day'
    utils.clear_target(outputdir)
    imageset = image.imageset_load(inputdir)
    imageset.filter_images(minutelist=[0, 30], fuzzy=5)
    io = image.ImageIO(debug=False)
    io.write_imageset(imageset.filtered_images_index, outputdir,
                      quality=quality, resize=resize, drawtimestamp=drawtimestamp, prefix=prefix,
                      timestampfontsize=fontsize)


def test_grab_image(cameraid=1):
    reload(image)
    outputdir = r'F:\Timelapse\2016\Seedlings'
    io = image.ImageIO()
    camera = get_camera(cameraid)
    prefix = 'seedlings'
    ext = 'jpg'
    imgformat = 'JPEG'
    timestamp = datetime.datetime.now()
    filenameformat = "{prefix}{timestamp:%Y-%m-%d-%H%M%S}.{ext}"
    timestampformat = '%Y-%m-%d %I:%M:%S %p'
    url = camera.image_url
    filename = "\\" + filenameformat.format(prefix=prefix,
                                            timestamp=timestamp,
                                            ext=ext)
    filepath = outputdir + filename
    print timestamp
    print "fetching url: " + url
    imageobj = io.fetch_image_from_url(url)
    # print "Adding timestamp \"{timestampformat}\" to {filename}".format(timestampformat=timestampformat,
    #                                                                    filename=filename)
    #  imageobj = io.timestamp_image(imageobj, timestamp, timestampformat=timestampformat)

    imageobj.save(filepath, imgformat, quality=50, optimize=True)
    print 'Saved {filepath} Successfully'.format(filepath=filepath)


def print_captures_with_children():
    # Print out all Capture objects with their children



    cameras = Camera.objects.all().order_by('pk')

    for cap in Capture.objects.all():
        print "|----------------------------------------------------------\n" \
              "| Capture Name: %s\n" \
              "|----------------------------------------------------------" % cap.name
        for sched in cap.captureschedule_set.values():
            print '|\t|------------------------------------------------------\n' \
                  '|\t| Schedule Name: %s\n' \
                  '|\t|------------------------------------------------------' % sched['name']
            for k, v in sched.iteritems():
                print "|\t|\t| %s: %s" % (k, v)
        for cam in cap.capturecamera_set.values():
            camera = cameras.get(pk=cam['camera_id'])
            print '|\t|------------------------------------------------------\n' \
                  '|\t| Camera Name: %s\n' \
                  '|\t| Camera Alias: %s\n' \
                  '|\t| Device Full Name: %s\n' \
                  '|\t| Camera Address: %s\n' \
                  '|\t|------------------------------------------------------' % (
                      cam['name'],
                      cam['camera_alias'],
                      camera.name,
                      camera.web_interface_url
                  )
            for k, v in cam.iteritems():
                print "|\t|\t| %s: %s" % (k, v)
