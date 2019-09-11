# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'F:\Work\python\bioinfo_excercise\PhyloSuite\PhyloSuite\PhyloSuite\uifiles\dirichlet_mrbayes.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dirichlet(object):
    def setupUi(self, Dirichlet):
        Dirichlet.setObjectName("Dirichlet")
        Dirichlet.resize(294, 131)
        self.gridLayout = QtWidgets.QGridLayout(Dirichlet)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(Dirichlet)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.toolButton = QtWidgets.QToolButton(Dirichlet)
        self.toolButton.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/picture/resourses/add-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton.setIcon(icon)
        self.toolButton.setObjectName("toolButton")
        self.horizontalLayout.addWidget(self.toolButton)
        self.toolButton_2 = QtWidgets.QToolButton(Dirichlet)
        self.toolButton_2.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/picture/resourses/delete.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton_2.setIcon(icon1)
        self.toolButton_2.setObjectName("toolButton_2")
        self.horizontalLayout.addWidget(self.toolButton_2)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.lineEdit = QtWidgets.QLineEdit(Dirichlet)
        self.lineEdit.setMinimumSize(QtCore.QSize(0, 30))
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(24)
        font.setBold(True)
        font.setWeight(75)
        self.lineEdit.setFont(font)
        self.lineEdit.setObjectName("lineEdit")
        self.gridLayout.addWidget(self.lineEdit, 1, 0, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.pushButton = QtWidgets.QPushButton(Dirichlet)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/picture/resourses/btn_ok.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton.setIcon(icon2)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout_2.addWidget(self.pushButton)
        self.pushButton_2 = QtWidgets.QPushButton(Dirichlet)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/picture/resourses/if_Delete_1493279.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_2.setIcon(icon3)
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout_2.addWidget(self.pushButton_2)
        self.gridLayout.addLayout(self.horizontalLayout_2, 2, 0, 1, 1)

        self.retranslateUi(Dirichlet)
        QtCore.QMetaObject.connectSlotsByName(Dirichlet)

    def retranslateUi(self, Dirichlet):
        _translate = QtCore.QCoreApplication.translate
        Dirichlet.setWindowTitle(_translate("Dirichlet", "Set dirichlet"))
        self.label.setText(_translate("Dirichlet", "Specify dirichlet:"))
        self.toolButton.setToolTip(_translate("Dirichlet", "Add number"))
        self.toolButton_2.setToolTip(_translate("Dirichlet", "Delete number"))
        self.pushButton.setText(_translate("Dirichlet", "Ok"))
        self.pushButton_2.setText(_translate("Dirichlet", "Cancel"))

from uifiles import myRes_rc

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dirichlet = QtWidgets.QDialog()
    ui = Ui_Dirichlet()
    ui.setupUi(Dirichlet)
    Dirichlet.show()
    sys.exit(app.exec_())

