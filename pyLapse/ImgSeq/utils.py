import os
import re
import sys
import traceback
from operator import itemgetter

import psutil
import tqdm
from concurrent.futures import as_completed, ProcessPoolExecutor, ThreadPoolExecutor


def setpriority():
    ps = psutil.Process(os.getpid())
    ps.nice(16384)


def clear_target(directory, mask='*.jpg'):
    import glob
    taggedfordeath = glob.glob(directory + r'\{mask}'.format(mask=mask))
    Threading().thread_with_progressbar(os.remove, taggedfordeath, sendarg_i=True)


class ThreadPoolExecutorStackTraced(ThreadPoolExecutor):
    def submit(self, fn, *args, **kwargs):
        """Submits the wrapped function instead of `fn`"""

        return super(ThreadPoolExecutorStackTraced, self).submit(
            self._function_wrapper, fn, *args, **kwargs)

    def _function_wrapper(self, fn, *args, **kwargs):
        """Wraps `fn` in order to preserve the traceback of any kind of
        raised exception
        """
        try:
            return fn(*args, **kwargs)
        except Exception:
            raise sys.exc_info()[0](traceback.format_exc())


class ProcessPoolExecutorStackTraced(ProcessPoolExecutor):
    def submit(self, fn, *args, **kwargs):
        """Submits the wrapped function instead of `fn`"""

        return super(ProcessPoolExecutorStackTraced, self).submit(
            self._function_wrapper, fn, *args, **kwargs)

    def _function_wrapper(self, fn, *args, **kwargs):
        """Wraps `fn` in order to preserve the traceback of any kind of
        raised exception

        """
        try:
            return fn(*args, **kwargs)
        except Exception:
            raise sys.exc_info()[0](traceback.format_exc())


def mkkwargs(keywords, valuemap=None, valueindexes=None, values=None, **kwargs):
    # print "mkkwargs: kwargs: %s" % keywords
    if valuemap and values and valueindexes:
        newargs = {}
        for k, v in valuemap.iteritems():
            if k in valueindexes:
                newargs[v] = values[k]

        keywords.update(newargs)
        keywords.update(kwargs)
        return keywords
    else:
        return keywords.update(kwargs)


def mkargs(oldargs, args=None):
    newargs = []
    try:
        args.__iter__()
        # print 'Multi Arg'
        newargs = [i for i in args]
        newargs.extend(oldargs)
    except AttributeError:
        # print 'Single Arg'
        newargs = [args]
        newargs.extend(oldargs)
    return newargs


def kw_send_idx_i_or_both(kws):
    kwkeys = dict(
        sendkw_i_idx=[1, 0],
        sendkw_idx_i=[0, 1],
        sendkw_i=[1],
        sendkw_idx=[0],
    )
    argkeys = dict(
        sendarg_i_idx=[1, 0],
        sendarg_idx_i=[0, 1],
        sendarg_i=[1],
        sendarg_idx=[0],
    )
    outdict = dict(
        arg_idx=[],
        kwarg_idx=[],
        keywords={}
    )
    kwkeymatch = []
    argkeymatch = []
    # Get the **kwarg values to see if idx or i needs to be sent to the threaded func.
    for k, v in kwkeys.iteritems():
        if k in kws:
            # print k, kws[k], kws
            if k:
                kwkeymatch.append(k)

    if len(kwkeymatch) > 1:
        raise AttributeError('Cannot specify more than one sendkw_ option')
    else:
        if len(kwkeymatch) <= 0:
            pass
        else:
            kws.pop(kwkeymatch[0])
            outdict['kw_idx'] = kwkeys[kwkeymatch[0]]

    # get the *arg values to see if idx or i needs to be sent to the threaded func.
    for k, v in argkeys.iteritems():
        if k in kws:
            # print k, kws[k], kws
            if k:
                argkeymatch.append(k)

    if len(argkeymatch) > 1:
        raise AttributeError('Cannot specify more than one sendarg_ option')
    else:
        if len(argkeymatch) <= 0:
            pass
        else:
            kws.pop(argkeymatch[0])
            outdict['arg_idx'] = argkeys[argkeymatch[0]]
    outdict['keywords'] = kws
    return outdict


class Threading:
    """
    Collection of threading tools
    """

    def __init__(self, cpu_count=None, debug=False, pbarunit='items'):
        self.debug = debug
        if cpu_count:
            self.cpu_count = cpu_count
        else:
            self.cpu_count = psutil.cpu_count()

    def thread_with_progressbar(self, func, iterable, *args, **kwargs):
        """
        :keyword sendarg_i_idx: pass i,idx of iterable to function as first arguments.
        :keyword sendarg_idx_i: pass idx,i of iterable to function as first arguments.
        :keyword sendarg_i: pass i of iterable to function as first argument.
        :keyword sendarg_idx: pass idx of iterable to function as first argument.
        :keyword sendkw_i_idx: pass i,idx of iterable to function as first arguments.
        :keyword sendkw_idx_i: pass idx,i of iterable to function as first arguments.
        :keyword sendkw_i: pass i of iterable to function as first argument.
        :keyword sendkw_idx: pass idx of iterable to function as first argument.
        :param func: function to run.
        :param args: args to pass to function
        :param kwargs: kwargs to pass to function
        :param iterable: iterable of things to thread with the function. 
        """
        kw_valuemap = {0: 't_idx', 1: 't_i'}
        idxi = kw_send_idx_i_or_both(kwargs)
        with ThreadPoolExecutorStackTraced(max_workers=self.cpu_count*5) as executor:
            futures = []

            for idx, i in enumerate(iterable):
                values = [idx, i]
                kwarg_idx = idxi['kwarg_idx']
                if len(kwarg_idx) < 1:
                    func_kwargs = kwargs
                else:
                    func_kwargs = mkkwargs(kwargs, kw_valuemap, kwarg_idx, values)

                argidx = idxi['arg_idx']
                if len(idxi['arg_idx']) < 1:
                    func_args = args
                else:
                    values = [idx, i]
                    func_args = mkargs(args, itemgetter(*argidx)(values))

                futures.append(executor.submit(func, *func_args, **func_kwargs))

            if not self.debug:
                pbargs = {
                    'total': len(futures),
                    'unit': ' images',
                    'unit_scale': True,
                    'leave': True,
                    'ascii': True
                }
                tbar = tqdm.tqdm(as_completed(futures), **pbargs)
                for f in tbar:
                    pass

            elif self.debug:
                result_limit = 100
                result_count = 0
                for future in as_completed(futures, timeout=300):
                    if result_count <= result_limit:
                        print future.result()
                    result_count += 1
            executor.shutdown(wait=True)

    def multiprocess_with_progressbar(self, func, iterable, *args, **kwargs):
        """
        :keyword send_i_idx: pass i,idx of iterable to function as first arguments.
        :keyword send_idx_i: pass idx,i of iterable to function as first arguments.
        :keyword send_i: pass i of iterable to function as first argument.
        :keyword send_idx: pass idx of iterable to function as first argument.
        :param func: function to run.
        :param args: args to pass to function
        :param kwargs: kwargs to pass to function
        :param iterable: iterable of things to thread with the function. 
        """
        kw_valuemap = {0: 't_idx', 1: 't_i'}
        idxi = kw_send_idx_i_or_both(kwargs)
        with ProcessPoolExecutorStackTraced(max_workers=self.cpu_count) as executor:
            futures = []

            for idx, i in enumerate(iterable):
                values = [idx, i]
                kwarg_idx = idxi['kwarg_idx']
                if len(kwarg_idx) < 1:
                    func_kwargs = kwargs
                else:
                    func_kwargs = mkkwargs(kwargs, kw_valuemap, kwarg_idx, values)

                argidx = idxi['arg_idx']
                if len(idxi['arg_idx']) < 1:
                    func_args = args
                else:
                    values = [idx, i]
                    func_args = mkargs(args, itemgetter(*argidx)(values))

                futures.append(executor.submit(func, *func_args, **func_kwargs))

            if not self.debug:
                pbargs = {
                    'total': len(futures),
                    'unit': ' images',
                    'unit_scale': True,
                    'leave': True,
                    'ascii': True
                }
                tbar = tqdm.tqdm(as_completed(futures), **pbargs)
                for f in tbar:
                    pass

            elif self.debug:
                result_limit = 100
                result_count = 0
                for future in as_completed(futures, timeout=300):
                    if result_count <= result_limit:
                        print future.result()
                    result_count += 1
            executor.shutdown(wait=True)


def is_image_url(url):
    return True if re.match(r'(http)?s?:?(//[^\"\']*\.(?:png|jpg|jpeg|gif|svg))', url) else False
