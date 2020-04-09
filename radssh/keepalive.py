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
RadSSH Keepalive Module
Extension to Paramiko to perform keepalive global-requests with
response, so we can tell if the remote server is responding, instead
of just padding out the local Send-Q buffer with unsendable data.
'''

import threading
import struct

import paramiko


class ServerNotResponding(Exception):
    '''
    Raised when (threshold) keepalive messages in a row fail to get
    any response, allowing better detection of severed connection.
    '''
    pass


class KeepAlive(object):
    '''
    Transport global_request() is not able to handle the scenario that
    KeepAlive test requires. The "wait" parameter, if True, will include
    in the request "want reply", but blocks the calling thread trying
    to read the reply; if False, the calling thread is not blocked, but
    the global-request is sent without "want reply" set, so there is
    nothing on the client side that indicates that the remote server
    ever got the keepalive message. Sent messages wind up in the socket
    Send-Q buffer, and no errors get detected by this process.

    This class sets up a way to send the global-request message with the
    "want reply" set, but does not block waiting for responses. After a
    short wait, if the ACK is not picked up, a counter for the number of
    pending requests is incremented, and only when it exceeds a specified
    threshold will a possible Exception be raised.

    The ping() call will fabricate a suitable keepalive global-request
    message, and use the transport completion_event to track the confirming
    response from the remote server. Oddly, RFC 4254 does not specify a
    keepalive global-request message; the operation relies on the requirement
    that the remote end MUST reply to global-request, even if the reply
    is a SSH_MSG_REQUEST_FAILURE. There is nothing special about the
    string "keepalive@openssh.com". All that is needed is that the server
    sends some response, even if it is a failure, to set the Event.
    '''
    def __init__(self, transport, threshold=5):
        self.transport = transport
        self.threshold = threshold
        self.transport.completion_event = threading.Event()
        self.pending_count = 0

    def ping(self):
        m = paramiko.Message()
        m.add_byte(struct.pack('b', paramiko.common.MSG_GLOBAL_REQUEST))
        m.add_string('keepalive@openssh.com')
        m.add_boolean(True)
        self.transport._send_user_message(m)
        self.transport.completion_event.wait(0.1)
        if self.transport.completion_event.is_set():
            self.transport.completion_event.clear()
            self.pending_count = 0
            return True
        self.pending_count += 1
        if self.pending_count > self.threshold:
            raise ServerNotResponding(self.transport.getName())
        return False
