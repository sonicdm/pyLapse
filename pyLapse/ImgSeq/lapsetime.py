"""
lapsetime:
library for handling time operations on image sets.
"""
import datetime

from tzlocal import get_localzone

import image
import utils
import dateutil
from dateutil import parser
import os


class TimeSpans:
    """
    constants for common timeframes
    """
    night = [21, 22, 23, 0, 1, 2, 3, 4, 5]
    everytenmins = [minute for minute in xrange(0, 51, 10)]
    everytwohours = [hour for hour in xrange(0, 25, 2)]
    everyfivemins = [minute for minute in xrange(0, 56, 5)]
    everytwomins = [minute for minute in xrange(0, 59, 2)]
    everydayhour = [hour for hour in xrange(6, 20, 1)]
    everyday2hours = [8, 10, 12, 14, 16, 20]
    fifteenminutes = [0, 15, 30, 45]
    dawntodusk = [i for i in (xrange(6, 21))]



def dayslice(fileindex,
             hourlist=[i for i in xrange(0, 24)],
             minutelist=None, verbose=False, fuzzy=5):
    """
    Select source images based on a selection of hours and minute ranges.
    Defaults to 1 image at the beginning of the hour for 24 hours a day.
    :param verbose: extra debug output enabled
    :type verbose: bool
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
    if verbose:
        print "hour list: %s" % hourlist
        print "minute list: %s" % minutelist
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
                match = find_nearest(hourminutes, targetminute, fuzzyness=fuzzy)
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


def get_timestamp_from_file(filepath, fuzzy=True):
    filename = os.path.basename(filepath)
    timestamp = parser.parse(filename, fuzzy=fuzzy)
    return timestamp


def find_nearest(array, value, fuzzyness=5):
    """Find nearest number to value in array
    :param fuzzyness: range of variance from target number
    :param value: number to find
    :param array: iterable to find number in
    :type value: int
    :type array: list
    :returns minute, minuteidx: Minute closest to value and its index.
    :rtype tuple: int,int
    """
    itemidx, item = min(enumerate(array), key=lambda x: abs(x[1] - value))
    if abs(value - item) <= fuzzyness:
        return item, itemidx


def get_fire_times(crontrigger, day):
    day = datetime.datetime(day.year, day.month, day.day).replace(tzinfo=get_localzone())
    # print "Day: %s" % day.date()
    cur_day = day
    last_fire = day - datetime.timedelta(microseconds=1)
    times = []
    seconds = [i for i in range(0, 86399)]
    while cur_day.date() == day.date():
        # print "Last Fire: %s" % last_fire
        now = last_fire + datetime.timedelta(microseconds=1)
        next_fire = crontrigger.get_next_fire_time(last_fire, now)
        # print "Next Fire: %s" % next_fire
        times.append(next_fire.replace(tzinfo=None))
        cur_day = next_fire
        last_fire = next_fire
    return times


def cron_image_filter(imageindex, cron_trigger, fuzzy=5):
    images = []
    for day, files in sorted(imageindex.iteritems()):
        dt_day = datetime.datetime.strptime(day, '%Y-%m-%d').replace(tzinfo=get_localzone())
        next_day = cron_trigger.get_next_fire_time(dt_day, dt_day)
        fire_times = get_fire_times(cron_trigger, dt_day)
        if next_day.date() == dt_day.date():
            # print dt_day
            last_match = None
            day_set = {key: value for key, value in sorted(files.iteritems(), key=lambda (k, v): (v, k))}
            reverse_day_set = {v: k for k, v in day_set.iteritems()}
            day_timestamps = day_set.values()
            time_keys = [find_nearest_dt(i, day_timestamps, fuzzy) for i in fire_times]
            time_keys = filter(lambda x: x != None, time_keys)
            for key in time_keys:
                images.append(reverse_day_set[key])

    return images


def find_nearest_dt(target_dt, dtlist, fuzzy=5):
    deltas = [x for x in dtlist if (x - target_dt).seconds <= fuzzy * 60]
    if len(deltas) < 1:
        return None
    else:
        return min(deltas, key=lambda x: x - target_dt)
