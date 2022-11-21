#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import glob

import re
from collections import OrderedDict

import datetime
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from src.CustomWidget import ClickedLable, AnimationShadowEffect, NoteMessage
from src.Lg_settings import Setting
from src.Lg_trimAl import TrimAl
from uifiles.Ui_work_flow import Ui_WorkFlow
from src.factory import Factory, Convertfmt
import inspect
import os
import sys
import subprocess
from src.Lg_IQTREE import IQTREE
from src.Lg_Mrbayes import MrBayes
from src.Lg_mafft import Mafft
from src.Lg_Concatenate import Matrix
from src.Lg_PartitionFinder import PartitionFinder
from src.Lg_Gblocks import Gblocks
from src.Lg_ModelFinder import ModelFinder
from src.Lg_macse import MACSE
from src.Lg_HmmCleaner import HmmCleaner
import platform


class QCustomQWidget(QWidget):
    def __init__(self, parent=None):
        super(QCustomQWidget, self).__init__(parent)
        self.gridLayout = QGridLayout(self)
        self.label = QLabel(self)  # MAFFT
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.pushButton_edit = QToolButton(parent=self)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_edit.sizePolicy().hasHeightForWidth())
        self.pushButton_edit.setMinimumSize(QSize(25, 25))
        self.pushButton_edit.setMaximumSize(QSize(25, 25))
        self.pushButton_edit.setIcon(QIcon(":/picture/resourses/cog.png"))
        self.pushButton_edit.setAutoRaise(True)
        self.pushButton_edit.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.pushButton_edit.setSizePolicy(sizePolicy)
        self.pushButton_edit.setToolTip("Set/view parameters")
        self.gridLayout.addWidget(self.pushButton_edit, 0, 1, 1, 1)
        spacerItem = QSpacerItem(130, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 0, 2, 1, 1)
        self.label_inputText = ClickedLable(self)
        self.gridLayout.addWidget(self.label_inputText, 0, 3, 1, 1)
        self.label_inputGif = ClickedLable(self)
        self.gridLayout.addWidget(self.label_inputGif, 0, 4, 1, 1)
        spacerItem2 = QSpacerItem(130, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem2, 0, 5, 1, 1)
        self.label_status = QLabel(self)
        self.gridLayout.addWidget(self.label_status, 0, 6, 1, 1)
        self.horizontalLayout = QHBoxLayout()
        self.label_3 = QLabel("", parent=self)  # software icon
        self.label_3.setMinimumSize(QSize(25, 25))
        self.label_3.setMaximumSize(QSize(25, 25))
        self.label_3.setScaledContents(True)
        self.horizontalLayout.addWidget(self.label_3)
        self.pushbutton_view = QPushButton("", parent=self)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushbutton_view.sizePolicy().hasHeightForWidth())
        self.pushbutton_view.setSizePolicy(sizePolicy)
        # self.pushbutton_view.setMinimumSize(QSize(25, 25))
        # self.pushbutton_view.setMaximumSize(QSize(25, 25))
        self.pushbutton_view.setToolTip("View results")
        self.pushbutton_view.setStyleSheet(
            " QPushButton {border-image: url(:/picture/resourses/report_disk_32px_507034_easyicon.net.png);"
            " background:none;"
            " border: 2px solid #B2B6B9;"
            " border-radius: 1px;"
            " padding-bottom: 5px;"
            " min-height: 5px;"
            " min-width: 9px;"
            " max-height: 9px;"
            " max-width: 5px;}"
            " QPushButton:hover:!pressed {border: 1px solid red;;}"
            " QPushButton:disabled {border-image: url(:/picture/resourses/report_disk_gray.png);}")
        self.pushbutton_view.setEnabled(False)
        self.horizontalLayout.addWidget(self.pushbutton_view)
        self.label_2 = QLabel("", parent=self)
        self.label_2.setMinimumSize(QSize(25, 25))
        self.label_2.setMaximumSize(QSize(25, 25))
        self.label_2.setScaledContents(True)
        self.horizontalLayout.addWidget(self.label_2)
        self.progressBar = QProgressBar(self)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setOrientation(Qt.Horizontal)
        self.horizontalLayout.addWidget(self.progressBar)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 7)
        self.factory = Factory()

    def setSoftwareText(self, text):
        self.softWare = text
        self.label.setText("<span style='font-weight:600; color:purple;'>" + self.softWare + "</span>")

    def setStatusText(self, text):
        self.status = text
        self.label_status.setText(self.status)
        if self.status == "finished":
            self.label_status.setStyleSheet('''
                                color: green;
                            ''')
        elif self.status == "running...":
            self.label_status.setStyleSheet('''
                                color: rgb(255, 0, 0);
                            ''')
        else:
            self.label_status.setStyleSheet('''
                                color: black;
                            ''')

    def setSoftwareIcon(self, imagePath):
        self.label_3.setPixmap(QPixmap(imagePath))

    def setStatusIcon(self, imagePath):
        if imagePath.endswith(".gif"):
            movie = QMovie(imagePath)
            self.label_2.setMovie(movie)
            movie.start()
        else:
            self.label_2.setPixmap(QPixmap(imagePath))

    # def setEditIcon(self, imagePath):
    #     icon = QIcon()
    #     icon.addPixmap(QPixmap(imagePath))
    #     self.pushButton_edit.setIcon(icon)
    #     self.pushButton_edit.setIconSize(QSize(25, 25))

    def setStatusGif(self, imagePath):
        self.status = "running"
        self.label_status.setText(self.status)
        movie = QMovie(imagePath)
        self.label_2.setMovie(movie)
        movie.start()

    def setExeWindow(self, exe_window):
        self.exe_window = exe_window
        self.pushButton_edit.clicked.connect(self.popUpWindow)

    def popUpWindow(self):
        self.exe_window.exec_()

    def setPopupExport(self, path):
        self.exportPath = path
        self.pushbutton_view.clicked.connect(self.popupExport)

    def popupExport(self):
        if os.path.exists(self.exportPath):
            self.factory.openPath(self.exportPath, self)

    def setInputState(self, gifPath):
        self.label_inputGif.clicked.connect(self.exe_window.exec_)
        self.label_inputText.setText('<span style="font-weight:bold; font-style: italic; color:red;">Input file here</span>')
        movie = QMovie(gifPath)
        self.label_inputGif.setMovie(movie)
        movie.start()
        aniEffect = AnimationShadowEffect(QColor("purple"))
        self.label_inputText.setGraphicsEffect(aniEffect)
        # aniEffect.start()
        aniEffect = AnimationShadowEffect(QColor("purple"))
        self.label_inputGif.setGraphicsEffect(aniEffect)
        # self.label_inputGif.graphicsEffect().animation.stop()
        # aniEffect.start()


class WorkFlow(QDialog, Ui_WorkFlow, object):
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    progressSig = pyqtSignal(int)  # 控制进度条
    startButtonStatusSig = pyqtSignal(list)
    logGuiSig = pyqtSignal(str)
    uninstallPackageSig = pyqtSignal(list)
    '''
    保存设置：界面一开始，就把用户选择的设置，拷贝到temporary里面（拷贝前先清空temporary），然后把这个组作为当前组，用户的设置都保存在里面（checkbox以及各个程序的设置），
    如果用户要保存设置，按那个add按钮，然后把temporary的设置拷贝到用户指定的那个workflow。
    '''

    def __init__(
            self,
            workPath=None,
            clearFolderSig=None,
            focusSig=None,
            parent=None):
        super(WorkFlow, self).__init__(parent)
        self.parent = parent
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.clearFolderSig = clearFolderSig
        self.focusSig = focusSig
        self.interrupt = False
        self.setupUi(self)
        #初始化一下路径
        self.MAFFTpath = ""
        self.GBpath = ""
        self.IQpath = ""
        self.MBpath = ""
        self.trimAlpath = ""
        self.PFpath = ""
        self.Py27Path = ""
        self.MACSEpath = ""
        self.HmmCleanerpath = ""
        self.javaPath = ""
        self.perlPath = ""
        # 先初始化一个，后面可能会变
        self.flowchart_report_path = self.factory.creat_dir(self.workPath + os.sep + "Flowchart_reports")
        # 保存设置
        self.workflow_settings = QSettings(
            self.thisPath +
            '/settings/workflow_settings.ini',
            QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.workflow_settings.setFallbacksEnabled(False)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        ###software path
        settingPath = self.thisPath + '/settings/setting_settings.ini'
        self.settings_ini = QSettings(settingPath, QSettings.IniFormat)
        self.settings_ini.setFallbacksEnabled(False)
        ###export path
        self.dict_analyses = collections.OrderedDict([("MAFFT", ["queue", ":/picture/resourses/mafft1.png",
                                                                 ":/picture/resourses/117 down arrow.gif"]),
                                                      ("MACSE",
                                                       ["queue", ":/picture/resourses/M.png",
                                                        ":/picture/resourses/117 down arrow.gif"]),
                                                      ("Gblocks",
                                                       ["queue", ":/picture/resourses/if_simpline_22_2305632.png",
                                                        ":/picture/resourses/117 down arrow.gif"]),
                                                      ("trimAl",
                                                       ["queue", ":/picture/resourses/icon--trim-confirm-0.png",
                                                        ":/picture/resourses/117 down arrow.gif"]),
                                                      ("HmmCleaner",
                                                       ["queue", ":/picture/resourses/clean.png",
                                                        ":/picture/resourses/117 down arrow.gif"]),
                                                      ("Concatenation", ["queue", ":/picture/resourses/cat1.png",
                                                                         ":/picture/resourses/117 down arrow.gif"]),
                                                      ("ModelFinder",
                                                       ["queue", ":/picture/resourses/if_tinder_334781.png",
                                                        ":/picture/resourses/117 down arrow.gif"]),
                                                      ("PartitionFinder", ["queue", ":/picture/resourses/pie-chart.png",
                                                                           ":/picture/resourses/117 down arrow.gif"]),
                                                      (
                                                      "IQ-TREE", ["queue", ":/picture/resourses/data-taxonomy-icon.png",
                                                                  ":/picture/resourses/waiting.png"]),
                                                      ("MrBayes",
                                                       ["queue", ":/picture/resourses/2000px-Paris_RER_B_icon.svg.png",
                                                        ":/picture/resourses/waiting.png"])]
                                                     )
        self.wait_icon_path = ":/picture/resourses/waiting.png"
        # 恢复用户的设置
        self.first_analysis = "MAFFT"  ##后面删掉，初定义一个，避免报错
        self.guiRestore() #里面会重新打开那个settings
        self.exception_signal.connect(self.popupException)
        self.startButtonStatusSig.connect(self.factory.ctrl_startButton_status)
        self.connectCheckbox()
        self.comboBox.activated[str].connect(self.copySettings)
        self.comboBox.currentIndexChanged[str].connect(self.ctrl_combobox2)
        self.list_now_running = []
        self.hasInputs = False
        ## 恢复workflow的设置，不能放到guiRestore，因为要经常调用它
        text = self.workflow_settings.value("comboBox", "")
        self.workflow_settings.beginGroup('Workflow')
        # f = open(r"C:\Users\Administrator\Desktop\1.txt", "a", encoding="utf-8")
        # for key in self.workflow_settings.allKeys():
        #     value = self.workflow_settings.value(key)
        #     if type(value) == str:
        #         value = value.replace("\"", "\\\"")
        #         value = value.replace("\n", "\\\n")
        #         value = "\"" + value + "\""
        #     # value = value.replace("'", "\'")
        #     f.write("\"%s\": %s,\n"%(key, value))
        groups = sorted(self.workflow_settings.childGroups())
        self.workflow_settings.beginGroup('temporary')  ##temporary设置为当前设置，各种设置都保存到temporary里面
        if "temporary" in groups:
            groups.remove("temporary")
        if groups:
            model = self.comboBox.model()
            self.comboBox.clear()
            for num, i in enumerate(groups):
                item = QStandardItem(i)
                item.setToolTip(i)
                # 背景颜色
                if num % 2 == 0:
                    item.setBackground(QColor(255, 255, 255))
                else:
                    item.setBackground(QColor(237, 243, 254))
                model.appendRow(item)
            if type(text) == str and (text in groups):
                self.comboBox.setCurrentText(text)
        # 给开始按钮添加菜单
        menu = QMenu(self)
        menu.setToolTipsVisible(True)
        self.work_action = QAction(QIcon(":/picture/resourses/work.png"), "", menu)
        self.work_action.triggered.connect(lambda: self.factory.swithWorkPath(self.work_action, parent=self))
        self.dir_action = QAction(QIcon(":/picture/resourses/folder.png"), "Name: use the workflow name", menu)
        self.dir_action.triggered.connect(self.setFlowchartName)
        menu.addAction(self.work_action)
        menu.addAction(self.dir_action)
        self.pushButton.toolButton.setMenu(menu)
        self.pushButton.toolButton.menu().installEventFilter(self)
        self.factory.swithWorkPath(self.work_action, init=True, parent=self)  # 初始化一下
        ## brief demo
        country = self.factory.path_settings.value("country", "UK")
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#5-13-1-Brief-example" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#5-13-1-Brief-example"
        self.label_2.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        self.listWidget_workflow.itemDoubleClicked.connect(lambda itemwidget: self.listWidget_workflow.itemWidget(itemwidget).exe_window.exec_())
        widgets = (self.gridLayout.itemAt(i).widget() for i in range(self.gridLayout.count()))
        self.list_allcheckbox = [widget for widget in widgets if isinstance(widget, QCheckBox)]
        # windows删除HMMcleaner
        if platform.system().lower() in ["windows"]:
            self.checkBox_10.setHidden(True)
        # 判断插件安装与否
        self.finishPluginsChecked = False
        self.list_uninstalled_software = []
        self.uninstallPackageSig.connect(self.popupUninstall)
        # 必须放到最后执行
        # self.copySettings()  # 初始化一下
        QTimer.singleShot(1, self.copySettings)  # 初始化一下

    @pyqtSlot()
    def on_pushButton_clicked(self):
        """
        execute program
        """
        self.fetchRunSummary()

    @pyqtSlot()
    def on_pushButton_6_clicked(self):
        """
        Stop
        """
        if self.isRunning():
            if len(self.list_now_running) == 1 and self.list_now_running[0].softWare == "MrBayes":
                # 贝叶斯结束
                reply = QMessageBox.question(
                    self,
                    "Confirmation",
                    "<p style='line-height:25px; height:25px'>You decided to kill MrBayes (run), and infer the tree based on current generations?</p>",
                    QMessageBox.Yes,
                    QMessageBox.Cancel)
                if reply == QMessageBox.Yes:
                    try:
                        self.list_now_running[0].exe_window.viewResultsEarly()
                        self.dict_reports["MrBayes"] = self.list_now_running[0].exe_window.exportPath  # 得到输出文件夹的路径
                        self.report += " " + self.list_now_running[0].exe_window.description
                        self.reference_report += "\n" + self.list_now_running[0].exe_window.reference
                        self.list_now_running = []
                        self.task_stop()
                        return
                    except:
                        pass
                else:
                    return
            else:
                reply = QMessageBox.question(
                    self,
                    "Confirmation",
                    "<p style='line-height:25px; height:25px'>The flowchart is still running, terminate it?</p>",
                    QMessageBox.Yes,
                    QMessageBox.Cancel)
                if reply == QMessageBox.Yes:
                    try:
                        for running_widget in self.list_now_running:
                            running_widget.exe_window.on_pushButton_2_clicked()
                    except:
                        pass
                else:
                    return
            self.interrupt = True
            QMessageBox.information(
                self,
                "Flowchart",
                "<p style='line-height:25px; height:25px'>Program has been terminated!</p>")
            self.task_interrupt()

    @pyqtSlot()
    def on_toolButton_clicked(self):
        """
        add workflow
        """
        workflowName, ok = QInputDialog.getText(
            self, 'Create workflow', 'Workflow name:')
        if ok and workflowName:
            if workflowName in [self.comboBox.itemText(i) for i in range(self.comboBox.count())]:
                reply = QMessageBox.question(
                    self,
                    "Flowchart",
                    "<p style='line-height:25px; height:25px'>You decided to overwrite the existing \"%s\" with the current settings?</p>"%workflowName,
                    QMessageBox.Yes,
                    QMessageBox.No)
                if reply == QMessageBox.No:
                    return
            else:
                self.comboBox.addItem(workflowName)
            for widget in self.list_workflow_widgets:
                ##先保存一遍当前设置
                widget.exe_window.guiSave()
            ##保存checkbox的设置
            for name, obj in inspect.getmembers(self):
                if isinstance(obj, QCheckBox):
                    state = obj.isChecked()
                    self.workflow_settings.setValue(name, state)
            self.factory.settingsGroup2Group(self.thisPath + '/settings/workflow_settings.ini', "temporary", workflowName,
                                             baseGroup="Workflow")
            self.refreshComboColor()
            self.comboBox.setCurrentText(workflowName)

    @pyqtSlot()
    def on_toolButton_2_clicked(self):
        """
        delete workflow
        """
        currentWorkflow = self.comboBox.currentText()
        reply = QMessageBox.question(
            self,
            "Flowchart",
            "<p style='line-height:25px; height:25px'>You decided to remove the workflow \"%s\"?</p>"%currentWorkflow,
            QMessageBox.Yes,
            QMessageBox.No)
        if reply == QMessageBox.No:
            return
        qsettings = QSettings(self.thisPath + '/settings/workflow_settings.ini', QSettings.IniFormat)
        qsettings.setFallbacksEnabled(False)
        qsettings.beginGroup("Workflow")
        qsettings.beginGroup(currentWorkflow)
        qsettings.remove("")
        qsettings.endGroup()
        qsettings.endGroup()
        self.comboBox.removeItem(self.comboBox.currentIndex())
        self.refreshComboColor()
        self.copySettings()

    def exec_flowchart(self):
        # 主要靠exec_analysis来循环运行程序
        if self.hasInputs:
            self.flowchart_report_path = self.factory.creat_dir(self.workPath + os.sep + "Flowchart_reports")
            flowchart_name = self.dir_action.text()
            if flowchart_name == "Name: use the workflow name":
                self.flowchart_name = self.comboBox.currentText()
            else:
                self.flowchart_name = flowchart_name[6:]
            ##判断flowchart_name是否已经存在
            qsettings = QSettings(self.thisPath + '/settings/workflow_settings.ini', QSettings.IniFormat)
            qsettings.setFallbacksEnabled(False)
            qsettings.beginGroup("Flowchart results")
            qsettings.beginGroup(os.path.normpath(self.flowchart_report_path))
            list_flowchart_results = qsettings.allKeys()
            if self.flowchart_name in list_flowchart_results:
                reply = QMessageBox.question(
                    self,
                    "Flowchart",
                    "<p style='line-height:25px; height:25px'>A results named \"%s\" exists in %s, replace it?</p>" %
                    (self.flowchart_name, os.path.normpath(self.flowchart_report_path)),
                    QMessageBox.Yes,
                    QMessageBox.No)
                if reply == QMessageBox.Yes:
                    #删除已经存在的结果，删除时报错就忽略掉
                    self.parent.deleteFlowchartResults(self.flowchart_report_path, self.flowchart_name)
                else:
                    return
            self.interrupt = False
            self.time_start = datetime.datetime.now()
            self.task_start()
            self.dict_reports = OrderedDict()
            self.report = ""
            self.exe_time_count = ""
            self.reference_report = ""
            self.list_all_analyses = []
            self.list_tree_analyses = []
            self.list_now_running = []
            self.refreshWorkPath()  #刷新工作路径
            for i in self.list_workflow_widgets:
                ## 先把建树步骤剔出来
                if i.softWare in ["IQ-TREE", "MrBayes"]:
                    self.list_tree_analyses.append(i)
                self.list_all_analyses.append(i.softWare)
            self.MB_MF = True if ("ModelFinder" in self.list_all_analyses) and (
            "MrBayes" in self.list_all_analyses) else False
            if self.list_tree_analyses:
                for j in self.list_tree_analyses:
                    self.list_workflow_widgets.remove(j)
            self.exec_analysis(status="start")
        else:
            first_widget = self.listWidget_workflow.itemWidget(self.listWidget_workflow.item(0))
            if (self.first_analysis == "MACSE") and first_widget.exe_window.checkBox_2.isChecked():
                QMessageBox.critical(
                    self,
                    "MACSE",
                    "<p style='line-height:25px; height:25px'>Since you selected \"Refine\" in MACSE, you should input "
                    "files into the \"Refine\" box first!</p>")
            else:
                # MACSE有自己的提醒
                QMessageBox.critical(
                    self,
                    "FlowChart",
                    "<p style='line-height:25px; height:25px'>Please input files first!</p>")

    def guiSave(self):
        # Save geometry
        qsettings = QSettings(self.thisPath + '/settings/workflow_settings.ini', QSettings.IniFormat)
        qsettings.setFallbacksEnabled(False)
        qsettings.setValue('size', self.size())
        # qsettings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            # if isinstance(obj, QCheckBox):
            #     state = obj.isChecked()
            #     qsettings.setValue(name, state)
            if isinstance(obj, QComboBox):
                # save combobox selection to registry
                text = obj.currentText()
                qsettings.setValue(name, text)

    def guiRestore(self):

        # Restore geometry
        qsettings = QSettings(self.thisPath + '/settings/workflow_settings.ini', QSettings.IniFormat)
        qsettings.setFallbacksEnabled(False)
        self.resize(qsettings.value('size', QSize(645, 664)))
        self.factory.centerWindow(self)
        # self.move(qsettings.value('pos', QPoint(875, 254)))

        # for name, obj in inspect.getmembers(self):
        #     if isinstance(obj, QCheckBox):
        #         value = self.workflow_settings.value(
        #             name, "true")  # get stored value from registry
        #         obj.setChecked(
        #             self.factory.str2bool(value))  # restore checkbox
            # if isinstance(obj, QComboBox):
            #     self.workflow_settings.beginGroup('Workflow')
            #     groups = self.workflow_settings.childGroups()
            #     self.workflow_settings.endGroup()
            #     if "temporary" in groups:
            #         groups.remove("temporary")
            #     if groups:
            #         index = self.workflow_settings.value(name, "0")
            #         model = obj.model()
            #         obj.clear()
            #         for num, i in enumerate(groups):
            #             item = QStandardItem(i)
            #             # 背景颜色
            #             if num % 2 == 0:
            #                 item.setBackground(QColor(255, 255, 255))
            #             else:
            #                 item.setBackground(QColor(237, 243, 254))
            #             model.appendRow(item)
            #         obj.setCurrentIndex(int(index))

    def popupException(self, exception):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setText(
            'The program encountered an unforeseen problem, please report the bug at <a href="https://github.com/dongzhang0725/PhyloSuite/issues">https://github.com/dongzhang0725/PhyloSuite/issues</a> or send an email with the detailed traceback to dongzhang0725@gmail.com')
        msg.setWindowTitle("Error")
        msg.setDetailedText(exception)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def closeEvent(self, event):
        self.guiSave()
        if self.isRunning():
            reply = QMessageBox.question(
                self,
                "Workflow",
                "<p style='line-height:25px; height:25px'>The program is still running, terminate it?</p>",
                QMessageBox.Yes,
                QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.interrupt = True
                for running_widget in self.list_now_running:
                    running_widget.exe_window.on_pushButton_2_clicked()
            else:
                event.ignore()

    def refreshAnalyses(self):
        ##如果check有，而list里面没有，就增加；
        self.listWidget_workflow.clear()
        self.judgePlugins()
        self.list_checked_Box_text = self.fetch_checked_Box_texts()  #里面初始化各个软件的路径
        num = 0
        # print("refresh")
        get_first_analysis = False
        self.list_workflow_widgets = []
        for analysis in self.dict_analyses:
            if analysis in self.list_checked_Box_text:
                if not get_first_analysis:
                    self.first_analysis = analysis
                    get_first_analysis = True
                # Create QCustomQWidget
                self.myQCustomQWidget = QCustomQWidget(self)
                self.myQCustomQWidget.setSoftwareText(analysis)
                self.myQCustomQWidget.setStatusText(self.dict_analyses[analysis][0])
                self.myQCustomQWidget.setSoftwareIcon(self.dict_analyses[analysis][1])
                self.myQCustomQWidget.setStatusIcon(self.dict_analyses[analysis][2])
                # self.myQCustomQWidget.setPopupExport(self.dict_analyses[analysis][3])
                self.myQCustomQWidget.pushButton_edit.clicked.connect(self.popupWindCloseInfo)
                exe_window = self.assign_exe(self.myQCustomQWidget)
                exe_window.workflow_finished.connect(self.exec_analysis)
                exe_window.ui_closeSig.connect(self.judgeInputs)
                exe_window.setWindowFlags(exe_window.windowFlags() | Qt.WindowMinMaxButtonsHint)
                exec("self.%s_exe = exe_window"%analysis.replace("-", "_"))
                self.myQCustomQWidget.setExeWindow(exe_window)
                if analysis == self.first_analysis:
                    self.myQCustomQWidget.setInputState(":/picture/resourses/import.gif")
                    self.myQCustomQWidget.label_inputText.clicked.connect(self.popupWindCloseInfo)
                    self.myQCustomQWidget.label_inputText.clicked.connect(self.myQCustomQWidget.exe_window.exec_)
                # Create QListWidgetItem
                myQListWidgetItem = QListWidgetItem(self.listWidget_workflow)
                # 背景颜色
                if num % 2 == 0:
                    myQListWidgetItem.setBackground(QColor(255, 255, 255))
                else:
                    myQListWidgetItem.setBackground(QColor(237, 243, 254))
                # Set size hint
                myQListWidgetItem.setSizeHint(self.myQCustomQWidget.sizeHint())
                # Add QListWidgetItem into QListWidget
                self.listWidget_workflow.addItem(myQListWidgetItem)
                self.listWidget_workflow.setItemWidget(myQListWidgetItem, self.myQCustomQWidget)
                self.list_workflow_widgets.append(self.myQCustomQWidget)
                num += 1
        if self.list_workflow_widgets:
            self.list_workflow_widgets[-1].setStatusIcon(self.wait_icon_path)
        # WorkThread(self.addExe2widgets, parent=self).start()

    def get_inputs(self, software_widget):
        exportPath = software_widget.exe_window.exportPath
        if software_widget.softWare == "MAFFT":
            return glob.glob(exportPath + os.sep + "*_mafft.[!log]*")
            # [exportPath + os.sep + i for i in os.listdir(exportPath) if (i not in ["summary and citation.txt", "removed_seqs", "summary.txt"]) and (not re.search(r"^PhyloSuite\w+\.log$", i))]
        elif software_widget.softWare == "MACSE":
            return glob.glob(exportPath + os.sep + "*_NT_removed_chars.*")
        elif software_widget.softWare == "Gblocks":
            return [exportPath + os.sep + i for i in os.listdir(exportPath) if os.path.splitext(i)[1].upper() == ".FASTA" and os.path.splitext(i)[0].endswith("_gb")]
        elif software_widget.softWare == "trimAl":
            return glob.glob(exportPath + os.sep + "*_trimAl.*")
        elif software_widget.softWare == "HmmCleaner":
            return glob.glob(exportPath + os.sep + "*_hmm.fasta")
        elif software_widget.softWare == "Concatenation":
            # phy格式的文件和partition.txt
            return [exportPath + os.sep + i for i in os.listdir(exportPath) if os.path.splitext(i)[1].upper() in [".PHY", ".TXT"]]
        elif software_widget.softWare == "ModelFinder":
            return [exportPath + os.sep + i for i in os.listdir(exportPath) if os.path.splitext(i)[1].upper() in [".PHY", ".PHYLIP", ".FAS", ".FASTA", ".NEX", ".NEXUS", ".NXS", ".ALN", ".IQTREE"]]
        elif software_widget.softWare == "PartitionFinder":
            return [exportPath + os.sep + i for i in os.listdir(exportPath) if os.path.splitext(i)[1].upper() in [".PHY", ".PHYLIP"]] + [exportPath + os.sep + os.path.join("analysis", "best_scheme.txt")]

    def assign_exe(self, software_widget):
        if software_widget.softWare == "MAFFT":
            mafft = Mafft(workPath=self.flowchart_report_path, mafft_exe=self.MAFFTpath, clearFolderSig=self.clearFolderSig, workflow=True, parent=self.parent)
            mafft.comboBox_4.clear()
            if self.first_analysis != "MAFFT":
                mafft.label_4.setEnabled(False)
                mafft.comboBox_4.setEnabled(False)
                mafft.comboBox_4.lineEdit().switchColor() #让它变成灰色
                mafft.pushButton_3.setEnabled(False)
            mafft.pushButton.setEnabled(False)
            mafft.pushButton_2.setEnabled(False)
            self.mafft_progressBar = software_widget.progressBar
            mafft.workflow_progress.connect(self.mafft_progress)
            return mafft
        elif software_widget.softWare == "MACSE":
            macse = MACSE(workPath=self.flowchart_report_path, macseEXE=self.MACSEpath,
                          java=self.javaPath, workflow=True, parent=self.parent)
            macse.comboBox_4.clear()
            macse.comboBox_5.clear()
            if self.first_analysis != "MACSE":
                macse.label_4.setEnabled(False)
                macse.comboBox_4.setEnabled(False)
                macse.comboBox_4.lineEdit().switchColor() #让它变成灰色
                macse.pushButton_3.setEnabled(False)
                macse.label_8.setEnabled(False)
                macse.comboBox_5.setEnabled(False)
                macse.comboBox_5.lineEdit().switchColor()  # 让它变成灰色
                macse.pushButton_4.setEnabled(False)
                macse.checkBox_2.setChecked(True) # 切换为refine模式，因为第一个是MAFFT
            macse.pushButton.setEnabled(False)
            macse.pushButton_2.setEnabled(False)
            self.MACSE_progressBar = software_widget.progressBar
            macse.workflow_progress.connect(self.MACSE_progress)
            return macse
        elif software_widget.softWare == "Gblocks":
            gblocks = Gblocks(workPath=self.flowchart_report_path, gb_exe=self.GBpath, workflow=True, parent=self.parent)
            gblocks.comboBox_4.clear()
            if self.first_analysis != "Gblocks":
                gblocks.label_4.setEnabled(False)
                gblocks.comboBox_4.setEnabled(False)
                gblocks.comboBox_4.lineEdit().switchColor() #让它变成灰色
                gblocks.pushButton_3.setEnabled(False)
            gblocks.pushButton.setEnabled(False)
            gblocks.pushButton_2.setEnabled(False)
            self.gblocks_progressBar = software_widget.progressBar
            gblocks.workflow_progress.connect(self.gblocks_progress)
            return gblocks
        elif software_widget.softWare == "trimAl":
            trimAl = TrimAl(workPath=self.flowchart_report_path, TApath=self.trimAlpath, workflow=True, parent=self.parent)
            trimAl.comboBox_4.clear()
            if self.first_analysis != "trimAl":
                trimAl.radioButton.setEnabled(False)
                trimAl.comboBox_4.setEnabled(False)
                trimAl.comboBox_4.lineEdit().switchColor() #让它变成灰色
                trimAl.pushButton_3.setEnabled(False)
                trimAl.radioButton_2.setEnabled(False)
                trimAl.lineEdit_2.setEnabled(False)
                trimAl.pushButton_4.setEnabled(False)
            else:
                ## 灰掉compare set
                trimAl.radioButton_2.setEnabled(False)
                trimAl.lineEdit_2.setEnabled(False)
                trimAl.pushButton_4.setEnabled(False)
            trimAl.pushButton.setEnabled(False)
            trimAl.pushButton_2.setEnabled(False)
            trimAl.comboBox.setCurrentIndex(0)
            trimAl.comboBox.setEnabled(False)
            self.trimAl_progressBar = software_widget.progressBar
            trimAl.workflow_progress.connect(self.trimAl_progress)
            return trimAl
        elif software_widget.softWare == "HmmCleaner":
            hmmCleaner = HmmCleaner(workPath=self.flowchart_report_path, HmmCleanerPath=self.HmmCleanerpath, perl=self.perlPath,
                                    workflow=True, parent=self.parent)
            hmmCleaner.comboBox_4.clear()
            if self.first_analysis != "HmmCleaner":
                hmmCleaner.label_4.setEnabled(False)
                hmmCleaner.comboBox_4.setEnabled(False)
                hmmCleaner.comboBox_4.lineEdit().switchColor() #让它变成灰色
                hmmCleaner.pushButton_3.setEnabled(False)
            hmmCleaner.pushButton.setEnabled(False)
            hmmCleaner.pushButton_2.setEnabled(False)
            hmmCleaner.checkBox_4.setChecked(False)
            hmmCleaner.checkBox_4.setEnabled(False)
            hmmCleaner.checkBox_3.setChecked(False)
            hmmCleaner.checkBox_3.setEnabled(False)
            self.HmmCleaner_progressBar = software_widget.progressBar
            hmmCleaner.workflow_progress.connect(self.HmmCleaner_progress)
            return hmmCleaner
        elif software_widget.softWare == "Concatenation":
            matrix = Matrix(workPath=self.flowchart_report_path, workflow=True, parent=self.parent)
            matrix.comboBox_4.clear()
            if self.first_analysis != "Concatenation":
                matrix.label_4.setEnabled(False)
                matrix.comboBox_4.setEnabled(False)
                matrix.comboBox_4.lineEdit().switchColor()  # 让它变成灰色
                matrix.pushButton_3.setEnabled(False)
            matrix.pushButton.setEnabled(False)
            matrix.pushButton_2.setEnabled(False)
            self.matrix_progressBar = software_widget.progressBar
            matrix.workflow_progress.connect(self.matrix_progress)
            return matrix
        elif software_widget.softWare == "ModelFinder":
            modelfinder = ModelFinder(workPath=self.flowchart_report_path, IQ_exe=self.IQpath, workflow=True, parent=self.parent)
            if self.first_analysis != "ModelFinder":
                modelfinder.label_5.setEnabled(False)
                modelfinder.label_8.setEnabled(False)
                modelfinder.lineEdit.clear()
                modelfinder.lineEdit.setEnabled(False)
                modelfinder.lineEdit_2.clear()
                modelfinder.lineEdit_2.setEnabled(False)
                modelfinder.textEdit.clear()
                # modelfinder.lineEdit_3.setEnabled(False)
                modelfinder.pushButton_3.setEnabled(False)
                modelfinder.pushButton_continue.setEnabled(False)
                modelfinder.pushButton_4.setEnabled(False)
                # modelfinder.pushButton_22.setEnabled(False)
            modelfinder.pushButton.setEnabled(False)
            modelfinder.pushButton_2.setEnabled(False)
            self.modelfinder_progressBar = software_widget.progressBar
            modelfinder.workflow_progress.connect(self.modelfinder_progress)
            return modelfinder
        elif software_widget.softWare == "PartitionFinder":
            partitionFinder = PartitionFinder(workPath=self.flowchart_report_path,
                                              partitionFinderFolder=self.PFpath,
                                              pythonEXE=self.Py27Path, workflow=True,
                                              parent=self.parent)
            if self.first_analysis != "PartitionFinder":
                partitionFinder.label_4.setEnabled(False)
                partitionFinder.label_6.setEnabled(False)
                partitionFinder.lineEdit.clear()
                partitionFinder.lineEdit.setEnabled(False)
                partitionFinder.lineEdit_2.clear()
                partitionFinder.lineEdit_2.setEnabled(False)
                partitionFinder.pushButton_3.setEnabled(False)
                partitionFinder.pushButton_4.setEnabled(False)
            partitionFinder.pushButton_7.setEnabled(False)
            partitionFinder.pushButton_8.setEnabled(False)
            partitionFinder.pushButton_5.setEnabled(False)
            partitionFinder.pushButton_2.setEnabled(False)
            self.partitionFinder_progressBar = software_widget.progressBar
            partitionFinder.workflow_progress.connect(self.partitionFinder_progress)
            return partitionFinder
        elif software_widget.softWare == "IQ-TREE":
            self.iqtree = IQTREE(workPath=self.flowchart_report_path, IQ_exe=self.IQpath, workflow=True, parent=self.parent)
            self.iqtree.label_5.setEnabled(False)
            self.iqtree.comboBox_11.refreshInputs([])
            self.iqtree.comboBox_11.setEnabled(False)
            self.iqtree.comboBox_11.lineEdit().switchColor()
            self.iqtree.lineEdit_3.clear()
            self.iqtree.lineEdit_3.setEnabled(False)
            self.iqtree.pushButton.setEnabled(False)
            self.iqtree.pushButton_2.setEnabled(False)
            self.iqtree.pushButton_3.setEnabled(False)
            self.iqtree.pushButton_22.setEnabled(False)
            self.iqtree.pushButton_continue.setEnabled(False)
            self.iqtree_progressBar = software_widget.progressBar
            self.iqtree.workflow_progress.connect(self.iqtree_progress)
            return self.iqtree
        elif software_widget.softWare == "MrBayes":
            self.mrbayes = MrBayes(workPath=self.flowchart_report_path, MB_exe=self.MBpath, workflow=True, parent=self.parent)
            self.mrbayes.label_5.setEnabled(False)
            self.mrbayes.lineEdit.clear()
            self.mrbayes.lineEdit.setEnabled(False)
            self.mrbayes.comboBox_5.setEnabled(False)
            self.mrbayes.pushButton.setEnabled(False)
            self.mrbayes.pushButton_2.setEnabled(False)
            self.mrbayes.pushButton_10.setEnabled(False)
            self.mrbayes.pushButton_continue.setEnabled(False)
            self.mrbayes.pushButton_3.setEnabled(False)
            self.mrbayes_progressBar = software_widget.progressBar
            self.mrbayes.workflow_progress.connect(self.mrbayes_progress)
            return self.mrbayes

    def mafft_progress(self, value):
        oldValue = self.mafft_progressBar.value()
        done_int = int(value)
        if done_int > oldValue:
            self.mafft_progressBar.setProperty("value", done_int)
            QCoreApplication.processEvents()

    def gblocks_progress(self, value):
        oldValue = self.gblocks_progressBar.value()
        done_int = int(value)
        if done_int > oldValue:
            self.gblocks_progressBar.setProperty("value", done_int)
            QCoreApplication.processEvents()

    def matrix_progress(self, value):
        oldValue = self.matrix_progressBar.value()
        done_int = int(value)
        if done_int > oldValue:
            self.matrix_progressBar.setProperty("value", done_int)
            QCoreApplication.processEvents()

    def modelfinder_progress(self, value):
        oldValue = self.modelfinder_progressBar.value()
        done_int = int(value)
        if done_int > oldValue:
            self.modelfinder_progressBar.setProperty("value", done_int)
            QCoreApplication.processEvents()

    def partitionFinder_progress(self, value):
        oldValue = self.partitionFinder_progressBar.value()
        done_int = int(value)
        if done_int > oldValue:
            self.partitionFinder_progressBar.setProperty("value", done_int)
            QCoreApplication.processEvents()

    def iqtree_progress(self, value):
        oldValue = self.iqtree_progressBar.value()
        done_int = int(value)
        if done_int > oldValue:
            self.iqtree_progressBar.setProperty("value", done_int)
            QCoreApplication.processEvents()

    def mrbayes_progress(self, value):
        oldValue = self.mrbayes_progressBar.value()
        done_int = int(value)
        if done_int > oldValue:
            self.mrbayes_progressBar.setProperty("value", done_int)
            QCoreApplication.processEvents()

    def MACSE_progress(self, value):
        oldValue = self.MACSE_progressBar.value()
        done_int = int(value)
        if done_int > oldValue:
            self.MACSE_progressBar.setProperty("value", done_int)
            QCoreApplication.processEvents()

    def trimAl_progress(self, value):
        oldValue = self.trimAl_progressBar.value()
        done_int = int(value)
        if done_int > oldValue:
            self.trimAl_progressBar.setProperty("value", done_int)
            QCoreApplication.processEvents()

    def HmmCleaner_progress(self, value):
        oldValue = self.HmmCleaner_progressBar.value()
        done_int = int(value)
        if done_int > oldValue:
            self.HmmCleaner_progressBar.setProperty("value", done_int)
            QCoreApplication.processEvents()

    def task_start(self):
        for i in [self.checkBox, self.checkBox_2, self.checkBox_3,
                  self.checkBox_4, self.checkBox_5, self.checkBox_6,
                  self.checkBox_7, self.checkBox_8, self.checkBox_9, self.checkBox_10]:
            i.setEnabled(False)
        self.pushButton.setEnabled(False)  # 使之失效
        self.pushButton.setStyleSheet(
            'QPushButton {color: red; background-color: rgb(219, 217, 217)}')
        self.pushButton.setText("Running...")

    def task_stop(self):
        time_end = datetime.datetime.now()
        self.time_used_des = "Flowchart start at: %s\nFlowchart finish at: %s\nTotal time used for Flowchart: %s\n" % (
                                                                                    str(self.time_start), str(time_end),
                                                                                    str(time_end - self.time_start))
        QMessageBox.information(
            self,
            "Flowchart",
            "<p style='line-height:25px; height:25px'>All the tasks finished!</p>")
        all_softwares = re.findall(r"MAFFT|Gblocks|ModelFinder|PartitionFinder2|MrBayes 3\.2\.6|IQ-TREE|MACSE v. 2.03|trimAl|HmmCleaner", self.report)
        for i in all_softwares:
            self.report = self.report.replace(i, "<font style='font-weight:bold; color:red;'>" + i + "</font>")
        report_html = '''<html>
<head>
<meta http-equiv=content-type content=text/html;charset=ISO-8859-1>
</head>
<body>
<div><span style="color:red; font-weight:bold;">PhyloSuite</span> (Zhang et al., 2020) was used to conduct, manage and streamline the analyses with the help of several plug-in programs: <br> ''' + self.report.replace("\n", "<br>") + "<br><br><font style='font-weight:bold; font-size:18px'>References</font>" + \
  "<br>Zhang, D., F. Gao, I. Jakovlić, H. Zou, J. Zhang, W.X. Li, and G.T. Wang, PhyloSuite: An integrated and scalable" \
  " desktop platform for streamlined molecular sequence data management and evolutionary phylogenetics studies. Molecular " \
  "Ecology Resources, 2020. 20(1): p. 348–355. DOI: 10.1111/1755-0998.13096." + self.reference_report.replace("\n", "<br>") + "<br><br>" + self.time_used_des.replace("\n", "<br>") + self.exe_time_count.replace("\n", "<br>") + "<br>" + '''</div>
</body>
</html>'''
        self.dict_reports["reports"] = report_html
        self.dict_reports["time"] = datetime.datetime.now()
        # self.reportSig.emit(self.dict_reports)
        qsettings = QSettings(self.thisPath + '/settings/workflow_settings.ini', QSettings.IniFormat)
        qsettings.setFallbacksEnabled(False)
        qsettings.beginGroup("Flowchart results")
        qsettings.beginGroup(os.path.normpath(self.flowchart_report_path))
        qsettings.setValue(self.flowchart_name, self.dict_reports)
        self.close()
        self.focusSig.emit(self.flowchart_report_path)

    def task_interrupt(self):
        self.list_now_running = []
        self.refreshAnalyses()
        ##恢复开始button
        self.pushButton.setEnabled(True)
        self.pushButton.setStyleSheet(self.qss_file)
        self.pushButton.setText("Check | Start")
        for i in [self.checkBox, self.checkBox_2, self.checkBox_3,
                  self.checkBox_4, self.checkBox_5, self.checkBox_6,
                  self.checkBox_7, self.checkBox_8, self.checkBox_9, self.checkBox_10]:
            i.setEnabled(True)

    def exec_analysis(self, status="start", final_analysis=None):
        if self.interrupt:
            return
        if status == "start":
            # 这是开始非建树程序的位置
            self.inputs_from_last = None
            self.last_analysis = self.list_workflow_widgets.pop(0)
            self.exec_program(self.last_analysis, self.inputs_from_last) #第一个软件不需要导入输入文件
        elif status == "finished":
            # 这是非建树程序结束的位置
            self.inputs_from_last = self.get_inputs(self.last_analysis) #得到下一个分析需要的输入文件
            self.last_analysis.setStatusIcon(":/picture/resourses/true.png")
            self.last_analysis.setStatusText("finished")
            self.last_analysis.pushbutton_view.setEnabled(True)
            self.list_now_running.remove(self.last_analysis) # 删除完成的分析
            if self.last_analysis.exe_window.description:
                self.report += " " + self.last_analysis.exe_window.description
            if self.last_analysis.exe_window.reference:
                self.reference_report += "\n" + self.last_analysis.exe_window.reference
            self.exe_time_count += "Time used for %s: %s\n"%(self.last_analysis.softWare,
                                                             self.last_analysis.exe_window.time_used)
            self.dict_reports[self.last_analysis.softWare] = self.last_analysis.exe_window.exportPath #得到输出文件夹的路径
            self.last_analysis.setPopupExport(self.last_analysis.exe_window.exportPath)
            if not self.list_workflow_widgets:
                ## 非建树分析结束
                self.ifFinished()
                return
            self.last_analysis = self.list_workflow_widgets.pop(0)
            self.exec_program(self.last_analysis, self.inputs_from_last)
        ##建树的分析
        elif status == "final analysis":
            # 这是开始建树程序的位置
            # self.list_now_running.append(self.last_analysis)  # 添加当前进行的分析
            self.exec_program(final_analysis, self.inputs_from_last)
        ##最后2个程序结束得指明是谁结束，这2个是建树程序结束的位置
        elif status == "IQ-TREE finished":
            self.iqtree_ItemWidget.setStatusIcon(":/picture/resourses/true.png")
            self.iqtree_ItemWidget.setStatusText("finished")
            self.iqtree_ItemWidget.pushbutton_view.setEnabled(True)
            self.list_now_running.remove(self.iqtree_ItemWidget)  # 删除完成的分析
            if self.iqtree_ItemWidget.exe_window.description:
                self.report += " " + self.iqtree_ItemWidget.exe_window.description
            if self.iqtree_ItemWidget.exe_window.reference:
                self.reference_report += "\n" + self.iqtree_ItemWidget.exe_window.reference
            self.exe_time_count += "Time used for %s: %s\n" % (
            self.iqtree_ItemWidget.softWare, self.iqtree_ItemWidget.exe_window.time_used)
            self.dict_reports[self.iqtree_ItemWidget.softWare] = self.iqtree_ItemWidget.exe_window.exportPath  # 得到输出文件夹的路径
            self.iqtree_ItemWidget.setPopupExport(self.iqtree_ItemWidget.exe_window.exportPath)
            self.ifFinished()
        elif status == "MrBayes finished":
            self.mrbayes_ItemWidget.setStatusIcon(":/picture/resourses/true.png")
            self.mrbayes_ItemWidget.setStatusText("finished")
            self.mrbayes_ItemWidget.pushbutton_view.setEnabled(True)
            self.list_now_running.remove(self.mrbayes_ItemWidget)  # 删除完成的分析
            if self.mrbayes_ItemWidget.exe_window.description:
                self.report += " " + self.mrbayes_ItemWidget.exe_window.description
            if self.mrbayes_ItemWidget.exe_window.reference:
                self.reference_report += "\n" + self.mrbayes_ItemWidget.exe_window.reference
            self.exe_time_count += "Time used for %s: %s\n" % (
            self.mrbayes_ItemWidget.softWare, self.mrbayes_ItemWidget.exe_window.time_used)
            self.dict_reports[
                self.mrbayes_ItemWidget.softWare] = self.mrbayes_ItemWidget.exe_window.exportPath  # 得到输出文件夹的路径
            self.mrbayes_ItemWidget.setPopupExport(self.mrbayes_ItemWidget.exe_window.exportPath)
            self.ifFinished()
        # print(self.list_now_running)

    def exec_program(self, software_widget, inputs):
        #输入文件为一些列表，然后自己取出需要的东西
        software_widget.setStatusGif(":/picture/resourses/running.gif")
        software_widget.setStatusText("running...")
        self.list_now_running.append(software_widget)  # 添加当前进行的分析
        # print(software_widget.softWare, software_widget, self.list_now_running)
        if software_widget.softWare == "MAFFT":
            if inputs:
                software_widget.exe_window.workflow_input(inputs)
            software_widget.exe_window.on_pushButton_clicked()
        elif software_widget.softWare == "MACSE":
            if inputs:
                if self.first_analysis != "MACSE":
                    # 证明第一个是MAFFT，需要MACSE来refine;如果是第一个程序，那么inputs就是none，要从用户导入的文件来运行
                    software_widget.exe_window.checkBox_2.setChecked(True)
                    software_widget.exe_window.input(software_widget.exe_window.comboBox_7, inputs)
            software_widget.exe_window.on_pushButton_clicked()
        elif software_widget.softWare == "Gblocks":
            if inputs:
                software_widget.exe_window.input(inputs)
            software_widget.exe_window.on_pushButton_clicked()
        elif software_widget.softWare == "trimAl":
            if inputs:
                software_widget.exe_window.input(inputs)
            software_widget.exe_window.on_pushButton_clicked()
        elif software_widget.softWare == "HmmCleaner":
            if inputs:
                software_widget.exe_window.input(inputs)
            software_widget.exe_window.on_pushButton_clicked()
        elif software_widget.softWare == "Concatenation":
            # if "ModelFinder" in self.list_all_analyses:
            #     ModelFinder_widgets = [self.listWidget_workflow.itemWidget(self.listWidget_workflow.item(i)) for i in
            #                     range(self.listWidget_workflow.count()) if self.listWidget_workflow.itemWidget(self.listWidget_workflow.item(i)).softWare == "ModelFinder"][0]
            #     part_is_checked = ModelFinder_widgets.exe_window.checkBox.isChecked()
            # else:
            #     part_is_checked = False
            # if ("PartitionFinder" in self.list_all_analyses) or part_is_checked:
            #     # 如果有partitionFinder,就必须生成partition文件
            #     software_widget.exe_window.checkBox_11.setChecked(True)
            if inputs:
                software_widget.exe_window.input(inputs)
            software_widget.exe_window.on_pushButton_clicked()
        elif software_widget.softWare == "ModelFinder":
            if inputs:
                ## 如果不是第一个程序，这一步是必来自concatenation的结果
                list_phy = [i for i in inputs if os.path.splitext(i)[1].upper() in [".PHY", ".PHYLIP"]]
                phy = list_phy[0] if list_phy else None
                list_partition = [i for i in inputs if "partition.txt" in i]
                partition = list_partition[0] if list_partition else None
                software_widget.exe_window.workflow_input(MSA=phy, partition=partition)
            if self.MB_MF:
                software_widget.exe_window.comboBox_5.setCurrentIndex(1)
                software_widget.exe_window.comboBox_5.setEnabled(False)
            software_widget.exe_window.on_pushButton_clicked()
        elif software_widget.softWare == "PartitionFinder":
            if inputs:
                ## 如果不是第一个程序，这一步是必来自concatenation的结果
                list_phy = [i for i in inputs if os.path.splitext(i)[1].upper() in [".PHY", ".PHYLIP"]]
                phy = list_phy[0] if list_phy else None
                list_partition = [i for i in inputs if "partition.txt" in i]
                partition = list_partition[0] if list_partition else None
                software_widget.exe_window.workflow_input(MSA=phy, partition=partition)
            software_widget.exe_window.on_pushButton_5_clicked()
        elif software_widget.softWare == "IQ-TREE":
            list_msa = []
            model = ["", None]
            mf_part_model = None
            for i in inputs:
                if "best_scheme.nex" in i:
                    mf_part_model = i
                elif os.path.splitext(i)[1].upper() in [".PHY", ".PHYLIP", ".FAS", ".FASTA", ".NEX", ".NEXUS", ".NXS", ".ALN"]:
                    list_msa.append(i)
                elif os.path.splitext(i)[1].upper() == ".IQTREE":
                    model = ["MB_normal", i]
                elif "best_scheme.txt" in i:
                    model = ["PF", i]
            # model_software = "partitionfinder" if "best_scheme.txt" in model else "modelfinder"
            ## 如果MB_MF和mf_part_model都有，model=[None, mf_part_model], 如果MB_MF，model=[model,""]，如果mf_part_model，model=[model,mf_part_model]
            # model = [None, ""] if self.MB_MF else model  #如果贝叶斯和modelfinder都被选上了，就用IQ-TREE的自动选模型
            if mf_part_model and self.MB_MF:
                ##model要选auto,而且也要导入partition文件, auto在ifFinished里面选好了
                model = ["MB_MF_part", mf_part_model]
            elif mf_part_model:
                ##直接把mf_part_model的模型导入即可
                model = ["mf_part_model", mf_part_model]
            elif self.MB_MF:
                ##model要选auto
                model = ["MB_MF", None]
            else:
                ##普通模型
                model = model
            software_widget.exe_window.workflow_input(MSA=[list_msa[0]], model_file=model)
            software_widget.exe_window.on_pushButton_clicked()
        elif software_widget.softWare == "MrBayes":
            list_msa = []
            model = None
            mf_part_model = None
            for i in inputs:
                if "best_scheme.nex" in i:
                    mf_part_model = i
                elif os.path.splitext(i)[1].upper() in [".PHY", ".PHYLIP", ".FAS", ".FASTA", ".NEX", ".NEXUS", ".NXS", ".ALN"]:
                    list_msa.append(i)
                elif os.path.splitext(i)[1].upper() == ".IQTREE":
                    model = i
                elif "best_scheme.txt" in i:
                    model = i
            model_software = "partitionfinder" if "best_scheme.txt" in i else "modelfinder"
            if list_msa:
                #转格式
                convertfmt = Convertfmt(**{"export_path": os.path.dirname(list_msa[0]), "files": [list_msa[0]], "export_nexi": True})
                convertfmt.exec_()
                input_MSA = convertfmt.f3
            if "best_scheme.txt" in model:
                ###partitionfinder
                rgx_blk = re.compile(r"(?si)begin mrbayes;(.+)end;")
                f = self.factory.read_file(model)
                scheme = f.read()
                f.close()
                input_model = rgx_blk.search(scheme).group(1).strip().replace("\t", "")
            else:
                ###modelfinder
                if not mf_part_model:
                    f = self.factory.read_file(model)
                    model_content = f.read()
                    f.close()
                    rgx_model = re.compile(r"Best-fit model according to.+?\: (.+)")
                    input_model = rgx_model.search(model_content).group(1)
                else:
                    f = self.factory.read_file(mf_part_model)
                    input_model = f.read()
            software_widget.exe_window.workflow_input(input_MSA=input_MSA, model=input_model)
            software_widget.exe_window.on_pushButton_clicked(workflow=True)

    def ifFinished(self):
        list_widgets = [self.listWidget_workflow.itemWidget(self.listWidget_workflow.item(i)) for i in
                        range(self.listWidget_workflow.count())]
        if self.list_tree_analyses:
            ##如果有建树分析，先执行建树分析
            for tree_analysis in self.list_tree_analyses:
                if tree_analysis.softWare == "IQ-TREE":
                    self.iqtree_ItemWidget = tree_analysis
                    if self.MB_MF and tree_analysis.exe_window.comboBox_7.currentIndex != 0:  #如果是贝叶斯和modelfinder都选上了
                        tree_analysis.exe_window.comboBox_7.setCurrentIndex(0)  #设为auto模式
                elif tree_analysis.softWare == "MrBayes":
                    self.mrbayes_ItemWidget = tree_analysis
                self.exec_analysis(status="final analysis", final_analysis=tree_analysis)
            self.list_tree_analyses = None  #执行以后要删掉，不然下次执行会陷入死循环
            return
        list_status = [j.status for j in list_widgets]
        if ("queue" in list_status) or ("running..." in list_status):
            return
        else:
            self.task_stop()

    def isRunning(self):
        if self.list_now_running:
            return True
        else:
            return False

    def fetchRunSummary(self):
        self.popupSummary = self.popUpSummary()
        self.dict_analy_summary = OrderedDict()
        settings = '''<html>
                    <head>
                    <style type=text/css>
                    .title {color: white; background-color: gray; font-size:12pt;}
                    body {font-size:10pt;}
                    </style>
                    </head>
                    <body>
                    <div>'''
        for widget in self.list_workflow_widgets:
            analysis = widget.softWare
            software = widget.exe_window
            summary = software.fetchWorkflowSetting()
            self.dict_analy_summary[analysis] = summary
            settings += summary
        #检查
        check_results = self.checkSettings()
        check_results = '<p class="title">Parameter check</p>' + check_results if check_results else \
            '<p class="title">Parameter check</p><span style="font-weight:600; color:green;">All parameters are valid!</span>'
        settings += check_results + '</div></body></html>'
        # print(settings)
        self.popupSummary.textBrowser.setHtml(settings)
        self.popupSummary.textBrowser.anchorClicked.connect(self.exec_link)
        self.popupSummary.exec_()

    def updateRunSummary(self, analysis, analysisSummary):
        if self.dehighlghtWidget:
            exec(self.dehighlghtWidget) ##取消控件闪烁
        if hasattr(self, "popupSummary") and hasattr(self, "dict_analy_summary"):
            if (analysis in self.dict_analy_summary) and (analysisSummary != self.dict_analy_summary[analysis]):
                self.dict_analy_summary[analysis] = analysisSummary
                settings = '''<html>
                            <head>
                            <style type=text/css>
                            .title {color: white; background-color: gray; font-size:11pt;}
                            </style>
                            </head>
                            <body>
                            <div>'''
                # 检查
                check_results = self.checkSettings()
                check_results = '<p class="title">Parameter check</p>' + check_results if check_results else \
                    '<p class="title">Parameter check</p><span style="font-weight:600; color:green;">All parameters are valid!</span>'
                settings += "".join(list(self.dict_analy_summary.values())) + \
                            check_results + '</div></body></html>'
                self.popupSummary.textBrowser.setHtml(settings)
        if hasattr(self, "last_position"):
            self.popupSummary.textBrowser.verticalScrollBar().setValue(self.last_position)

    def refreshRunSummary(self):
        #自动校正过后刷新
        if hasattr(self, "popupSummary"):
            self.dict_analy_summary = OrderedDict()
            settings = '''<html>
                        <head>
                        <style type=text/css>
                        .title {color: white; background-color: gray; font-size:12pt;}
                        body {font-size:10pt;}
                        </style>
                        </head>
                        <body>
                        <div>'''
            for widget in self.list_workflow_widgets:
                analysis = widget.softWare
                software = widget.exe_window
                summary = software.fetchWorkflowSetting()
                self.dict_analy_summary[analysis] = summary
                settings += summary
            #检查
            check_results = self.checkSettings()
            check_results = '<p class="title">Parameter check</p>' + check_results if check_results else \
                '<p class="title">Parameter check</p><span style="font-weight:600; color:green;">All parameters are valid!</span>'
            settings += check_results + '</div></body></html>'
            self.popupSummary.textBrowser.setHtml(settings)
        if hasattr(self, "last_position"):
            self.popupSummary.textBrowser.verticalScrollBar().setValue(self.last_position)

    def popUpSummary(self):
        dialog = QDialog(self)
        dialog.resize(600, 700)
        dialog.setWindowTitle("Flowchart settings")
        dialog.gridLayout = QGridLayout(dialog)
        dialog.label = QLabel("Flowchart profile (click <span style=\"color:blue\">blue word</span> to set):", dialog)
        dialog.gridLayout.addWidget(dialog.label, 0, 0, 1, 2)
        dialog.textBrowser = QTextBrowser(dialog)
        dialog.textBrowser.setOpenLinks(False)
        dialog.gridLayout.addWidget(dialog.textBrowser, 1, 0, 1, 2)
        dialog.pushButton_3 = QPushButton(QIcon(":/picture/resourses/HTML.png"), "Save as html", dialog)
        dialog.pushButton_3.clicked.connect(self.saveHTML)
        dialog.gridLayout.addWidget(dialog.pushButton_3, 2, 0, 1, 1)
        dialog.pushButton_4 = QPushButton(QIcon(":/picture/resourses/text-blue.png"), "Save as txt", dialog)
        dialog.pushButton_4.clicked.connect(self.saveTXT)
        dialog.gridLayout.addWidget(dialog.pushButton_4, 2, 1, 1, 1)
        dialog.pushButton = QPushButton(QIcon(":/picture/resourses/if_start_60207.png"), "Ok, start", dialog)
        dialog.pushButton.clicked.connect(self.exec_flowchart)
        dialog.pushButton.clicked.connect(dialog.close)
        dialog.gridLayout.addWidget(dialog.pushButton, 3, 0, 1, 1)
        dialog.pushButton_2 = QPushButton(QIcon(":/picture/resourses/if_Delete_1493279.png"), "Cancel", dialog)
        dialog.pushButton_2.clicked.connect(dialog.close)
        dialog.gridLayout.addWidget(dialog.pushButton_2, 3, 1, 1, 1)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
        return dialog

    def exec_link(self, qurl):
        self.popupWindCloseInfo()
        self.last_position = self.popupSummary.textBrowser.verticalScrollBar().value()
        text = qurl.toString()
        list_text = text.split(" ")
        if list_text[0] == "autocorrect":
            ##自动校正模式
            for i in list_text[1:]:
                exec(i)
            self.refreshRunSummary()
        else:
            exe_window = list_text[0]
            ##得到highlight的控件
            rgx_highlights = re.search(r"factory\.highlightWidgets\([^ ]+\)", text)
            self.dehighlghtWidget = exe_window + "." + rgx_highlights.group().\
                replace("x.", exe_window + ".").replace("highlightWidgets", "deHighlightWidgets") if rgx_highlights else ""
            if len(list_text) > 1:
                commands = list_text[1:]
                str_command = "[x." + ", x.".join(commands) + "]"
                exec("%s.showSig.connect(lambda x: %s)"%(exe_window, str_command))
            exec("%s.closeSig.connect(self.updateRunSummary)"%exe_window)
            # print("%s.closeSig.connect(lambda x, y: %s)" % (exe_window, dehighlghtWidget))
            # exec("%s.closeSig.connect(lambda x, y: %s)" % (exe_window, dehighlghtWidget))  #取消闪烁控件
            exec("%s.exec_()" % exe_window)

    def saveHTML(self):
        html = self.popupSummary.textBrowser.toHtml()
        fileName = QFileDialog.getSaveFileName(
            self, "PhyloSuite", "profile", "HTML Format(*.html)")
        if fileName[0]:
            with open(fileName[0], "w", encoding="utf-8") as f:
                f.write(html)

    def saveTXT(self):
        text = self.popupSummary.textBrowser.toPlainText()
        text = re.sub(r"(?m)^\*\*\*", "\n***", text)
        text = re.sub(r"^\n", "", text)
        fileName = QFileDialog.getSaveFileName(
            self, "PhyloSuite", "profile", "TEXT Format(*.txt)")
        if fileName[0]:
            with open(fileName[0], "w", encoding="utf-8") as f:
                f.write(text)

    def judgeInputs(self, analysis):
        if analysis == self.first_analysis:
            first_widget = self.listWidget_workflow.itemWidget(self.listWidget_workflow.item(0))
            if first_widget.exe_window.isFileIn():
                first_widget.label_inputGif.setVisible(False)
                first_widget.label_inputText.setVisible(False)
                self.hasInputs = True
            else:
                first_widget.label_inputGif.setVisible(True)
                first_widget.label_inputText.setVisible(True)
                self.hasInputs = False

    def judgeAnalyses(self, bool_):
        if not bool_:
            if self.checkBox.isChecked() or self.checkBox_3.isChecked() or \
                    self.checkBox_8.isChecked() or self.checkBox_9.isChecked() or self.checkBox_10.isChecked():
                QMessageBox.information(
                    self,
                    "PhyloSuite",
                    "<p style='line-height:25px; height:25px'>'Concatenation' is necessary for some of the "
                    "downstream functions, so it cannot be unchecked</p>")
                self.checkBox_2.setChecked(True)

    def checkSettings(self):
        # 检查设置是否合格
        settings_body = "".join(list(self.dict_analy_summary.values()))
        self.popupSummary.textBrowser.setHtml(settings_body)
        text = self.popupSummary.textBrowser.toPlainText()
        check_results = ""
        ##['MAFFT', 'Gblocks', 'Concatenate Sequence', 'ModelFinder', 'IQ-TREE', 'MrBayes', 'PartitionFinder']
        list_analyses = re.findall("\*\*\*(.+?)\*\*\*", text)
        #sequence type
        ##normal,codon,N2P
        mafft_type = re.search(r"\*\*\*MAFFT\*\*\*[^\*]+Alignment mode: ([^\n]+)", text).group(1) \
            if re.search(r"\*\*\*MAFFT\*\*\*[^\*]+Alignment mode: ([^\n]+)", text) else ""
        ##MACSE
        hasMACSE = True if re.search(r"\*\*\*MACSE", text) else False
        ##Nucleotide,Protein,Codons
        gblocks_type = re.search(r"\*\*\*Gblocks\*\*\*[^\*]+Data type: ([^\n]+)", text).group(1) \
            if re.search(r"\*\*\*Gblocks\*\*\*[^\*]+Data type: ([^\n]+)", text) else ""
        ##Nucleotide,Amino acid
        PF_type = re.search(r"\*\*\*PartitionFinder\*\*\*[^\*]+Sequence type: ([^\n]+)", text).group(1) \
            if re.search(r"\*\*\*PartitionFinder\*\*\*[^\*]+Sequence type: ([^\n]+)", text) else ""
        ##Auto detect,DNA,Protein,Codon,Binary,Morphology,DNA-->AA
        MF_type = re.search(r"\*\*\*ModelFinder\*\*\*[^\*]+Sequence type: ([^\n]+)", text).group(1) \
            if re.search(r"\*\*\*ModelFinder\*\*\*[^\*]+Sequence type: ([^\n]+)", text) else ""
        ##Auto detect,DNA,Protein,Codon,Binary,Morphology,DNA-->AA
        IQ_type = re.search(r"\*\*\*IQ-TREE\*\*\*[^\*]+Sequence type: ([^\n]+)", text).group(1) \
            if re.search(r"\*\*\*IQ-TREE\*\*\*[^\*]+Sequence type: ([^\n]+)", text) else ""
        incontensy = ""
        list_corrects = []
        # print(mafft_type, gblocks_type, PF_type, MF_type, IQ_type)
        if mafft_type == "Codon":
            ##要不要把正确的也写出来
            if gblocks_type and gblocks_type != "Codons":
                incontensy += "Gblocks (%s), "%gblocks_type
                list_corrects.append("self.Gblocks_exe.radioButton_3.setChecked(True)")
            if PF_type and PF_type != "Nucleotide":
                incontensy += "PartitionFinder (%s), " % PF_type
                list_corrects.append("self.PartitionFinder_exe.tabWidget.setCurrentIndex(0)")
            if MF_type and MF_type not in ["Auto detect", "Codon", "DNA", "DNA-->AA"]:
                incontensy += "ModelFinder (%s), " % MF_type
                list_corrects.append("self.ModelFinder_exe.comboBox_3.setCurrentIndex(0)")
            if IQ_type and IQ_type not in ["Auto detect", "Codon", "DNA", "DNA-->AA"]:
                incontensy += "IQ-TREE (%s), " % IQ_type
                list_corrects.append("self.IQ_TREE_exe.comboBox_3.setCurrentIndex(0)")
            if incontensy:
                incontensy = re.sub(r", ([^,]+?), $", " and \\1", "MAFFT (Codon), " + incontensy)
                check_results += '<span style="font-weight:600; color:red;">Error: </span>' \
                                 'Sequence types are inconsistent between %s. '%incontensy
                check_results += '<a href="autocorrect  %s">&hearts;autocorrect&hearts;</a><br>'%" ".join(list_corrects)
        elif mafft_type == "N2P":
            if gblocks_type and gblocks_type != "Protein":
                incontensy += "Gblocks (%s), "%gblocks_type
                list_corrects.append("self.Gblocks_exe.radioButton_2.setChecked(True)")
            if PF_type and PF_type != "Amino acid":
                incontensy += "PartitionFinder (%s), " % PF_type
                list_corrects.append("self.PartitionFinder_exe.tabWidget.setCurrentIndex(1)")
            if MF_type and MF_type not in ["Auto detect", "Protein"]:
                incontensy += "ModelFinder (%s), " % MF_type
                list_corrects.append("self.ModelFinder_exe.comboBox_3.setCurrentIndex(0)")
            if IQ_type and IQ_type not in ["Auto detect", "Protein"]:
                incontensy += "IQ-TREE (%s), " % IQ_type
                list_corrects.append("self.IQ_TREE_exe.comboBox_3.setCurrentIndex(0)")
            if incontensy:
                incontensy = re.sub(r", ([^,]+?), $", " and \\1", "MAFFT (Protein), " + incontensy)
                check_results += '<span style="font-weight:600; color:red;">Error: </span>' \
                                 'Sequence types are inconsistent in %s. '%incontensy
                check_results += '<a href="autocorrect  %s">&hearts;autocorrect&hearts;</a><br>' % " ".join(list_corrects)
        elif mafft_type == "Normal":
            check_results += '<span style="font-weight:600; color:purple;">Warning: </span>' \
                             'Since you chose "Normal" alignment mode in MAFFT, which means the sequence type can ' \
                             'either be nucleotide or protein, please select the sequence type manually (for Gblocks, PartitionFinder etc.).<br>'
        elif gblocks_type == "Nucleotide":
            if PF_type and PF_type != "Nucleotide":
                incontensy += "PartitionFinder (%s), " % PF_type
                list_corrects.append("self.PartitionFinder_exe.tabWidget.setCurrentIndex(0)")
            if MF_type and MF_type not in ["Auto detect", "DNA"]:
                incontensy += "ModelFinder (%s), " % MF_type
                list_corrects.append("self.ModelFinder_exe.comboBox_3.setCurrentIndex(0)")
            if IQ_type and IQ_type not in ["Auto detect", "DNA"]:
                incontensy += "IQ-TREE (%s), " % IQ_type
                list_corrects.append("self.IQ_TREE_exe.comboBox_3.setCurrentIndex(0)")
            if incontensy:
                incontensy = re.sub(r", ([^,]+?), $", " and \\1", "Gblocks (Nucleotide), " + incontensy)
                check_results += '<span style="font-weight:600; color:red;">Error: </span>' \
                                 'Sequence types are inconsistent in %s. '%incontensy
                check_results += '<a href="autocorrect  %s">&hearts;autocorrect&hearts;</a><br>' % " ".join(list_corrects)
        elif gblocks_type == "Protein":
            if PF_type and PF_type != "Amino acid":
                incontensy += "PartitionFinder (%s), " % PF_type
                list_corrects.append("self.PartitionFinder_exe.tabWidget.setCurrentIndex(1)")
            if MF_type and MF_type not in ["Auto detect", "Protein"]:
                incontensy += "ModelFinder (%s), " % MF_type
                list_corrects.append("self.ModelFinder_exe.comboBox_3.setCurrentIndex(0)")
            if IQ_type and IQ_type not in ["Auto detect", "Protein"]:
                incontensy += "IQ-TREE (%s), " % IQ_type
                list_corrects.append("self.IQ_TREE_exe.comboBox_3.setCurrentIndex(0)")
            if incontensy:
                incontensy = re.sub(r", ([^,]+?), $", " and \\1", "Gblocks (Protein), " + incontensy)
                check_results += '<span style="font-weight:600; color:red;">Error: </span>' \
                                 'Sequence types are inconsistent in %s. '%incontensy
                check_results += '<a href="autocorrect  %s">&hearts;autocorrect&hearts;</a><br>' % " ".join(list_corrects)
        elif gblocks_type == "Codons":
            if PF_type and PF_type != "Nucleotide":
                incontensy += "PartitionFinder (%s), " % PF_type
                list_corrects.append("self.PartitionFinder_exe.tabWidget.setCurrentIndex(0)")
            if MF_type and MF_type not in ["Auto detect", "Codon", "DNA", "DNA-->AA"]:
                incontensy += "ModelFinder (%s), " % MF_type
                list_corrects.append("self.ModelFinder_exe.comboBox_3.setCurrentIndex(0)")
            if IQ_type and IQ_type not in ["Auto detect", "Codon", "DNA", "DNA-->AA"]:
                incontensy += "IQ-TREE (%s), " % IQ_type
                list_corrects.append("self.IQ_TREE_exe.comboBox_3.setCurrentIndex(0)")
            if incontensy:
                incontensy = re.sub(r", ([^,]+?), $", " and \\1", "Gblocks (Codons), " + incontensy)
                check_results += '<span style="font-weight:600; color:red;">Error: </span>' \
                                 'Sequence types are inconsistent in %s. '%incontensy
                check_results += '<a href="autocorrect  %s">&hearts;autocorrect&hearts;</a><br>' % " ".join(list_corrects)
        elif PF_type == "Nucleotide":
            if MF_type and MF_type not in ["Auto detect", "Codon", "DNA", "DNA-->AA"]:
                incontensy += "ModelFinder (%s), " % MF_type
                list_corrects.append("self.ModelFinder_exe.comboBox_3.setCurrentIndex(0)")
            if IQ_type and IQ_type not in ["Auto detect", "Codon", "DNA", "DNA-->AA"]:
                incontensy += "IQ-TREE (%s), " % IQ_type
                list_corrects.append("self.IQ_TREE_exe.comboBox_3.setCurrentIndex(0)")
            if incontensy:
                incontensy = re.sub(r", ([^,]+?), $", " and \\1", "PartitionFinder (Nucleotide), " + incontensy)
                check_results += '<span style="font-weight:600; color:red;">Error: </span>' \
                                 'Sequence types are inconsistent in %s. '%incontensy
                check_results += '<a href="autocorrect  %s">&hearts;autocorrect&hearts;</a><br>' % " ".join(list_corrects)
        elif PF_type == "Amino acid":
            if MF_type and MF_type not in ["Auto detect", "Protein"]:
                incontensy += "ModelFinder (%s), " % MF_type
                list_corrects.append("self.ModelFinder_exe.comboBox_3.setCurrentIndex(0)")
            if IQ_type and IQ_type not in ["Auto detect", "Protein"]:
                incontensy += "IQ-TREE (%s), " % IQ_type
                list_corrects.append("self.IQ_TREE_exe.comboBox_3.setCurrentIndex(0)")
            if incontensy:
                incontensy = re.sub(r", ([^,]+?), $", " and \\1", "PartitionFinder (Amino acid), " + incontensy)
                check_results += '<span style="font-weight:600; color:red;">Error: </span>' \
                                 'Sequence types are inconsistent in %s. '%incontensy
                check_results += '<a href="autocorrect  %s">&hearts;autocorrect&hearts;</a><br>' % " ".join(list_corrects)
        if hasMACSE:
            ##数据类型检查
            incontensy = ""
            ##要不要把正确的也写出来
            if gblocks_type and gblocks_type != "Codons":
                incontensy += "Gblocks (%s), " % gblocks_type
                list_corrects.append("self.Gblocks_exe.radioButton_3.setChecked(True)")
            if PF_type and PF_type != "Nucleotide":
                incontensy += "PartitionFinder (%s), " % PF_type
                list_corrects.append("self.PartitionFinder_exe.tabWidget.setCurrentIndex(0)")
            if MF_type and MF_type not in ["Auto detect", "Codon", "DNA", "DNA-->AA"]:
                incontensy += "ModelFinder (%s), " % MF_type
                list_corrects.append("self.ModelFinder_exe.comboBox_3.setCurrentIndex(0)")
            if IQ_type and IQ_type not in ["Auto detect", "Codon", "DNA", "DNA-->AA"]:
                incontensy += "IQ-TREE (%s), " % IQ_type
                list_corrects.append("self.IQ_TREE_exe.comboBox_3.setCurrentIndex(0)")
            if mafft_type and mafft_type != "Codon":
                incontensy += "MAFFT (%s), " % mafft_type
                list_corrects.append("self.MAFFT_exe.codon_radioButton.setChecked(True)")
            if incontensy:
                incontensy = re.sub(r", ([^,]+?), $", " and \\1", "MACSE (Codon alignment), " + incontensy)
                check_results += '<span style="font-weight:600; color:red;">Error: </span>' \
                                 'Sequence types are inconsistent between %s. ' % incontensy
                check_results += '<a href="autocorrect  %s">&hearts;autocorrect&hearts;</a><br>' % " ".join(
                    list_corrects)
            ## 密码表核对
            mafft_codeTable = re.search(r"\*\*\*MAFFT\*\*\*[^\*]+Code table: ([^\n]+)", text).group(1) \
                   if re.search(r"\*\*\*MAFFT\*\*\*[^\*]+Code table: ([^\n]+)", text) else ""
            MACSE_codeTable = re.search(r"\*\*\*MACSE.+\*\*\*[^\*]+Code table: ([^\n]+)", text).group(1) \
                   if re.search(r"\*\*\*MACSE.+\*\*\*[^\*]+Code table: ([^\n]+)", text) else ""
            if mafft_codeTable and (mafft_codeTable != MACSE_codeTable):
                check_results += '<span style="font-weight:600; color:red;">Error: </span>' \
                                 'As you selected \"%s\" in MAFFT, ' \
                                 'you should also select this code table in MACSE. '%mafft_codeTable
                index = self.MAFFT_exe.comboBox_9.currentIndex()
                check_results += '<a href="autocorrect self.MACSE_exe.comboBox_9.setCurrentIndex(%d)">&hearts;autocorrect&hearts;</a><br>'%index
        # elif MF_type == "Amino acid":
        #     if MF_type and MF_type not in ["Auto detect", "Protein"]:
        #         incontensy += "ModelFinder (%s), " % MF_type
        #     if IQ_type and IQ_type not in ["Auto detect", "Protein"]:
        #         incontensy += "IQ-TREE (%s), " % IQ_type
        #     if incontensy:
        #         check_results += '<span style="font-weight:600; color:red;">Error: </span>' \
        #                          'Sequence types are inconsistent in %s '%re.sub(r", $", "", incontensy)
        if ("ModelFinder" in list_analyses) and ("IQ-TREE" in list_analyses) and ("MrBayes" not in list_analyses):
            IQ_model = re.search(r"\*\*\*IQ-TREE\*\*\*[^\*]+Models: ([^\n]+)", text).group(1) \
                if re.search(r"\*\*\*IQ-TREE\*\*\*[^\*]+Models: ([^\n]+)", text) else ""
            if IQ_model == "Auto (calculate the best-fit model and reconstruct phylogeny)":
                check_results += '<span style="font-weight:600; color:purple;">Warning: </span>' \
                                 'Since ModelFinder has been selected, "Auto" among IQ-TREE "Models" options will be ignored<br>'
        if ("ModelFinder" in list_analyses) and ("MrBayes" in list_analyses):
            MF_model_for = re.search(r"\*\*\*ModelFinder\*\*\*[^\*]+Model used for: ([^\n]+)", text).group(1) \
                if re.search(r"\*\*\*ModelFinder\*\*\*[^\*]+Model used for: ([^\n]+)", text) else ""
            if MF_model_for != "Mrbayes":
                check_results += '<span style="font-weight:600; color:red;">Error: </span>' \
                                 'As results of ModelFinder are used for MrBayes, ' \
                                 'you should select "MrBayes" among the "Model for" options in ModelFinder. '
                check_results += '<a href="autocorrect self.ModelFinder_exe.comboBox_5.setCurrentIndex(1)">&hearts;autocorrect&hearts;</a><br>'
            if "IQ-TREE" in list_analyses:
                IQ_model = re.search(r"\*\*\*IQ-TREE\*\*\*[^\*]+Models: ([^\n]+)", text).group(1) \
                    if re.search(r"\*\*\*IQ-TREE\*\*\*[^\*]+Models: ([^\n]+)", text) else ""
                if IQ_model != "Auto (calculate the best-fit model and reconstruct phylogeny)":
                    check_results += '<span style="font-weight:600; color:red;">Error: </span>' \
                                     'As results of ModelFinder are used for MrBayes, ' \
                                     'you should select "Auto" among the "Models" options in IQ-TREE. '
                    check_results += '<a href="autocorrect self.IQ_TREE_exe.comboBox_7.setCurrentIndex(0)">&hearts;autocorrect&hearts;</a><br>'
        # partition
        MF_partiton = re.search(r"\*\*\*ModelFinder\*\*\*[^\*]+Partition mode: ([^\n]+)", text).group(1) \
                    if re.search(r"\*\*\*ModelFinder\*\*\*[^\*]+Partition mode: ([^\n]+)", text) else ""
        IQ_partiton = re.search(r"\*\*\*IQ-TREE\*\*\*[^\*]+Partition mode: ([^\n]+)", text).group(1) \
            if re.search(r"\*\*\*IQ-TREE\*\*\*[^\*]+Partition mode: ([^\n]+)", text) else ""
        MB_partiton = re.search(r"\*\*\*MrBayes\*\*\*[^\*]+Partition mode: ([^\n]+)", text).group(1) \
            if re.search(r"\*\*\*MrBayes\*\*\*[^\*]+Partition mode: ([^\n]+)", text) else ""
        if "PartitionFinder" in list_analyses:
            # 有PF也必须partition模式
            if IQ_partiton and IQ_partiton != "Yes":
                check_results += '<span style="font-weight:600; color:red;">Error: </span>' \
                                 'Since you selected PartitionFinder for model selection, you should select "Partition mode" in the IQ-TREE. '
                check_results += '<a href="autocorrect self.IQ_TREE_exe.checkBox_8.setChecked(True)">&hearts;autocorrect&hearts;</a><br>'
            if MB_partiton and MB_partiton != "Yes (auto configure according to the results of previous step)":
                check_results += '<span style="font-weight:600; color:red;">Error: </span>' \
                                 'Since you selected PartitionFinder for model selection, you should select "Partition models" in the MrBayes. '
                check_results += '<a href="autocorrect self.MrBayes_exe.popup_part_window=False self.MrBayes_exe.pushButton_partition.setChecked(True)">&hearts;autocorrect&hearts;</a><br>'
            if "IQ-TREE" in list_analyses and self.IQ_TREE_exe.comboBox_7.currentText() == "Auto":
                check_results += '<span style="font-weight:600; color:purple;">Warning: </span>' \
                    'Since PartitionFinder has been selected, "Auto" among IQ-TREE "Models" options will be ignored<br>'
            if ("PartitionFinder" in list_analyses) and ("MrBayes" in list_analyses):
                if self.PartitionFinder_exe.tabWidget.currentIndex() == 0:
                    if self.PartitionFinder_exe.comboBox_2.currentText() == "mrbayes":
                        mrbayes_choosed = True
                    else:
                        mrbayes_choosed = False
                else:
                    if self.PartitionFinder_exe.comboBox_8.currentText() == "mrbayes":
                        mrbayes_choosed = True
                    else:
                        mrbayes_choosed = False
                if not mrbayes_choosed:
                    check_results += '<span style="font-weight:600; color:red;">Error: </span>' \
                                     'Since you selected PartitionFinder for model selection and MrBayes for tree reconstruction, you should select "mrbayes" in the "models" option of PartitionFinder. '
                    check_results += '<a href="autocorrect self.PartitionFinder_exe.comboBox_2.setCurrentText(\'mrbayes\') self.PartitionFinder_exe.comboBox_8.setCurrentText(\'mrbayes\')">&hearts;autocorrect&hearts;</a><br>'
        elif MF_partiton and MF_partiton == "Yes":
            # MF+partition模式
            if IQ_partiton and (IQ_partiton != "Yes") and ("MrBayes" not in list_analyses):
                check_results += '<span style="font-weight:600; color:red;">Error: </span>' \
                                 'Since you selected "Partition mode" in ModelFinder, you should also select "Partition mode" in IQ-TREE. '
                check_results += '<a href="autocorrect self.IQ_TREE_exe.checkBox_8.setChecked(True)">&hearts;autocorrect&hearts;</a><br>'
            if MB_partiton and MB_partiton != "Yes (auto configure according to the results of previous step)":
                check_results += '<span style="font-weight:600; color:red;">Error: </span>' \
                                 'Since you selected "Partition mode" in ModelFinder, you should also select "Partition models" in MrBayes. '
                check_results += '<a href="autocorrect self.MrBayes_exe.popup_part_window=False self.MrBayes_exe.pushButton_partition.setChecked(True)">&hearts;autocorrect&hearts;</a><br>'
        elif MF_partiton and MF_partiton == "No":
            # MF+非partition模式
            if IQ_partiton and (IQ_partiton != "No") and ("MrBayes" not in list_analyses):
                check_results += '<span style="font-weight:600; color:red;">Error: </span>' \
                                 "Since you haven't selected \"Partition mode\" in ModelFinder, you shouldn't select \"Partition mode\" in IQ-TREE either. "
                check_results += '<a href="autocorrect self.IQ_TREE_exe.checkBox_8.setChecked(False)">&hearts;autocorrect&hearts;</a><br>'
            if MB_partiton and MB_partiton != "No":
                check_results += '<span style="font-weight:600; color:red;">Error: </span>' \
                                 'Since you haven\'t selected "Partition mode" in ModelFinder, you shouldn\'t select "Partition models" in MrBayes either. '
                check_results += '<a href="autocorrect self.MrBayes_exe.pushButton_partition.setChecked(False)">&hearts;autocorrect&hearts;</a><br>'
        # PF and phylip, formats
        CAT_formats = re.search(r"\*\*\*Concatenate Sequence\*\*\*[^\*]+Export formats: ([^\n]+)", text).group(1) \
            if re.search(r"\*\*\*Concatenate Sequence\*\*\*[^\*]+Export formats: ([^\n]+)", text) else ""
        if (("Gblocks" in list_analyses) or ("MAFFT" in list_analyses)) and ("PartitionFinder" in list_analyses) \
                and ("Phylip" not in CAT_formats):
            check_results += '<span style="font-weight:600; color:red;">Error: </span>Since you selected PartitionFinder' \
                             ', you should select "Phylip" format in the Concatenation function. '
            check_results += '<a href="autocorrect self.Concatenation_exe.checkBox.setChecked(True)">&hearts;autocorrect&hearts;</a><br>'
        # print(CAT_formats, re.search(r"(Phylip|Nexus|Fasta)", CAT_formats).group())
        if ("Concatenate Sequence" in list_analyses) and (not re.search(r"(Phylip|Nexus|Fasta)", CAT_formats)):
            check_results += '<span style="font-weight:600; color:red;">Error: </span>At least one of the ' \
                             'fasta, phylip and nexus formats should be selected in the Concatenation function. '
            check_results += '<a href="autocorrect self.Concatenation_exe.checkBox.setChecked(True)">&hearts;autocorrect&hearts;</a><br>'
        return check_results

    def popupWindCloseInfo(self):
        ##提醒关闭窗口即保存参数
        qsettings = QSettings(self.thisPath + '/settings/workflow_settings.ini', QSettings.IniFormat)
        qsettings.setFallbacksEnabled(False)
        value = qsettings.value(
            "remind_window", "true")
        if self.factory.str2bool(value):
            icon = ":/picture/resourses/msg_info.png"  #":/picture/resourses/msg_info.png"
            message = "When using Flowchart, the Function window (the window that you opened) is only used to set parameters, so the \"Start\" button is disabled. " \
                      "After you select the settings, just close the window. Your settings are saved automatically."
            windInfo = NoteMessage(message, icon, singleBtn=True, parent=self)
            windInfo.checkBox.clicked.connect(lambda bool_: qsettings.setValue("remind_window", not bool_))
            windInfo.exec_()

    def refreshCheckbox(self):
        ##当前在temporary
        self.checkBox_2.toggled.disconnect() # 阻止信号发送，不然会报错
        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QCheckBox):
                value = self.workflow_settings.value(
                    name, "false")  # 默认改为false，这样新添加的软件都不会被选中
                obj.blockSignals(True)
                obj.setChecked(
                    self.factory.str2bool(value))  # restore checkbox
                obj.blockSignals(False)
        self.checkBox_2.toggled.connect(self.judgeAnalyses)

    def copySettings(self):
        current_workflow = self.comboBox.currentText()
        self.factory.settingsGroup2Group(self.thisPath + '/settings/workflow_settings.ini', current_workflow,
                                         "temporary", baseGroup="Workflow")
        self.refreshCheckbox() #刷新checkbox
        # 刷新程序控件
        self.refreshAnalyses()

    def refreshComboColor(self):
        allItems = [self.comboBox.itemText(i) for i in range(self.comboBox.count())]
        model = self.comboBox.model()
        self.comboBox.clear()
        for num, i in enumerate(allItems):
            item = QStandardItem(i)
            item.setToolTip(i)
            # 背景颜色
            if num % 2 == 0:
                item.setBackground(QColor(255, 255, 255))
            else:
                item.setBackground(QColor(237, 243, 254))
            model.appendRow(item)

    def ctrl_concatente(self, bool_):
        if bool_:
            self.checkBox_2.setChecked(True)

    def eventFilter(self, obj, event):
        # modifiers = QApplication.keyboardModifiers()
        if (event.type() == QEvent.Show) and (obj == self.pushButton.toolButton.menu()):
            if re.search(r"\d+_\d+_\d+\-\d+_\d+_\d+",
                         self.dir_action.text()) or self.dir_action.text() == "Output Dir: ":
                self.factory.sync_dir(self.dir_action)  ##同步文件夹名字
            menu_x_pos = self.pushButton.toolButton.menu().pos().x()
            menu_width = self.pushButton.toolButton.menu().size().width()
            button_width = self.pushButton.toolButton.size().width()
            pos = QPoint(menu_x_pos - menu_width + button_width,
                         self.pushButton.toolButton.menu().pos().y())
            self.pushButton.toolButton.menu().move(pos)
            return True
        # 其他情况会返回系统默认的事件处理方法。
        return super(WorkFlow, self).eventFilter(obj, event)  # 0

    def refreshWorkPath(self):
        for i in self.list_workflow_widgets:
            i.exe_window.workPath = self.flowchart_report_path

    def setFlowchartName(self):
        name, ok = QInputDialog.getText(
            self, 'Set flowchart name', 'Flowchart name:')
        if ok and name:
            self.dir_action.setText("Name: %s"%name)

    def ctrl_combobox2(self, text):
        if text in ['Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees',
                                'Concatenation, Select best-fit partition model for AA, and Build BI tree',
                                'Concatenation, Select best-fit partition model for DNA, and Build BI tree',
                                'Concatenation, Select best-fit partition model for DNA, and Build ML tree',
                                'Select best-fit model then build BI tree', 'Test run',
                                'Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model']:
            self.toolButton_2.setDisabled(True)
        else:
            self.toolButton_2.setDisabled(False)

    def judgePlugins(self):
        if not self.finishPluginsChecked:
            dict_ = {"MAFFT": "mafft",
                     "Gblocks": "gblocks",
                     "IQ-TREE": "iq-tree",
                     "MrBayes": "MrBayes",
                     "PartitionFinder": "PF2",
                     "ModelFinder": "iq-tree",
                     "MACSE": "macse",
                     "trimAl": "trimAl",
                     "HmmCleaner": "HmmCleaner"}
            # return True
            for i in self.dict_analyses:
                if i == "Concatenation":
                    continue
                plugin = dict_[i]
                pluginPath = self.factory.programIsValid(plugin, mode="tool")
                if plugin == "PF2":
                    # PF2path = self.factory.programIsValid(plugin, mode="tool")
                    if pluginPath:
                        self.PFpath = pluginPath
                        pf_compiled = pluginPath + os.sep + "PartitionFinder.exe" if platform.system().lower() == "windows" else \
                            pluginPath + os.sep + "PartitionFinder"
                        py27Path = self.factory.programIsValid("python27", mode="tool")
                        self.Py27Path = py27Path    #不管有没有py27，是False的时候也要赋值，partitionfinder里面会有判断
                        if not os.path.exists(pf_compiled):
                            ##PF2脚本模式
                            if not py27Path:
                                self.list_uninstalled_software.append("Python 2.7")
                    else:
                        self.list_uninstalled_software.append(i)
                elif plugin == "macse":
                    if pluginPath:
                        self.MACSEpath = pluginPath
                        self.javaPath = self.factory.programIsValid("java", mode="tool")
                        if not self.javaPath:
                            self.list_uninstalled_software.append("JAVA (JRE > 1.5)")
                    else:
                        self.list_uninstalled_software.append(i)
                elif plugin == "HmmCleaner":
                    if pluginPath:
                        self.HmmCleanerpath = pluginPath
                        # hmmbuild
                        popen = subprocess.Popen(
                            "hmmbuild -h", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
                        stdout = self.factory.getSTDOUT(popen)
                        if not re.search(r"hmmbuild \[-options\]", stdout, re.I):
                            self.list_uninstalled_software.append("HMMER")
                        #PERL
                        self.perlPath = self.factory.programIsValid("perl", mode="tool")
                        if self.HmmCleanerpath != "HmmCleaner.pl":
                            if not self.perlPath:
                                self.list_uninstalled_software.append("Perl 5")
                    else:
                        self.list_uninstalled_software.append(i)
                else:
                    if not pluginPath:
                        i = "IQ-TREE" if i == "ModelFinder" else i
                        self.list_uninstalled_software.append(i)
                    else:
                        if plugin == "mafft":
                            self.MAFFTpath = pluginPath
                        elif plugin == "gblocks":
                            self.GBpath = pluginPath
                        elif plugin == "iq-tree":
                            self.IQpath = pluginPath
                        elif plugin == "MrBayes":
                            self.MBpath = pluginPath
                        elif plugin == "trimAl":
                            self.trimAlpath = pluginPath
            self.finishPluginsChecked = True
        self.judgeUninstall()

    def judgeCleanSoftwares(self, bool_):
        # for obj in [self.checkBox_3, self.checkBox_9, self.checkBox_10]:
        #     obj.blockSignals(True)
        #     # try: obj.disconnect()
        #     # except: pass
        sender = self.sender()
        if bool_:
            # 一般联动的时候至少会保证有一个软件是checked的
            if sender == self.checkBox_3:
                # self.checkBox_9.blockSignals(True)
                # self.checkBox_10.blockSignals(True)
                self.checkBox_9.setChecked(False)
                self.checkBox_10.setChecked(False)
                # self.checkBox_9.blockSignals(False)
                # self.checkBox_10.blockSignals(False)
            elif sender == self.checkBox_9:
                self.checkBox_3.setChecked(False)
                self.checkBox_10.setChecked(False)
            elif sender == self.checkBox_10:
                self.checkBox_3.setChecked(False)
                self.checkBox_9.setChecked(False)
            self.refreshAnalyses()
        else:
            if (not self.checkBox_3.isChecked()) and (not self.checkBox_9.isChecked()) and (not self.checkBox_10.isChecked()):
                #当3个都不check的时候
                self.refreshAnalyses()

        # for obj in [self.checkBox_3, self.checkBox_9, self.checkBox_10]:
        #     obj.blockSignals(False)


    def popupUninstall(self, list_softwares):
        if "HMMER" in list_softwares:
            list_softwares.remove("HMMER")
            message = "As HmmCleaner relies on HMMER version 3.1b2 (http://hmmer.org)! Please also install it and add its subprograms (e.g. hmmbuild) to " \
                      "the environment variable ($PATH, mandatory)."
        else:
            message = ""
        if list_softwares:
            message = "Please install %s first! %s"% (
                ", ".join(list(set(list_softwares))), message)
        reply = QMessageBox.information(
            self,
            "Information",
            "<p style='line-height:25px; height:25px'>%s</p>"%message,
            QMessageBox.Ok,
            QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            self.close()
            self.setting = Setting(self)
            self.setting.display_table(self.setting.listWidget.item(1))
            # 隐藏？按钮
            self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.setting.exec_()

    def judgeUninstall(self):
        list_checked_Box_text = self.fetch_checked_Box_texts()
        if "MACSE" in list_checked_Box_text: list_checked_Box_text.append("JAVA (JRE > 1.5)")
        if "HmmCleaner" in list_checked_Box_text: [list_checked_Box_text.append("Perl 5"), list_checked_Box_text.append("HMMER")]
        if "PartitionFinder" in list_checked_Box_text: list_checked_Box_text.append("Python 2.7")
        if "ModelFinder" in list_checked_Box_text: list_checked_Box_text.append("IQ-TREE")
        list_uninstall = list(set(self.list_uninstalled_software).intersection(set(list_checked_Box_text)))
        if list_uninstall:
            self.pushButton.setEnabled(False)
            self.uninstallPackageSig.emit(list_uninstall)
            return False
        self.pushButton.setEnabled(True)
        return True

    def fetch_checked_Box_texts(self):
        list_checked_Box_text = [widget.text() for widget in self.list_allcheckbox if widget.isChecked()]
        return list_checked_Box_text

    def connectCheckbox(self):
        self.checkBox.clicked.connect(self.refreshAnalyses)
        self.checkBox.toggled.connect(self.ctrl_concatente)
        self.checkBox_2.clicked.connect(self.refreshAnalyses)
        # self.checkBox_3.clicked.connect(self.refreshAnalyses)
        self.checkBox_4.clicked.connect(self.refreshAnalyses)
        ## 5和6指定了按钮组，所以槽函数只执行一次
        self.checkBox_5.clicked.connect(self.refreshAnalyses)
        self.checkBox_6.clicked.connect(self.refreshAnalyses)
        self.checkBox_7.clicked.connect(self.refreshAnalyses)
        self.checkBox_2.toggled.connect(self.judgeAnalyses)
        self.checkBox_8.toggled.connect(lambda bool_: [self.refreshAnalyses(), self.ctrl_concatente(bool_)])
        # 3个clean软件不能指定按钮组，因为也有可能全部不选
        self.checkBox_3.toggled.connect(lambda bool_: [self.ctrl_concatente(bool_),
                                                       self.judgeCleanSoftwares(
                                                           bool_)])  # refreshAnalyses在judgeCleanSoftwares会执行
        self.checkBox_9.toggled.connect(lambda bool_: [self.ctrl_concatente(bool_),
                                                       self.judgeCleanSoftwares(bool_)])
        self.checkBox_10.toggled.connect(lambda bool_: [self.ctrl_concatente(bool_),
                                                        self.judgeCleanSoftwares(bool_)])

    # def ctrlModelSelBoxes(self, bool_):
    #     sender = self.sender()
    #     if bool_:
    #         ##2个至少有一个是true，所以就保证只执行一次refresh
    #         if sender == self.checkBox_5: self.checkBox_4.setChecked(False)
    #         elif sender == self.checkBox_4: self.checkBox_5.setChecked(False)
    #         self.refreshAnalyses()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = WorkFlow()
    ui.show()
    sys.exit(app.exec_())