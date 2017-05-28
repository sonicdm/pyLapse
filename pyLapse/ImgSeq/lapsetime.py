"""
lapsetime:
library for handling time operations on image sets.
"""
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
