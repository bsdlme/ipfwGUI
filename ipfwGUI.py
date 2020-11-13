#!/usr/bin/env python3.7

# Copyright (c) 2020 Lars Engels. All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QMessageBox
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QLabel, QPushButton, QLineEdit, QCheckBox

from subprocess import check_output

SYSRC_BIN = '/usr/sbin/sysrc'
SERVICE_BIN = '/usr/sbin/service'

class simpleIpfwGui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple ipfw GUI for FreeBSD")
        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)

        self.layout = QGridLayout()
        self.centralWidget.setLayout(self.layout)

        self.firewallEnabled = self.getFirewallState()
        self.allowedPorts = self.getAllowedPorts()

        self.widgets()

    def widgets(self):
        self.labelTitle = QLabel("Simple ipfw GUI for FreeBSD")
        self.labelTitle.setAlignment(Qt.AlignCenter)

        self.labelIpfwEnable = QLabel("Enable ipfw Firewall? ")
        self.labelOpenPorts = QLabel("Allowed ports:")

        self.IpfwEnable = QCheckBox()
        self.IpfwEnable.setToolTip('Check this to enable the firewall.')
        if self.firewallEnabled.lower() == "yes":
            self.IpfwEnable.setChecked(True)

        self.allowedPortsLE = QLineEdit()
        self.allowedPortsLE.setFixedWidth(120)
        self.allowedPortsLE.setText(self.allowedPorts)

        self.buttonApply = QPushButton("Apply")
        self.buttonApply.setFixedWidth(120)
        self.buttonApply.clicked.connect(self.applyChanges)

        self.buttonQuit = QPushButton("Quit")
        self.buttonQuit.setFixedWidth(120)
        self.buttonQuit.clicked.connect(QApplication.instance().quit)

        self.layout.addWidget(self.labelTitle, 0, 1, alignment=Qt.AlignBottom)
        self.layout.addWidget(self.labelIpfwEnable, 1, 0, alignment=Qt.AlignRight)
        self.layout.addWidget(self.labelOpenPorts, 2, 0, alignment=Qt.AlignRight)
        self.layout.addWidget(self.IpfwEnable, 1, 1, alignment=Qt.AlignLeft)
        self.layout.addWidget(self.allowedPortsLE, 2, 1, alignment=Qt.AlignLeft)
        self.layout.addWidget(self.buttonApply, 3, 1, alignment=Qt.AlignRight)
        self.layout.addWidget(self.buttonQuit, 3, 2, alignment=Qt.AlignRight)

        self.checkPrivileges()

    def applyChanges(self):
        if not self.checkPrivileges():
            return
        if self.IpfwEnable.isChecked() == True:
            self.fwEnable = "YES"
            self.serviceAction = "start"
        else:
            self.fwEnable = "NO"
            self.serviceAction = "onestop"

        print(check_output([SYSRC_BIN, 'firewall_enable=' + self.fwEnable]).rstrip().decode("utf-8"))
        print(check_output([SYSRC_BIN, 'firewall_type=workstation']).rstrip().decode("utf-8"))
        print(check_output([SYSRC_BIN, 'firewall_allowservices=any']).rstrip().decode("utf-8"))
        print(check_output([SYSRC_BIN, 'firewall_myservices=' + self.allowedPortsLE.text()]).rstrip().decode("utf-8"))
        print(check_output([SERVICE_BIN, 'ipfw', self.serviceAction]))

    def getFirewallState(self):
        return (check_output([SYSRC_BIN, '-n', 'firewall_enable'])).rstrip().decode("utf-8")

    def getAllowedPorts(self):
        return (check_output([SYSRC_BIN, '-n', 'firewall_myservices'])).rstrip().decode("utf-8")

    def checkPrivileges(self):
        if os.geteuid() != 0:
            QMessageBox.information(self, "Not enough privileges", "You started the firewall management GUI as a regular user and can only read the firewall settings.\n\nIf you want to edit settings, run the firewall management GUI as root.")
            return False
        else:
            return True


def main():
    ipfwGUI = QApplication(sys.argv)

    gui = simpleIpfwGui()
    gui.show()

    sys.exit(ipfwGUI.exec())


if __name__ == '__main__':
    main()
