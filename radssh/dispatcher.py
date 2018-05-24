#
# Copyright (c) 2014, 2016, 2018 LexisNexis Risk Data Management Inc.
#
# This file is part of the RadSSH software package.
#
# RadSSH is free software, released under the Revised BSD License.
# You are permitted to use, modify, and redsitribute this software
# according to the Revised BSD License, a copy of which should be
# included with the distribution as file LICENSE.txt
#

'''
Dispatcher Module
'''

import threading
from itertools import count
import time
import logging
import traceback
try:
    import queue
except ImportError:
    import Queue as queue


class UnfinishedJobs(Exception):
    '''Exception raised by async_results() iterator when queue is stalled'''
    def __init__(self, remaining, total):
        Exception.__init__(self, remaining, total)
        self.message = 'Waiting on %d of %d results' % (remaining, total)


class JobSummary(object):
    '''Dispatcher info returned from a submitted Job'''
    def __init__(self, completed, job_id, result, start_time=None, **kwargs):
        self.job_id = job_id
        self.result = result
        self.completed = completed
        self.thread_name = threading.currentThread().getName()
        self.end_time = time.time()
        # if we don't have a start_time, then default it to end_time (instant)
        self.start_time = start_time if start_time else self.end_time
        # Catch any other named aruments passed in
        self.__dict__.update(kwargs)

    def __str__(self):
        if self.completed:
            return 'Completed [%s] (Run by %s in %g seconds)' % (self.result, self.thread_name, (self.end_time - self.start_time))
        else:
            return 'Failed [%r] (Run by %s in %g seconds)' % (self.result, self.thread_name, (self.end_time - self.start_time))


def generic_dispatch(inQ, outQ):
    '''General purpose dispatch thread'''
    while True:
        start_time = 0
        try:
            request = inQ.get()
            start_time = time.time()
            # If sent a null request, request to terminate thread
            if not request:
                break
            job_id, fn, args, kwargs = request
            result = fn(*args, **kwargs)
            if outQ:
                outQ.put((job_id, JobSummary(True, job_id, result, start_time)))
        except Exception as e:
            # Set result to the exception instead of the return value, since we don't have one
            if outQ:
                outQ.put((job_id, JobSummary(False, job_id, e, start_time)))
            logging.debug(traceback.format_exc())
        finally:
            inQ.task_done()


class Dispatcher(object):
    '''Generic threaded queue job dispatcher'''
    def __init__(self, outQ=None, threadpool_size=100, dynamic_expansion=False):
        self.inQ = queue.Queue()
        self.outQ = outQ
        self.threadpool_size = threadpool_size
        self.workers = []
        self.requests = 0
        self.thread_sequence = count()
        self.job_sequence = count()
        self.terminated = threading.Event()
        if dynamic_expansion:
            # Start a few threads now, submit will dynamically grow if needed
            self.dynamic = True
            self.start_threads(10)
        else:
            self.dynamic = False
            self.start_threads(threadpool_size)

    def start_threads(self, num=1):
        '''Grow the threadpool by the requested size, up to limit threadpool_size, set in __init__()'''
        if self.terminated.is_set():
            return
        while num > 0 and len(self.workers) < self.threadpool_size:
            thr = threading.Thread(target=generic_dispatch, args=(self.inQ, self.outQ))
            thr.setDaemon(True)
            thr.setName('%s-%d' % ('dispatcher', next(self.thread_sequence)))
            thr.start()
            self.workers.append(thr)
            num -= 1
        # Turn off dynamic expansion if we hit threadpool_size
        if num:
            self.dynamic = False

    def submit(self, handler, *args, **kwargs):
        if not callable(handler):
            raise TypeError('Cannot use %r as dispatch handler' % handler)
        if self.terminated.is_set():
            raise RuntimeError('Dispatcher has been terminated: Unable to submit calls')
        if self.dynamic and self.inQ.size() > 1:
            # Start a few more worker threads if we are backlogged
            self.start_threads(3)
        job_id = next(self.job_sequence)
        self.inQ.put((job_id, handler, args, kwargs))
        self.requests += 1
        return job_id

    def wait(self):
        if not self.terminated.is_set():
            self.inQ.join()
            self.requests = 0

    def async_results(self, timeout=3):
        '''Poll for results - can be used as iterator'''
        if not self.outQ or self.terminated.is_set():
            raise StopIteration
        while self.inQ.unfinished_tasks:
            # Results still coming in
            try:
                result = self.outQ.get(timeout=timeout)
                yield result
            except queue.Empty:
                raise UnfinishedJobs(self.inQ.unfinished_tasks, self.requests)
        # Drain remainder of queue, no more waiting
        while True:
            try:
                result = self.outQ.get_nowait()
                yield result
            except queue.Empty:
                self.wait()
                break

    def terminate(self):
        '''Clenup a Dispatcher as best as we can'''
        # Should only be called when a dispatched thread call goes so wrong that
        # it is unable to self-poll and return/timeout on its own, as in flaky connection
        # requests. exec_command calls can check the user_abort event when socket reads
        # from stdout/stderr timeout. When interrupting connection_worker thread loops,
        # it is necessary to construct a new Dispatcher object with fresh queues and thread
        # pool, since the lost connection thread(s) will prevent the join()/wait() and
        # unfinished_tasks from behaving properly, and it is more straightforward to
        # abandon the Dispacher than deal with a future outQ object eventually showing up
        # when we least expect it.
        # Set the terminated flag, and put a bunch of None objects into inQ to trigger the
        # non-blocked threads to terminate cleanly. Other resource cleanup may be added later,
        # but stopping whatever threads we can is top priority.
        self.terminated.set()
        for thr in self.workers:
            self.inQ.put(None)
