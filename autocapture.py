from pyLapse.ImgSeq import cameras, settings
from pyLapse.ImgSeq import collections
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import colorama

seed_output = settings.seed_closet['inputdir']
outside_output = settings.outside['inputdir']

scheduler = BlockingScheduler()
lastrun = ""


def main():
    colorama.init(autoreset=True)

    print colorama.Fore.GREEN + "Starting Time Lapse Auto Capture"
    scheduler.add_job(grab_outside, 'cron', hour='5-21', minute="*", id='outside_day')
    scheduler.add_job(grab_outside, 'cron', hour='21-24,00-05', minute='*/15', id='outside_night')
    scheduler.add_job(grab_closet, 'cron', hour='5-22', minute="*", id='closet_day')
    scheduler.add_job(grab_closet, 'cron', hour='23,00-05', minute='*/15', id='closet_night')
    scheduler.add_job(next_job, 'cron', minute='*')
    print colorama.Fore.CYAN + "Starting Jobs:"
    scheduler.print_jobs()
    scheduler.start()


def next_job():
    scheduler.print_jobs()


def grab_outside():
    imageurl = cameras.outside_camera.imageurl
    name = cameras.outside_camera.name
    print colorama.Fore.YELLOW + "{timestamp}: Grabbing {cameraname} from {url}\n".format(cameraname=name, url=imageurl,
                                                                                          timestamp=datetime.now())
    cameras.outside_camera.save_image(outside_output, prefix="Outside ")
    print colorama.Fore.GREEN + "{timestamp}: Success Grabbed {cameraname} from {url}\n".format(cameraname=name,
                                                                                                url=imageurl,
                                                                                                timestamp=datetime.now())


def grab_closet():
    imageurl = cameras.seed_closet_camera.imageurl
    name = cameras.seed_closet_camera.name
    print colorama.Fore.YELLOW + "{timestamp}: Grabbing {cameraname} from {url}\n".format(cameraname=name, url=imageurl,
                                                                                          timestamp=datetime.now())
    cameras.seed_closet_camera.save_image(seed_output, prefix="Seed Closet ")
    print colorama.Fore.GREEN + "{timestamp}: Success Grabbed {cameraname} from {url}\n".format(cameraname=name,
                                                                                                url=imageurl,
                                                                                                timestamp=datetime.now())


if __name__ == '__main__':
    main()
