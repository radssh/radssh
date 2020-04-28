#
# Copyright (c) 2020 LexisNexis Risk Data Management Inc.
#
# This file is part of the RadSSH software package.
#
# RadSSH is free software, released under the Revised BSD License.
# You are permitted to use, modify, and redsitribute this software
# according to the Revised BSD License, a copy of which should be
# included with the distribution as file LICENSE.txt
#
"""
SSHConfig class for handling SSH configuration options composited
from a variety of sources, prioritized as follows:
 - Connection spec (user@host:port) for those 3 values only
 - Command Line options of the form "-o OptionName=Value", as well
 as various other explicit forms like "-p port" and "-l login_name"
 - Intermediate values loaded from user's .radssh_config file
 - User's normal SSH .ssh/config file
 - System SSH /etc/ssh/ssh_config file
 - RadSSH defaults (defined here)

Only the User and System ssh_config files support the OpenSSH Host/Match
dynamic rules, and are loaded into paramiko.SSHConfig objects. The rest
are plain dict objects. Calling `options()` with a destination will do
the paramiko.SSHConfig.lookup() to get the host-specific values, and all
of the layers are combined as a collections.ChainMap.

Some options are explicitly processed and populated in the top-level
mapping in the ChainMap, and some options listed as defaults are not
currently supported by paramiko. These must be filtered prior to actual
use in paramiko calls. Some care needs to be taken as some options
support multiple values as lists (IdentityFile, CertificateFile), while
others are single comma-separated strings representing multiple values.
"""

import fnmatch
import getpass
import pathlib
import collections

import paramiko


class RadSSHConfig():
    """
    Loads ssh_config files from user and system default locations. Allows
    override(s) supplied as dictionaries from command line options and/or
    .radssh_config file. Calling `options(hostname)` will construct a
    ChainMap usable for all related ssh options for the given host, using
    designated priority:
        user, port from "user@hostname:port" if provided
        command_line_options (dict)
        radssh_config_options (dict)
        user_config_filename (default: ~/.ssh/config)
        system_config_filename (default: /etc/ssh/ssh_config)
        RadSSHConfig.default_config (dict)
    """
    def __init__(self, command_line_options=None, radssh_config_options=None,
                 user_config_filename="~/.ssh/config",
                 system_config_filename="/etc/ssh/ssh_config"):
        self.default_config["user"] = getpass.getuser()
        sysconfig = pathlib.Path(system_config_filename)
        if sysconfig.exists():
            self.system_config = paramiko.SSHConfig.from_path(sysconfig)
        else:
            self.system_config = paramiko.SSHConfig()
        userconfig = pathlib.Path(user_config_filename).expanduser()
        if userconfig.exists():
            self.user_config = paramiko.SSHConfig.from_path(userconfig)
        else:
            self.user_config = paramiko.SSHConfig()
        # Build a normalized dict from radssh_config_options
        self.radssh_config = {}
        if radssh_config_options:
            for key, value in radssh_config_options.items():
                # ensure keys are lowercase, and only add to dict
                # if it is a recognized/supported key name
                key = key.lower()
                if key in self.default_config:
                    self.radssh_config[key] = value
        # Build a normalized dict from command_line_options
        self.cmdline_config = {}
        if command_line_options:
            for key, value in command_line_options.items():
                # ensure keys are lowercase, and only add to dict
                # if it is a recognized/supported key name
                key = key.lower()
                if key in self.default_config:
                    self.cmdline_config[key] = value

    def options(self, destination):
        """
        From a destination string ([user@]hostname[:port]), build a
        ChainMap of ssh_config options to be used for connecting and
        authenticating the corresponding ssh connection.
        """
        dest = {}
        if destination.startswith("ssh://"):
            destination = destination[6:]
        if "@" in destination:
            dest["user"], destination = destination.split("@", 1)
        if ":" in destination:
            destination, dest["port"] = destination.rsplit(":", 1)
        # save as original_hostname, as ssh_config could remap it as hostname
        dest["original_hostname"] = destination
        chainmap = collections.ChainMap(dest, self.cmdline_config,
                                        self.radssh_config,
                                        self.user_config.lookup(destination),
                                        self.system_config.lookup(destination),
                                        self.default_config)
        # Handle late stage updates as some select options can be
        # represented cumulatively, or updated with +/- specifications
        # TBD
        if chainmap["identityfile"] is None:
            dest["identityfile"] = self.default_identityfile
        else:
            dest["identityfile"] = []
            for m in chainmap.maps:
                if m.get("identityfile"):
                    dest["identityfile"].extend(m["identityfile"])
        # Gather up all referenced CertificateFiles
        dest["certificatefile"] = []
        for m in chainmap.maps:
            if m.get("certificatefile"):
                dest["certificatefile"].extend(m["certificatefile"])
        if not dest["certificatefile"]:
            dest["certificatefile"] = \
                [x + "-cert.pub" for x in dest["identityfile"]]
        # Only need to handle +/- for these options if the uppermost
        # setting starts with + or -, otherwise the value is the current list
        # Note: ^ was added in OpenSSH 8.0 to allow prepending as an
        # alternative to + which appends to the tail of the list
        for option_name in ("ciphers", "hostbasedkeytypes",
                            "hostkeyalgorithms", "kexalgorithms",
                            "macs", "pubkeyacceptedkeytypes"):
            if chainmap[option_name][0] in ("+", "-", "^"):
                dest[option_name] = self.reassemble(chainmap, option_name)
        return chainmap

    def reassemble(self, chainmap, option_name):
        # Construct option list by add/subtract/prepend options
        # return a single comma separated list
        values = []
        for m in reversed(chainmap.maps):
            x = m.get(option_name)
            if x:
                if x[0] == "+":
                    for v in x[1:].split(","):
                        if v not in values:
                            values.append(v)
                elif x[0] == '^':
                    new_values = []
                    for v in x[1:].split(","):
                        if v in values:
                            values.remove(v)
                        new_values.append(v)
                    new_values.extend(values)
                    values = new_values
                elif x[0] == "-":
                    for pattern in x[1:].split(","):
                        values = [opt for opt in values
                                  if not fnmatch.fnmatch(opt, pattern)]
                else:
                    # Reset value list to current setting
                    values = x.split(",")
        return ",".join(values)

    default_identityfile = ["~/.ssh/id_dsa", "~/.ssh/id_ecdsa",
                            "~/.ssh/id_ed25519", "~/.ssh/id_rsa"]

    default_keytypes = "ecdsa-sha2-nistp256-cert-v01@openssh.com," \
                       "ecdsa-sha2-nistp384-cert-v01@openssh.com," \
                       "ecdsa-sha2-nistp521-cert-v01@openssh.com," \
                       "ssh-ed25519-cert-v01@openssh.com," \
                       "rsa-sha2-512-cert-v01@openssh.com," \
                       "rsa-sha2-256-cert-v01@openssh.com," \
                       "ssh-rsa-cert-v01@openssh.com," \
                       "ecdsa-sha2-nistp256,ecdsa-sha2-nistp384," \
                       "ecdsa-sha2-nistp521,ssh-ed25519," \
                       "rsa-sha2-512,rsa-sha2-256,ssh-rsa"

    default_config = {
        "hostname": None,
        "port": "22",
        "user": "",
        # Miscellaneous Options
        "fingerprinthash": "sha256",
        "loglevel": "info",
        # Connection Options
        "addressfamily": "any",
        "bindaddress": None,
        "ciphers": "chacha20-poly1305@openssh.com," \
                   "aes128-ctr,aes192-ctr,aes256-ctr," \
                   "aes128-gcm@openssh.com,aes256-gcm@openssh.com",
        "compression": "no",
        "connectionattempts": "1",
        "connecttimeout": "20",
        "controlmaster": "no",
        "controlpath": "none",
        "controlpersist": "no",
        "hostkeyalgorithms": default_keytypes,
        "kexalgorithms": "curve25519-sha256,curve25519-sha256@libssh.org," \
                         "ecdh-sha2-nistp256,ecdh-sha2-nistp384," \
                         "ecdh-sha2-nistp521," \
                         "diffie-hellman-group-exchange-sha256," \
                         "diffie-hellman-group16-sha512," \
                         "diffie-hellman-group18-sha512," \
                         "diffie-hellman-group-exchange-sha1," \
                         "diffie-hellman-group14-sha256," \
                         "diffie-hellman-group14-sha1",
        "macs": "umac-64-etm@openssh.com,umac-128-etm@openssh.com," \
                "hmac-sha2-256-etm@openssh.com," \
                "hmac-sha2-512-etm@openssh.com," \
                "hmac-sha1-etm@openssh.com," \
                "umac-64@openssh.com,umac-128@openssh.com," \
                "hmac-sha2-256,hmac-sha2-512,hmac-sha1",
        "nohostauthenticationforlocalhost": "no",
        "proxycommand": None,
        "proxyjump": None,
        "proxyusefdpass": "no",
        "rekeylimit": "default none",
        "serveralivecountmax": "3",
        "serveraliveinterval": "0",
        "tcpkeepalive": "yes",

        # Hostkey Verification Options
        "checkhostip": "yes",
        "casignaturealgorithms": "ecdsa-sha2-nistp256," \
                                 "ecdsa-sha2-nistp384," \
                                 "ecdsa-sha2-nistp521," \
                                 "ssh-ed25519,rsa-sha2-512," \
                                 "rsa-sha2-256,ssh-rsa",
        "globalknownhostsfile": "/etc/ssh/ssh_known_hosts",
        "hashknownhosts": "no",
        "hostkeyalias": None,
        "revokedhostkeys": None,
        "stricthostkeychecking": "ask",
        "updatehostkeys": "no",
        "userknownhostsfile": "~/.ssh/known_hosts",
        "verifyhostkeydns": "no",

        # User Authentication Options
        "addkeystoagent": "no",
        "batchmode": "no",
        "certificatefile":  None,  # Deferred setting
        "challengeresponseauthentication": "yes",
        "enablesshkeysign": "no",
        "gssapiauthentication": "no",
        "gssapidelegatecredentials": "no",
        "hostbasedauthentication": "no",
        "hostbasedkeytypes": default_keytypes,
        "identitiesonly": "no",
        "identityagent": "SSH_AUTH_SOCK",
        "identityfile": None,  # Deferred setting
        "kbdinteractiveauthentication": "yes",
        "kbdinteractivedevices": "pam,bsdauth",
        "numberofpasswordprompts": "3",
        "passwordauthentication": "yes",
        "pkcs11provider": None,
        "preferredauthentications": "gssapi-with-mic,hostbased," \
                                    "publickey,keyboard-interactive," \
                                    "password",
        "pubkeyacceptedkeytypes": default_keytypes,
        "pubkeyauthentication": "yes"
    }


if __name__ == "__main__":
    cfg = RadSSHConfig(command_line_options={"USER": "joe", "duff": True},
                       radssh_config_options={"user": "mama"})
    z = cfg.options('ssh://user@freeipa:2345')
