RadSSH
======

RadSSH is a Python package that is built with Paramiko.

Documentation for the project is hosted on ReadTheDocs, at http://radssh.readthedocs.org

Frequently Asked Questions: https://github.com/radssh/radssh/blob/master/FAQ.md

RadSSH is installable via **pip**, using ``pip install radssh``.

----

The RadSSH shell behaves similar to a normal ssh command line client, but instead of connecting to one host (at a time), you can connect to dozens or even hundreds at a time, and issue interactive command lines to all hosts at once. It requires very little learning curve to get started, and leverages on existing command line syntax that you already know.

```
[paul@localhost ~]$ python -m radssh.shell huey dewey louie
Please enter a password for (paul) :
Connecting to 3 hosts...
...
RadSSH $ hostname
[huey] huey.example.org
[dewey] dewey.example.org
[louie] louie.example.org
Average completion time for 3 hosts: 0.058988s

RadSSH $ uptime
[huey]  15:21:28 up 6 days, 22:49, 17 users,  load average: 0.30, 0.43, 0.39
[louie] 15:43  up 652 days,  4:59, 0 users, load averages: 0.44 0.20 0.17
[dewey]  15:21:28 up 109 days, 23:28,  3 users,  load average: 0.27, 0.09, 0.07
Average completion time for 3 hosts: 0.044532s

RadSSH $ df -h /
[huey] Filesystem            Size  Used Avail Use% Mounted on
[huey] /dev/mapper/vg-Scientific
[huey]                        24G   22G  694M  97% /
[louie] Filesystem     Size   Used  Avail Capacity  Mounted on
[louie] /dev/disk0s3   234G   134G    99G    57%    /
[dewey] Filesystem                        Size  Used Avail Use% Mounted on
[dewey] /dev/mapper/vg_pkapp745-LogVol00   20G   17G  2.1G  89% /
Average completion time for 3 hosts: 0.036792s

RadSSH $ *exit
Shell exiting
```

RadSSH includes a loadable plugin facility to extend the functionality of the shell with basic Python scripting, as well as a high level API that can be used to build stand alone applications for dedicated SSH control processing in a parallel environment.

Interested in more? 
 - Download at https://pypi.python.org/pypi/radssh
 - Read the Docs at http://radssh.readthedocs.org/en/latest/index.html
 - Participate at https://github.com/radssh/radssh
