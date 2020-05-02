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
    values = ("One", "Two", "Three", "Four")
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
    assert sb.pull() == b"One\nTwo\nThree\nFour\n"

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

def test_multiple_writers():
    sb_queue = queue.Queue()
    sb1 = StreamBuffer(sb_queue, tag="Writer1", presplit=True, blocksize=13)
    sb2 = StreamBuffer(sb_queue, tag="Writer2", presplit=True, blocksize=13)
    sb3 = StreamBuffer(sb_queue, tag="Writer3", presplit=True, blocksize=13)
    sb1.push(b"1\n" * 6)
    sb2.push(b"22\n" * 4)  # Flush order 1
    sb3.push(b"333\n" * 3)
    assert sb_queue.qsize() == 0
    # Trigger 2 to flush (4 lines)
    sb2.push(b"")
    assert sb_queue.qsize() == 4
    assert list(sb2) == ["22"] * 4 + [""]

    sb3.push(b"333\n" * 3)  # Flush order 2, combined with first set of 333's
    sb2.push(b"22\n" * 4)  # Flush order 3, due to close() call
    sb2.close()
    sb1.push(b"1\n" * 6)  # Flush order 4, combined with earliest push

    # Expected final output sequence, based on flush order, not push
    seq = ["22"] * 4 + ["333"] * 6 + ["22"] * 4 + ["1"] * 12
    assert sb_queue.qsize() == len(seq)
    for x in seq:
        tag, output = sb_queue.get()
        assert output == x
