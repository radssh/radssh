#
# Copyright (c) 2014 LexisNexis Risk Data Management Inc.
#
# This file is part of the RadSSH software package.
#
# RadSSH is free software, released under the Revised BSD License.
# You are permitted to use, modify, and redsitribute this software
# according to the Revised BSD License, a copy of which should be
# included with the distribution as file LICENSE.txt
#

'''
StreamBuffer Module
Class definition for converting a stream of input data into chunks,
typically newline delimited, into a python queue object. Pushed
data is acculumulated and delivered to the queue per selectable
thresholds.
'''
from __future__ import print_function  # Requires Python 2.6 or higher

try:
    import queue
except ImportError:
    import Queue as queue

pre_split = False


class StreamBuffer(object):
    '''StreamBuffer Class'''
    def __init__(self, queue=None, tag=None, delimiter='\n', blocksize=1024):
        if tag:
            self.tag = tag
        else:
            self.tag = '%d' % id(self)
        self.queue = queue
        self.delimiter = delimiter
        self.blocksize = blocksize
        # Local data: empty buffer with reset marker position
        self.buffer = ''
        self.marker = 0
        self.pull_marker = 0
        self.line_count = 0
        self.active = True
        self.discards = 0

    def push(self, data):
        '''Appends data to buffer, and adds records (lines) to queue'''
        if not self.active:
            raise EOFError
        flush_needed = False
        if data:
            self.buffer += data.decode()
            if len(self.buffer) - self.marker > self.blocksize:
                flush_needed = True
        else:
            # If empty push call, and there is queued data, flush what we collected
            # regardless of blocksize length specified
            if len(self.buffer) - self.marker > 0:
                flush_needed = True

        if self.queue and flush_needed:
            pending = self.buffer[self.marker:]
            if pre_split:
                # Put multiple items on queue
                # split on delimiter before queueing
                lines = pending.split(self.delimiter)
                for x in lines[0:-1]:
                    self.line_count += 1
                    try:
                        self.queue.put_nowait((self.tag, x))
                    except queue.Full:
                        self.discards += 1
                # Place back to a partial last line
                self.marker = len(self.buffer) - len(lines[-1])
            else:
                # put single item on queue
                # reader will be responsible for splitting
                pos = pending.rfind(self.delimiter)
                if pos >= 0:
                    try:
                        self.queue.put_nowait((self.tag, pending[:pos]))
                    except queue.Full:
                        self.discards += 1
                    self.line_count += pending[:pos].count(self.delimiter)
                    self.marker += 1 + pos

    def pull(self, size=0):
        '''Non-queue access to accumulated data'''
        if not self.active and self.pull_marker == len(self.buffer):
            raise EOFError
        data = self.buffer[self.pull_marker:]
        if size == 0 or self.pull_marker + size <= len(self.buffer):
            # Return all pending data
            self.pull_marker = len(self.buffer)
            return data
        self.pull_marker += size
        return data[:size]

    def rewind(self, position=0):
        if position < 0 or position > len(self.buffer):
            raise ValueError('Invalid rewind position %d: only range [0:%d] exists' % (position, len(self.buffer)))
        self.pull_marker = position

    def close(self):
        '''Signal end of writes - flushes queue but saves position for further pulls'''
        if self.queue and len(self.buffer) > self.marker:
            if self.buffer[-1] == self.delimiter:
                self.buffer = self.buffer[:-1]
            pending = self.buffer[self.marker:]
            if pre_split:
                lines = pending.split(self.delimiter)
                for x in lines:
                    self.line_count += 1
                    self.queue.put((self.tag, x))
            else:
                self.queue.put((self.tag, pending))
                self.line_count += pending.count(self.delimiter)
                self.marker = len(self.buffer)
        self.active = False

    def __iter__(self):
        for x in self.buffer.split(self.delimiter):
            yield x

    def __len__(self):
        return len(self.buffer)

    def __str__(self):
        return '<%s-%s>' % (self.__class__.__name__, self.tag)


if __name__ == '__main__':
    q = queue.Queue()
    b = StreamBuffer(q, blocksize=20)
    print(b)
    b.push('one\ntwo\nthree\nfour')
    try:
        while True:
            x = q.get(block=False)
            print(x)
    except queue.Empty:
        print('-------\n')
    b.push('...(line continuattion for 4)\n\nCan I have\nA little more')
    try:
        while True:
            x = q.get(block=False)
            print(x)
    except queue.Empty:
        print('-------\n')
    b.close()
    try:
        while True:
            x = q.get(block=False)
            print(x)
    except queue.Empty:
        print('-------\n')
