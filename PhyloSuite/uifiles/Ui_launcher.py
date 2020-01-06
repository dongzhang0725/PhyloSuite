# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'F:\Work\python\bioinfo_excercise\PhyloSuite\codes\PhyloSuite\uifiles\launcher.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_launcher(object):
    def setupUi(self, launcher):
        launcher.setObjectName("launcher")
        launcher.setWindowModality(QtCore.Qt.NonModal)
        launcher.resize(579, 177)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/picture/resourses/windowIcon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        launcher.setWindowIcon(icon)
        self.gridLayout = QtWidgets.QGridLayout(launcher)
        self.gridLayout.setObjectName("gridLayout")
        self.textEdit = QtWidgets.QTextEdit(launcher)
        self.textEdit.setObjectName("textEdit")
        self.gridLayout.addWidget(self.textEdit, 0, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(launcher)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.comboBox = QtWidgets.QComboBox(launcher)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox.sizePolicy().hasHeightForWidth())
        self.comboBox.setSizePolicy(sizePolicy)
        self.comboBox.setEditable(False)
        self.comboBox.setObjectName("comboBox")
        self.horizontalLayout.addWidget(self.comboBox)
        self.pushButton_3 = QtWidgets.QPushButton(launcher)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_3.sizePolicy().hasHeightForWidth())
        self.pushButton_3.setSizePolicy(sizePolicy)
        self.pushButton_3.setMinimumSize(QtCore.QSize(30, 26))
        self.pushButton_3.setMaximumSize(QtCore.QSize(16777215, 26))
        self.pushButton_3.setStyleSheet("QPushButton {\n"
"    border-image: url(:/picture/resourses/Open_folder_add_512px_1186192_easyicon.net.png);\n"
"padding: 2px;\n"
"}\n"
"\n"
"\n"
" QPushButton:hover:!pressed\n"
"{\n"
"  border: 1px solid red;\n"
"}")
        self.pushButton_3.setText("")
        self.pushButton_3.setObjectName("pushButton_3")
        self.horizontalLayout.addWidget(self.pushButton_3)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)
        self.checkBox = QtWidgets.QCheckBox(launcher)
        self.checkBox.setChecked(True)
        self.checkBox.setObjectName("checkBox")
        self.gridLayout.addWidget(self.checkBox, 2, 0, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.pushButton = QtWidgets.QPushButton(launcher)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())
        self.pushButton.setSizePolicy(sizePolicy)
        self.pushButton.setMinimumSize(QtCore.QSize(75, 24))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/picture/resourses/btn_ok.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton.setIcon(icon1)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout_2.addWidget(self.pushButton)
        self.pushButton_2 = QtWidgets.QPushButton(launcher)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_2.sizePolicy().hasHeightForWidth())
        self.pushButton_2.setSizePolicy(sizePolicy)
        self.pushButton_2.setMinimumSize(QtCore.QSize(75, 24))
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/picture/resourses/btn_close.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_2.setIcon(icon2)
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout_2.addWidget(self.pushButton_2)
        self.gridLayout.addLayout(self.horizontalLayout_2, 3, 0, 1, 1)

        self.retranslateUi(launcher)
        QtCore.QMetaObject.connectSlotsByName(launcher)

    def retranslateUi(self, launcher):
        _translate = QtCore.QCoreApplication.translate
        launcher.setWindowTitle(_translate("launcher", "Set workplace"))
        self.textEdit.setHtml(_translate("launcher", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'SimSun\'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Select a directory as workplace</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">  PhyloSuite uses the workplace directory to store data and results</p></body></html>"))
        self.label.setText(_translate("launcher", "Workplace:"))
        self.checkBox.setText(_translate("launcher", "Use this as the default and do not ask again"))
        self.pushButton.setText(_translate("launcher", "Ok"))
        self.pushButton_2.setText(_translate("launcher", "Cancel"))

from uifiles import myRes_rc

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    launcher = QtWidgets.QDialog()
    ui = Ui_launcher()
    ui.setupUi(launcher)
    launcher.show()
    sys.exit(app.exec_())

