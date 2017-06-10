import datetime
import os
import time
from operator import itemgetter

from apscheduler.triggers.cron import CronTrigger
from tzlocal import get_localzone

import image
import lapsetime
import utils
from pyLapse.ImgSeq.lapsetime import get_fire_times, find_nearest_dt

testoutputdir = r'F:\test\\'
testseqdir = r'F:\test\\'

"""
Time Span Tests
"""


def test_cron():
    from lapsetime import cron_image_filter
    reload(lapsetime)
    ct = CronTrigger(minute='*/15')
    imageset = load_test_image_set()
    image_list = cron_image_filter(imageset.imageindex, ct)
    return image_list


def test_match_time_to_fire_list():
    imageset = load_test_image_set()
    ct = CronTrigger(minute='*/30', hour='6-12')
    print ct
    day = '2017-06-04'
    day_dt = datetime.datetime.strptime(day, '%Y-%m-%d')
    day_set = imageset.get_day_files(day)
    print day_set
    reverse_day_set = {v: k for k, v in day_set.iteritems()}
    print reverse_day_set
    fire_times = get_fire_times(ct, day_dt)
    day_files = day_set.keys()
    day_timestamps = day_set.values()

    for fire in fire_times:
        print 'Fire Time: %s' % fire
        print find_nearest_dt(fire, day_timestamps)


def test_dayslice():
    imageset = load_test_image_set()
    imageslice = lapsetime.dayslice(imageset.imageindex, lapsetime.TimeSpans.everytwohours)
    print imageslice


def get_timestamp_from_file_test():
    reload(lapsetime)
    imageset = load_test_image_set()
    for f in imageset.images[:30]:
        timestamp = lapsetime.get_timestamp_from_file(f)
        print f
        print timestamp


"""
Image Handler Tests
"""


def load_test_image_set():
    reload(image)
    inputdir = r'F:\Timelapse\2016\Outside 1'
    imageset = image.imageset_load(inputdir)
    return imageset


"""
File Handling Tests
"""


def collection_create():
    import collections
    reload(collections)
    from settings import seed_closet
    inputdir = r'F:\Timelapse\2016\Outside 1'
    outputdir = r'F:\test'
    test_collection = collections.Collection('Test Outside', outputdir, inputdir, export_configs=seed_closet['exports'])
    return test_collection


def touch(path):
    with open(path, 'a'):
        os.utime(path, None)


def create_dummy_files():
    reload(utils)
    outputdir = r'F:\test\\'
    imageset = load_test_image_set()
    threading = utils.Threading(debug=False)
    outfiles = [os.path.normpath(outputdir + os.path.basename(path)) for path in imageset.images[:500]]
    threading.thread_with_progressbar(touch, outfiles, sendarg_i=True)


def clear_target_test():
    create_dummy_files()
    targetdir = r'F:\test\\'
    utils.clear_target(targetdir)


def download_file():
    import pyLapse.misctests
    url = pyLapse.misctests.get_camera(1)


"""
Threading and process tests
"""


def test_scheduling():
    from apscheduler.schedulers.blocking import BlockingScheduler
    from cameras import seed_closet_camera
    outputdir = r'F:\test'

    def next_run():
        sched.print_jobs()

    def save_image(capture):
        print datetime.datetime.now()
        print "Saving Image"
        seed_closet_camera.save_image(outputdir, prefix="Scheduled")

    sched = BlockingScheduler()
    sched.add_job(save_image, 'cron', ['day'], minute='*', hour='5-21', )
    sched.add_job(save_image, 'cron', ['night'], minute='*/15', hour='21-24,00-05')
    sched.add_job(next_run, 'interval', minutes=1)
    return sched


def thread_dummy_func(*args, **kwargs):
    time.sleep(0.05)
    return args, kwargs


def threaded_progressbar_test():
    reload(utils)
    imageset = load_test_image_set()
    threading = utils.Threading(debug=True)
    threading.thread_with_progressbar(thread_dummy_func, imageset.images[:50], sendarg_i=True)


def mkkwargs_testing():
    testkwargs = dict(test='test', othertest=True)
    testvaluemap = {0: 'value0', 1: 'value1', 4: 'not used'}
    testvalues = ['result1', 'result2', 'not mapped']
    testvalueindex = [0, 1, 3]
    # this should work
    print "These Should Work:"
    kwargs1 = utils.mkkwargs(testkwargs, valuemap=testvaluemap, valueindexes=testvalueindex, values=testvalues)
    assert isinstance(kwargs1, dict), "kwargs1: Test failed. Did not return a dict."
    print "kwargs1: Passed. ({})".format(kwargs1)


def mkargs_testing(*args, **kwargs):
    reload(utils)
    print args
    print kwargs

    imageset = load_test_image_set()
    testlist = ['i'] * 10
    testkws = {'sendarg_i_idx': True}
    joinedkw = testkws.copy()
    joinedkw.update(kwargs)

    print joinedkw
    idxi = utils.kw_send_idx_i_or_both(joinedkw)
    print idxi
    arg_bools = [v for k, v in kwargs.items() if 'sendarg_' in k]
    argidx = idxi['arg_idx']
    # print arg_bools
    for idx, i in enumerate(testlist[:10]):
        if len(argidx) < 1:
            print 'no sendarg_'
            func_args = args
        else:
            print 'with sendarg_'
            values = [idx, i]
            # print itemgetter(*idxi)(values)
            mkargs1 = utils.mkargs(args, itemgetter(*argidx)(values))
            print mkargs1


# Unit Tests


if __name__ == '__main__':
    clear_target_test()
