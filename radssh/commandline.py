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
CommandLine - traverse a command line list of arguments, and break it down
into 3 categories:
  - ssh-like arguments, of the forms "-x" (single flag), "-p port" (flag
    with value), "-o optionname=value", or "-o optionname value"
  - radssh-like arguments, of the form --keyword=value
  - anything else, saved as a list

This gathers and assembles the arguments, but does not validate that their
values make sense. That is not determined until the values are used, and may
not be interpreted correctly at that point either. i.e. - it is possible to
set PublicKeyAcceptedTypes to "foo" here.
"""

from radssh.sshconfig import RadSSHConfig

class CommandLine():
    def __init__(self, *args):
        self.ssh_command_line_config = {}
        self.radssh_command_line_config = {}
        self.argument_list = []
        # IdentityFile can be specified multiple times
        identity_files = []

        arg = iter(args)
        for opt in arg:
            if opt[:2] == "--":
                # RadSSH legacy style: --keyword=value
                if "=" not in opt:
                    raise ValueError("Unrecognized comamnd line option: {}".
                                     format(opt))
                keyword, value = opt[2:].split("=", 1)
                self.radssh_command_line_config[keyword] = value
            elif opt[0] == "-":
                # OpenSSH style: - followed by single character
                flag = opt[1:]
                if len(flag) != 1:
                    raise ValueError("SSH options may not be combined: {}".
                                     format(opt))
                if flag == "4":
                    self.ssh_option("AddressFamily", "inet")
                elif flag == "6":
                    self.ssh_option("AddressFamily", "inet6")
                elif flag == "A":
                    self.ssh_option("ForwardAgent", "yes")
                elif flag == "a":
                    self.ssh_option("ForwardAgent", "no")
                elif flag == "B":
                    self.ssh_option("BindInterface", next(arg))
                elif flag == "b":
                    self.ssh_option("BindAddress", next(arg))
                elif flag == "c":
                    self.ssh_option("Ciphers", next(arg))
                elif flag == "D":
                    raise ValueError("SSH option -D not supported")
                elif flag == "E":
                    raise ValueError("SSH option -E not supported")
                elif flag == "e":
                    self.ssh_option("EscapeChar", next(arg))
                elif flag == "F":
                    self.ssh_option("UserConfigFile", next(arg))
                elif flag == "f":
                    raise ValueError("SSH option -f not supported")
                elif flag == "G":
                    raise ValueError("SSH option -G not supported")
                elif flag == "g":
                    raise ValueError("SSH option -g not supported")
                elif flag == "I":
                    self.ssh_option("PKCS11Provider", next(arg))
                elif flag == "i":
                    identity_files.append(next(arg))
                elif flag == "J":
                    raise ValueError("SSH option -J not supported")
                elif flag == "K":
                    self.ssh_option("GSSAPIAuthentication", "yes")
                    self.ssh_option("GSSAPIDelegateCredentials", "yes")
                elif flag == "k":
                    self.ssh_option("GSSAPIAuthentication", "yes")
                    self.ssh_option("GSSAPIDelegateCredentials", "no")
                elif flag == "L":
                    raise ValueError("SSH option -L not supported")
                elif flag == "l":
                    self.ssh_option("User", next(arg))
                elif flag == "M":
                    raise ValueError("SSH option -M not supported")
                elif flag == "m":
                    self.ssh_option("MACs", next(arg))
                elif flag == "N":
                    raise ValueError("SSH option -N not supported")
                elif flag == "n":
                    raise ValueError("SSH option -n not supported")
                elif flag == "O":
                    raise ValueError("SSH option -O not supported")
                elif flag == "o":
                    # See if it is keyword=value or keyword value
                    keyword = next(arg)
                    if "=" in keyword:
                        keyword, value = keyword.split("=", 1)
                    else:
                        value = next(arg)
                    if keyword.lower() not in RadSSHConfig.default_config:
                        raise ValueError("SSH option {} not recognized".format(
                                         keyword
                        ))
                    self.ssh_option(keyword, value)
                elif flag == "p":
                    self.ssh_option("Port", next(arg))
                elif flag == "Q":
                    raise ValueError("SSH option -Q not supported")
                elif flag == "q":
                    self.ssh_option("Verbosity", "quiet")
                elif flag == "R":
                    raise ValueError("SSH option -R not supported")
                elif flag == "S":
                    raise ValueError("SSH option -S not supported")
                elif flag == "s":
                    raise ValueError("SSH option -s not supported")
                elif flag == "T":
                    self.ssh_option("Port", next(arg))
                elif flag == "t":
                    self.ssh_option("Port", next(arg))
                elif flag == "V":
                    raise ValueError("SSH option -V not supported")
                elif flag == "v":
                    self.ssh_option("Verbosity", "verbose")
                elif flag == "W":
                    raise ValueError("SSH option -W not supported")
                elif flag == "w":
                    raise ValueError("SSH option -w not supported")
                elif flag == "X":
                    self.ssh_option("ForwardX11", "yes")
                elif flag == "x":
                    self.ssh_option("ForwardX11", "no")
                elif flag == "Y":
                    self.ssh_option("ForwardX11Trusted", "yes")
                elif flag == "y":
                    raise ValueError("SSH option -y not supported")
                else:
                    raise ValueError("Unrecognized SSH option: {}".format(
                                     opt
                    ))
            else:
                self.argument_list.append(opt)


    def ssh_option(self, option_name, option_value):
        # raise error if option is being set more than once
        # normalize option names to be all lowercase
        option = option_name.lower()
        if option in self.ssh_command_line_config:
            raise ValueError("SSH Option {} cannot be set multiple times".format(
                             option_name
            ))
        self.ssh_command_line_config[option] = option_value


def main():
    import sys
    import pprint
    cmd = CommandLine(*sys.argv[1:])
    print("OpenSSH options recognized on command line:")
    pprint.pprint(cmd.ssh_command_line_config)
    print("\nRadSSH options recognized on command line:")
    pprint.pprint(cmd.radssh_command_line_config)
    print("\nExtra arguments (host-specs) on command line:")
    pprint.pprint(cmd.argument_list)

if __name__ == "__main__":
    main()
