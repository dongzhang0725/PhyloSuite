# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\works\ZD\phylosuite\uifiles\partition_defination.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_PartDefine(object):
    def setupUi(self, PartDefine):
        PartDefine.setObjectName("PartDefine")
        PartDefine.resize(650, 599)
        self.gridLayout_2 = QtWidgets.QGridLayout(PartDefine)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.splitter = QtWidgets.QSplitter(PartDefine)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName("splitter")
        self.layoutWidget = QtWidgets.QWidget(self.splitter)
        self.layoutWidget.setObjectName("layoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.layoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(self.layoutWidget)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.tableView_partition = QtWidgets.QTableView(self.layoutWidget)
        self.tableView_partition.setObjectName("tableView_partition")
        self.gridLayout.addWidget(self.tableView_partition, 1, 0, 1, 2)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.pushButton_2 = QtWidgets.QPushButton(self.layoutWidget)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/picture/resourses/table_row_add_after.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_2.setIcon(icon)
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout_2.addWidget(self.pushButton_2)
        self.pushButton = QtWidgets.QPushButton(self.layoutWidget)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/picture/resourses/delete.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton.setIcon(icon1)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout_2.addWidget(self.pushButton)
        self.gridLayout.addLayout(self.horizontalLayout_2, 2, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton_adp = QtWidgets.QPushButton(self.layoutWidget)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/picture/resourses/table_column_add_after.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_adp.setIcon(icon2)
        self.pushButton_adp.setObjectName("pushButton_adp")
        self.horizontalLayout.addWidget(self.pushButton_adp)
        self.pushButton_delp = QtWidgets.QPushButton(self.layoutWidget)
        self.pushButton_delp.setIcon(icon1)
        self.pushButton_delp.setObjectName("pushButton_delp")
        self.horizontalLayout.addWidget(self.pushButton_delp)
        self.gridLayout.addLayout(self.horizontalLayout, 2, 1, 1, 1)
        self.layoutWidget1 = QtWidgets.QWidget(self.splitter)
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.layoutWidget1)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_2 = QtWidgets.QLabel(self.layoutWidget1)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.textEdit = QtWidgets.QTextEdit(self.layoutWidget1)
        self.textEdit.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.textEdit.setReadOnly(True)
        self.textEdit.setObjectName("textEdit")
        self.verticalLayout.addWidget(self.textEdit)
        self.gridLayout_2.addWidget(self.splitter, 0, 0, 1, 2)
        self.pushButton_blk = QtWidgets.QPushButton(PartDefine)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/picture/resourses/refresh-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_blk.setIcon(icon3)
        self.pushButton_blk.setObjectName("pushButton_blk")
        self.gridLayout_2.addWidget(self.pushButton_blk, 1, 0, 1, 1)
        self.pushButton_close = QtWidgets.QPushButton(PartDefine)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/picture/resourses/if_Delete_1493279.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_close.setIcon(icon4)
        self.pushButton_close.setObjectName("pushButton_close")
        self.gridLayout_2.addWidget(self.pushButton_close, 1, 1, 1, 1)

        self.retranslateUi(PartDefine)
        QtCore.QMetaObject.connectSlotsByName(PartDefine)

    def retranslateUi(self, PartDefine):
        _translate = QtCore.QCoreApplication.translate
        PartDefine.setWindowTitle(_translate("PartDefine", "Partition definitions"))
        self.label.setText(_translate("PartDefine", "Specify data blocks:"))
        self.pushButton_2.setText(_translate("PartDefine", "Add Subset"))
        self.pushButton.setText(_translate("PartDefine", "Delete Subset"))
        self.pushButton_adp.setText(_translate("PartDefine", "Add Partition"))
        self.pushButton_delp.setText(_translate("PartDefine", "Delete Partition"))
        self.label_2.setText(_translate("PartDefine", "Command block:"))
        self.pushButton_blk.setText(_translate("PartDefine", "Generate Command Block"))
        self.pushButton_close.setText(_translate("PartDefine", "Close"))

from uifiles import myRes_rc

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    PartDefine = QtWidgets.QDialog()
    ui = Ui_PartDefine()
    ui.setupUi(PartDefine)
    PartDefine.show()
    sys.exit(app.exec_())

