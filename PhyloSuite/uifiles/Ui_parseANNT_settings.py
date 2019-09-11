# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'F:\Work\python\bioinfo_excercise\PhyloSuite\PhyloSuite\PhyloSuite\uifiles\parseANNT_settings.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_ParAnnt_settings(object):
    def setupUi(self, ParAnnt_settings):
        ParAnnt_settings.setObjectName("ParAnnt_settings")
        ParAnnt_settings.setWindowModality(QtCore.Qt.NonModal)
        ParAnnt_settings.resize(697, 538)
        ParAnnt_settings.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        self.verticalLayout = QtWidgets.QVBoxLayout(ParAnnt_settings)
        self.verticalLayout.setObjectName("verticalLayout")
        self.splitter = QtWidgets.QSplitter(ParAnnt_settings)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.listWidget = QtWidgets.QListWidget(self.splitter)
        self.listWidget.setObjectName("listWidget")
        self.layoutWidget = QtWidgets.QWidget(self.splitter)
        self.layoutWidget.setObjectName("layoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.layoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(2)
        self.gridLayout.setObjectName("gridLayout")
        self.tableView = QtWidgets.QTableView(self.layoutWidget)
        self.tableView.setAcceptDrops(True)
        self.tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tableView.setSortingEnabled(True)
        self.tableView.setObjectName("tableView")
        self.tableView.horizontalHeader().setCascadingSectionResizes(False)
        self.tableView.horizontalHeader().setSortIndicatorShown(True)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.gridLayout.addWidget(self.tableView, 0, 0, 1, 2)
        self.pushButton = QtWidgets.QPushButton(self.layoutWidget)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/picture/resourses/table_row_add_after.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton.setIcon(icon)
        self.pushButton.setObjectName("pushButton")
        self.gridLayout.addWidget(self.pushButton, 1, 1, 1, 1)
        self.pushButton_2 = QtWidgets.QPushButton(self.layoutWidget)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/picture/resourses/delete.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_2.setIcon(icon1)
        self.pushButton_2.setObjectName("pushButton_2")
        self.gridLayout.addWidget(self.pushButton_2, 1, 0, 1, 1)
        self.verticalLayout.addWidget(self.splitter)

        self.retranslateUi(ParAnnt_settings)
        QtCore.QMetaObject.connectSlotsByName(ParAnnt_settings)

    def retranslateUi(self, ParAnnt_settings):
        _translate = QtCore.QCoreApplication.translate
        ParAnnt_settings.setWindowTitle(_translate("ParAnnt_settings", "Parse annotation settings"))
        self.pushButton.setText(_translate("ParAnnt_settings", "Add"))
        self.pushButton_2.setText(_translate("ParAnnt_settings", "Delete"))

from uifiles import myRes_rc

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ParAnnt_settings = QtWidgets.QDialog()
    ui = Ui_ParAnnt_settings()
    ui.setupUi(ParAnnt_settings)
    ParAnnt_settings.show()
    sys.exit(app.exec_())

