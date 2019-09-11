# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'F:\Work\python\bioinfo_excercise\PhyloSuite\PhyloSuite\PhyloSuite\uifiles\seqViewSetting.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_seqViewSetting(object):
    def setupUi(self, seqViewSetting):
        seqViewSetting.setObjectName("seqViewSetting")
        seqViewSetting.resize(444, 357)
        self.verticalLayout = QtWidgets.QVBoxLayout(seqViewSetting)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_2 = QtWidgets.QLabel(seqViewSetting)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.lineEdit_fontSet = QtWidgets.QLineEdit(seqViewSetting)
        self.lineEdit_fontSet.setStyleSheet("QLineEdit {\n"
"    border: 1px solid gray;  \n"
"    border-radius: 3px; \n"
"    background: white;  \n"
"    selection-background-color: green; \n"
"}\n"
"\n"
"QLineEdit:hover {\n"
"    border: 1px solid blue;  \n"
"}")
        self.lineEdit_fontSet.setReadOnly(True)
        self.lineEdit_fontSet.setObjectName("lineEdit_fontSet")
        self.horizontalLayout.addWidget(self.lineEdit_fontSet)
        self.toolButton = QtWidgets.QToolButton(seqViewSetting)
        self.toolButton.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/picture/resourses/if_font_173018.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton.setIcon(icon)
        self.toolButton.setAutoRaise(True)
        self.toolButton.setObjectName("toolButton")
        self.horizontalLayout.addWidget(self.toolButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.label = QtWidgets.QLabel(seqViewSetting)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.tableView = QtWidgets.QTableView(seqViewSetting)
        self.tableView.setStyleSheet("QTableView {\n"
"    selection-background-color: none;\n"
"    outline: 0;\n"
"}")
        self.tableView.setObjectName("tableView")
        self.verticalLayout.addWidget(self.tableView)

        self.retranslateUi(seqViewSetting)
        QtCore.QMetaObject.connectSlotsByName(seqViewSetting)

    def retranslateUi(self, seqViewSetting):
        _translate = QtCore.QCoreApplication.translate
        seqViewSetting.setWindowTitle(_translate("seqViewSetting", "Sequence display settings"))
        self.label_2.setText(_translate("seqViewSetting", "Font:"))
        self.label.setText(_translate("seqViewSetting", "Double click to set colors:"))

from uifiles import myRes_rc

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    seqViewSetting = QtWidgets.QDialog()
    ui = Ui_seqViewSetting()
    ui.setupUi(seqViewSetting)
    seqViewSetting.show()
    sys.exit(app.exec_())

