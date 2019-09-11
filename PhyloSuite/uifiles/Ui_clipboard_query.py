# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'F:\Work\python\bioinfo_excercise\PhyloSuite\PhyloSuite\PhyloSuite\uifiles\clipboard_query.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_ClipboardQ(object):
    def setupUi(self, ClipboardQ):
        ClipboardQ.setObjectName("ClipboardQ")
        ClipboardQ.resize(478, 198)
        ClipboardQ.setMinimumSize(QtCore.QSize(478, 0))
        ClipboardQ.setMaximumSize(QtCore.QSize(478, 16777215))
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(ClipboardQ)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.widget_container = QtWidgets.QWidget(ClipboardQ)
        self.widget_container.setStyleSheet("QWidget#widget_container {border: 1px ridge gray; background-color: white}")
        self.widget_container.setObjectName("widget_container")
        self.gridLayout = QtWidgets.QGridLayout(self.widget_container)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(self.widget_container)
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.radioButton = QtWidgets.QRadioButton(self.widget_container)
        self.radioButton.setChecked(True)
        self.radioButton.setObjectName("radioButton")
        self.verticalLayout.addWidget(self.radioButton)
        self.radioButton_2 = QtWidgets.QRadioButton(self.widget_container)
        self.radioButton_2.setObjectName("radioButton_2")
        self.verticalLayout.addWidget(self.radioButton_2)
        self.radioButton_4 = QtWidgets.QRadioButton(self.widget_container)
        self.radioButton_4.setObjectName("radioButton_4")
        self.verticalLayout.addWidget(self.radioButton_4)
        self.radioButton_3 = QtWidgets.QRadioButton(self.widget_container)
        self.radioButton_3.setObjectName("radioButton_3")
        self.verticalLayout.addWidget(self.radioButton_3)
        self.gridLayout.addLayout(self.verticalLayout, 1, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_2 = QtWidgets.QLabel(self.widget_container)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.lineEdit = QtWidgets.QLineEdit(self.widget_container)
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout.addWidget(self.lineEdit)
        self.label_3 = QtWidgets.QLabel(self.widget_container)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout.addWidget(self.label_3)
        self.lineEdit_2 = QtWidgets.QLineEdit(self.widget_container)
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.horizontalLayout.addWidget(self.lineEdit_2)
        self.gridLayout.addLayout(self.horizontalLayout, 2, 0, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.pushButton = QtWidgets.QPushButton(self.widget_container)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/picture/resourses/btn_ok.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton.setIcon(icon)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout_2.addWidget(self.pushButton)
        self.pushButton_2 = QtWidgets.QPushButton(self.widget_container)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/picture/resourses/btn_close.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_2.setIcon(icon1)
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout_2.addWidget(self.pushButton_2)
        self.gridLayout.addLayout(self.horizontalLayout_2, 3, 0, 1, 1)
        self.verticalLayout_3.addWidget(self.widget_container)

        self.retranslateUi(ClipboardQ)
        QtCore.QMetaObject.connectSlotsByName(ClipboardQ)

    def retranslateUi(self, ClipboardQ):
        _translate = QtCore.QCoreApplication.translate
        ClipboardQ.setWindowTitle(_translate("ClipboardQ", "Type of clipboard contents"))
        self.label.setText(_translate("ClipboardQ", "Which type of sequence are in the clipboard contents"))
        self.radioButton.setText(_translate("ClipboardQ", "Nucleotide sequence"))
        self.radioButton_2.setText(_translate("ClipboardQ", "Protein sequence"))
        self.radioButton_4.setText(_translate("ClipboardQ", "RNA sequence"))
        self.radioButton_3.setText(_translate("ClipboardQ", "Not a sequence"))
        self.label_2.setText(_translate("ClipboardQ", "ID:"))
        self.label_3.setText(_translate("ClipboardQ", "Organism:"))
        self.pushButton.setText(_translate("ClipboardQ", "Ok"))
        self.pushButton_2.setText(_translate("ClipboardQ", "Cancel"))

from uifiles import myRes_rc

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ClipboardQ = QtWidgets.QDialog()
    ui = Ui_ClipboardQ()
    ui.setupUi(ClipboardQ)
    ClipboardQ.show()
    sys.exit(app.exec_())

