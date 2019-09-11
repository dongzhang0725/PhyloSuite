# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'F:\Work\python\bioinfo_excercise\PhyloSuite\PhyloSuite\PhyloSuite\uifiles\gbEditor.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_GBeditor(object):
    def setupUi(self, GBeditor):
        GBeditor.setObjectName("GBeditor")
        GBeditor.resize(720, 651)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(GBeditor.sizePolicy().hasHeightForWidth())
        GBeditor.setSizePolicy(sizePolicy)
        GBeditor.setSizeGripEnabled(True)
        self.gridLayout = QtWidgets.QGridLayout(GBeditor)
        self.gridLayout.setObjectName("gridLayout")
        self.tableWidget = QtWidgets.QTableWidget(GBeditor)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableWidget.sizePolicy().hasHeightForWidth())
        self.tableWidget.setSizePolicy(sizePolicy)
        self.tableWidget.setMinimumSize(QtCore.QSize(0, 85))
        self.tableWidget.setMaximumSize(QtCore.QSize(16777215, 85))
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.gridLayout.addWidget(self.tableWidget, 0, 0, 1, 1)
        self.textBrowser = QtWidgets.QTextBrowser(GBeditor)
        self.textBrowser.setAutoFillBackground(True)
        self.textBrowser.setTabChangesFocus(True)
        self.textBrowser.setUndoRedoEnabled(True)
        self.textBrowser.setReadOnly(False)
        self.textBrowser.setOpenExternalLinks(True)
        self.textBrowser.setObjectName("textBrowser")
        self.gridLayout.addWidget(self.textBrowser, 1, 0, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.checkBox = QtWidgets.QCheckBox(GBeditor)
        self.checkBox.setChecked(True)
        self.checkBox.setObjectName("checkBox")
        self.horizontalLayout.addWidget(self.checkBox)
        self.spinBox = QtWidgets.QSpinBox(GBeditor)
        self.spinBox.setMinimumSize(QtCore.QSize(0, 24))
        self.spinBox.setMinimum(1)
        self.spinBox.setMaximum(10000)
        self.spinBox.setProperty("value", 200)
        self.spinBox.setObjectName("spinBox")
        self.horizontalLayout.addWidget(self.spinBox)
        self.horizontalLayout_2.addLayout(self.horizontalLayout)
        self.pushButton_2 = QtWidgets.QPushButton(GBeditor)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/picture/resourses/valid_shield-512.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_2.setIcon(icon)
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout_2.addWidget(self.pushButton_2)
        self.gridLayout.addLayout(self.horizontalLayout_2, 2, 0, 1, 1)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.pushButton = QtWidgets.QPushButton(GBeditor)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/picture/resourses/Spotlight_OS_X.svg.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton.setIcon(icon1)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout_3.addWidget(self.pushButton)
        self.pushButton_7 = QtWidgets.QPushButton(GBeditor)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/picture/resourses/original.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_7.setIcon(icon2)
        self.pushButton_7.setObjectName("pushButton_7")
        self.horizontalLayout_3.addWidget(self.pushButton_7)
        self.gridLayout.addLayout(self.horizontalLayout_3, 3, 0, 1, 1)

        self.retranslateUi(GBeditor)
        self.checkBox.toggled['bool'].connect(self.spinBox.setEnabled)
        QtCore.QMetaObject.connectSlotsByName(GBeditor)

    def retranslateUi(self, GBeditor):
        _translate = QtCore.QCoreApplication.translate
        GBeditor.setWindowTitle(_translate("GBeditor", "GenBank Editor"))
        self.checkBox.setText(_translate("GBeditor", "Set NCR threshold (intergenic region > ? bp):"))
        self.pushButton_2.setText(_translate("GBeditor", "Validate"))
        self.pushButton.setText(_translate("GBeditor", "Find"))
        self.pushButton_7.setToolTip(_translate("GBeditor", "Predict unrecognized tRNAs using ARWEN"))
        self.pushButton_7.setText(_translate("GBeditor", "Predict tRNA (LEU and SER)"))

from uifiles import myRes_rc

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    GBeditor = QtWidgets.QDialog()
    ui = Ui_GBeditor()
    ui.setupUi(GBeditor)
    GBeditor.show()
    sys.exit(app.exec_())

