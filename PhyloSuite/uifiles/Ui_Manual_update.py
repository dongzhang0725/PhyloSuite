# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\works\ZD\phylosuite\PhyloSuite\uifiles\Manual_update.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Manual_update(object):
    def setupUi(self, Manual_update):
        Manual_update.setObjectName("Manual_update")
        Manual_update.resize(650, 207)
        Manual_update.setMinimumSize(QtCore.QSize(650, 0))
        Manual_update.setMaximumSize(QtCore.QSize(16777215, 16777215))
        Manual_update.setSizeGripEnabled(True)
        self.gridLayout = QtWidgets.QGridLayout(Manual_update)
        self.gridLayout.setObjectName("gridLayout")
        self.label_3 = QtWidgets.QLabel(Manual_update)
        self.label_3.setScaledContents(False)
        self.label_3.setWordWrap(True)
        self.label_3.setOpenExternalLinks(True)
        self.label_3.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByMouse)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 0, 0, 1, 3)
        self.label = QtWidgets.QLabel(Manual_update)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)
        self.lineEdit = QtWidgets.QLineEdit(Manual_update)
        self.lineEdit.setDragEnabled(True)
        self.lineEdit.setReadOnly(True)
        self.lineEdit.setObjectName("lineEdit")
        self.gridLayout.addWidget(self.lineEdit, 1, 1, 1, 1)
        self.toolButton_3 = QtWidgets.QToolButton(Manual_update)
        self.toolButton_3.setStyleSheet("")
        self.toolButton_3.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/picture/resourses/Open_folder_add_512px_1186192_easyicon.net.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton_3.setIcon(icon)
        self.toolButton_3.setIconSize(QtCore.QSize(30, 30))
        self.toolButton_3.setCheckable(False)
        self.toolButton_3.setChecked(False)
        self.toolButton_3.setAutoRaise(True)
        self.toolButton_3.setObjectName("toolButton_3")
        self.gridLayout.addWidget(self.toolButton_3, 1, 2, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton = QtWidgets.QPushButton(Manual_update)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/picture/resourses/btn_ok.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton.setIcon(icon1)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout.addWidget(self.pushButton)
        self.pushButton_2 = QtWidgets.QPushButton(Manual_update)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/picture/resourses/btn_close.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_2.setIcon(icon2)
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout.addWidget(self.pushButton_2)
        self.gridLayout.addLayout(self.horizontalLayout, 2, 0, 1, 3)

        self.retranslateUi(Manual_update)
        QtCore.QMetaObject.connectSlotsByName(Manual_update)

    def retranslateUi(self, Manual_update):
        _translate = QtCore.QCoreApplication.translate
        Manual_update.setWindowTitle(_translate("Manual_update", "Update manually"))
        self.label_3.setText(_translate("Manual_update", "<html><head/><body><p>You can download the latest update package from <a href=\"http://phylosuite.jushengwu.com/updates/update.zip\"><span style=\" text-decoration: underline; color:#0000ff;\">here</span></a>, and then specify the path below.</p></body></html>"))
        self.label.setText(_translate("Manual_update", "Update file path:"))
        self.lineEdit.setPlaceholderText(_translate("Manual_update", "~/update_xxx.zip"))
        self.pushButton.setText(_translate("Manual_update", "Ok"))
        self.pushButton_2.setText(_translate("Manual_update", "Cancel"))

from uifiles import myRes_rc

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Manual_update = QtWidgets.QDialog()
    ui = Ui_Manual_update()
    ui.setupUi(Manual_update)
    Manual_update.show()
    sys.exit(app.exec_())

