"""
An example file that uses apscheduler to automate capturing of images using ImgSeq
"""
from pyLapse.ImgSeq.cameras import Camera
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime

seed_output = r'F:\Timelapse\2016\Seedling Closet'
outside_output = r'F:\Timelapse\2016\Outside 1'
outside = Camera('Galaxy S4 Outside', r'http://192.168.1.106:8080/photoaf.jpg', 'Outside')
seed_closet = Camera('Galaxy S4 Seed Closet', r'http://192.168.1.105:8080/photoaf.jpg', 'Closet')
scheduler = BlockingScheduler()


def main():
    print "Starting Time Lapse Auto Capture"
    scheduler.add_job(grab_outside, 'cron', hour='5-21', minute="*", id='outside_day')
    scheduler.add_job(grab_outside, 'cron', hour='21-24,00-05', minute='*/15', id='outside_night')
    scheduler.add_job(grab_closet, 'cron', hour='5-22', minute="*", id='closet_day')
    scheduler.add_job(grab_closet, 'cron', hour='23,00-05', minute='*/15', id='closet_night')
    scheduler.add_job(next_job, 'cron', minute='*')
    print "Starting Jobs:"
    scheduler.print_jobs()
    scheduler.start()


def next_job():
    scheduler.print_jobs()


def grab_outside():
    imageurl = outside.imageurl
    name = outside.name
    print "{timestamp}: Grabbing {cameraname} from {url}\n".format(cameraname=name, url=imageurl,
                                                                   timestamp=datetime.now())
    outside.save_image(outside_output, prefix="Outside ")
    print "{timestamp}: Success Grabbed {cameraname} from {url}\n".format(cameraname=name, url=imageurl,
                                                                          timestamp=datetime.now())


def grab_closet():
    imageurl = seed_closet.imageurl
    name = seed_closet.name
    print "{timestamp}: Grabbing {cameraname} from {url}\n".format(cameraname=name, url=imageurl,
                                                                   timestamp=datetime.now())
    seed_closet.save_image(seed_output, prefix="Seed Closet ")
    print "{timestamp}: Success Grabbed {cameraname} from {url}\n".format(cameraname=name, url=imageurl,
                                                                          timestamp=datetime.now())


if __name__ == '__main__':
    main()
