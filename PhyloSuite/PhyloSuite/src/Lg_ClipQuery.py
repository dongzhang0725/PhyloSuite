#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
description goes here
'''

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from uifiles.Ui_clipboard_query import Ui_ClipboardQ


class Lg_ClipQuery(QDialog, Ui_ClipboardQ, object):
    closeGUI_signal = pyqtSignal()

    def __init__(self, parent=None):
        super(Lg_ClipQuery, self).__init__(parent)
        self.setupUi(self)
        self.is_fas = False
        self.pushButton_2.clicked.connect(lambda : [self.close(), self.setResult(QDialog.Rejected)])
        self.pushButton.clicked.connect(self.judge)

    def judge(self):
        self.ID = self.lineEdit.text()
        self.organism = self.lineEdit_2.text()
        if self.ID or self.radioButton_3.isChecked() or self.is_fas:
            self.close()
            self.setResult(QDialog.Accepted)
        else:
            QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>Please specify an ID!</p>")