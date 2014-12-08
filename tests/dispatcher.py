from __future__ import print_function

import threading
import time
import sys
import uuid
try:
    import queue
except ImportError:
    import Queue as queue

from radssh.dispatcher import UnfinishedJobs, JobSummary, Dispatcher

epoch = time.time()

# Set some default values
threadpool_size = 3
job_count = 10
async_timeout = 2


# Define a test function to be called asynchronously
# it produces some stdout chatter so we can see the independent thread process flow
def arg_printer(*args, **kwargs):
    # Print out input parameters and thread name on entry
    sys.stdout.write('>>> Args: %s, Kwargs: %s in thread %s\n' % (args, kwargs, threading.currentThread().getName()))
    sys.stdout.flush()

    # Do a sleep to delay so we can see threads take some time to work
    time.sleep(args[0])
    if args[0] == 3:
        # Raise exception (after sleeping) on the value 3
        raise ValueError('For some reason, the value THREE is rejected, so I raise an exception.')

    # Make up some tuple values as a return value
    sys.stdout.write('<<< Thread %s returning its result\n' % (threading.currentThread().getName()))
    sys.stdout.flush()
    return('%d - 5 = %d' % (args[0], args[0] - 5), '//%s//' % args[1], time.time() - epoch)

# If we really don't care about feedback of results, we don't need a resultQ
# the Dispatcher will discard the results if we don't have one. For this
# test case, we prefer not to be flying blind.
resultQ = queue.Queue()
d = Dispatcher(resultQ, threadpool_size)

# Submit a bunch of requests into the dispatcher queue. submit() returns a job_id
# so that we can match up the responses with the corresponding request, since they won't be
# guaranteed to come back in the order they were submitted
for x in range(job_count):
    job_id = d.submit(arg_printer, x, 'foo', other=uuid.uuid4())
    print('Submitted job %d as [%s]' % (x, job_id))

# After submitting have the main thread report when it is done - some console output
# will have been emitted from the worker threads at this point, add a few seconds sleep
# on the main thread to wait for a few more lines
print('MAIN THREAD: Submits Complete')
time.sleep(3)

# Okay, main thread - time to check on what finished while we were sleeping...
print('MAIN THREAD: Processing Results')
try:
    # Pull results back through async_results iterator. Some will be ready,
    # some will trickle in as we iterate, if none come in before the wait timeout
    # then the iterator will raise UnfinishedJobs to let us know how many are still
    # in-flight
    for job_id, summary in d.async_results(async_timeout):
        print('MAIN THREAD ***', job_id, summary)
except UnfinishedJobs as e:
    print('MAIN THREAD: No more async results ready')
    print('MAIN THREAD: Still waiting on %d of %d' % e.args)
    # Explicit call to wait() to block until ALL the rest of the results arrive
    d.wait()
    print('MAIN THREAD: All jobs completed - wait() returned control')

# Cannot re-use the iterator, but you can call again to async_results
# and resume where we left off. Call with a timeout of 0 since we expect them
# all to be ready on the result queue.
try:
    for job_id, summary in d.async_results(0):
        print('MAIN THREAD: Late result arrival ***', job_id, summary)
except UnfinishedJobs as e:
    print('MAIN THREAD: This should not be if we waited correctly')
    print(e.message)

print('MAIN THREAD: No more results')
