# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\works\ZD\phylosuite\uifiles\addFile.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_addFile(object):
    def setupUi(self, addFile):
        addFile.setObjectName("addFile")
        addFile.resize(548, 535)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(addFile)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.groupBox_3 = QtWidgets.QGroupBox(addFile)
        self.groupBox_3.setObjectName("groupBox_3")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.groupBox_3)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtWidgets.QLabel(self.groupBox_3)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.comboBox = QtWidgets.QComboBox(self.groupBox_3)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox.sizePolicy().hasHeightForWidth())
        self.comboBox.setSizePolicy(sizePolicy)
        self.comboBox.setObjectName("comboBox")
        self.horizontalLayout_2.addWidget(self.comboBox)
        self.label_3 = ClickedLableGif(self.groupBox_3)
        self.label_3.setText("")
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_2.addWidget(self.label_3)
        self.verticalLayout_2.addWidget(self.groupBox_3)
        self.groupBox = QtWidgets.QGroupBox(addFile)
        self.groupBox.setCheckable(False)
        self.groupBox.setChecked(False)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.pushButton = QtWidgets.QPushButton(self.groupBox)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/picture/resourses/Open_folder_add_512px_1186192_easyicon.net.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton.setIcon(icon)
        self.pushButton.setIconSize(QtCore.QSize(16, 18))
        self.pushButton.setObjectName("pushButton")
        self.gridLayout.addWidget(self.pushButton, 0, 0, 1, 1)
        self.verticalLayout_2.addWidget(self.groupBox)
        self.groupBox_2 = QtWidgets.QGroupBox(addFile)
        self.groupBox_2.setEnabled(True)
        self.groupBox_2.setFlat(False)
        self.groupBox_2.setCheckable(False)
        self.groupBox_2.setChecked(False)
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox_2)
        self.verticalLayout.setObjectName("verticalLayout")
        self.plainTextEdit = QtWidgets.QPlainTextEdit(self.groupBox_2)
        self.plainTextEdit.setEnabled(True)
        self.plainTextEdit.viewport().setProperty("cursor", QtGui.QCursor(QtCore.Qt.IBeamCursor))
        self.plainTextEdit.setMouseTracking(True)
        self.plainTextEdit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.plainTextEdit.setPlaceholderText("")
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.verticalLayout.addWidget(self.plainTextEdit)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(self.groupBox_2)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.lineEdit = QtWidgets.QLineEdit(self.groupBox_2)
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout.addWidget(self.lineEdit)
        self.toolButton = QtWidgets.QToolButton(self.groupBox_2)
        self.toolButton.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/picture/resourses/Question-mark.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton.setIcon(icon1)
        self.toolButton.setAutoRaise(True)
        self.toolButton.setObjectName("toolButton")
        self.horizontalLayout.addWidget(self.toolButton)
        self.label_4 = QtWidgets.QLabel(self.groupBox_2)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout.addWidget(self.label_4)
        self.comboBox_2 = QtWidgets.QComboBox(self.groupBox_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox_2.sizePolicy().hasHeightForWidth())
        self.comboBox_2.setSizePolicy(sizePolicy)
        self.comboBox_2.setObjectName("comboBox_2")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.horizontalLayout.addWidget(self.comboBox_2)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.pushButton_2 = QtWidgets.QPushButton(self.groupBox_2)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/picture/resourses/if_start_60207.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_2.setIcon(icon2)
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout_3.addWidget(self.pushButton_2)
        self.pushButton_8 = QtWidgets.QPushButton(self.groupBox_2)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/picture/resourses/NCBI-logo-2.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_8.setIcon(icon3)
        self.pushButton_8.setObjectName("pushButton_8")
        self.horizontalLayout_3.addWidget(self.pushButton_8)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.verticalLayout_2.addWidget(self.groupBox_2)

        self.retranslateUi(addFile)
        self.groupBox_2.toggled['bool'].connect(self.groupBox.setEnabled)
        self.groupBox.toggled['bool'].connect(self.groupBox_2.setEnabled)
        QtCore.QMetaObject.connectSlotsByName(addFile)

    def retranslateUi(self, addFile):
        _translate = QtCore.QCoreApplication.translate
        addFile.setWindowTitle(_translate("addFile", "Input"))
        self.groupBox_3.setTitle(_translate("addFile", "Export"))
        self.label_2.setText(_translate("addFile", "Export path:"))
        self.label_3.setToolTip(_translate("addFile", "Brief example"))
        self.groupBox.setTitle(_translate("addFile", "Input by files"))
        self.pushButton.setText(_translate("addFile", "Choose Files"))
        self.groupBox_2.setTitle(_translate("addFile", "Input by IDs"))
        self.plainTextEdit.setToolTip(_translate("addFile", "<html><head/><body><p>\n"
"<pre style=\" font-size:12pt;\">\n"
"One id per line, for example:\n"
"KX289585\n"
"MF187611\n"
"GU130252\n"
"GU130251\n"
"EF643519\n"
"</pre>\n"
"</p></body></html>"))
        self.label.setText(_translate("addFile", "Email:"))
        self.lineEdit.setPlaceholderText(_translate("addFile", "A.N.Other@example.com"))
        self.label_4.setText(_translate("addFile", "Database:"))
        self.comboBox_2.setItemText(0, _translate("addFile", "nucleotide"))
        self.comboBox_2.setItemText(1, _translate("addFile", "protein"))
        self.pushButton_2.setText(_translate("addFile", "Start"))
        self.pushButton_8.setText(_translate("addFile", "Search in NCBI"))

from src.CustomWidget import ClickedLableGif
from uifiles import myRes_rc

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    addFile = QtWidgets.QDialog()
    ui = Ui_addFile()
    ui.setupUi(addFile)
    addFile.show()
    sys.exit(app.exec_())

