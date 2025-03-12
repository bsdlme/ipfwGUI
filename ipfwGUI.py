#!/usr/bin/env python3

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

from subprocess import check_output, CalledProcessError
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QWidget, QGridLayout,
    QCheckBox, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QStatusBar, QStyle
)

# Constants for system binaries
SYSRC_BIN = '/usr/sbin/sysrc'
SERVICE_BIN = '/usr/sbin/service'
SOCKSTAT_BIN = '/usr/bin/sockstat'


class SimpleIpfwGui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Firewall GUI for FreeBSD")
        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)

        self.layout = QGridLayout()
        self.centralWidget.setLayout(self.layout)

        self.firewallEnabled, self.firewallRunningString, self.firewallRunningBool = self.getFirewallState()
        self.allowedPorts = self.getAllowedPorts()

        self.setupWidgets()
        self.checkPrivileges()

    def setupWidgets(self):
        self.labelTitle = QLabel("Simple Firewall GUI for FreeBSD")
        self.labelTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.checkBoxIpfwEnable = QCheckBox()
        self.checkBoxIpfwEnable.setToolTip('Check this to enable the firewall.')
        self.checkBoxIpfwEnable.setChecked(self.firewallEnabled.lower() == "yes")

        self.buttonApply = QPushButton("Apply")
        self.buttonApply.setFixedWidth(120)
        self.buttonApply.clicked.connect(self.applyChanges)

        self.buttonQuit = QPushButton("Quit")
        self.buttonQuit.setFixedWidth(120)
        self.buttonQuit.clicked.connect(QApplication.instance().quit)

        self.createTable()

        self.statusBar = QStatusBar()
        self.statusBar.showMessage(self.firewallRunningString)
        self.updateStatusBar()
        self.setStatusBar(self.statusBar)

        self.layout.addWidget(self.labelTitle, 0, 1)
        self.layout.addWidget(QLabel("Enable Firewall? "), 1, 0)
        self.layout.addWidget(self.checkBoxIpfwEnable, 1, 1)
        self.layout.addWidget(self.tableWidget, 2, 0, 1, 3)
        self.layout.addWidget(self.buttonApply, 5, 1, alignment=Qt.AlignmentFlag.AlignRight)
        self.layout.addWidget(self.buttonQuit, 5, 2)

    def createTable(self):
        self.tableWidget = QTableWidget()
        self.tableContent = self.getListenPorts()

        self.tableWidget.setRowCount(len(self.tableContent))
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setHorizontalHeaderLabels(["Process", "Protocol", "Port", "Allow"])

        for lineNum, line in enumerate(self.tableContent):
            proc, proto, port = line
            self.tableWidget.setItem(lineNum, 0, QTableWidgetItem(proc))
            self.tableWidget.setItem(lineNum, 1, QTableWidgetItem(proto))
            self.tableWidget.setItem(lineNum, 2, QTableWidgetItem(port))

            checkbox = QTableWidgetItem()
            checkbox.setFlags(checkbox.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            checkbox.setCheckState(Qt.CheckState.Checked if f"{port}/{proto.rstrip('46')}" in self.allowedPorts else Qt.CheckState.Unchecked)
            self.tableWidget.setItem(lineNum, 3, checkbox)

    def applyChanges(self):
        if not self.checkPrivileges():
            return

        self.fwEnable = "YES" if self.checkBoxIpfwEnable.isChecked() else "NO"
        self.serviceAction = "start" if self.fwEnable == "YES" else "onestop"

        allowedPortsNew = [
            f"{self.tableWidget.item(i, 2).text()}/{self.tableWidget.item(i, 1).text().rstrip('46')}"
            for i in range(self.tableWidget.rowCount())
            if self.tableWidget.item(i, 3).checkState() == Qt.CheckState.Checked
        ]


        allowedPortsNew = sorted(set(allowedPortsNew), key=self.natural_keys)

        try:
            check_output([SYSRC_BIN, f'firewall_enable={self.fwEnable}'])
            check_output([SYSRC_BIN, 'firewall_type=workstation'])
            check_output([SYSRC_BIN, 'firewall_allowservices=any'])
            check_output([SYSRC_BIN, f'firewall_myservices={" ".join(allowedPortsNew)}'])
            check_output([SERVICE_BIN, 'ipfw', self.serviceAction])
        except CalledProcessError as e:
            QMessageBox.critical(self, "Error", f"Failed to apply changes: {e}")
            return

        self.firewallEnabled, self.firewallRunningString, self.firewallRunningBool = self.getFirewallState()
        self.updateStatusBar()

    def getFirewallState(self):
        try:
            firewallEnabled = check_output([SYSRC_BIN, '-n', 'firewall_enable']).strip().decode("utf-8")
            firewallRunningString = check_output(f"{SERVICE_BIN} ipfw forcestatus; exit 0", shell=True).strip().decode("utf-8")
            firewallRunningBool = firewallRunningString == "ipfw is enabled"
            firewallRunningString = firewallRunningString.replace('enabled', 'running').replace('ipfw', 'Firewall')
            return firewallEnabled, firewallRunningString, firewallRunningBool
        except CalledProcessError:
            return "NO", "Firewall status unknown", False

    def getAllowedPorts(self):
        try:
            return check_output([SYSRC_BIN, '-n', 'firewall_myservices']).strip().decode("utf-8").split()
        except CalledProcessError:
            return []

    def checkPrivileges(self):
        if os.geteuid() != 0:
            QMessageBox.information(self, "Not enough privileges",
              "You started the firewall management GUI as a regular user and can only read the firewall settings.\n\nIf you want to edit settings, run the firewall management GUI as root.")
            return False
        return True

    def updateStatusBar(self):
        self.statusBar.setStyleSheet("background-color : lightgreen" if self.firewallRunningBool else "background-color : pink")
        self.statusBar.showMessage(self.firewallRunningString)

    def getListenPorts(self):
        try:
            # Get the output from sockstat
            sockstat_output = check_output([SOCKSTAT_BIN, '-46s']).decode('utf-8')

            # Process the output
            lines = sockstat_output.strip().splitlines()
            connections = []

            for line in lines:
                cols = line.split()
                if cols[-1] != "LISTEN":
                    continue
                if len(cols) >= 6:
                    proc  = cols[1]  # Process name
                    proto = cols[4]  # Protocol
                    port  = cols[5]  # Port
                    port = port.rsplit(':', -1)[-1]
                    if port == "*":
                        continue
                    # Append the cleaned data
                    connections.append((proc, proto, port))

            # Sort connections by port
            connections.sort(key=lambda x: int(x[2]))  # Sort by port

            return connections

        except CalledProcessError as e:
            print(f"Error retrieving listening ports: {e}")
            return []

    def natural_keys(self, text):
        return [int(c) if c.isdigit() else c for c in re.split('(\d+)', text)]

def main():
    app = QApplication(sys.argv)
    gui = SimpleIpfwGui()
    gui.show()
    gui.setGeometry(QStyle.alignedRect(Qt.LayoutDirection.LeftToRight, Qt.AlignmentFlag.AlignCenter, gui.size(), app.primaryScreen().geometry()))
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
