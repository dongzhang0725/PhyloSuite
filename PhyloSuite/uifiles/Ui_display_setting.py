# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'F:\Work\python\bioinfo_excercise\PhyloSuite\codes\PhyloSuite\uifiles\display_setting.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_DisplaySettings(object):
    def setupUi(self, DisplaySettings):
        DisplaySettings.setObjectName("DisplaySettings")
        DisplaySettings.resize(786, 529)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(DisplaySettings)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.splitter = QtWidgets.QSplitter(DisplaySettings)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.layoutWidget = QtWidgets.QWidget(self.splitter)
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label = QtWidgets.QLabel(self.layoutWidget)
        self.label.setObjectName("label")
        self.verticalLayout_3.addWidget(self.label)
        self.treeView = QtWidgets.QTreeView(self.layoutWidget)
        self.treeView.setObjectName("treeView")
        self.treeView.header().setVisible(False)
        self.verticalLayout_3.addWidget(self.treeView)
        self.widget = QtWidgets.QWidget(self.splitter)
        self.widget.setObjectName("widget")
        self.gridLayout = QtWidgets.QGridLayout(self.widget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_2 = QtWidgets.QLabel(self.widget)
        self.label_2.setStatusTip("")
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.label_3 = QtWidgets.QLabel(self.widget)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout.addWidget(self.label_3)
        self.label_6 = ClickedLableGif(self.widget)
        self.label_6.setText("")
        self.label_6.setAlignment(QtCore.Qt.AlignCenter)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout.addWidget(self.label_6)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 2)
        self.listWidget = QtWidgets.QListWidget(self.widget)
        self.listWidget.setAcceptDrops(True)
        self.listWidget.setTabKeyNavigation(True)
        self.listWidget.setDragEnabled(True)
        self.listWidget.setDragDropOverwriteMode(False)
        self.listWidget.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.listWidget.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.listWidget.setAlternatingRowColors(True)
        self.listWidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.listWidget.setSelectionRectVisible(False)
        self.listWidget.setObjectName("listWidget")
        self.gridLayout.addWidget(self.listWidget, 1, 0, 1, 1)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.pushButton_del = QtWidgets.QPushButton(self.widget)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/picture/resourses/delete.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_del.setIcon(icon)
        self.pushButton_del.setObjectName("pushButton_del")
        self.verticalLayout.addWidget(self.pushButton_del)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.pushButton = QtWidgets.QPushButton(self.widget)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/picture/resourses/btn_ok.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton.setIcon(icon1)
        self.pushButton.setObjectName("pushButton")
        self.verticalLayout.addWidget(self.pushButton)
        self.pushButton_2 = QtWidgets.QPushButton(self.widget)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/picture/resourses/btn_close.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_2.setIcon(icon2)
        self.pushButton_2.setObjectName("pushButton_2")
        self.verticalLayout.addWidget(self.pushButton_2)
        self.gridLayout.addLayout(self.verticalLayout, 1, 1, 1, 1)
        self.verticalLayout_2.addWidget(self.splitter)

        self.retranslateUi(DisplaySettings)
        QtCore.QMetaObject.connectSlotsByName(DisplaySettings)

    def retranslateUi(self, DisplaySettings):
        _translate = QtCore.QCoreApplication.translate
        DisplaySettings.setWindowTitle(_translate("DisplaySettings", "Displayed settings of table"))
        self.label.setText(_translate("DisplaySettings", "All available information to display:"))
        self.treeView.setToolTip(_translate("DisplaySettings", "Click to add"))
        self.label_2.setText(_translate("DisplaySettings", "Informations selected to display:"))
        self.label_3.setText(_translate("DisplaySettings", "Demo:"))
        self.label_6.setToolTip(_translate("DisplaySettings", "Brief example"))
        self.listWidget.setToolTip(_translate("DisplaySettings", "try to drag to reorder"))
        self.pushButton_del.setToolTip(_translate("DisplaySettings", "Delete selected item(s)"))
        self.pushButton_del.setText(_translate("DisplaySettings", "Delete"))
        self.pushButton.setText(_translate("DisplaySettings", "Ok"))
        self.pushButton_2.setText(_translate("DisplaySettings", "Cancel"))

from src.CustomWidget import ClickedLableGif
from uifiles import myRes_rc

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    DisplaySettings = QtWidgets.QDialog()
    ui = Ui_DisplaySettings()
    ui.setupUi(DisplaySettings)
    DisplaySettings.show()
    sys.exit(app.exec_())

