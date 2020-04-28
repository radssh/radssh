# Test cases for RadSSHConfig (sshconfig.py)

import pytest

from radssh.sshconfig import RadSSHConfig

# Make dicts for sample command_line_options and radssh_config_options
command_line_options = {
    "FingerprintHash": "md5",
    "ProxyCommand": "cmd /bin/echo"
}

radssh_config_options = {
    "IDENTITYAgent": "$GPG_AGENT_SOCK",
    "IdentityFile": ["/dev/null"],
    "HostKeyAlgorithms": "+foo,bar,baz",
    "PubkeyAcceptedKeyTypes": "-ecdsa*",
    "UnknownOption": "123",
    "ProxyCommand": "rad /bin/echo"
}

def test_default_values():
    cfg = RadSSHConfig(user_config_filename="/dev/null", system_config_filename="/dev/null")
    options = cfg.options("alpha123")
    # maps should be 6 layers deep
    assert len(options.maps) == 6

    assert options["hostname"] == "alpha123"
    assert options["port"] == "22"
    assert options["fingerprinthash"] == "sha256"
    assert options["addkeystoagent"] == "no"
    assert options["identitiesonly"] == "no"

    assert options["hostkeyalgorithms"] == RadSSHConfig.default_config["hostkeyalgorithms"]
    # ChainMap.maps[0] should have original_hostname plus defaults for IdentityFile
    assert "hostname" not in options.maps[0]
    assert "original_hostname" in options.maps[0]
    assert "identityfile" in options.maps[0]
    assert "certificatefile" in options.maps[0]
    assert len(options.maps[0]) == 3
    # maps[1] and maps[2] should be empty, since we didn't pass anything
    assert not options.maps[1]
    assert not options.maps[2]
    # /dev/null should result in just hostname for maps[3] and maps[4]
    assert list(options.maps[3]) == ["hostname"]
    assert options.maps[3]["hostname"] == "alpha123"
    assert list(options.maps[4]) == ["hostname"]
    assert options.maps[4]["hostname"] == "alpha123"

    assert options.maps[5] is RadSSHConfig.default_config


def test_dict_overrides():
    cfg = RadSSHConfig(command_line_options=command_line_options,
                       radssh_config_options=radssh_config_options,
                       user_config_filename="/dev/null",
                       system_config_filename="/dev/null")
    options = cfg.options("dict_overrides")
    assert options["fingerprinthash"] == "md5" # Default sha256
    assert options["proxycommand"] == "cmd /bin/echo"
    # IdentityAgent should not appear in maps 0, 1, 3, or 4
    assert options["identityagent"] == "$GPG_AGENT_SOCK"
    assert "identityagent" not in options.maps[0]
    assert "identityagent" not in options.maps[1]
    assert "identityagent" not in options.maps[3]
    assert "identityagent" not in options.maps[4]
    # UnknownOption should not be promoted from dict at all
    assert "unknownoption" not in options
    # IdentityFile is supplied as a single value
    assert len(options["identityfile"]) == 1
    # CertificateFile should also follow suit
    assert len(options["certificatefile"]) == 1
    # Nonsensical filename, but should be derived according to rules
    assert options["certificatefile"][0] == "/dev/null-cert.pub"

    # +option working for HostKeyAlgorithms
    assert len(options["hostkeyalgorithms"].split(",")) == \
           3 + len(cfg.default_keytypes.split(","))
    assert options["hostkeyalgorithms"].split(",")[-3] == "foo"
    assert options["hostkeyalgorithms"].split(",")[-2] == "bar"
    assert options["hostkeyalgorithms"].split(",")[-1] == "baz"

    # -option working for PubkeyAcceptedKeyTypes
    assert len(options["pubkeyacceptedkeytypes"].split(",")) == 8
    assert "ecdsa" not in options["pubkeyacceptedkeytypes"]
    assert "ecdsa" in cfg.default_config["pubkeyacceptedkeytypes"]

    # confirm proxycommand is in map for radssh_config
    assert options.maps[2]["proxycommand"] == "rad /bin/echo"


def test_missing_config_files():
    cfg = RadSSHConfig(user_config_filename="./tests/path/does/not/exist",
                       system_config_filename="./tests/path/does/not/exist")
    options = cfg.options("host1")
    assert len(options.maps[3]) == 1
    assert len(options.maps[4]) == 1


def test_config_files():
    cfg = RadSSHConfig(user_config_filename="./tests/files/user_ssh_config",
                       system_config_filename="./tests/files/system_ssh_config")
    options = cfg.options("host1")
    assert options["addkeystoagent"] == "yes"
    assert options["identitiesonly"] == "yes"
