# ipfwGUI
#### A very simple GUI for the ipfw packet filter (AKA firewall) for FreeBSD

With ipfwGUI it is possible to create a "workstation" type [firewall](https://www.freebsd.org/cgi/man.cgi?firewall) and allow incoming traffic to your host.
The ports to be allowed can be only be selected from a list of ports in LISTEN status for now. You need to start the listening daemon before you start ipfwGUI.

#### Installation

ipfwGUI needs PyQt5 to run. To install it run:

```
pkg install py38-qt5
```

#### Running ipfwGUI

If you run ipfwGUI as a user you can only view the current settings. To actually be able to change settings you need to run ipfwGUI with doas or sudo.

#### Screenshot

![screenshot](https://github.com/bsdlme/ipfwGUI/blob/main/screenshots/screenshot1.jpg?raw=true)
