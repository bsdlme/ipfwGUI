# ipfwGUI

## A simple GUI for the ipfw packet filter (AKA firewall) for FreeBSD

With ipfwGUI it is possible to create a "workstation" type
[firewall](https://www.freebsd.org/cgi/man.cgi?firewall)
and allow incoming traffic to your host.
The ports to be allowed can be only be selected from a list of ports in LISTEN
status for now. You need to start the listening daemon before you start ipfwGUI.
ipfwGUI always permits both IPv4 and IPv6 at the same time.

### Installation

ipfwGUI needs Python3 and PyQt6 to run. To install it run:

```sh
pkg install python3 py311-qt6-pyqt
# optional:
pkg install dsbsu|sudo|doas
```

### Running ipfwGUI

If you run ipfwGUI as a user you can view the current settings. To actually
be able to change settings you need to run ipfwGUI with doas or sudo or dsbsu.

### Screenshot

![screenshot](https://github.com/bsdlme/ipfwGUI/blob/main/screenshots/screenshot1.jpg?raw=true)
