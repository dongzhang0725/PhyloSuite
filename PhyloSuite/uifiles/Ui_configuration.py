# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\HUAWEI\works\phylosuite\PhyloSuite_gitee\PhyloSuite\uifiles\configuration.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_configuration(object):
    def setupUi(self, configuration):
        configuration.setObjectName("configuration")
        configuration.resize(750, 643)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(configuration)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.groupBox = QtWidgets.QGroupBox(configuration)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.toolButton = QtWidgets.QToolButton(self.groupBox)
        self.toolButton.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/picture/resourses/interface-controls-text-wrap-512.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton.setIcon(icon)
        self.toolButton.setCheckable(True)
        self.toolButton.setObjectName("toolButton")
        self.horizontalLayout_2.addWidget(self.toolButton)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.textEdit = QtWidgets.QTextEdit(self.groupBox)
        self.textEdit.setObjectName("textEdit")
        self.verticalLayout.addWidget(self.textEdit)
        self.verticalLayout_2.addWidget(self.groupBox)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton = QtWidgets.QPushButton(configuration)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/picture/resourses/if_start_60207.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton.setIcon(icon1)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout.addWidget(self.pushButton)
        self.pushButton_2 = QtWidgets.QPushButton(configuration)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/picture/resourses/if_Delete_1493279.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_2.setIcon(icon2)
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout.addWidget(self.pushButton_2)
        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.retranslateUi(configuration)
        QtCore.QMetaObject.connectSlotsByName(configuration)

    def retranslateUi(self, configuration):
        _translate = QtCore.QCoreApplication.translate
        configuration.setWindowTitle(_translate("configuration", "Dialog"))
        self.groupBox.setTitle(_translate("configuration", "Configuration"))
        self.toolButton.setToolTip(_translate("configuration", "Use Wraps"))
        self.pushButton.setText(_translate("configuration", "SAVE AND RUN"))
        self.pushButton_2.setText(_translate("configuration", "CANCEL"))

from uifiles import myRes_rc

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    configuration = QtWidgets.QDialog()
    ui = Ui_configuration()
    ui.setupUi(configuration)
    configuration.show()
    sys.exit(app.exec_())

