import pytest

from radssh import known_hosts


c = known_hosts.KnownHostFileCache()


def test_cache():
    # Starting state with no entries
    assert len(c.entries) == 0
    # Load a sample known_hosts file to get something in cache
    kh1 = c.load("tests/files/sample_known_hosts")
    assert len(c.entries) == 1
    assert len(kh1.entries) == 6
    # Loading same file a second time should not create new entry
    kh1 = c.load("tests/files/sample_known_hosts")
    assert len(c.entries) == 1
    assert len(kh1.entries) == 6
    # Loading an empty file is permitted
    kh2 = c.load("/dev/null")
    assert len(c.entries) == 2
    assert len(kh2.entries) == 0

def test_comment_line():
    kh = c.load("tests/files/sample_known_hosts")
    # First line is a comment. The comment value has newline stripped
    assert kh.entries[0].comment == "# Comment line"
    # contents is the entire line, including the newline
    assert kh.entries[0].contents == "# Comment line\n"
    # comment line has None as keytype
    assert kh.entries[0].keytype is None

def test_github_entry():
    # Test entries loaded from file based on file position (line numbers)
    kh = c.load("tests/files/sample_known_hosts")
    # github key entry
    github = kh.entries[1]
    assert str(github.filename) == "tests/files/sample_known_hosts"
    assert github.linenumber == 2
    assert github.marker is None
    assert github.keytype == "ssh-rsa"
    assert github.comment == "GitHub Server RSA Key"
    k = github.key
    assert k.get_name() == "ssh-rsa"
    assert k.get_bits() == 2048
    assert github.fingerprint() == "SHA256:nThbg6kXUpJWGl7E1IGOCspRomTxdCARLviKw6E5SY8="
    assert github.fingerprint("MD5") == "MD5:16:27:ac:a5:76:28:2d:36:63:1b:56:4d:eb:df:a6:48"
    # Not a hashed entry, and has no wildcards or negations
    assert github.hashed_host is None
    assert not github.negations
    assert not github.patterns
    assert len(github.hosts) == 2
    assert github.hosts[0] == "github.com"
    assert github.hosts[1] == "192.30.253.112"
    assert github.match("github.com")
    assert github.match("192.30.253.112")
    assert not github.match("www.github.com")

def test_hashed_host():
    # Hashed host entry for container.testing
    kh = c.load("tests/files/sample_known_hosts")
    e = kh.entries[2]
    assert e.marker is None
    assert e.keytype == "ssh-rsa"
    assert e.hashed_host
    assert not e.patterns
    assert not e.hosts
    assert e.match("container.testing")
    assert e.fingerprint() == "SHA256:xoqHw59JmUyqnm5gt4hMzzlHLBbdv7kj/vcKTaIduCM="

def test_bandit_labs():
    # Non-standard port, ecdsa key
    kh = c.load("tests/files/sample_known_hosts")
    e = kh.entries[3]
    assert e.keytype == "ecdsa-sha2-nistp256"
    assert not e.patterns
    assert len(e.hosts) == 1
    assert e.hosts[0] == "[bandit.labs.overthewire.org]:2220"
    assert e.match("[bandit.labs.overthewire.org]:2220")
    assert not e.match("bandit.labs.overthewire.org")
    assert not e.match("bandit.labs.overthewire.org:2220")
    assert e.fingerprint() == "SHA256:98UL0ZWr85496EtCRkKlo20X3OPnyPSB5tB5RPbhczc="

def test_cert_authority():
    # marker, wildcard, ed25519 entry
    kh = c.load("tests/files/sample_known_hosts")
    e = kh.entries[4]
    assert e.marker == "@cert-authority"
    assert e.keytype == "ssh-ed25519"
    assert e.fingerprint() == "SHA256:NqvcGTv3rfwkcEvh30bgWkpWcUto4lITtZsiSAxGB5g="
    assert not e.hosts
    assert len(e.patterns) == 1
    assert e.patterns[0] == "*.testing"
    assert e.match("host1.testing")
    assert e.match("x.y.z.testing")
    assert not e.match("hots1.testing.com")

def test_revoked():
    # @revoked entry
    kh = c.load("tests/files/sample_known_hosts")
    e = kh.entries[5]
    assert e.marker == "@revoked"
    assert e.keytype == "ssh-rsa"
    assert e.match("ssh.chat")

def test_negation():
    # entry with pattern "!host"
    kh = c.load("tests/files/sample_known_hosts")
    e = kh.entries[4]
    assert e.negations
    assert len(e.negations) == 1
    assert e.negations[0] == "reject.*.testing"
    assert e.match("reject.testing")
    assert not e.match("reject.x.y.z.testing")

def test_searches():
    # Testing of various top-level search calls
    kh = c.load("tests/files/sample_known_hosts")
    github = list(kh.matching_keys("github.com"))
    assert len(github) == 1
    empty_list = list(kh.matching_keys(""))
    assert len(empty_list) == 0
    testing = list(kh.matching_keys("foo.testing"))
    assert len(testing) == 1
    reject = list(kh.matching_keys("reject.x.testing"))
    assert len(reject) == 0
    chat = list(kh.matching_keys("ssh.chat"))
    assert len(chat) == 1
    assert chat[0].marker == "@revoked"
