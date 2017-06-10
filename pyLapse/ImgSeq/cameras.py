from pyLapse.ImgSeq.utils import is_image_url
from pyLapse.ImgSeq.image import ImageIO, save_image
from datetime import datetime


class Camera:
    def __init__(self, name, imageurl, location=None):
        self.name = name

        if is_image_url(imageurl):
            self.imageurl = imageurl
        else:
            raise ValueError(imageurl + ' does not seem to be an image url')
        self.location = location

    def __repr__(self):
        return '<Camera: {name}>'.format(name=self.name, imageurl=self.imageurl)

    def __str__(self):
        return 'Camera: {name} {imageurl}'.format(name=self.name, imageurl=self.imageurl)

    @property
    def imageurl(self):
        return self.imageurl

    @imageurl.setter
    def imageurl(self, value):
        if is_image_url(value):
            self.imageurl = value
        else:
            raise ValueError(value + ' does not seem to be an image url')

    def fetch_image(self):
        img = ImageIO().fetch_image_from_url(self.imageurl)
        return img

    def save_image(self, outputdir, **kwargs):
        image = self.fetch_image()
        timestamp = datetime.now()
        save_image(image, outputdir, timestamp, **kwargs)


outside_camera = Camera('Galaxy S4 Outside', r'http://192.168.1.106:8080/photoaf.jpg', 'Outside')
seed_closet_camera = Camera('Galaxy S4 Seed Closet', r'http://192.168.1.105:8080/photoaf.jpg', 'Closet')
