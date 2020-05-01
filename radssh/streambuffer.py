#
# Copyright (c) 2014, 2016, 2018, 2020 LexisNexis Risk Data Management Inc.
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

This is a low-level class that allows async data from multiple sources
(RadSSHConnections) to send stdout or stderr data as it is read off the
network. The StreamBuffers linked to each RadSSHConnection will accumulate
the data as it comes in, and only post to the console thread's listening
queue in full line increments. The queue object may be omitted, which will
make the StreamBuffer behave like an ordinary memory buffer that can be
explicitly pulled to get access to the accumulated data.

In general, lines of data are not pushed to the queue until a minimum number
of bytes have been accumulated. This can be adjusted by the blocksize parameter
and the sender can request an explicit flush of pending data by calling
`push("")`, which will push any accumulated full lines of data, but if the last
line is incomplete, it will be unsent.

When the StreamBuffer is closed, all pending data will be flushed to the
queue, regardless of size and regardless of whether or not a trailing newline
is present at the end of the pushed data. Once closed, the StreamBuffer will
raise an EOFError if more data is pushed. Pending data may be pulled after
a close is issued.
'''

import queue


class StreamBuffer(object):
    '''StreamBuffer Class'''
    def __init__(self, queue=None, tag=None, delimiter=b'\n',
                 blocksize=1024, presplit=False, encoding='utf-8'):
        if tag:
            self.tag = tag
        else:
            self.tag = '%d' % id(self)
        self.queue = queue
        self.delimiter = delimiter
        self.blocksize = blocksize
        # Local data: empty buffer with reset marker position
        self.buffer = bytes()
        self.marker = 0
        self.pull_marker = 0
        self.line_count = 0
        self.active = True
        self.discards = 0
        self.pre_split = presplit
        self.encoding = encoding

    def push(self, data):
        '''Appends data to buffer, and adds records (lines of text) to queue'''
        if not self.active:
            raise EOFError
        flush_needed = False
        if not isinstance(data, bytes):
            # If we're fed some unicode string, normalize buffer content
            # back to encoded bytes
            data = data.encode(self.encoding, 'xmlcharrefreplace')

        if data:
            self.buffer += data
            if len(self.buffer) - self.marker > self.blocksize:
                flush_needed = True
        else:
            # If empty push call, and there is queued data, flush what
            # we collected, regardless of blocksize length specified
            if len(self.buffer) - self.marker > 0:
                flush_needed = True

        if self.queue and flush_needed:
            pending = self.buffer[self.marker:]
            if self.pre_split:
                # Put multiple items on queue
                # split on delimiter before queueing
                lines = pending.split(self.delimiter)
                for x in lines[0:-1]:
                    self.line_count += 1
                    try:
                        data = x.decode(self.encoding, 'replace')
                        self.queue.put_nowait((self.tag, data))
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
                        data = pending[:pos].decode(self.encoding, 'replace')
                        self.queue.put_nowait((self.tag, data))
                    except queue.Full:
                        self.discards += 1
                    self.line_count += pending[:pos].count(self.delimiter)
                    self.marker += 1 + pos

    def pull(self, size=0):
        '''Non-queue access to accumulated data as bytes'''
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
        if position < 0:
            raise ValueError('Rewind position cannot be negative')
        if position > len(self.buffer):
            raise ValueError('Rewind position ({}) exceeds length ({})'.format(
                             position, len(self.buffer)))
        self.pull_marker = position

    def close(self):
        '''
        Signal end of writes - forces a queue flush, but
        saves position for further pulls
        '''
        if self.buffer and self.buffer[-1:] == self.delimiter:
            self.buffer = self.buffer[:-1]
        if self.queue and len(self.buffer) > self.marker:
            self.push(b'')
            if len(self.buffer) > self.marker:
                # Flush partial last line
                pending = self.buffer[self.marker:]
                data = pending.decode(self.encoding, 'replace')
                self.queue.put((self.tag, data))
                self.line_count += 1
        self.marker = len(self.buffer)
        self.active = False

    def __iter__(self):
        '''Yield lines of text from accumulated bytes in buffer'''
        for x in self.buffer.split(self.delimiter):
            yield x.decode(self.encoding, 'replace')

    def __len__(self):
        '''Count of bytes (not characters) in buffer'''
        return len(self.buffer)

    def __str__(self):
        return '<%s-%s>' % (self.__class__.__name__, self.tag)
