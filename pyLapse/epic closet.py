import datetime, urllib2, os, sys
from PIL import Image

os.chdir('J:\TOOL KIT\scripts\pyLapse\pyLapse')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pyLapseweb.settings")
sys.path.extend(
    ['J:\\TOOL KIT\\scripts\\pyLapse', 'J:\\TOOL KIT\\scripts\\CatalogBoss', 'J:/TOOL KIT/scripts/pyLapse/pyLapse'])
import django

django.setup()
from ImgSeq import image, utils, lapsetime
import misctests

resolution = (1920, 1080)

quality = 40
reload(image)
outputdir = r'F:\\Timelapse\\2016\\Sex Closet'
if not os.path.isdir(outputdir):
    os.makedirs(outputdir)
io = image.ImageIO()
camera = misctests.get_camera(2)
prefix = 'Sex Closet'
ext = 'jpg'
imgformat = 'JPEG'
filenameformat = "{prefix}{timestamp: %Y-%m-%d-%H%M%S}.{ext}"
timestampformat = '%Y-%m-%d %I:%M:%S %p'
url = camera.image_url
print "fetching url: " + url
imageobj = io.fetch_image_from_url(url)
timestamp = datetime.datetime.now()
filename = "\\" + filenameformat.format(prefix=prefix,
                                        timestamp=timestamp,
                                        ext=ext)
filepath = outputdir + filename

imageobj.thumbnail(resolution)
imageobj.save(filepath, imgformat, quality=85, optimize=True)
print 'Saved {filepath} Successfully'.format(filepath=filepath)
