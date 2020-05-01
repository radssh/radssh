import queue
from radssh.streambuffer import StreamBuffer

# Common queue object - all tests should ensure
# queue is empty upon completion ot test
sb_queue = queue.Queue(maxsize=3)

def test_initial_state():
    sb = StreamBuffer(sb_queue, tag="TestMode")
    assert str(sb) == "<StreamBuffer-TestMode>"
    assert sb.queue == sb_queue
    assert sb.active
    assert len(sb) == 0
    assert sb.buffer == b''
    assert sb_queue.qsize() == 0

def test_full_line():
    sb = StreamBuffer(sb_queue, tag="TestMode")
    sb.push("One\n")
    # Queue should be empty, without an explicit flush
    assert sb_queue.qsize() == 0
    sb.push("")
    assert sb_queue.qsize() == 1
    tag, data = sb_queue.get()
    assert tag == "TestMode"
    assert data == "One"
    assert sb.pull() == b"One\n"

def test_multiline():
    # With a queue size of 3, the 4th line is expected to be
    # quietly discarded and not show up in the queue
    values = ("One", "Two", "3", "Four")
    sb = StreamBuffer(sb_queue, tag="TestMode", presplit=True)
    sb.push("\n".join(values))
    sb.push(b"\n")
    # Queue should be empty, without an explicit flush
    assert sb_queue.qsize() == 0

    sb.push("")
    assert sb_queue.qsize() == 3
    assert sb.discards == 1
    for x in values[:3]:
        tag, data = sb_queue.get()
        assert tag == "TestMode"
        assert data == x
    # Doing a pull() should show ALL the pushed data, even if
    # if did not get pushed to the queue
    assert sb.pull() == b"One\nTwo\n3\nFour\n"

def test_partial_line():
    sb = StreamBuffer(sb_queue, tag="TestMode", presplit=True)
    sb.push("Not yet....")
    sb.push("")
    assert sb_queue.qsize() == 0
    assert sb.pull() == b"Not yet...."
    # Check we can use __iter__ to get buffer as strings,
    # including pending data that was not yet sent to queue
    as_lines = list(sb)
    assert len(as_lines) == 1
    assert as_lines[0] == "Not yet...."
