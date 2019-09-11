#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from uifiles.Ui_NmlPoPup import Ui_NmlPoPup


class NmlPoPup(QDialog, Ui_NmlPoPup, object):
    typeSig = pyqtSignal(str)
    def __init__(
            self,
            parent=None):
        super(NmlPoPup, self).__init__(parent)
        self.setupUi(self)

    @pyqtSlot()
    def on_toolButton_clicked(self):
        self.close()
        self.typeSig.emit("mt")

    @pyqtSlot()
    def on_toolButton_2_clicked(self):
        self.close()
        self.typeSig.emit("seq")

