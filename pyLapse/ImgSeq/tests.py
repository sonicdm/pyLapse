import utils
import image
import lapsetime
import time
import os
from operator import itemgetter

testoutputdir = r'F:\test\\'
testseqdir = r'F:\test\\'


"""
Time Span Tests
"""


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
    inputdir = r'M:\Plants\2016\Filbert Window'
    imageset = image.imageset_load(inputdir)
    return imageset


"""
File Handling Tests
"""


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


"""
Threading and process tests
"""


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
    testlist = ['i']*10
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


if __name__ == '__main__':
    clear_target_test()
