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
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QMessageBox, QStatusBar
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QLabel, QPushButton, QLineEdit, QCheckBox

from subprocess import check_output

SYSRC_BIN = '/usr/sbin/sysrc'
SERVICE_BIN = '/usr/sbin/service'

class simpleIpfwGui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Firewall GUI for FreeBSD")
        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)

        self.layout = QGridLayout()
        self.centralWidget.setLayout(self.layout)

        # firewallEnabled: firewall_enabled=YES in rc.conf, firewallRunningString: ipfw loaded and running
        (self.firewallEnabled, self.firewallRunningString, self.firewallRunningBool) = self.getFirewallState()
        self.allowedPorts = self.getAllowedPorts()

        self.widgets()

    def widgets(self):
        self.labelTitle = QLabel("Simple Firewalll GUI for FreeBSD")
        self.labelTitle.setAlignment(Qt.AlignCenter)

        self.labelcheckBoxIpfwEnable = QLabel("Enable Firewall? ")
        self.labelAllowedPorts = QLabel("Allowed incoming ports:")

        self.checkBoxIpfwEnable = QCheckBox()
        self.checkBoxIpfwEnable.setToolTip('Check this to enable the firewall.')
        if self.firewallEnabled.lower() == "yes":
            self.checkBoxIpfwEnable.setChecked(True)

        self.editAllowedPorts = QLineEdit()
        self.editAllowedPorts.setFixedWidth(120)
        self.editAllowedPorts.setText(self.allowedPorts)

        self.buttonApply = QPushButton("Apply")
        self.buttonApply.setFixedWidth(120)
        self.buttonApply.clicked.connect(self.applyChanges)

        self.buttonQuit = QPushButton("Quit")
        self.buttonQuit.setFixedWidth(120)
        self.buttonQuit.clicked.connect(QApplication.instance().quit)

        self.buttonHelp = QPushButton("Help")
        self.buttonHelp.setFixedWidth(120)
        self.buttonHelp.clicked.connect(QApplication.instance().quit)

        self.statusBar = QStatusBar()
        self.statusBar.showMessage(self.firewallRunningString)
        self.updateStatusBar()
        self.setStatusBar(self.statusBar)

        self.layout.addWidget(self.labelTitle,              0, 1)

        self.layout.addWidget(self.labelcheckBoxIpfwEnable, 1, 0)
        self.layout.addWidget(self.checkBoxIpfwEnable,      1, 1)

        self.layout.addWidget(self.labelAllowedPorts,       2, 0)
        self.layout.addWidget(self.editAllowedPorts,        2, 1)

        self.layout.addWidget(self.buttonHelp,              3, 0)
        self.layout.addWidget(self.buttonApply,             3, 1, alignment=Qt.AlignRight)
        self.layout.addWidget(self.buttonQuit,              3, 2)

        self.checkPrivileges()

    def applyChanges(self):
        if not self.checkPrivileges():
            return
        if self.checkBoxIpfwEnable.isChecked() == True:
            self.fwEnable = "YES"
            self.serviceAction = "start"
        else:
            self.fwEnable = "NO"
            self.serviceAction = "onestop"

        print(check_output([SYSRC_BIN, 'firewall_enable=' + self.fwEnable]).rstrip().decode("utf-8"))
        print(check_output([SYSRC_BIN, 'firewall_type=workstation']).rstrip().decode("utf-8"))
        print(check_output([SYSRC_BIN, 'firewall_allowservices=any']).rstrip().decode("utf-8"))
        print(check_output([SYSRC_BIN, 'firewall_myservices=' + self.editAllowedPorts.text()]).rstrip().decode("utf-8"))
        print(check_output([SERVICE_BIN, 'ipfw', self.serviceAction]))
        (self.firewallEnabled, self.firewallRunningString, self.firewallRunningBool) = self.getFirewallState()
        self.updateStatusBar()

    def getFirewallState(self):
        self.firewallEnabled = check_output([SYSRC_BIN, '-n', 'firewall_enable']).rstrip().decode("utf-8")
        self.firewallRunningString = check_output(SERVICE_BIN + ' ipfw forcestatus; exit 0', shell=True).rstrip().decode("utf-8")
        if self.firewallRunningString == "ipfw is enabled":
            self.firewallRunningBool = True
        else:
            self.firewallRunningBool = False
        self.firewallRunningString = self.firewallRunningString.replace('enabled', 'running')
        self.firewallRunningString = self.firewallRunningString.replace('ipfw', 'Firewall')
        return (self.firewallEnabled, self.firewallRunningString, self.firewallRunningBool)

    def getAllowedPorts(self):
        return (check_output([SYSRC_BIN, '-n', 'firewall_myservices'])).rstrip().decode("utf-8")

    def checkPrivileges(self):
        if os.geteuid() != 0:
            QMessageBox.information(self, "Not enough privileges",
              "You started the firewall management GUI as a regular user and can only read the firewall settings.\n\nIf you want to edit settings, run the firewall management GUI as root.")
            return False
        else:
            return True

    def updateStatusBar(self):
        if self.firewallRunningBool == True:
            self.statusBar.setStyleSheet("background-color : lightgreen") 
        else:
            self.statusBar.setStyleSheet("background-color : pink") 
        self.statusBar.showMessage(self.firewallRunningString)


def main():
    ipfwGUI = QApplication(sys.argv)

    gui = simpleIpfwGui()
    gui.show()

    sys.exit(ipfwGUI.exec())


if __name__ == '__main__':
    main()
