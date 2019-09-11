# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'F:\Work\python\bioinfo_excercise\PhyloSuite\PhyloSuite\PhyloSuite\uifiles\popUp.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_pop(object):
    def setupUi(self, pop):
        pop.setObjectName("pop")
        pop.resize(442, 379)
        self.gridLayout = QtWidgets.QGridLayout(pop)
        self.gridLayout.setObjectName("gridLayout")
        self.textEdit = QtWidgets.QTextEdit(pop)
        self.textEdit.setObjectName("textEdit")
        self.gridLayout.addWidget(self.textEdit, 1, 0, 1, 2)
        self.pushButton = QtWidgets.QPushButton(pop)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/picture/resourses/btn_ok.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton.setIcon(icon)
        self.pushButton.setObjectName("pushButton")
        self.gridLayout.addWidget(self.pushButton, 2, 0, 1, 1)
        self.pushButton_2 = QtWidgets.QPushButton(pop)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/picture/resourses/if_Delete_1493279.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_2.setIcon(icon1)
        self.pushButton_2.setObjectName("pushButton_2")
        self.gridLayout.addWidget(self.pushButton_2, 2, 1, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtWidgets.QLabel(pop)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.toolButton = QtWidgets.QToolButton(pop)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/picture/resourses/interface-controls-text-wrap-512.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton.setIcon(icon2)
        self.toolButton.setCheckable(True)
        self.toolButton.setObjectName("toolButton")
        self.horizontalLayout_2.addWidget(self.toolButton)
        self.gridLayout.addLayout(self.horizontalLayout_2, 0, 0, 1, 2)

        self.retranslateUi(pop)
        QtCore.QMetaObject.connectSlotsByName(pop)

    def retranslateUi(self, pop):
        _translate = QtCore.QCoreApplication.translate
        pop.setWindowTitle(_translate("pop", "popi"))
        self.pushButton.setText(_translate("pop", "OK"))
        self.pushButton_2.setText(_translate("pop", "Cancel"))
        self.label.setText(_translate("pop", "Set weights:"))
        self.toolButton.setToolTip(_translate("pop", "Use Wraps"))
        self.toolButton.setText(_translate("pop", "..."))

from uifiles import myRes_rc

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    pop = QtWidgets.QDialog()
    ui = Ui_pop()
    ui.setupUi(pop)
    pop.show()
    sys.exit(app.exec_())

