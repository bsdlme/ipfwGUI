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
import re

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QMessageBox, QStatusBar
from PyQt5.QtWidgets import QTableWidget,QTableWidgetItem
from PyQt5.QtWidgets import QGridLayout, QStyle
from PyQt5.QtWidgets import QLabel, QPushButton, QLineEdit, QCheckBox

from subprocess import check_output

SYSRC_BIN = '/usr/sbin/sysrc'
SERVICE_BIN = '/usr/sbin/service'
SOCKSTAT_BIN = '/usr/bin/sockstat'

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
        self.labelTitle = QLabel("Simple Firewall GUI for FreeBSD")
        self.labelTitle.setAlignment(Qt.AlignCenter)

        self.labelcheckBoxIpfwEnable = QLabel("Enable Firewall? ")
        self.labelAllowedPorts = QLabel("Allowed incoming ports:")

        self.checkBoxIpfwEnable = QCheckBox()
        self.checkBoxIpfwEnable.setToolTip('Check this to enable the firewall.')
        if self.firewallEnabled.lower() == "yes":
            self.checkBoxIpfwEnable.setChecked(True)

        self.editAllowedPorts = QLineEdit()
        self.editAllowedPorts.setFixedWidth(340)
        self.editAllowedPorts.setText(' '.join(self.allowedPorts))

        self.buttonApply = QPushButton("Apply")
        self.buttonApply.setFixedWidth(120)
        self.buttonApply.clicked.connect(self.applyChanges)

        self.buttonQuit = QPushButton("Quit")
        self.buttonQuit.setFixedWidth(120)
        self.buttonQuit.clicked.connect(QApplication.instance().quit)

        self.buttonHelp = QPushButton("Help")
        self.buttonHelp.setFixedWidth(120)
        self.buttonHelp.clicked.connect(QApplication.instance().quit)

        self.createTable()

        self.statusBar = QStatusBar()
        self.statusBar.showMessage(self.firewallRunningString)
        self.updateStatusBar()
        self.setStatusBar(self.statusBar)

        self.layout.addWidget(self.labelTitle,              0, 1)

        self.layout.addWidget(self.labelcheckBoxIpfwEnable, 1, 0)
        self.layout.addWidget(self.checkBoxIpfwEnable,      1, 1)

        self.layout.addWidget(self.tableWidget, 2, 0, 1, 3)

        self.layout.addWidget(self.labelAllowedPorts,       3, 0)
        self.layout.addWidget(self.editAllowedPorts,        3, 1, 1, 3)

        self.layout.addWidget(self.buttonHelp,              4, 0)
        self.layout.addWidget(self.buttonApply,             4, 1, alignment=Qt.AlignRight)
        self.layout.addWidget(self.buttonQuit,              4, 2)

        self.checkPrivileges()

    def createTable(self):
        self.tableWidget = QTableWidget()
        self.tableContent = self.getListenPorts().strip().decode("utf-8")

        self.tableWidget.setRowCount(self.tableContent.count("\n"))
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setHorizontalHeaderLabels(["Process", "Protocol", "Port", "Allowed"])
        self.lineNum = 0
        for line in self.tableContent.split("\n"):
            (self.proc, self.proto, self.port) = line.split()
            self.tableWidget.setItem(self.lineNum, 0, QTableWidgetItem(self.proc))
            self.tableWidget.setItem(self.lineNum, 1, QTableWidgetItem(self.proto))
            self.tableWidget.setItem(self.lineNum, 2, QTableWidgetItem(self.port))
            self.checkbox = QTableWidgetItem()
            self.checkbox.setFlags(self.checkbox.flags() | Qt.ItemIsUserCheckable)
            self.checkbox.setCheckState(Qt.Unchecked)
            self.tableWidget.setItem(self.lineNum, 3, self.checkbox)
            self.lineNum += 1
        self.tableWidget.move(0,0)

    def applyChanges(self):
        if not self.checkPrivileges():
            return
        if self.checkBoxIpfwEnable.isChecked() == True:
            self.fwEnable = "YES"
            self.serviceAction = "start"
        else:
            self.fwEnable = "NO"
            self.serviceAction = "onestop"

        # Add enabled checkboxes to the list
        items = []
        for i in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(i, 3)
            if item.checkState() == Qt.Checked:
                items.append(item)

        for it in items:
            r = it.row()
            self.allowedPorts.append(self.tableWidget.item(r, 2).text() + "/" + self.tableWidget.item(r, 1).text().rstrip('46'))

        self.editAllowedPorts.setText(' '.join(self.allowedPorts))
        self.sanitizeInput(self.editAllowedPorts.text())

        print(check_output([SYSRC_BIN, 'firewall_enable=' + self.fwEnable]).rstrip().decode("utf-8"))
        print(check_output([SYSRC_BIN, 'firewall_type=workstation']).rstrip().decode("utf-8"))
        print(check_output([SYSRC_BIN, 'firewall_allowservices=any']).rstrip().decode("utf-8"))
        print(check_output([SYSRC_BIN, 'firewall_myservices=' + self.editAllowedPorts.text().strip()]).decode("utf-8"))
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
        return (check_output([SYSRC_BIN, '-n', 'firewall_myservices'])).strip().decode("utf-8").split("\n")

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

    def getListenPorts(self):
        return (check_output(SOCKSTAT_BIN + ' -46lLwqj0 | tr -s " " | cut -d " " -f 2,5,6 | awk -F\'[ :]\' \'{sub(/\*/, "", $1);sub(/[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/, "", $1); conn[$NF] = sprintf("%s %s", $1,$2)} END{for (port in conn){ print conn[port], port}}\' | sort -nk3 | sed \'/\*$/d\'', shell=True))

    def sanitizeInput(self, allowedPorts):
        tmpArray = []
        for elem in self.editAllowedPorts.text().split(" "):
            tmpArray.append(elem.strip(' ,;:\t'))

        tmpArray.sort()
        self.editAllowedPorts.setText(' '.join(list(set(tmpArray))))
        return

def main():
    ipfwGUI = QApplication(sys.argv)

    gui = simpleIpfwGui()
    gui.show()
    # Center main window
    gui.setGeometry(QStyle.alignedRect(Qt.LeftToRight, Qt.AlignCenter, gui.size(), 
        ipfwGUI.primaryScreen().geometry()))

    sys.exit(ipfwGUI.exec())


if __name__ == '__main__':
    main()
