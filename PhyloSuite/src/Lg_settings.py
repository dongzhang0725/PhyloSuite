#!/usr/bin/env python
# -*- coding: utf-8 -*-
import glob
import re
import zipfile
from collections import OrderedDict
from pathlib import Path
from zipfile import ZipFile

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from src.update import UpdateAPP
from uifiles.Ui_PF_exe_path import Ui_PF2ExePath
from uifiles.Ui_settings import Ui_Settings
from src.factory import Factory, HttpWindowDownload, WorkThread
from uifiles.Ui_exe_path import Ui_ExePath
from src.CustomWidget import MySettingTableModel
import sys
import os
import inspect
import traceback
import copy
import platform
from src.plugins import dict_url, dict_plugin_settings

class LG_exePath(QDialog, Ui_ExePath, object):
    downloadSig = pyqtSignal()
    closeSig = pyqtSignal(str, str)

    def __init__(self, parent=None, label1=None, label2=None, label3=None, placeholdertext=None,
                 flag="RscriptPath", target="Rscript.exe", link=None):
        super(LG_exePath, self).__init__(parent)
        self.parent = parent
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.downloadRes = "Chinese resource"
        self.setupUi(self)
        if label1:
            self.label_3.setText(label1)
        if label2:
            self.label.setText(label2)
        if label3:
            self.label_2.setText(label3)
        if placeholdertext:
            self.lineEdit.setPlaceholderText(placeholdertext)
        self.flag = flag
        self.target = " ".join(target) if type(target) == list else target
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        self.pushButton.setFocus()
        self.lineEdit.installEventFilter(self)
        self.label_4.linkActivated.connect(self.exe_link)
        country = self.factory.path_settings.value("country", "UK")
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/PhyloSuite-demo/how-to-configure-plugins/" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/PhyloSuite-demo/how-to-configure-plugins/"
        self.label_6.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        self.comboBox.currentTextChanged.connect(self.switchRes)
        if platform.system().lower() in ["darwin", "windows"]:
            self.toolButton_3.setStyleSheet("QToolButton {background: transparent;}")
        if not link:
            self.gridLayout_2.removeWidget(self.label_4)
            self.label_4.close()
            self.label_4.deleteLater()
            del self.label_4
        elif (platform.system().lower() == "linux") or (flag in ["java", "perl", "HmmCleaner"]) or \
                ("If download failed," not in link):
            # self.gridLayout_2.removeWidget(self.pushButton_5)
            # self.pushButton_5.close()
            # self.pushButton_5.deleteLater()
            # del self.pushButton_5
            for i in [self.pushButton_5, self.label_7, self.comboBox]:
                i.setVisible(False)
            self.label_4.setText(link)
            self.label_4.setWordWrap(True)
        else:
            self.label_4.setText(link)
            self.label_4.setWordWrap(True)
        self.adjustSize()
        ##调用一下
        self.switchRes("Chinese resource")
        if (flag in ["RscriptPath", "python27"]) or (platform.system().lower() == "linux"):
            self.comboBox.setEnabled(False)

    @pyqtSlot()
    def on_toolButton_3_clicked(self):
        if self.flag != "PF2":
            fileName = QFileDialog.getOpenFileName(
                self, "Input File", filter="%s *;;"%self.target)
            if fileName[0]:
                if os.path.isfile(fileName[0]):
                    self.lineEdit.setText(fileName[0])
                else:
                    QMessageBox.critical(
                        self,
                        "Settings",
                        "<p style='line-height:25px; height:25px'>Please specify the %s executable file!</p>"%self.target)
        else:
            options = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
            directory = QFileDialog.getExistingDirectory(self, "Choose folder", options=options)
            if directory:
                # ok = self.factory.checkPath(directory, parent=self)
                self.lineEdit.setText(directory)

    @pyqtSlot()
    def on_pushButton_clicked(self):
        """
        ok
        """
        path = self.lineEdit.text()
        if self.factory.programIsValid_2(self.flag, path, parent=self, btn="OK") == "succeed":
            self.closeSig.emit(self.flag, path)
            self.close()
        else:
            if path.endswith("HmmCleaner.pl"):
                ##dependencies没有配置成功
                country = self.factory.path_settings.value("country", "UK")
                url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/PhyloSuite-demo/how-to-configure-plugins/#2-4-HmmCleaner-configuration" if \
                    country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/PhyloSuite-demo/how-to-configure-plugins/#2-4-HmmCleaner-configuration"
                QMessageBox.critical(
                    self,
                    "Settings",
                    "<p style='line-height:25px; height:25px'>The "
                    "<a href=\"https://cpandeps.grinnz.com/?dist=Bio-MUST-Apps-HmmCleaner&phase=build&perl_version=v5.30.0&style=table\">"
                    "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">dependencies</span></a> "
                    "(e.g. Bio-FastParsers) of HmmCleaner are not installed. You can install HmmCleaner following this " \
                    "<a href=\"%s\">" \
                    "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">instruction</a>." \
                    "</span></p>"%url)
            elif self.flag not in ["python27"]: #python27和java有自己的提醒
                QMessageBox.critical(
                    self,
                    "Settings",
                    "<p style='line-height:25px; height:25px'>The path is not validated!</p>")

    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        """
        cancel
        """
        self.close()

    @pyqtSlot()
    def on_pushButton_5_clicked(self):
        """
        download
        """
        self.downloadSig.emit()
        self.hide()

    def eventFilter(self, obj, event):
        # modifiers = QApplication.keyboardModifiers()
        if isinstance(
                obj,
                QLineEdit):
            if event.type() == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    # must accept the dragEnterEvent or else the dropEvent
                    # can't occur !!!
                    event.accept()
                    return True
            if event.type() == QEvent.Drop:
                files = [u.toLocalFile() for u in event.mimeData().urls()]
                if files:
                    if len(files) == 1:
                        if self.factory.programIsValid_2(self.flag, files[0], parent=self) == "succeed":
                            obj.setText(files[0])
                        else:
                            if self.flag not in ("python27", "java"):  # python27和java有自己的提醒
                                QMessageBox.warning(
                                    self,
                                    "Settings",
                                    "<p style='line-height:25px; height:25px'>Only '%s' file is validated!</p>"%self.target)
                    else:
                        QMessageBox.warning(
                            self,
                            "Settings",
                            "<p style='line-height:25px; height:25px'>Only one file is validated!</p>")
        # 其他情况会返回系统默认的事件处理方法。
        return super(LG_exePath, self).eventFilter(obj, event)  # 0

    def closeEvent(self, event):
        path = self.lineEdit.text()
        self.closeSig.emit(self.flag, path)

    def exe_link(self, qtext):
        if qtext.strip() == "PF2 install":
            PF2_installed = self.parent.plugin_is_installed("PF2")
            if PF2_installed:
                reply = QMessageBox.question(
                    self,
                    "Uninstall PartitionFinder2",
                    "<p style='line-height:25px; height:25px'>Please confirm that you decided to uninstall "
                    "PartitionFinder2 Python script and replace it with the compiled PartitionFinder2.</p>",
                    QMessageBox.Yes,
                    QMessageBox.Cancel)
                if reply == QMessageBox.Cancel:
                    return
            self.close()
            self.parent.on_download_partfind_button_clicked()
        else:
            QDesktopServices.openUrl(QUrl(qtext))

    def switchRes(self, resource):
        if not resource: return
        self.downloadRes = resource
        if platform.system().lower() in ["darwin", "windows"]:
            try:
                url = dict_url[platform.system().lower()][self.parent.pc_bit][resource][self.flag]
                self.label_4.setText(re.sub(r"<a href=\".*?\">", "<a href=\"%s\">" % url, self.label_4.text()))
            except: pass


class LG_PF2_exePath(QDialog, Ui_PF2ExePath, object):
    downloadSig = pyqtSignal(str)
    closeSig = pyqtSignal(str, str)

    def __init__(self, placeholdertext=None, link1=None, link2=None, pythonOk=False, parent=None):
        super(LG_PF2_exePath, self).__init__(parent)
        self.factory = Factory()
        self.parent = parent
        self.thisPath = self.factory.thisPath
        self.setupUi(self)
        self.downloadRes = "Chinese resource"
        self.groupBox_2.toggled.connect(lambda bool_: self.groupBox_3.setChecked(not bool_))
        self.groupBox_3.toggled.connect(lambda bool_: self.groupBox_2.setChecked(not bool_))
        self.groupBox_2.setChecked(True)
        if pythonOk:
            self.pushButton_11.setText("Already installed!")
            self.pushButton_11.setDisabled(True)
        if link1: self.label_8.setText(link1)
        if link2: self.label_7.setText(link2)
        if placeholdertext:
            self.lineEdit_3.setPlaceholderText(placeholdertext)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        country = self.factory.path_settings.value("country", "UK")
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/PhyloSuite-demo/how-to-configure-plugins/" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/PhyloSuite-demo/how-to-configure-plugins/"
        self.label_9.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        self.comboBox.currentTextChanged.connect(self.switchRes)
        self.switchRes("Chinese resource")
        self.adjustSize()
        if platform.system().lower() == "linux":
            self.comboBox.setEnabled(False)

    @pyqtSlot()
    def on_pushButton_9_clicked(self):
        """
        ok
        """
        path = self.lineEdit_3.text()
        if self.factory.programIsValid_2("PF2", path, parent=self, btn="OK") == "succeed":
            self.closeSig.emit("PF2", path)
            self.close()
        else:
            QMessageBox.critical(
                self,
                "Settings",
                "<p style='line-height:25px; height:25px'>The path is not validated!</p>")

    @pyqtSlot()
    def on_pushButton_10_clicked(self):
        """
        cancel
        """
        self.close()

    @pyqtSlot()
    def on_pushButton_6_clicked(self):
        """
        download compiled PF2
        """
        self.downloadSig.emit("compiled PF2")
        self.hide()

    @pyqtSlot()
    def on_pushButton_8_clicked(self):
        """
        download PF2
        """
        self.downloadSig.emit("PF2")
        self.hide()

    @pyqtSlot()
    def on_toolButton_5_clicked(self):
        options = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
        directory = QFileDialog.getExistingDirectory(self, "Choose folder", options=options)
        if directory:
            self.lineEdit_3.setText(directory)

    @pyqtSlot()
    def on_pushButton_11_clicked(self):
        """
        configure python27
        """
        self.close()
        self.parent.on_download_python27_button_clicked()

    def closeEvent(self, event):
        path = self.lineEdit_3.text()
        self.closeSig.emit("PF2", path)

    def switchRes(self, resource):
        if not resource: return
        self.downloadRes = resource
        if platform.system().lower() in ["darwin", "windows"]:
            try:
                url = dict_url[platform.system().lower()][self.parent.pc_bit][resource]["compiled PF2"]
                self.label_7.setText(re.sub(r"<a href=\".*?\">", "<a href=\"%s\">" % url, self.label_7.text()))
            except: pass
            try:
                url = dict_url[platform.system().lower()][self.parent.pc_bit][resource]["PF2"]
                self.label_8.setText(re.sub(r"<a href=\".*?\">", "<a href=\"%s\">" % url, self.label_8.text()))
            except: pass


class Setting(QDialog, Ui_Settings, object):
    '''安装软件的路线：先是执行on_download_xxx，然后弹出询问窗口，判断是自己指定，还是download
      1、如果是指定，点ok会发送closeSig，然后执行XXXexePath_window_close，然后会根据这个路径是否存在来给出download按钮的状态
      2、如果是下载，就会调用downloadXXX，进而调用HttpWindowDownload执行下载任务，下载以后一般的程序是直接解压程序包，然后发送
         save_pathSig信号，执行saveEXEpath，判断路径是否存在以后，直接将程序及其对应路径保存；python27和R特殊一下，下载的是安装包，
         下载完执行安装，安装以后会弹出来提示让配置路径，配置完以后，就是按照1的方式往下执行
    '''

    installButtonSig = pyqtSignal(list)
    # progressSig = pyqtSignal(QWidget, int)  # 控制进度条
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    save_pathSig = pyqtSignal(str, str)
    # progressDialogSig = pyqtSignal(QWidget, int)  # 控制进度条
    closeSig = pyqtSignal()
    ##如果分类群被修改，就发送这个信号
    taxmyChangeSig = pyqtSignal(list)
    ##zip/unzip
    zipSig = pyqtSignal(str)
    installFinishedSig = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super(Setting, self).__init__(parent)
        # self.thisPath = os.path.dirname(os.path.realpath(__file__))
        self.parent = parent
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.setupUi(self)
        self.currentPath = self.thisPath
        iniCheckWorker = WorkThread(lambda: self.factory.init_check(self),
                                    parent=self)
        iniCheckWorker.start()
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        # self.factory.init_check(self)
        ##信号槽
        self.comboBox.currentTextChanged.connect(self.judgeSettings)
        self.settings = QSettings(
            self.thisPath + '/settings/setting_settings.ini', QSettings.IniFormat)
        self.settings.setFallbacksEnabled(False)
        self.mainwindow_settings = QSettings(
            self.thisPath +
            '/settings/mainwindow_settings.ini',
            QSettings.IniFormat, parent=self)
        self.mainwindow_settings.setFallbacksEnabled(False)
        self.workflow_settings = QSettings(
            self.thisPath +
            '/settings/workflow_settings.ini',
            QSettings.IniFormat)
        self.workflow_settings.setFallbacksEnabled(False)
        self.launcher_settings = QSettings(
            self.thisPath + '/settings/launcher_settings.ini', QSettings.IniFormat)
        self.launcher_settings.setFallbacksEnabled(False)
        # 设置比例
        self.splitter.setStretchFactor(1, 7)
        items = ["Taxonomy Recognition",
                 "Plugins",
                 "General",
                 ]
        self.listWidget.addItems(items)
        self.listWidget.itemClicked.connect(self.display_table)
        self.dict_name_row = {"mafft": 0,
                             "RscriptPath": 1,
                             "python27": 2,
                             "PF2": 3,
                             "gblocks": 4,
                             "iq-tree": 5,
                             "MrBayes": 6,
                             "tbl2asn": 7,
                              "mpi": 8,
                              "java": 9,
                              "macse": 10,
                              "trimAl": 11,
                              "perl": 12,
                              "HmmCleaner": 13,
                              "CodonW": 14,
                              "plot_engine": 15
                              }
        for plugin in dict_plugin_settings:
            if "link_mac" not in dict_plugin_settings[plugin]:
                continue
            self.dict_name_row[plugin] = len(self.dict_name_row)
        # print(self.dict_name_row)
        # self.display_table(self.listWidget.item(0))
        # 设置行数
        self.tableWidget.setRowCount(len(self.dict_name_row))
        # 预设置按钮
        self.download_mafft_button = QPushButton("Install", self)
        self.download_mafft_button.clicked.connect(
            self.on_download_mafft_button_clicked)
        self.tableWidget.setCellWidget(self.dict_name_row["mafft"], 3, self.download_mafft_button)
        self.download_tbl2asn_button = QPushButton("Install", self)
        self.download_tbl2asn_button.clicked.connect(
            self.on_download_tbl2asn_button_clicked)
        self.tableWidget.setCellWidget(self.dict_name_row["tbl2asn"], 3, self.download_tbl2asn_button)
        self.download_Rscript_button = QPushButton("Install", self)
        self.download_Rscript_button.clicked.connect(
            self.on_download_Rscript_button_clicked)
        self.tableWidget.setCellWidget(self.dict_name_row["RscriptPath"], 3, self.download_Rscript_button)
        self.download_python27_button = QPushButton("Install", self)
        self.download_python27_button.clicked.connect(
            self.on_download_python27_button_clicked)
        self.tableWidget.setCellWidget(self.dict_name_row["python27"], 3, self.download_python27_button)
        self.download_partfind_button = QPushButton("Install", self)
        self.download_partfind_button.clicked.connect(
            self.on_download_partfind_button_clicked)
        self.tableWidget.setCellWidget(self.dict_name_row["PF2"], 3, self.download_partfind_button)
        self.download_gblocks_button = QPushButton("Install", self)
        self.download_gblocks_button.clicked.connect(
            self.on_download_gblocks_button_clicked)
        self.tableWidget.setCellWidget(self.dict_name_row["gblocks"], 3, self.download_gblocks_button)
        self.download_iq_tree_button = QPushButton("Install", self)
        self.download_iq_tree_button.clicked.connect(
            self.on_download_iq_tree_button_clicked)
        self.tableWidget.setCellWidget(self.dict_name_row["iq-tree"], 3, self.download_iq_tree_button)
        self.download_MrBayes_button = QPushButton("Install", self)
        self.download_MrBayes_button.clicked.connect(
            self.on_download_MrBayes_button_clicked)
        self.tableWidget.setCellWidget(self.dict_name_row["MrBayes"], 3, self.download_MrBayes_button)
        self.download_mpi_button = QPushButton("Install", self)
        self.download_mpi_button.clicked.connect(
            self.on_download_mpi_button_clicked)
        self.tableWidget.setCellWidget(self.dict_name_row["mpi"], 3, self.download_mpi_button)
        self.download_java_button = QPushButton("Install", self)
        self.download_java_button.clicked.connect(
            self.on_download_java_button_clicked)
        self.tableWidget.setCellWidget(self.dict_name_row["java"], 3, self.download_java_button)
        self.download_macse_button = QPushButton("Install", self)
        self.download_macse_button.clicked.connect(
            self.on_download_macse_button_clicked)
        self.tableWidget.setCellWidget(self.dict_name_row["macse"], 3, self.download_macse_button)
        self.download_trimAl_button = QPushButton("Install", self)
        self.download_trimAl_button.clicked.connect(
            self.on_download_trimAl_button_clicked)
        self.tableWidget.setCellWidget(self.dict_name_row["trimAl"], 3, self.download_trimAl_button)
        self.download_perl_button = QPushButton("Install", self)
        self.download_perl_button.clicked.connect(
            self.on_download_perl_button_clicked)
        self.tableWidget.setCellWidget(self.dict_name_row["perl"], 3, self.download_perl_button)
        self.download_HmmCleaner_button = QPushButton("Install", self)
        self.download_HmmCleaner_button.clicked.connect(
            self.on_download_HmmCleaner_button_clicked)
        self.tableWidget.setCellWidget(self.dict_name_row["HmmCleaner"], 3, self.download_HmmCleaner_button)
        self.download_CodonW_button = QPushButton("Install", self)
        self.download_CodonW_button.clicked.connect(
            self.on_download_CodonW_button_clicked)
        self.tableWidget.setCellWidget(self.dict_name_row["CodonW"], 3, self.download_CodonW_button)
        self.download_plot_engine_button = QPushButton("Install", self)
        self.download_plot_engine_button.clicked.connect(
            self.on_download_plot_engine_button_clicked)
        self.tableWidget.setCellWidget(self.dict_name_row["plot_engine"], 3, self.download_plot_engine_button)
        self.dict_name_button = {"mafft": self.download_mafft_button,
                                 "RscriptPath": self.download_Rscript_button,
                                 "python27": self.download_python27_button,
                                 "PF2": self.download_partfind_button,
                                 "gblocks": self.download_gblocks_button,
                                 "iq-tree": self.download_iq_tree_button,
                                 "MrBayes": self.download_MrBayes_button,
                                 "tbl2asn": self.download_tbl2asn_button,
                                 "mpi": self.download_mpi_button,
                                 "java": self.download_java_button,
                                 "macse": self.download_macse_button,
                                 "trimAl": self.download_trimAl_button,
                                 "perl": self.download_perl_button,
                                 "HmmCleaner": self.download_HmmCleaner_button,
                                 "CodonW": self.download_CodonW_button,
                                 "plot_engine": self.download_plot_engine_button
                                 }
        for plugin in dict_plugin_settings:
            if "link_mac" not in dict_plugin_settings[plugin]:
                continue
            setattr(self, f"install_button{self.dict_name_row[plugin]}",
                    QPushButton("Install", self))
            # getattr(self, f"install_button{self.dict_name_row[plugin]}").setStyleSheet(self.qss_file)
            getattr(self, f"install_button{self.dict_name_row[plugin]}").clicked.connect(lambda checked,
                                                                                                dict_settings=dict_plugin_settings[plugin]:
                                    self.plugin_download_button_clicked(**dict_settings))
            self.tableWidget.setItem(self.dict_name_row[plugin], 0,
                                     QTableWidgetItem(f'{dict_plugin_settings[plugin]["plugin_name"]} v'
                                                      f'{dict_plugin_settings[plugin]["version"]}'))
            self.tableWidget.setItem(self.dict_name_row[plugin], 1,
                                     QTableWidgetItem(f'{dict_plugin_settings[plugin]["description"]}'))
            self.tableWidget.setItem(self.dict_name_row[plugin], 2, QTableWidgetItem("Uninstalled"))
            self.tableWidget.setCellWidget(self.dict_name_row[plugin], 3,
                                           getattr(self, f"install_button{self.dict_name_row[plugin]}"))
            self.dict_name_button[plugin] = getattr(self, f"install_button{self.dict_name_row[plugin]}")
        self.installButtonSig.connect(self.factory.ctrl_installButton_status)
        # self.progressSig.connect(self.runProgress)
        self.exception_signal.connect(self.popupException)
        self.save_pathSig.connect(self.saveEXEpath)
        self.zipSig.connect(self.zip_waiting)
        self.plugin_path = self.factory.creat_dir(
            self.currentPath + os.sep + "plugins")
        self.tableView_2.installEventFilter(self)
        # 恢复用户的设置
        self.guiRestore()
        self.display_table(self.listWidget.item(0))
        self.pc_bit = self.fetch_os_bit()
        ## 拖拽表格列
        self.tableView_2.horizontalHeader().setSectionsMovable(True)
        self.tableView_2.horizontalHeader().setDragEnabled(True)
        self.tableView_2.horizontalHeader().setDragDropMode(QAbstractItemView.InternalMove)
        if platform.system().lower() in ["linux", "darwin"]:
            # self.tableWidget.removeRow(self.dict_name_row["tbl2asn"])
            self.tableWidget.setRowHidden(self.dict_name_row["tbl2asn"], True)
        if platform.system().lower() in ["windows", "darwin"]:
            # self.tableWidget.removeRow(self.dict_name_row["mpi"])
            self.tableWidget.setRowHidden(self.dict_name_row["mpi"], True)
        if platform.system().lower() == "windows":
            self.tableWidget.setRowHidden(self.dict_name_row["perl"], True)
            self.tableWidget.setRowHidden(self.dict_name_row["HmmCleaner"], True)
        ## brief demo
        country = self.factory.path_settings.value("country", "UK")
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#4-4-1-Lineage-recognition" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#4-4-1-Lineage-recognition"
        self.label_6.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        self.installFinishedSig.connect(self.Install_finished)
        ##设置白色背景
        p = self.tableWidget.palette()
        p.setColor(QPalette.Background, Qt.white)
        self.tableWidget.setPalette(p)
        ##设置span
        self.tableWidget.setSpan(2, 0, 2, 1)
        self.tableWidget.setSpan(9, 0, 2, 1)
        self.tableWidget.setSpan(12, 0, 2, 1)
        ## 信号槽
        self.lineEdit.clicked.connect(self.setFont)
        self.lineEdit_2.clicked.connect(self.setFont)

    def fetch_os_bit(self):
        return "64bit" if platform.machine().endswith('64') else "32bit"

    @pyqtSlot()
    def on_pushButton_clicked(self):
        """
        restore settings
        """
        reply = QMessageBox.question(
            self,
            "Settings",
            "<p style='line-height:25px; height:25px'>Please confirm that you decided to restore the settings "
            "to default.</p>",
            QMessageBox.Yes,
            QMessageBox.Cancel)
        if reply == QMessageBox.Yes:
            list_ini = glob.glob(self.factory.thisPath + os.sep + 'settings' + os.sep + "*.ini")
            for i in list_ini:
                if os.path.exists(i):
                    try: os.remove(i)
                    except: pass
            QMessageBox.information(
                self, "Settings", "<p style='line-height:25px; height:25px'>Settings restored successfully! "
                                  "Please restart PhyloSuite now</p>")

    @pyqtSlot()
    def on_pushButton_export_clicked(self):
        """
        export settings
        """
        msgBox = QMessageBox(self)
        # msgBox.setWindowFlags(msgBox.windowFlags() | Qt.WindowCloseButtonHint)
        # msgBox.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText('Please choose the settings that you want to export.')
        msgBox.addButton(QPushButton('Setings'), QMessageBox.NoRole)
        msgBox.addButton(QPushButton('Plugins'), QMessageBox.NoRole)
        msgBox.addButton(QPushButton('Setings and plugins'), QMessageBox.NoRole)
        msgBox.addButton(QPushButton('Cancel'), QMessageBox.RejectRole)
        ret = msgBox.exec_()
        plugins = f"{self.thisPath}{os.sep}plugins"
        settings = f"{self.thisPath}{os.sep}settings"
        if ret == 0:
            list_export_dirs = [settings]
        elif ret == 1:
            list_export_dirs = [plugins]
        elif ret == 2:
            list_export_dirs = [plugins, settings]
        elif ret == 3:
            list_export_dirs = []
        if not list_export_dirs:
            return
        fileName = QFileDialog.getSaveFileName(
            self, "PhyloSuite", "PhyloSuite_settings", "ZIP Format(*.zip)")
        for folder in list_export_dirs:
            if Path(folder) in Path(fileName[0]).parents:
                QMessageBox.warning(
                    self,
                    "Warning",
                    f"<p style='line-height:25px; height:25px'>For recursion reason, "
                    f"the settings file cannot be saved under \"{folder}\" folder, "
                    f"please select a new path!</p>")
                return
        if fileName[0]:
            self.progressDialog = self.factory.myProgressDialog(
                "Please Wait", "Exporting...", parent=self, busy=True)
            self.progressDialog.show()
            zipWorker = WorkThread(
                lambda: self.factory.zipFolder(fileName[0], list_export_dirs),
                parent=self)
            zipWorker.start()
            zipWorker.finished.connect(lambda: [self.progressDialog.close(), QMessageBox.information(
                self, "Save settings to file", "<p style='line-height:25px; "
                                               "height:25px'>Settings saved successfully! </p>")])

    @pyqtSlot()
    def on_pushButton_import_clicked(self):
        """
        import settings
        """
        fileName = QFileDialog.getOpenFileName(
            self, "Input setting file", filter="ZIP Format(*.zip);;")
        if fileName[0]:
            self.progressDialog = self.factory.myProgressDialog(
                "Please Wait", "Importing...", parent=self, busy=True)
            self.progressDialog.show()
            zipWorker = WorkThread(
                lambda: self.factory.unzipFolder(fileName[0], self.thisPath),
                parent=self)
            zipWorker.start()
            zipWorker.finished.connect(lambda: [self.progressDialog.close(), QMessageBox.information(
                self, "Import settings", "<p style='line-height:25px; "
                                               "height:25px'>Settings imported successfully! </p>")])

    @pyqtSlot()
    def on_download_mafft_button_clicked(self):
        """
        download mafft
        """
        flag = "mafft"
        if self.download_mafft_button.text() == "Install":
            label1 = "<html><head/><body><p>If you have <span style=\"color:red\">MAFFT</span>, please <span style=\" font-weight:600; color:#ff0000;\">specify</span>.</p></body></html>"
            label2 = "MAFFT Path:"
            label3 = "<html><head/><body><p>If you don\'t have MAFFT, please <span style=\" font-weight:600; color:#ff0000;\">download</span>.</p></body></html>"
            self.installStatus(flag, "start")
            url = self.getURls("mafft")
            link = "<html><head/><body><p>If download failed, click <a href=\"%s\">" \
                   "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</a>" \
                   "</span> to download manually and then specify the path as indicated above.</p></body></html>" % url
            if platform.system().lower() == "windows":
                placeholdertext = "C:\\mafft-win\\mafft.bat"
                self.MAFFT_target = "mafft.bat"
            elif platform.system().lower() == "darwin":
                placeholdertext = "../mafft-mac/mafft.bat"
                self.MAFFT_target = "mafft.bat"
            else:
                placeholdertext = "/usr/bin/mafft"
                self.MAFFT_target = "All File (*)"
                link = "<html><head/><body><p><a href=\"https://mafft.cbrc.jp/alignment/software/linux.html\">" \
                       "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">MAFFT download link (make sure that you download <br>the version with RNA structural alignments)</a>" \
                       "</span></p></body></html>"
            self.lg_exePath_mafft = LG_exePath(self, label1, label2, label3, placeholdertext, flag, self.MAFFT_target, link)
            if platform.system().lower() in ["darwin", "windows"]:
                self.lg_exePath_mafft.downloadSig.connect(self.downloadMAFFT)
            self.lg_exePath_mafft.closeSig.connect(self.saveEXEpath)
            # 添加最大化按钮
            self.lg_exePath_mafft.setWindowFlags(self.lg_exePath_mafft.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.lg_exePath_mafft.exec_()
            # self.saveEXEpath("mafft", self.plugin_path + os.sep + "mafft-win")
        else:
            # 删除
            zipFile = self.plugin_path + os.sep + "mafft.zip"
            zipFolder = glob.glob(f"{self.plugin_path}{os.sep}mafft*{os.sep}")
            zipFolder = zipFolder[0] if zipFolder else ""
            if os.path.exists(zipFolder):
                self.factory.remove_dir_directly(zipFolder, removeRoot=True)
            if os.path.exists(zipFile):
                os.remove(zipFile)

            # if platform.system().lower() == "windows":
            #     zipFile = self.plugin_path + os.sep + "mafft.zip"
            #     zipFolder = self.plugin_path + os.sep + "mafft-win"
            #     if os.path.exists(zipFolder):
            #         self.factory.remove_dir_directly(zipFolder, removeRoot=True)
            #     if os.path.exists(zipFile):
            #         os.remove(zipFile)
            # elif platform.system().lower() == "darwin":
            #     zipFile = self.plugin_path + os.sep + "mafft.zip"
            #     zipFolder = self.plugin_path + os.sep + "mafft-mac"
            #     if os.path.exists(zipFolder):
            #         self.factory.remove_dir_directly(zipFolder, removeRoot=True)
            #     if os.path.exists(zipFile):
            #         os.remove(zipFile)

            self.settings.setValue("mafft", "")
            QMessageBox.information(
                self, "Settings", "<p style='line-height:25px; height:25px'>Uninstalled successfully!</p>")
            self.installStatus(flag, "uninstall")
            # download_mafft_button = self.tableWidget.cellWidget(0, 3)
            # self.installButtonSig.emit(
            #     [download_mafft_button, self.tableWidget, 0, "uninstall", self.qss_file])

    @pyqtSlot()
    def on_download_tbl2asn_button_clicked(self):
        """
        download tbl2asn
        """
        flag = "tbl2asn"
        if self.download_tbl2asn_button.text() == "Install":
            # self.installButtonSig.emit(
            #     [self.download_tbl2asn_button, self.tableWidget, 1, "start", self.qss_file])
            label1 = "<html><head/><body><p>If you have tbl2asn, please <span style=\" font-weight:600; color:#ff0000;\">specify</span>.</p></body></html>"
            label2 = "tbl2asn Path:"
            label3 = "<html><head/><body><p>If you don\'t have tbl2asn, please <span style=\" font-weight:600; color:#ff0000;\">download</span>.</p></body></html>"
            self.installStatus(flag, "start")
            link = "<html><head/><body><p>If download failed, click <a href=\"https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/tbl2asn.zip\">" \
                   "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</a>" \
                   "</span> to download manually and then specify the path as indicated above.</p></body></html>"
            if platform.system().lower() == "windows":
                placeholdertext = "C:\\win.tbl2asn\\tbl2asn.exe"
                self.TS_target = "tbl2asn.exe"
            else:
                placeholdertext = "/usr/bin/tbl2asn"
                self.TS_target = "All File (*)"
                link = "<html><head/><body><p><a href=\"ftp://ftp.ncbi.nih.gov/toolbox/ncbi_tools/converters/by_program/tbl2asn/\">" \
                       "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">tbl2asn download link (not needed in linux)</a>" \
                       "</span></p></body></html>"
            self.lg_exePath_ts = LG_exePath(self, label1, label2, label3, placeholdertext, flag,
                                               self.TS_target, link=link)
            if platform.system().lower() == "windows":
                self.lg_exePath_ts.downloadSig.connect(self.downloadTS)
            self.lg_exePath_ts.closeSig.connect(self.saveEXEpath)
            # 添加最大化按钮
            self.lg_exePath_ts.setWindowFlags(self.lg_exePath_ts.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.lg_exePath_ts.exec_()
        else:
            # 删除
            zipFile = self.plugin_path + os.sep + "tbl2asn.zip"
            zipFolder = glob.glob(f"{self.plugin_path}{os.sep}tbl2asn*{os.sep}")
            zipFolder = zipFolder[0] if zipFolder else ""
            if os.path.exists(zipFolder):
                self.factory.remove_dir_directly(zipFolder, removeRoot=True)
            if os.path.exists(zipFile):
                os.remove(zipFile)

            # if platform.system().lower() == "windows":
            #     zipFile = self.plugin_path + os.sep + "tbl2asn.zip"
            #     zipFolder = self.plugin_path + os.sep + "tbl2asn-master"
            #     if os.path.exists(zipFolder):
            #         self.factory.remove_dir_directly(zipFolder, removeRoot=True)
            #     if os.path.exists(zipFile):
            #         os.remove(zipFile)

            self.settings.setValue("tbl2asn", "")
            QMessageBox.information(
                self, "Settings", "<p style='line-height:25px; height:25px'>Uninstalled successfully!</p>")
            self.installStatus(flag, "uninstall")
            # download_tbl2asn_button = self.tableWidget.cellWidget(1, 3)
            # self.installButtonSig.emit(
            #     [download_tbl2asn_button, self.tableWidget, 1, "uninstall", self.qss_file])

    @pyqtSlot()
    def on_download_Rscript_button_clicked(self):
        """
        install Rscript
        """
        flag = "RscriptPath"
        if self.download_Rscript_button.text() == "Install":
            # self.installButtonSig.emit(
            #     [self.download_Rscript_button, self.tableWidget, 2, "start", self.qss_file])
            self.installStatus(flag, "start")
            url = self.getURls("Rscript")
            link = "<html><head/><body><p>If download failed, click <a href=\"%s\">" \
                   "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</a>" \
                   "</span> to download manually and then specify the path as indicated above.</p></body></html>" % url
            if platform.system().lower() == "windows":
                placeholdertext = "C:\\R\\bin\\Rscript.exe"
                self.R_target = "Rscript.exe"
            elif platform.system().lower() == "darwin":
                placeholdertext = "../R/bin/Rscript"
                self.R_target = "Rscript"
            else:
                placeholdertext = "/usr/bin/Rscript"
                self.R_target = "All File (*)"
                link = "<html><head/><body><p><a href=\"https://cran.r-project.org/src/base/R-3/\">" \
                       "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">R download link</a>" \
                       "</span></p></body></html>"
            self.lg_exePath = LG_exePath(self, placeholdertext=placeholdertext, flag=flag, target=self.R_target, link=link)
            if platform.system().lower() in ["darwin", "windows"]:
                self.lg_exePath.downloadSig.connect(self.downloadRscript)
            self.lg_exePath.closeSig.connect(self.saveEXEpath)
            # 添加最大化按钮
            self.lg_exePath.setWindowFlags(self.lg_exePath.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.lg_exePath.exec_()
        else:
            self.settings.setValue("RscriptPath", "")
            QMessageBox.information(
                self, "Settings", "<p style='line-height:25px; height:25px'>Uninstalled successfully!</p>")
            self.installStatus(flag, "uninstall")
            # download_Rscript_button = self.tableWidget.cellWidget(2, 3)
            # self.installButtonSig.emit(
            #     [download_Rscript_button, self.tableWidget, 2, "uninstall", self.qss_file])

    @pyqtSlot()
    def on_download_python27_button_clicked(self):
        """
        install python 2.7
        """
        flag = "python27"
        if self.download_python27_button.text() == "Install":
            # self.installButtonSig.emit(
            #     [self.download_python27_button, self.tableWidget, 3, "start", self.qss_file])
            label1 = "<html><head/><body><p>If you have <span style=\"color:red\">python 2.7</span>, please <span style=\" font-weight:600; color:#ff0000;\">specify</span> (Note that the dependencies numpy, pandas, pytables, pyparsing, scipy and sklearn must be enabled).</p></body></html>"
            label2 = "Python 2.7:"
            label3 = "<html><head/><body><p>If you don\'t have python 2.7, please <span style=\" font-weight:600; color:#ff0000;\">download</span> Anaconda (Python 2.7 graphical installer).</p></body></html>"
            self.installStatus(flag, "start")
            if platform.system().lower() in ["darwin", "windows"]:
                url = self.getURls("python27")
                link = "<html><head/><body><p>If download failed, click <a href=\"%s\">" \
                       "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</a>" \
                       "</span> to download manually and then specify the path as indicated above. <br>" \
                       "<span style=\"font-weight:600; color:red;\">We strongly encourage you to install the compiled PartitionFinder2 (click <a href=\"PF2 install\"><span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</span></a> to install), " \
                       "which doesn't rely on Python 2.7 any more!!!</span></p></body></html>" % url
            if platform.system().lower() == "windows":
                placeholdertext = "C:\\python27\\python.exe"
                self.PY_target = "python.exe"
            elif platform.system().lower() == "darwin":
                placeholdertext = "../python27/bin/python"
                self.PY_target = "All File (*)"
            else:
                placeholdertext = "/usr/bin/python"
                self.PY_target = "All File (*)"
                link = "<html><head/><body><p><a href=\"https://www.anaconda.com/download/#linux\">" \
                       "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">Anaconda2 download link</a>" \
                       "</span></p></body></html>"
            self.lg_exePath_python27 = LG_exePath(self, label1, label2, label3, placeholdertext, flag, self.PY_target, link)
            if platform.system().lower() in ["darwin", "windows"]:
                self.lg_exePath_python27.downloadSig.connect(self.downloadpython27)
            self.lg_exePath_python27.closeSig.connect(self.saveEXEpath)
            # 添加最大化按钮
            self.lg_exePath_python27.setWindowFlags(self.lg_exePath_python27.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.lg_exePath_python27.exec_()
        else:
            self.settings.setValue("python27", "")
            QMessageBox.information(
                self, "Settings", "<p style='line-height:25px; height:25px'>Uninstalled successfully!</p>")
            self.installStatus(flag, "uninstall")
            # download_python27_button = self.tableWidget.cellWidget(3, 3)
            # self.installButtonSig.emit(
            #     [download_python27_button, self.tableWidget, 3, "uninstall", self.qss_file])

    @pyqtSlot()
    def on_download_partfind_button_clicked(self):
        """
        install PartitionFinder
        """
        flag = "PF2"
        if self.download_partfind_button.text() == "Install":
            if platform.system().lower() in ["darwin", "windows"]:
                self.installStatus(flag, "start")
                url = self.getURls("PF2")
                link1 = "<html><head/><body><p>If download failed, click <a href=\"%s\">" \
                       "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</a>" \
                       "</span> to download manually and then specify the path as indicated above.</p></body></html>" % url
                url2 = self.getURls("compiled PF2")
                link2 = "<html><head/><body><p>If download failed, click <a href=\"%s\">" \
                        "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</a>" \
                        "</span> to download manually and then specify the path as indicated above.</p></body></html>" % url2
                if platform.system().lower() == "windows":
                    placeholdertext = "C:\\Partitionfinder\\partitionfinder-2.1.1"
                elif platform.system().lower() == "darwin":
                    placeholdertext = "../Partitionfinder/partitionfinder-2.1.1"
                else:
                    placeholdertext = "/usr/bin/partitionfinder-2.1.1"
                py27status = self.factory.programIsValid("python27")
                pythonOK = False if py27status == "uninstall" else True
                self.lg_exePath_PF = LG_PF2_exePath(placeholdertext, link1, link2, pythonOK, self)
                if platform.system().lower() in ["darwin", "windows"]:
                    self.lg_exePath_PF.downloadSig.connect(self.downloadPF2)
                self.lg_exePath_PF.closeSig.connect(self.saveEXEpath)
                # 添加最大化按钮
                self.lg_exePath_PF.setWindowFlags(self.lg_exePath_PF.windowFlags() | Qt.WindowMinMaxButtonsHint)
                self.lg_exePath_PF.exec_()
            else:
                label1 = "<html><head/><body><p>If you have <span style=\"color:red\">PartitionFinder2</span>, please <span style=\" font-weight:600; color:#ff0000;\">specify (folder)</span>.</p></body></html>"
                label2 = "PF2 Path:"
                label3 = "<html><head/><body><p>If you don\'t have PartitionFinder2, please <span style=\" font-weight:600; color:#ff0000;\">download</span>.</p></body></html>"
                self.installStatus(flag, "start")
                if platform.system().lower() == "windows":
                    placeholdertext = "C:\\Partitionfinder\\partitionfinder-2.1.1"
                    self.PF_target = "partitionfinder-2.1.1"
                    link = None
                elif platform.system().lower() == "darwin":
                    placeholdertext = "../Partitionfinder/partitionfinder-2.1.1"
                    self.PF_target = "partitionfinder-2.1.1"
                    link = None
                else:
                    placeholdertext = "/usr/bin/partitionfinder-2.1.1"
                    self.PF_target = "All File (*)"
                    link = "<html><head/><body><p><a href=\"https://github.com/brettc/partitionfinder/releases/tag/v2.1.1\">" \
                           "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">partitionfinder-2.1.1 download link</a>" \
                           "<span style=\" font-size:12pt;\"/></p></body></html>"
                self.lg_exePath_PF = LG_exePath(self, label1, label2, label3, placeholdertext, flag, self.PF_target, link)
                if platform.system().lower() in ["darwin", "windows"]:
                    self.lg_exePath_PF.downloadSig.connect(self.downloadPF2)
                self.lg_exePath_PF.closeSig.connect(self.saveEXEpath)
                # 添加最大化按钮
                self.lg_exePath_PF.setWindowFlags(self.lg_exePath_PF.windowFlags() | Qt.WindowMinMaxButtonsHint)
                self.lg_exePath_PF.exec_()
        else:
            # 删除
            def deleteFiles():
                zipFile = self.plugin_path + os.sep + "partitionfinder.zip"
                zipFolder = glob.glob(f"{self.plugin_path}{os.sep}partitionfinder*{os.sep}")
                zipFolder = zipFolder[0] if zipFolder else ""
                if os.path.exists(zipFolder):
                    self.factory.remove_dir_directly(zipFolder, removeRoot=True)
                if os.path.exists(zipFile):
                    os.remove(zipFile)

                # zipFile = self.plugin_path + os.sep + "partitionfinder-2.1.1.zip"
                # zipFolder = self.plugin_path + os.sep + "partitionfinder-2.1.1"
                # if os.path.exists(zipFolder):
                #     self.factory.remove_dir_directly(zipFolder, removeRoot=True)
                # if os.path.exists(zipFile):
                #     os.remove(zipFile)
            def deleteFinished(flag):
                self.settings.setValue("PF2", "")
                self.refreshPython27()
                self.installStatus(flag, "uninstall")
                QMessageBox.information(
                    self, "Settings",
                    "<p style='line-height:25px; height:25px'>Uninstalled successfully!</p>")
            if platform.system().lower() in ["darwin", "windows"]:
                self.zipSig.emit("Removing")
                deleteWorker = WorkThread(deleteFiles, parent=self)
                deleteWorker.finished.connect(lambda: [self.zipSig.emit("Unzip finished"),
                                                       deleteFinished(flag),
                                                       ])
                deleteWorker.start()
            else:
                deleteFinished(flag)

    @pyqtSlot()
    def on_download_gblocks_button_clicked(self):
        """
        install Gblocks
        """
        flag = "gblocks"
        if self.download_gblocks_button.text() == "Install":
            # self.installButtonSig.emit(
            #     [self.download_gblocks_button, self.tableWidget, 5, "start", self.qss_file])
            label1 = "<html><head/><body><p>If you have <span style=\"color:red\">Gblocks 0.91b</span>, please <span style=\" font-weight:600; color:#ff0000;\">specify</span>.</p></body></html>"
            label2 = "Gblocks Path:"
            label3 = "<html><head/><body><p>If you don\'t have Gblocks, please <span style=\" font-weight:600; color:#ff0000;\">download</span>.</p></body></html>"
            self.installStatus(flag, "start")
            url = self.getURls("gblocks")
            link = "<html><head/><body><p>If download failed, click <a href=\"%s\">" \
                   "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</a>" \
                   "</span> to download manually and then specify the path as indicated above.</p></body></html>" % url
            if platform.system().lower() == "windows":
                placeholdertext = "C:\\Gblocks_0.91b\\Gblocks.exe"
                self.GB_target = "Gblocks.exe"
            elif platform.system().lower() == "darwin":
                placeholdertext = "../Gblocks_0.91b/Gblocks"
                self.GB_target = "Gblocks"
            else:
                placeholdertext = "/usr/bin/Gblocks"
                self.GB_target = "All File (*)"
                link = "<html><head/><body><p><a href=\"http://molevol.cmima.csic.es/castresana/Gblocks.html\">" \
                       "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">Gblocks_0.91b download link</a>" \
                       "</span></p></body></html>"
            self.lg_exePath_gb = LG_exePath(self, label1, label2, label3, placeholdertext, flag, self.GB_target, link)
            if platform.system().lower() in ["darwin", "windows"]:
                self.lg_exePath_gb.downloadSig.connect(self.downloadGB)
            self.lg_exePath_gb.closeSig.connect(self.saveEXEpath)
            # 添加最大化按钮
            self.lg_exePath_gb.setWindowFlags(self.lg_exePath_gb.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.lg_exePath_gb.exec_()
        else:
            # 删除
            zipFile = self.plugin_path + os.sep + "Gblocks.zip"
            zipFolder = glob.glob(f"{self.plugin_path}{os.sep}Gblocks*{os.sep}")
            zipFolder = zipFolder[0] if zipFolder else ""
            if os.path.exists(zipFolder):
                self.factory.remove_dir_directly(zipFolder, removeRoot=True)
            if os.path.exists(zipFile):
                os.remove(zipFile)

            # if platform.system().lower() in ["windows", "darwin"]:
            #     zipFile = self.plugin_path + os.sep + "Gblocks.zip"
            #     zipFolder = self.plugin_path + os.sep + "Gblocks_0.91b"
            #     if os.path.exists(zipFolder):
            #         self.factory.remove_dir_directly(zipFolder, removeRoot=True)
            #     if os.path.exists(zipFile):
            #         os.remove(zipFile)
            self.settings.setValue("gblocks", "")
            QMessageBox.information(
                self, "Settings", "<p style='line-height:25px; height:25px'>Uninstalled successfully!</p>")
            self.installStatus(flag, "uninstall")
            # download_button = self.tableWidget.cellWidget(5, 3)
            # self.installButtonSig.emit(
            #     [download_button, self.tableWidget, 5, "uninstall", self.qss_file])

    @pyqtSlot()
    def on_download_iq_tree_button_clicked(self):
        """
        install IQ-TREE
        """
        flag = "iq-tree"
        if self.download_iq_tree_button.text() == "Install":
            # self.installButtonSig.emit(
            #     [self.download_iq_tree_button, self.tableWidget, 6, "start", self.qss_file])
            label1 = "<html><head/><body><p>If you have <span style=\"color:red\">IQ-TREE v. 1.6.8</span>, please <span style=\" font-weight:600; color:#ff0000;\">specify</span>.</p></body></html>"
            label2 = "IQ-TREE Path:"
            label3 = "<html><head/><body><p>If you don\'t have IQ-TREE, please <span style=\" font-weight:600; color:#ff0000;\">download</span>.</p></body></html>"
            self.installStatus(flag, "start")
            url = self.getURls("iq-tree")
            link = "<html><head/><body><p>If download failed, click <a href=\"%s\">" \
                   "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</a>" \
                   "</span> to download manually and then specify the path as indicated above.</p></body></html>" % url
            if platform.system().lower() == "windows":
                placeholdertext = "C:\\iqtree-1.6.8-Windows\\bin\\iqtree.exe"
                self.IQ_target = ["iqtree.exe", "iqtree2.exe"]
            elif platform.system().lower() == "darwin":
                placeholdertext = "../iqtree-1.6.8-MacOSX/bin/iqtree"
                self.IQ_target = ["iqtree", "iqtree2"]
            else:
                placeholdertext = "/usr/bin/iqtree"
                self.IQ_target = "All File (*)"
                link = "<html><head/><body><p><a href=\"http://www.iqtree.org/#download\">" \
                       "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">IQ-TREE download link</a>" \
                       "</span></p></body></html>"
            self.lg_exePath_iq = LG_exePath(self, label1, label2, label3, placeholdertext, flag, self.IQ_target, link)
            if platform.system().lower() in ["darwin", "windows"]:
                self.lg_exePath_iq.downloadSig.connect(self.downloadIQ)
            self.lg_exePath_iq.closeSig.connect(self.saveEXEpath)
            # 添加最大化按钮
            self.lg_exePath_iq.setWindowFlags(self.lg_exePath_iq.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.lg_exePath_iq.exec_()
        else:
            # 删除
            zipFile = self.plugin_path + os.sep + "iqtree.zip"
            zipFolder = glob.glob(f"{self.plugin_path}{os.sep}iqtree*{os.sep}")
            zipFolder = zipFolder[0] if zipFolder else ""
            if os.path.exists(zipFolder):
                self.factory.remove_dir_directly(zipFolder, removeRoot=True)
            if os.path.exists(zipFile):
                os.remove(zipFile)
            self.settings.setValue("iq-tree", "")
            QMessageBox.information(
                self, "Settings", "<p style='line-height:25px; height:25px'>Uninstalled successfully!</p>")
            self.installStatus(flag, "uninstall")
            # download_button = self.tableWidget.cellWidget(6, 3)
            # self.installButtonSig.emit(
            #     [download_button, self.tableWidget, 6, "uninstall", self.qss_file])

    @pyqtSlot()
    def on_download_MrBayes_button_clicked(self):
        """
        install MrBayes
        """
        flag = "MrBayes"
        if self.download_MrBayes_button.text() == "Install":
            # self.installButtonSig.emit(
            #     [self.download_MrBayes_button, self.tableWidget, 6, "start", self.qss_file])
            label1 = "<html><head/><body><p>If you have <span style=\"color:red\">MrBayes 3.2.6 (v3.2 or higher)</span>, please <span style=\" font-weight:600; color:#ff0000;\">specify</span>.</p></body></html>"
            label2 = "MrBayes Path:"
            label3 = "<html><head/><body><p>If you don\'t have MrBayes, please <span style=\" font-weight:600; color:#ff0000;\">download</span>.</p></body></html>"
            self.installStatus(flag, "start")
            url = self.getURls("MrBayes")
            link = "<html><head/><body><p>If download failed, click <a href=\"%s\">" \
                   "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</a>" \
                   "</span> to download manually and then specify the path as indicated above.</p></body></html>" % url
            if platform.system().lower() == "windows":
                placeholdertext = "C:\\MrBayes\\mrbayes_x64.exe" if self.pc_bit == "64bit" else "C:\\MrBayes\\mrbayes_x86.exe"
                self.MB_target = ["mrbayes_x64.exe", "mb.3.2.7-win64.exe"] if self.pc_bit == "64bit" \
                                                        else ["mrbayes_x86.exe", "mb.3.2.7-win32.exe"]
            elif platform.system().lower() == "darwin":
                placeholdertext = "../MrBayes/mb"
                self.MB_target = "mb"
            else:
                placeholdertext = "/usr/bin/mrbayes326/bin/mb"
                self.MB_target = "All File (*)"
                link = "<html><head/><body><p><a href=\"https://codeload.github.com/NBISweden/MrBayes/tar.gz/v3.2.6\">" \
                       "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">MrBayes download link</a>" \
                       "</span></p></body></html>"
            self.lg_exePath_mb = LG_exePath(self, label1, label2, label3, placeholdertext, flag, self.MB_target, link)
            if platform.system().lower() in ["darwin", "windows"]:
                self.lg_exePath_mb.downloadSig.connect(self.downloadMB)
            self.lg_exePath_mb.closeSig.connect(self.saveEXEpath)
            # 添加最大化按钮
            self.lg_exePath_mb.setWindowFlags(self.lg_exePath_mb.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.lg_exePath_mb.exec_()
        else:
            # 删除
            zipFile = self.plugin_path + os.sep + "MrBayes.zip"
            zipFolder = glob.glob(f"{self.plugin_path}{os.sep}MrBayes*{os.sep}")
            zipFolder = zipFolder[0] if zipFolder else ""
            if os.path.exists(zipFolder):
                self.factory.remove_dir_directly(zipFolder, removeRoot=True)
            if os.path.exists(zipFile):
                os.remove(zipFile)

            # if platform.system().lower() in ["darwin", "windows"]:
            #     zipFile = self.plugin_path + os.sep + "MrBayes.zip"
            #     zipFolder = self.plugin_path + os.sep + "MrBayes"
            #     if os.path.exists(zipFolder):
            #         self.factory.remove_dir_directly(zipFolder, removeRoot=True)
            #     if os.path.exists(zipFile):
            #         os.remove(zipFile)
            self.settings.setValue("MrBayes", "")
            QMessageBox.information(
                self, "Settings", "<p style='line-height:25px; height:25px'>Uninstalled successfully!</p>")
            self.installStatus(flag, "uninstall")
            # download_button = self.tableWidget.cellWidget(7, 3)
            # self.installButtonSig.emit(
            #     [download_button, self.tableWidget, 7, "uninstall", self.qss_file])

    @pyqtSlot()
    def on_download_mpi_button_clicked(self):
        """
        download mpi
        """
        flag = "mpi"
        if self.download_mpi_button.text() == "Install":
            label1 = "<html><head/><body><p>If you have <span style=\"color:red\">MPICH2</span>, please <span style=\" font-weight:600; color:#ff0000;\">specify</span>.</p></body></html>"
            label2 = "MPICH2 path:"
            label3 = "<html><head/><body><p>If you don\'t have MPICH2, please <span style=\" font-weight:600; color:#ff0000;\">configure</span>.</p></body></html>"
            self.installStatus(flag, "start")
            if platform.system().lower() == "darwin":
                placeholdertext = "/usr/local/bin/mpirun"
                self.mpi_target = "All File (*)"
                link = "<html><head/><body><p><a href=\"http://macappstore.org/mpich2/\">" \
                       "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">MPICH2 configure tutorial</a>" \
                       "</span></p></body></html>"
            else:
                placeholdertext = "/usr/bin/mpirun"
                self.mpi_target = "All File (*)"
                link = "<html><head/><body><p><a href=\"http://mpitutorial.com/tutorials/installing-mpich2/\">" \
                       "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">MPICH2 configure tutorial.</a>" \
                       "</span><br><span style=\" font-size:12pt;\">Or using \"sudo apt install mpich\"</span></p></body></html>"
            self.lg_exePath_mpi = LG_exePath(self, label1, label2, label3, placeholdertext, flag, self.mpi_target,
                                               link)
            self.lg_exePath_mpi.closeSig.connect(self.saveEXEpath)
            # 添加最大化按钮
            self.lg_exePath_mpi.setWindowFlags(self.lg_exePath_mpi.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.lg_exePath_mpi.exec_()
            # self.saveEXEpath("mpi", self.plugin_path + os.sep + "mpi-win")
        else:
            # 删除
            self.settings.setValue("mpi", "")
            QMessageBox.information(
                self, "Settings", "<p style='line-height:25px; height:25px'>Uninstalled successfully!</p>")
            self.installStatus(flag, "uninstall")

    @pyqtSlot()
    def on_download_java_button_clicked(self):
        """
        install java
        """
        flag = "java"
        if self.download_java_button.text() == "Install":
            # self.installButtonSig.emit(
            #     [self.download_python27_button, self.tableWidget, 3, "start", self.qss_file])
            label1 = "<html><head/><body><p>If you have <span style=\"color:red\">JAVA (JRE > 1.5)</span>, please <span style=\" font-weight:600; color:#ff0000;\">specify</span>.</p></body></html>"
            label2 = "JAVA:"
            label3 = "<html><head/><body><p>If you don\'t have JAVA, please <span style=\" font-weight:600; color:#ff0000;\">configure</span>.</p></body></html>"
            self.installStatus(flag, "start")
            # if platform.system().lower() in ["darwin", "windows"]:
            #     url = self.getURls("python27")
            #     link = "<html><head/><body><p>If download failed, click <a href=\"%s\">" \
            #            "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</a>" \
            #            "</span> to download manually and then specify the path as indicated above. <br>" \
            #            "<span style=\"font-weight:600; color:red;\">We strongly encourage you to install the compiled PartitionFinder2 (click <a href=\"PF2 install\"><span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</span></a> to install), " \
            #            "which doesn't rely on Python 2.7 any more!!!</span></p></body></html>" % url
            link = "<html><head/><body><p>Please download and install java from <a href=\"https://www.java.com/en/download/\">" \
                   "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</a>" \
                   "</span>. Normally JAVA will be automatically added to environment variables, so when you finish the " \
                   "installation, you need to close and reopen PhyloSuite to see if it installed successfully" \
                   " (if you see \"Uninstall\" button, it means success). If you did not succeed, please check the JRE version (> 1.5) or specify" \
                   " the JAVA executable file manually (using options above).</p></body></html>"
            if platform.system().lower() == "windows":
                placeholdertext = "C:\\Java\\javapath\\java.exe"
                self.JAVA_target = "java.exe"
            elif platform.system().lower() == "darwin":
                placeholdertext = "/usr/bin/java"
                self.JAVA_target = "All File (*)"
            else:
                placeholdertext = "/usr/bin/java"
                self.JAVA_target = "All File (*)"
            self.lg_exePath_java = LG_exePath(self, label1, label2, label3, placeholdertext, flag, self.JAVA_target,
                                                  link)
            # if platform.system().lower() in ["darwin", "windows"]:
            #     self.lg_exePath_java.downloadSig.connect(self.downloadpython27)
            self.lg_exePath_java.closeSig.connect(self.saveEXEpath)
            # 添加最大化按钮
            self.lg_exePath_java.setWindowFlags(self.lg_exePath_java.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.lg_exePath_java.exec_()
        else:
            self.settings.setValue("java", "")
            QMessageBox.information(
                self, "Settings", "<p style='line-height:25px; height:25px'>Uninstalled successfully!</p>")
            self.installStatus(flag, "uninstall")
            # download_python27_button = self.tableWidget.cellWidget(3, 3)
            # self.installButtonSig.emit(
            #     [download_python27_button, self.tableWidget, 3, "uninstall", self.qss_file])

    @pyqtSlot()
    def on_download_macse_button_clicked(self):
        """
        install MACSE
        """
        flag = "macse"
        if self.download_macse_button.text() == "Install":
            # self.installButtonSig.emit(
            #     [self.download_python27_button, self.tableWidget, 3, "start", self.qss_file])
            label1 = "<html><head/><body><p>If you have <span style=\"color:red\">MACSE v2.03</span>, please <span style=\" font-weight:600; color:#ff0000;\">specify</span>.</p></body></html>"
            label2 = "MACSE:"
            label3 = "<html><head/><body><p>If you don\'t have MACSE, please <span style=\" font-weight:600; color:#ff0000;\">download</span>.</p></body></html>"
            self.installStatus(flag, "start")
            url = self.getURls("macse")
            link = "<html><head/><body><p>If download failed, click <a href=\"%s\">" \
                   "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</a>" \
                   "</span> to download manually and then specify the path as indicated above.</p></body></html>" % url
            self.MACSE_target = ["macse.jar", "macse_v2.03.jar", "macse_v2.05.jar", "macse_v2.07.jar"]
            if platform.system().lower() == "windows":
                placeholdertext = "C:\\MACSE\\macse*.jar"
            elif platform.system().lower() in "darwin":
                placeholdertext = "../MACSE/macse*.jar"
            else:
                placeholdertext = "../MACSE/macse*.jar"
                link = "<html><head/><body><p><a href=\"https://bioweb.supagro.inra.fr/macse/releases/macse_v2.05.jar\">" \
                       "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">MACSE download link</a>" \
                       "</span>. Please download it and specify the MACSE executable" \
                       " file (<span style=\" font-weight:600; color:#ff0000;\">macse_v2.05.jar</span>) manually " \
                       "(using options above).</p></body></html>"
            self.lg_exePath_macse = LG_exePath(self, label1, label2, label3, placeholdertext, flag, self.MACSE_target,
                                                  link)
            if platform.system().lower() in ["darwin", "windows"]:
                self.lg_exePath_macse.downloadSig.connect(self.downloadMS)
            self.lg_exePath_macse.closeSig.connect(self.saveEXEpath)
            # 添加最大化按钮
            self.lg_exePath_macse.setWindowFlags(self.lg_exePath_macse.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.lg_exePath_macse.exec_()
        else:
            # 删除
            zipFile = self.plugin_path + os.sep + "macse.jar.zip"
            exeFile = glob.glob(f"{self.plugin_path}{os.sep}macse*.jar")
            exeFile = exeFile[0] if exeFile else ""
            if os.path.exists(exeFile):
                os.remove(exeFile)
            if os.path.exists(zipFile):
                os.remove(zipFile)

            # exeFile = self.plugin_path + os.sep + "macse_v2.03.jar"
            # zipFile = self.plugin_path + os.sep + "macse.jar.zip"
            # if os.path.exists(exeFile):
            #     os.remove(exeFile)
            # if os.path.exists(zipFile):
            #     os.remove(zipFile)
            self.settings.setValue("macse", "")
            QMessageBox.information(
                self, "Settings", "<p style='line-height:25px; height:25px'>Uninstalled successfully!</p>")
            self.installStatus(flag, "uninstall")
            # download_python27_button = self.tableWidget.cellWidget(3, 3)
            # self.installButtonSig.emit(
            #     [download_python27_button, self.tableWidget, 3, "uninstall", self.qss_file])

    @pyqtSlot()
    def on_download_trimAl_button_clicked(self):
        """
        install trimAl
        """
        flag = "trimAl"
        if self.download_trimAl_button.text() == "Install":
            # self.installButtonSig.emit(
            #     [self.download_python27_button, self.tableWidget, 3, "start", self.qss_file])
            label1 = "<html><head/><body><p>If you have <span style=\"color:red\">trimAl v1.2</span>, please <span style=\" font-weight:600; color:#ff0000;\">specify</span>.</p></body></html>"
            label2 = "trimAl:"
            label3 = "<html><head/><body><p>If you don\'t have trimAl, please <span style=\" font-weight:600; color:#ff0000;\">configure</span>.</p></body></html>"
            self.installStatus(flag, "start")
            if platform.system().lower() == "windows":
                placeholdertext = "C:\\trimAl\\trimal.exe"
                url = self.getURls("trimAl")
                link = "<html><head/><body><p>If download failed, click <a href=\"%s\">" \
                       "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</a>" \
                       "</span> to download manually and then specify the path as indicated above.</p></body></html>" % url
                self.trimAl_target = "trimal.exe"
            elif platform.system().lower() in "darwin":
                placeholdertext = "../trimAl/trimal"
                link = "<html><head/><body><p><span style=\" font-weight:600; color:#ff0000;\">If you already have " \
                       "<a href=\"https://docs.conda.io/en/latest/\">Conda</a> installed, " \
                       "you can install trimAl via the \"conda install -c bioconda trimal\" or " \
                       "\"conda install -c bioconda/label/cf201901 trimal\" command. </span><br>" \
                       "If you don't have Conda, you need to download trimAl " \
                       "<a href=\"http://trimal.cgenomics.org/downloads\">" \
                       "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</span></a> " \
                       "and install it following this " \
                       "<a href=\"https://github.com/scapella/trimal/blob/trimAl/README\">" \
                       "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">instructions" \
                       "</span></a>. If you are adding trimAl to environment variables, when you finish the installation, " \
                       "you need to close and reopen PhyloSuite to see if it installed successfully" \
                       " (if you see \"Uninstall\" button, it means success). Otherwise you need to specify the trimAl executable" \
                       " file (<span style=\" font-weight:600; color:#ff0000;\">trimal</span>) manually (using options above).</p>" \
                       "</body></html>"
                self.trimAl_target = "trimal"
            else:
                placeholdertext = "../trimAl/trimal"
                link = "<html><head/><body><p><span style=\" font-weight:600; color:#ff0000;\">If you already have " \
                       "<a href=\"https://docs.conda.io/en/latest/\">Conda</a> installed, " \
                       "you can install trimAl via the \"conda install -c bioconda trimal\" or " \
                       "\"conda install -c bioconda/label/cf201901 trimal\" command. </span><br>" \
                       "If you don't have Conda, you need to download trimAl " \
                       "<a href=\"http://trimal.cgenomics.org/downloads\">" \
                       "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</span></a> " \
                       "and install it following this " \
                       "<a href=\"https://github.com/scapella/trimal/blob/trimAl/README\">" \
                       "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">instructions" \
                       "</span></a>. If you are adding trimAl to environment variables, when you finish the installation, " \
                       "you need to close and reopen PhyloSuite to see if it installed successfully" \
                       " (if you see \"Uninstall\" button, it means success). Otherwise you need to specify the trimAl executable" \
                       " file (<span style=\" font-weight:600; color:#ff0000;\">trimal</span>) manually (using options above).</p>" \
                       "</body></html>"
                self.trimAl_target = "trimal"
            self.lg_exePath_trimAl = LG_exePath(self, label1, label2, label3, placeholdertext, flag, self.trimAl_target,
                                               link)
            if platform.system().lower() in ["darwin", "windows"]:
                self.lg_exePath_trimAl.downloadSig.connect(self.downloadTrimAl)
            self.lg_exePath_trimAl.closeSig.connect(self.saveEXEpath)
            # 添加最大化按钮
            self.lg_exePath_trimAl.setWindowFlags(self.lg_exePath_trimAl.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.lg_exePath_trimAl.exec_()
        else:
            # 删除
            zipFile = self.plugin_path + os.sep + "trimal.zip"
            zipFolder = glob.glob(f"{self.plugin_path}{os.sep}trimAl*{os.sep}")
            zipFolder = zipFolder[0] if zipFolder else ""
            if os.path.exists(zipFolder):
                self.factory.remove_dir_directly(zipFolder, removeRoot=True)
            if os.path.exists(zipFile):
                os.remove(zipFile)

            # if platform.system().lower() == "windows":
            #     zipFile = self.plugin_path + os.sep + "trimal.zip"
            #     zipFolder = self.plugin_path + os.sep + "trimAl"
            #     if os.path.exists(zipFolder):
            #         self.factory.remove_dir_directly(zipFolder, removeRoot=True)
            #     if os.path.exists(zipFile):
            #         os.remove(zipFile)
            self.settings.setValue("trimAl", "")
            QMessageBox.information(
                self, "Settings", "<p style='line-height:25px; height:25px'>Uninstalled successfully!</p>")
            self.installStatus(flag, "uninstall")

    @pyqtSlot()
    def on_download_perl_button_clicked(self):
        """
        install perl
        """
        flag = "perl"
        if self.download_perl_button.text() == "Install":
            label1 = "<html><head/><body><p>If you have <span style=\"color:red\">perl (> 5)</span>, please <span style=\" font-weight:600; color:#ff0000;\">specify</span>.</p></body></html>"
            label2 = "perl:"
            label3 = "<html><head/><body><p>If you don\'t have perl, please <span style=\" font-weight:600; color:#ff0000;\">configure</span>.</p></body></html>"
            self.installStatus(flag, "start")
            link = "<html><head/><body><p>Please download and install Perl from <a href=\"https://www.perl.org/get.html\">" \
                   "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</a>" \
                   "</span>. Normally Perl will be automatically added to environment variables, so when you finish the " \
                   "installation, you need to close and reopen PhyloSuite to see if it installed successfully" \
                   " (if you see \"Uninstall\" button, it means success). If you did not succeed, please specify" \
                   " the Perl executable file manually (using options above).</p></body></html>"
            if platform.system().lower() == "windows":
                placeholdertext = "C:\\Perl\\perl\\bin\\perl.exe"
                self.perl_target = "perl.exe"
            elif platform.system().lower() == "darwin":
                placeholdertext = "/usr/bin/perl"
                self.perl_target = "All File (*)"
            else:
                placeholdertext = "/usr/bin/perl"
                self.perl_target = "All File (*)"
            self.lg_exePath_perl = LG_exePath(self, label1, label2, label3, placeholdertext, flag, self.perl_target,
                                              link)
            self.lg_exePath_perl.closeSig.connect(self.saveEXEpath)
            # 添加最大化按钮
            self.lg_exePath_perl.setWindowFlags(self.lg_exePath_perl.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.lg_exePath_perl.exec_()
        else:
            self.settings.setValue("perl", "")
            QMessageBox.information(
                self, "Settings", "<p style='line-height:25px; height:25px'>Uninstalled successfully!</p>")
            self.installStatus(flag, "uninstall")

    @pyqtSlot()
    def on_download_HmmCleaner_button_clicked(self):
        """
        install HmmCleaner
        """
        flag = "HmmCleaner"
        if self.download_HmmCleaner_button.text() == "Install":
            label1 = "<html><head/><body><p>If you have <span style=\"color:red\">HmmCleaner</span>, please <span style=\" font-weight:600; color:#ff0000;\">specify</span>.</p></body></html>"
            label2 = "HmmCleaner:"
            label3 = "<html><head/><body><p>If you don\'t have HmmCleaner, please <span style=\" font-weight:600; color:#ff0000;\">configure</span>.</p></body></html>"
            self.installStatus(flag, "start")
            country = self.factory.path_settings.value("country", "UK")
            url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/PhyloSuite-demo/how-to-configure-plugins/#2-4-HmmCleaner-configuration" if \
                country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/PhyloSuite-demo/how-to-configure-plugins/#2-4-HmmCleaner-configuration"
            link = "<html><head/><body><p>Please install HmmCleaner following this " \
                   "<a href=\"%s\">" \
                   "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">instruction</a>" \
                   "</span>. If you are adding HmmCleaner to environment variables, when you finish the installation," \
                   " you need to close and reopen PhyloSuite to see if it installed successfully" \
                   " (if you see \"Uninstall\" button, it means success). Otherwise you need to specify the HmmCleaner executable" \
                   " file (<span style=\" font-weight:600; color:#ff0000;\">HmmCleaner.pl</span>) manually (using options above).</p>" \
                   "<span style=\" font-weight:600; color:#ff0000;\">Please note that HmmCleaner also relies on Perl 5 " \
                   "and HMMER (all executables from HMMER have to be added in the environment variable $PATH).</span></body></html>"%url
            if platform.system().lower() == "windows":
                placeholdertext = "C:path-to-HmmCleaner/HmmCleaner.pl"
                self.HmmCleaner_target = "HmmCleaner.pl"
            elif platform.system().lower() == "darwin":
                placeholdertext = "/usr/bin/HmmCleaner.pl"
                self.HmmCleaner_target = "HmmCleaner.pl"
            else:
                placeholdertext = "/usr/bin/HmmCleaner.pl"
                self.HmmCleaner_target = "HmmCleaner.pl"
            self.lg_exePath_HmmCleaner = LG_exePath(self, label1, label2, label3, placeholdertext, flag, self.HmmCleaner_target,
                                              link)
            self.lg_exePath_HmmCleaner.closeSig.connect(self.saveEXEpath)
            # 添加最大化按钮
            self.lg_exePath_HmmCleaner.setWindowFlags(self.lg_exePath_HmmCleaner.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.lg_exePath_HmmCleaner.exec_()
        else:
            self.settings.setValue("HmmCleaner", "")
            QMessageBox.information(
                self, "Settings", "<p style='line-height:25px; height:25px'>Uninstalled successfully!</p>")
            self.installStatus(flag, "uninstall")

    @pyqtSlot()
    def on_download_CodonW_button_clicked(self):
        """
        install CodonW
        """
        flag = "CodonW"
        if self.download_CodonW_button.text() == "Install":
            # self.installButtonSig.emit(
            #     [self.download_python27_button, self.tableWidget, 3, "start", self.qss_file])
            label1 = "<html><head/><body><p>If you have <span style=\"color:red\">CodonW v1.4.4</span>, please <span style=\" font-weight:600; color:#ff0000;\">specify</span>.</p></body></html>"
            label2 = "CodonW:"
            label3 = "<html><head/><body><p>If you don\'t have CodonW, please <span style=\" font-weight:600; color:#ff0000;\">configure</span>.</p></body></html>"
            self.installStatus(flag, "start")
            if platform.system().lower() == "windows":
                placeholdertext = "C:\\CodonW\\CodonW.exe"
                url = self.getURls("CodonW")
                link = "<html><head/><body><p>If download failed, click <a href=\"%s\">" \
                       "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</a>" \
                       "</span> to download manually and then specify the path as indicated above.</p></body></html>" % url
                self.CodonW_target = "CodonW.exe"
            elif platform.system().lower() in "darwin":
                placeholdertext = "../CodonW/codonw"
                link = "<html><head/><body><p><span style=\" font-weight:600; color:#ff0000;\">If you already have " \
                       "<a href=\"https://docs.conda.io/en/latest/\">Conda</a> installed, " \
                       "you can install CodonW via the \"conda install -c bioconda codonw\" or " \
                       "\"conda install -c bioconda/label/cf201901 codonw\" command. </span><br>" \
                       "If you don't have Conda, you need to download CodonW " \
                       "<a href=\"http://codonw.sourceforge.net/#Downloading%20and%20Installation\">" \
                       "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</span></a>. " \
                       "If you are adding CodonW to environment variables, when you finish the installation, " \
                       "you need to close and reopen PhyloSuite to see if it installed successfully" \
                       " (if you see \"Uninstall\" button, it means success). Otherwise you need to specify the CodonW executable" \
                       " file (<span style=\" font-weight:600; color:#ff0000;\">CodonW</span>) manually (using options above).</p>" \
                       "</body></html>"
                self.CodonW_target = "codonw"
            else:
                placeholdertext = "../CodonW/codonw"
                link = "<html><head/><body><p><span style=\" font-weight:600; color:#ff0000;\">If you already have " \
                       "<a href=\"https://docs.conda.io/en/latest/\">Conda</a> installed, " \
                       "you can install CodonW via the \"conda install -c bioconda codonw\" or " \
                       "\"conda install -c bioconda/label/cf201901 codonw\" command. </span><br>" \
                       "If you don't have Conda, you need to download CodonW " \
                       "<a href=\"http://codonw.sourceforge.net/#Downloading%20and%20Installation\">" \
                       "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</span></a>. " \
                       "If you are adding CodonW to environment variables, when you finish the installation, " \
                       "you need to close and reopen PhyloSuite to see if it installed successfully" \
                       " (if you see \"Uninstall\" button, it means success). Otherwise you need to specify the CodonW executable" \
                       " file (<span style=\" font-weight:600; color:#ff0000;\">CodonW</span>) manually (using options above).</p>" \
                       "</body></html>"
                self.CodonW_target = "codonw"
            self.lg_exePath_CodonW = LG_exePath(self, label1, label2, label3, placeholdertext, flag, self.CodonW_target,
                                                link)
            if platform.system().lower() in ["darwin", "windows"]:
                self.lg_exePath_CodonW.downloadSig.connect(self.downloadCodonW)
            self.lg_exePath_CodonW.closeSig.connect(self.saveEXEpath)
            # 添加最大化按钮
            self.lg_exePath_CodonW.setWindowFlags(self.lg_exePath_CodonW.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.lg_exePath_CodonW.exec_()
        else:
            # 删除
            zipFile = self.plugin_path + os.sep + "CodonW.zip"
            zipFolder = glob.glob(f"{self.plugin_path}{os.sep}*CodonW*{os.sep}")
            zipFolder = zipFolder[0] if zipFolder else ""
            if os.path.exists(zipFolder):
                self.factory.remove_dir_directly(zipFolder, removeRoot=True)
            if os.path.exists(zipFile):
                os.remove(zipFile)

            # if platform.system().lower() == "windows":
            #     zipFile = self.plugin_path + os.sep + "CodonW.zip"
            #     zipFolder = self.plugin_path + os.sep + "Win32CodonW"
            #     if os.path.exists(zipFolder):
            #         self.factory.remove_dir_directly(zipFolder, removeRoot=True)
            #     if os.path.exists(zipFile):
            #         os.remove(zipFile)
            # elif platform.system().lower() == "darwin":
            #     zipFile = self.plugin_path + os.sep + "CodonW.zip"
            #     zipFolder = self.plugin_path + os.sep + "MacOSCodonW"
            #     if os.path.exists(zipFolder):
            #         self.factory.remove_dir_directly(zipFolder, removeRoot=True)
            #     if os.path.exists(zipFile):
            #         os.remove(zipFile)
            self.settings.setValue("CodonW", "")
            QMessageBox.information(
                self, "Settings", "<p style='line-height:25px; height:25px'>Uninstalled successfully!</p>")
            self.installStatus(flag, "uninstall")

    @pyqtSlot()
    def on_download_plot_engine_button_clicked(self):
        """
        install plot engine for phylosuite
        """
        flag = "plot_engine"
        if self.download_plot_engine_button.text() == "Install":
            reply = QMessageBox.information(
                self,
                "Reminder",
                "<p style='line-height:25px; height:25px'>"
                "Note that only the latest version of \"PhyloSuite\" can download and configure the plot engine. <br><br>"
                "Note that if you installed \"PhyloSuite\" using \"pip\", "
                "please select \"Ok\" button and install necessary packages via: <br>"
                "pip install plotly==5.10.0<br>"
                "pip install pandas==1.1.5<br>"
                "pip install kaleido==0.2.1<br>"
                "pip install statsmodels==0.10.2<br><br>"
                "Otherwise select the \"Ignore\" button to continue downloading the plot engine!</p>",
                QMessageBox.Ok,
                QMessageBox.Ignore)
            if reply == QMessageBox.Ignore:
                items = ("Chinese resource", "Coding", "Gitlab", "Github")
                item, ok = QInputDialog.getItem(self, "Select the preferred download resource",
                                                      "Resource:", items, 0, False)
                if ok and item:
                    self.downloadPlotEngine(item)
        else:
            # 删除
            # 删除plotly、pandas那几个文件夹就行或者直接显示删除成功，让用户重新下载
            # zipFile = self.plugin_path + os.sep + "CodonW.zip"
            # zipFolder = glob.glob(f"{self.plugin_path}{os.sep}*CodonW*{os.sep}")
            # zipFolder = zipFolder[0] if zipFolder else ""
            # if os.path.exists(zipFolder):
            #     self.factory.remove_dir_directly(zipFolder, removeRoot=True)
            # if os.path.exists(zipFile):
            #     os.remove(zipFile)
            # self.settings.setValue("CodonW", "")
            QMessageBox.information(
                self, "Settings", "<p style='line-height:25px; height:25px'>Uninstalled successfully!</p>")
            self.installStatus(flag, "uninstall")

    def plugin_download_button_clicked(self, **kwargs):
        """
        install plugins, 适用于所有的plugins
        plugin_name
        button

        """
        flag = kwargs["plugin_name"]
        install_button = getattr(self, f"install_button{self.dict_name_row[flag]}")
        if install_button.text() == "Install":
            # self.installButtonSig.emit(
            #     [self.download_python27_button, self.tableWidget, 3, "start", self.qss_file])
            label1 = kwargs["label1"]
            label2 = kwargs["label2"]
            label3 = kwargs["label3"]
            self.installStatus(flag, "start")
            if platform.system().lower() == "windows":
                placeholdertext = kwargs["placeholdertext_win"]
                url = self.getURls(flag)
                link = "<html><head/><body><p>If download failed, click <a href=\"%s\">" \
                       "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</a>" \
                       "</span> to download manually and then specify the path as indicated above.</p></body></html>" % url
                self.target = kwargs["target_win"]
            elif platform.system().lower() in "darwin":
                placeholdertext = kwargs["placeholdertext_mac"]
                link = kwargs["link_mac"]
                self.target = kwargs["target_mac"]
            else:
                placeholdertext = kwargs["placeholdertext_linux"]
                link = kwargs["link_linux"]
                self.target = kwargs["target_linux"]
            self.lg_exePath = LG_exePath(self, label1, label2, label3, placeholdertext, flag, self.target,
                                                link)
            if platform.system().lower() in ["darwin", "windows"]:
                self.lg_exePath.downloadSig.connect(lambda : self.downloadPlugins(**kwargs))
            self.lg_exePath.closeSig.connect(self.saveEXEpath)
            # 添加最大化按钮
            self.lg_exePath.setWindowFlags(self.lg_exePath.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.lg_exePath.exec_()
        else:
            # 删除
            zipFile = self.plugin_path + os.sep + kwargs["zipFileName_win"]
            zipFolder = glob.glob(f"{self.plugin_path}{os.sep}*{kwargs['zipFolderFlag']}*{os.sep}")
            zipFolder = zipFolder[0] if zipFolder else ""
            if os.path.exists(zipFolder):
                self.factory.remove_dir_directly(zipFolder, removeRoot=True)
            if os.path.exists(zipFile):
                os.remove(zipFile)

            # if platform.system().lower() == "windows":
            #     zipFile = self.plugin_path + os.sep + kwargs["zipFileName_win"]
            #     zipFolder = self.plugin_path + os.sep + kwargs["zipFolder_win"]
            #     if os.path.exists(zipFolder):
            #         self.factory.remove_dir_directly(zipFolder, removeRoot=True)
            #     if os.path.exists(zipFile):
            #         os.remove(zipFile)
            # elif platform.system().lower() == "darwin":
            #     zipFile = self.plugin_path + os.sep + kwargs["zipFileName_mac"]
            #     zipFolder = self.plugin_path + os.sep + kwargs["zipFolder_mac"]
            #     if os.path.exists(zipFolder):
            #         self.factory.remove_dir_directly(zipFolder, removeRoot=True)
            #     if os.path.exists(zipFile):
            #         os.remove(zipFile)
            # self.settings.setValue(flag, "")
            WorkThread(self.judgePluginInstall, parent=self).start()
            QMessageBox.information(
                self, "Settings", "<p style='line-height:25px; height:25px'>Uninstalled successfully!</p>")
            # self.installStatus(flag, "uninstall")

    @pyqtSlot()
    def on_pushButton_6_clicked(self):
        """
        add row
        """
        currentModel = self.tableView_2.model()
        if currentModel:
            currentData = currentModel.arraydata
            currentHeader = currentModel.headerdata
            currentModel.layoutAboutToBeChanged.emit()
            length = len(currentHeader)
            currentData.append([""] * length)
            currentModel.layoutChanged.emit()
            self.tableView_2.scrollToBottom()

    @pyqtSlot()
    def on_pushButton_7_clicked(self):
        """
        add column
        """
        currentModel = self.tableView_2.model()
        if currentModel:
            currentData = currentModel.arraydata
            header = currentModel.headerdata
            columnName, ok = QInputDialog.getText(
                self, 'Settings', 'Column Name:')
            if ok and columnName:
                columnName = columnName.strip()
                header.append(columnName)
                currentModel.layoutAboutToBeChanged.emit()
                for i in currentData:
                    i.append("")
                currentModel.layoutChanged.emit()
                self.tableView_2.scrollToBottom()
                ##判断新加的类群是否和刚刚删的一样
                if hasattr(self, "removedTaxmy") and columnName in self.removedTaxmy:
                    self.removedTaxmy.remove(columnName)

    @pyqtSlot()
    def on_pushButton_8_clicked(self):
        """
        delete row
        """
        indices = self.tableView_2.selectedIndexes()
        currentModel = self.tableView_2.model()
        if currentModel and indices:
            currentData = currentModel.arraydata
            rows = sorted(set(index.row() for index in indices), reverse=True)
            for row in rows:
                currentModel.layoutAboutToBeChanged.emit()
                currentData.pop(row)
                currentModel.layoutChanged.emit()

    @pyqtSlot()
    def on_pushButton_9_clicked(self):
        """
        delete column
        """
        indices = self.tableView_2.selectedIndexes()
        currentModel = self.tableView_2.model()
        self.removedTaxmy = []
        if currentModel and indices:
            currentData = currentModel.arraydata
            header = currentModel.headerdata
            columns = sorted(set(index.column() for index in indices), reverse=True)
            for column in columns:
                if header[column] not in ['Class', 'Order', 'Family', 'Genus']:
                    currentModel.layoutAboutToBeChanged.emit()
                    self.removedTaxmy.append(header.pop(column))
                    for i in currentData:
                        i.pop(column)
                    currentModel.layoutChanged.emit()
                else:
                    QMessageBox.information(
                        self, "Settings", "<p style='line-height:25px; height:25px'>\"%s\" cannot be removed!</p>"%header[column])

    @pyqtSlot()
    def on_toolButton_3_clicked(self):
        """
        add settings
        """
        inputDialog = QInputDialog(self)
        inputDialog.setMinimumWidth(500)
        settingName, ok = inputDialog.getText(
            self, 'Add setting', 'New setting name:%s' % (" " * 26))
        if ok:
            allSettings = self.settings.value("Taxonomy Recognition")
            if settingName not in allSettings:
                allSettings[settingName] = [['Class', 'Order', 'Superfamily', 'Family', 'Subfamily', 'Genus'],
                                           [['', '*tera', '*dea', '*dae', '*nae', ''],
                                            ['', '', '*ida', '', '', ''],
                                            ['', '', '', '', '', ''],
                                            ['', '', '', '', '', ''],
                                            ['', '', '', '', '', '']]]
                self.saveTaxonomySettings(allSettings)
                self.refresh_taxonomyCombo(settingName)
            else:
                QMessageBox.information(
                    self, "Settings",
                    "<p style='line-height:25px; height:25px'>A setting named \"%s\" existing. Please select a new name.</p>" % settingName)

    @pyqtSlot()
    def on_toolButton_4_clicked(self):
        """
        remove settings
        """
        allSettings = self.settings.value("Taxonomy Recognition")
        currentSettingName = self.comboBox.currentText()
        if currentSettingName in allSettings:
            reply = QMessageBox.information(
                self,
                "PhyloSuite",
                "This will delete \"%s\" setting, continue?"%currentSettingName,
                QMessageBox.Yes,
                QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                allSettings.pop(currentSettingName)
                self.saveTaxonomySettings(allSettings)
                self.refresh_taxonomyCombo()

    @pyqtSlot()
    def on_toolButton_6_clicked(self):
        """
        import settings
        """
        fileName = QFileDialog.getOpenFileName(
            self, "Input setting file", filter="INIT Format(*.ini);;")
        if fileName[0]:
            setting_name = QSettings(
                fileName[0], QSettings.IniFormat)
            setting_name.setFallbacksEnabled(False)
            setting = setting_name.value("exported taxonomy settings", None)
            if setting:
                inputDialog = QInputDialog(self)
                inputDialog.setMinimumWidth(500)
                settingName, ok = inputDialog.getText(
                    self, 'Import setting', 'Set setting name:%s' % (" " * 26))
                if ok:
                    allSettings = self.settings.value("Taxonomy Recognition")
                    if settingName not in allSettings:
                        allSettings[settingName] = setting
                        self.saveTaxonomySettings(allSettings)
                        self.refresh_taxonomyCombo(settingName)
                    else:
                        QMessageBox.information(
                            self, "Settings",
                            "<p style='line-height:25px; height:25px'>A setting named \"%s\" existing. Please select a new name.</p>" % settingName)

    @pyqtSlot()
    def on_toolButton_5_clicked(self):
        """
        export settings
        """
        allSettings = self.settings.value("Taxonomy Recognition")
        currentSettingName = self.comboBox.currentText()
        fileName, format = QFileDialog.getSaveFileName(self,
                                                      "Export current setting",
                                                      currentSettingName,
                                                      "INIT Format(*.ini);;")
        if fileName and (currentSettingName in allSettings):
            setting_name = QSettings(
                fileName, QSettings.IniFormat)
            setting_name.setFallbacksEnabled(False)
            setting_name.setValue("exported taxonomy settings", allSettings[currentSettingName])

    def display_table(self, listItem):
        listItem.setSelected(True)
        # self.listWidget.setItemSelected(listItem, True)
        name = listItem.text()
        if name == "General":
            self.stackedWidget.setCurrentIndex(2)
        elif name == "Plugins":
            self.stackedWidget.setCurrentIndex(0)
        elif name == "Taxonomy Recognition":
            self.stackedWidget.setCurrentIndex(1)
            # data = self.settings.value(name, None)
            # if not data:
            #     #保证至少有个数据
            #     ini_data = OrderedDict(
            #         [("Default taxonomy settings", [['Class', 'Order', 'Superfamily', 'Family', 'Subfamily', 'Genus'],
            #                                        [['', '*tera', '*dea', '*dae', '*nae', ''],
            #                                         ['', '', '*ida', '', '', ''],
            #                                         ['', '', '', '', '', ''],
            #                                         ['', '', '', '', '', ''],
            #                                         ['', '', '', '', '', '']]])])
            #     self.settings.setValue(name, ini_data)
            #     data = ini_data
            # self.refreshTaxonomyTable(data["Default taxonomy settings"])

    def depositeTable2Data(self):
        self.tableView_2.updateEditorData()
        name = self.listWidget.currentItem().text()
        allSettings = self.settings.value(name)
        currentModel = self.tableView_2.model()
        header = currentModel.headerdata
        array = currentModel.arraydata
        currentData = [header, array]
        allSettings[self.comboBox.currentText()] = currentData
        self.saveTaxonomySettings(allSettings)
        if currentData != self.init_data:
            self.haveNewTaxmy = True
        else:
            self.haveNewTaxmy = False

    # def runProgress(self, widget, num):
    #     widget.setProperty("value", num)
    #     QCoreApplication.processEvents()
    #
    # def runProgressDialog(self, widget, num):
    #     # self.progressDialog.setLabelText("Installing %s..." % package)
    #     widget.setProperty("value", num)
    #     QCoreApplication.processEvents()

    def guiSave(self):
        # Save geometry
        self.settings.setValue('size', self.size())
        # self.settings.setValue('pos', self.pos())
        ###存数据
        self.updateTableView2()
        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QComboBox):
                if name == "comboBox":
                    settingName = self.comboBox.currentText()
                    self.settings.setValue(name, settingName)
        #         array = []  # 每一行存：name, description, status, install, progress
        #         for row in range(obj.rowCount()):
        #             Name = obj.item(row, 0).text()
        #             description = obj.item(row, 1).text()
        #             status = obj.item(row, 2).text()
        #             install = obj.cellWidget(row, 3)
        #             install_text = install.text()
        #             install_icon_url = self.dict_icon_url[install_text]
        #             array.append([Name, description, status,
        #                           install_text, install_icon_url])
        #         if install_text != "Installing...":
        #             # 下载的时候关闭窗口，就不保存
        #             self.settings.setValue(name, array)

    def guiRestore(self):
        # Restore geometry
        self.resize(self.settings.value('size', QSize(844, 500)))
        self.factory.centerWindow(self)
        # self.move(self.settings.value('pos', QPoint(596, 231)))
        data = self.settings.value("Taxonomy Recognition", None)
        if not data:
            #保证至少有个数据
            ini_data = OrderedDict(
                [("Default taxonomy settings", [['Class', 'Order', 'Superfamily', 'Family', 'Subfamily', 'Genus'],
                                               [['', '*tera', '*dea', '*dae', '*nae', ''],
                                                ['', '', '*ida', '', '', ''],
                                                ['', '', '', '', '', ''],
                                                ['', '', '', '', '', ''],
                                                ['', '', '', '', '', '']]])])
            self.settings.setValue("Taxonomy Recognition", ini_data)
        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                if name == "comboBox":
                    settingName = self.settings.value("comboBox", "Default taxonomy settings")
                    self.refresh_taxonomyCombo(settingName)
            if isinstance(obj, QTableWidget):
                WorkThread(self.judgePluginInstall, parent=self).start()
                # for i in ["mafft", "tbl2asn", "RscriptPath", "PF2", "gblocks", "iq-tree", "MrBayes", "mpi",
                #           "java", "macse", "trimAl", "perl", "HmmCleaner"]:
                #     status = self.factory.programIsValid(i)
                #     self.installStatus(i, status)
                # self.refreshPython27() ##python 2.7的状态单独判断
            if isinstance(obj, QCheckBox):
                if name == "checkBox":
                    ifPopRemoveRemind = self.mainwindow_settings.value("ifPopRemoveRemind", "true")
                    obj.setChecked(
                        self.factory.str2bool(ifPopRemoveRemind))
                    obj.toggled.connect(lambda bool_: self.mainwindow_settings.setValue('ifPopRemoveRemind', bool_))
                elif name == "checkBox_2":
                    value = self.workflow_settings.value("remind_window", "true")
                    obj.setChecked(
                        self.factory.str2bool(value))
                    obj.toggled.connect(lambda bool_: self.workflow_settings.setValue("remind_window", bool_))
                elif name == "checkBox_3":
                    value = self.mainwindow_settings.value("not auto check update", "0")
                    obj.setChecked(not
                        self.factory.str2bool(value))
                    obj.toggled.connect(lambda bool_: self.mainwindow_settings.setValue("not auto check update", not bool_))
                elif name == "checkBox_4":
                    value = self.mainwindow_settings.value("auto detect", "true")
                    obj.setChecked(self.factory.str2bool(value))
                    obj.toggled.connect(lambda bool_: self.mainwindow_settings.setValue("auto detect", bool_))
                elif name == "checkBox_5":
                    value = self.launcher_settings.value("ifLaunch", "true")
                    obj.setChecked(not self.factory.str2bool(value))
                    obj.toggled.connect(lambda bool_: self.launcher_settings.setValue("ifLaunch", not bool_))
            elif isinstance(obj, QLineEdit):
                family, size = re.findall(r"\*{font-family: (.+?); font-size: (\d+?)pt;}", self.qss_file)[0]
                self.lineEdit.setText(family)
                self.lineEdit_2.setText(size)

    def closeEvent(self, event):
        self.guiSave()
        self.closeSig.emit()
        if hasattr(self, "haveNewTaxmy") and self.haveNewTaxmy:
            if hasattr(self, "removedTaxmy"):
                ##有类群被删掉
                self.taxmyChangeSig.emit(self.removedTaxmy)
            else:
                self.taxmyChangeSig.emit([])

    def popupException(self, exception):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setText(
            'The program encountered an unforeseen problem, please report the bug at <a href="https://github.com/dongzhang0725/PhyloSuite/issues">https://github.com/dongzhang0725/PhyloSuite/issues</a> or send an email with the detailed traceback to dongzhang0725@gmail.com')
        msg.setWindowTitle("Error")
        msg.setDetailedText(exception)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def saveEXEpath(self, name, path, mode="other"):
        flag = "save"
        if name.endswith("##**"):
            flag = "download and install"
            name = name.rstrip("##**")
        status = self.factory.programIsValid_2(name, path, parent=self)
        if flag != "download and install":
            # 如果是download，就避免调用该方法，因为后面还会调用judgePluginInstall，频繁调用会导致卡死
            self.installButtonSig.emit(
                [self.dict_name_button[name], self.tableWidget, self.dict_name_row[name], status, self.qss_file])
        if status == "succeed":
            self.settings.setValue(name, path) # 该行代码导致报错
            if name == "PF2":
                self.refreshPython27()
            if mode == "install":
                # WorkThread(self.judgePluginInstall, parent=self).start()
                QMessageBox.information(
                    self.parent, "Settings", "<p style='line-height:25px;height:25px'>installed successfully!</p>")

    def downloadMAFFT(self):
        try:
            dict_args = {}
            dict_args["httpURL"] = self.getURls("mafft")
            dict_args["exportPath"] = self.plugin_path + os.sep + "mafft.zip"
            dict_args["download_button"] = self.download_mafft_button
            dict_args["tableWidget"] = self.tableWidget
            dict_args["row"] = self.dict_name_row["mafft"]
            dict_args["status"] = "succeed"
            dict_args["qss"] = self.qss_file
            dict_args["installButtonSig"] = self.installButtonSig
            dict_args["flag"] = "mafft"
            dict_args["exe_path_window"] = self.lg_exePath_mafft
            dict_args["save_pathSig"] = self.save_pathSig
            dict_args["target"] = self.MAFFT_target
            dict_args["installFinishedSig"] = self.installFinishedSig
            httpwindow = HttpWindowDownload(parent=self, **dict_args)
        except:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号
            self.installStatus("mafft", "uninstall")

    def downloadTS(self):
        try:
            dict_args = {}
            dict_args[
                "httpURL"] = self.getURls("tbl2asn") #"https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/tbl2asn.zip"
            dict_args["exportPath"] = self.plugin_path + \
                                      os.sep + "tbl2asn.zip"
            dict_args["download_button"] = self.download_tbl2asn_button
            dict_args["tableWidget"] = self.tableWidget
            dict_args["row"] = self.dict_name_row["tbl2asn"]
            dict_args["status"] = "succeed"
            dict_args["qss"] = self.qss_file
            dict_args["installButtonSig"] = self.installButtonSig
            dict_args["flag"] = "tbl2asn"
            dict_args["exe_path_window"] = self.lg_exePath_ts
            dict_args["save_pathSig"] = self.save_pathSig
            dict_args["target"] = self.TS_target
            dict_args["installFinishedSig"] = self.installFinishedSig
            httpwindow = HttpWindowDownload(parent=self, **dict_args)
        except:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号
            self.installStatus("tbl2asn", "uninstall")

    def downloadRscript(self):
        try:
            dict_args = {}
            if platform.system().lower() == "windows":
                dict_args["exportPath"] = self.plugin_path + \
                                          os.sep + "R-3.4.4-win.exe"
            elif platform.system().lower() == "darwin":
                dict_args["exportPath"] = self.plugin_path + \
                                          os.sep + "R-3.5.1.pkg"
            dict_args["httpURL"] = self.getURls("Rscript")
            dict_args["download_button"] = self.download_Rscript_button
            dict_args["tableWidget"] = self.tableWidget
            dict_args["row"] = self.dict_name_row["RscriptPath"]
            dict_args["status"] = "succeed"
            dict_args["qss"] = self.qss_file
            dict_args["installButtonSig"] = self.installButtonSig
            dict_args["flag"] = "RscriptPath"
            dict_args["exe_path_window"] = self.lg_exePath
            dict_args["save_pathSig"] = self.save_pathSig
            dict_args["target"] = self.R_target
            dict_args["installFinishedSig"] = self.installFinishedSig
            self.lg_exePath.close()
            self.lg_exePath.deleteLater()
            del self.lg_exePath
            httpwindow = HttpWindowDownload(parent=self, **dict_args)
            # httpwindow.installFinishedSig.connect(self.Install_finished)
        except:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号
            self.installStatus("RscriptPath", "uninstall")

    def downloadpython27(self):
        try:
            dict_args = {}
            if platform.system().lower() == "windows":
                dict_args["exportPath"] = self.plugin_path + \
                                          os.sep + "Anaconda2-5.2.0-Windows_%s.exe" % self.pc_bit
            elif platform.system().lower() == "darwin":
                dict_args["exportPath"] = self.plugin_path + \
                                          os.sep + "Anaconda2-5.2.0-MacOSX-x86_64.pkg"
            dict_args["httpURL"] = self.getURls("python27")
            dict_args["download_button"] = self.download_python27_button
            dict_args["tableWidget"] = self.tableWidget
            dict_args["row"] = self.dict_name_row["python27"]
            dict_args["status"] = "succeed"
            dict_args["qss"] = self.qss_file
            dict_args["installButtonSig"] = self.installButtonSig
            dict_args["flag"] = "python27"
            dict_args["exe_path_window"] = self.lg_exePath_python27
            dict_args["save_pathSig"] = self.save_pathSig
            dict_args["target"] = self.PY_target
            dict_args["installFinishedSig"] = self.installFinishedSig
            self.lg_exePath_python27.close()
            self.lg_exePath_python27.deleteLater()
            del self.lg_exePath_python27
            self.py27_httpwindow = HttpWindowDownload(parent=self, **dict_args)
        except:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号
            self.installStatus("python27", "uninstall")

    def downloadPF2(self, flag="PF2"):
        ## 如果是下载compiled，就换个链接
        try:
            dict_args = {}
            dict_args["httpURL"] = self.getURls(flag)
            dict_args["exportPath"] = self.plugin_path + \
                                      os.sep + "partitionfinder.zip"
            dict_args["download_button"] = self.download_partfind_button
            dict_args["tableWidget"] = self.tableWidget
            dict_args["row"] = self.dict_name_row["PF2"]
            dict_args["status"] = "succeed"
            dict_args["qss"] = self.qss_file
            dict_args["installButtonSig"] = self.installButtonSig
            dict_args["flag"] = "PF2"
            dict_args["exe_path_window"] = self.lg_exePath_PF
            dict_args["save_pathSig"] = self.save_pathSig
            dict_args["target"] = ""
            dict_args["installFinishedSig"] = self.installFinishedSig
            httpwindow = HttpWindowDownload(parent=self, **dict_args)
        except:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号
            self.installStatus("PF2", "uninstall")

    def downloadGB(self):
        try:
            dict_args = {}
            dict_args["httpURL"] = self.getURls("gblocks")
            dict_args["exportPath"] = self.plugin_path + \
                                      os.sep + "Gblocks.zip"
            dict_args["download_button"] = self.download_gblocks_button
            dict_args["tableWidget"] = self.tableWidget
            dict_args["row"] = self.dict_name_row["gblocks"]
            dict_args["status"] = "succeed"
            dict_args["qss"] = self.qss_file
            dict_args["installButtonSig"] = self.installButtonSig
            dict_args["flag"] = "gblocks"
            dict_args["exe_path_window"] = self.lg_exePath_gb
            dict_args["save_pathSig"] = self.save_pathSig
            dict_args["target"] = self.GB_target
            dict_args["installFinishedSig"] = self.installFinishedSig
            httpwindow = HttpWindowDownload(parent=self, **dict_args)
        except:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号
            self.installStatus("gblocks", "uninstall")

    def downloadIQ(self):
        try:
            dict_args = {}
            dict_args["httpURL"] = self.getURls("iq-tree")
            dict_args["exportPath"] = self.plugin_path + os.sep + "iqtree.zip"
            dict_args["download_button"] = self.download_iq_tree_button
            dict_args["tableWidget"] = self.tableWidget
            dict_args["row"] = self.dict_name_row["iq-tree"]
            dict_args["status"] = "iq-tree"
            dict_args["qss"] = self.qss_file
            dict_args["installButtonSig"] = self.installButtonSig
            dict_args["flag"] = "iq-tree"
            dict_args["exe_path_window"] = self.lg_exePath_iq
            dict_args["save_pathSig"] = self.save_pathSig
            dict_args["target"] = self.IQ_target
            dict_args["installFinishedSig"] = self.installFinishedSig
            httpwindow = HttpWindowDownload(parent=self, **dict_args)
        except:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号
            self.installStatus("iq-tree", "uninstall")

    def downloadMB(self):
        try:
            dict_args = {}
            dict_args["httpURL"] = self.getURls("MrBayes")
            dict_args["exportPath"] = self.plugin_path + \
                                      os.sep + "MrBayes.zip"
            dict_args["download_button"] = self.download_MrBayes_button
            dict_args["tableWidget"] = self.tableWidget
            dict_args["row"] = self.dict_name_row["MrBayes"]
            dict_args["status"] = "succeed"
            dict_args["qss"] = self.qss_file
            dict_args["installButtonSig"] = self.installButtonSig
            dict_args["flag"] = "MrBayes"
            dict_args["exe_path_window"] = self.lg_exePath_mb
            dict_args["save_pathSig"] = self.save_pathSig
            dict_args["target"] = self.MB_target
            dict_args["installFinishedSig"] = self.installFinishedSig
            httpwindow = HttpWindowDownload(parent=self, **dict_args)
        except:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号
            self.installStatus("MrBayes", "uninstall")

    def downloadMS(self):
        try:
            dict_args = {}
            dict_args["httpURL"] = self.getURls("macse")
            dict_args["exportPath"] = self.plugin_path + \
                                      os.sep + "macse.jar.zip"
            dict_args["download_button"] = self.download_macse_button
            dict_args["tableWidget"] = self.tableWidget
            dict_args["row"] = self.dict_name_row["macse"]
            dict_args["status"] = "succeed"
            dict_args["qss"] = self.qss_file
            dict_args["installButtonSig"] = self.installButtonSig
            dict_args["flag"] = "macse"
            dict_args["exe_path_window"] = self.lg_exePath_macse
            dict_args["save_pathSig"] = self.save_pathSig
            dict_args["target"] = self.MACSE_target
            dict_args["installFinishedSig"] = self.installFinishedSig
            httpwindow = HttpWindowDownload(parent=self, **dict_args)
        except:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号
            self.installStatus("macse", "uninstall")

    def downloadTrimAl(self):
        try:
            dict_args = {}
            dict_args["httpURL"] = self.getURls("trimAl")
            dict_args["exportPath"] = self.plugin_path + \
                                      os.sep + "trimal.zip"
            dict_args["download_button"] = self.download_trimAl_button
            dict_args["tableWidget"] = self.tableWidget
            dict_args["row"] = self.dict_name_row["trimAl"]
            dict_args["status"] = "succeed"
            dict_args["qss"] = self.qss_file
            dict_args["installButtonSig"] = self.installButtonSig
            dict_args["flag"] = "trimAl"
            dict_args["exe_path_window"] = self.lg_exePath_trimAl
            dict_args["save_pathSig"] = self.save_pathSig
            dict_args["target"] = self.trimAl_target
            dict_args["installFinishedSig"] = self.installFinishedSig
            httpwindow = HttpWindowDownload(parent=self, **dict_args)
        except:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号
            self.installStatus("trimAl", "uninstall")

    def downloadCodonW(self):
        try:
            dict_args = {}
            dict_args["httpURL"] = self.getURls("CodonW")
            dict_args["exportPath"] = self.plugin_path + \
                                      os.sep + "CodonW.zip"
            dict_args["download_button"] = self.download_CodonW_button
            dict_args["tableWidget"] = self.tableWidget
            dict_args["row"] = self.dict_name_row["CodonW"]
            dict_args["status"] = "succeed"
            dict_args["qss"] = self.qss_file
            dict_args["installButtonSig"] = self.installButtonSig
            dict_args["flag"] = "CodonW"
            dict_args["exe_path_window"] = self.lg_exePath_CodonW
            dict_args["save_pathSig"] = self.save_pathSig
            dict_args["target"] = self.CodonW_target
            dict_args["installFinishedSig"] = self.installFinishedSig
            httpwindow = HttpWindowDownload(parent=self, **dict_args)
        except:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号
            self.installStatus("CodonW", "uninstall")

    def downloadPlotEngine(self, resource):
        try:
            dict_args = {}
            if not os.path.exists(f"{self.thisPath}{os.sep}os_bit"):
                pc_bit = self.pc_bit
            else:
                with open(f"{self.thisPath}{os.sep}os_bit", encoding="utf-8", errors="ignore") as f:
                    pc_bit = f.readline().rstrip()
            dict_args["httpURL"] = dict_url[platform.system().lower()][pc_bit][resource]["plot engine"]
            dict_args["exportPath"] = self.thisPath + \
                                      os.sep + "plot_engine.zip"
            dict_args["download_button"] = self.download_plot_engine_button
            dict_args["tableWidget"] = self.tableWidget
            dict_args["row"] = self.dict_name_row["plot_engine"]
            dict_args["status"] = "succeed"
            dict_args["qss"] = self.qss_file
            dict_args["installButtonSig"] = self.installButtonSig
            dict_args["flag"] = "plot_engine"
            dict_args["save_pathSig"] = ""
            dict_args["target"] = ""
            dict_args["installFinishedSig"] = self.installFinishedSig
            httpwindow = HttpWindowDownload(parent=self, **dict_args)
        except:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号
            self.installStatus("CodonW", "uninstall")

    def downloadPlugins(self, **kargs):
        try:
            dict_args = {}
            dict_args["httpURL"] = self.getURls(kargs["plugin_name"])
            dict_args["exportPath"] = self.plugin_path + \
                                      os.sep + kargs["zipFileName_win"]
            dict_args["download_button"] = getattr(self,
                                                   f"install_button{self.dict_name_row[kargs['plugin_name']]}")
            dict_args["tableWidget"] = self.tableWidget
            dict_args["row"] = self.dict_name_row[kargs["plugin_name"]]
            dict_args["status"] = "succeed"
            dict_args["qss"] = self.qss_file
            dict_args["installButtonSig"] = self.installButtonSig
            dict_args["flag"] = kargs["plugin_name"]
            dict_args["exe_path_window"] = self.lg_exePath
            dict_args["save_pathSig"] = self.save_pathSig
            dict_args["target"] = self.target
            dict_args["installFinishedSig"] = self.installFinishedSig
            httpwindow = HttpWindowDownload(parent=self, **dict_args)
        except:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号
            self.installStatus(kargs["plugin_name"], "uninstall")

    def updateTableView2(self):
        model = self.tableView_2.model()
        if not model:
            return
        list_logicIndex = [self.tableView_2.horizontalHeader().logicalIndex(i) for i in
                       range(self.tableView_2.horizontalHeader().count())]
        header = model.headerdata[:]
        updated_header = [header[k] for k in list_logicIndex]
        data = model.arraydata[:]
        zip_data = list(map(list, zip(*data)))
        updated_data = list(map(list, zip(*[zip_data[j] for j in list_logicIndex])))
        currentData = [updated_header, updated_data]
        allSettings = self.settings.value("Taxonomy Recognition")
        allSettings[self.comboBox.currentText()] = currentData
        self.saveTaxonomySettings(allSettings)

    def installStatus(self, flag, status):
        self.installButtonSig.emit(
            [self.dict_name_button[flag], self.tableWidget, self.dict_name_row[flag], status, self.qss_file])

    def getURls(self, program):
        url = ""
        platform_ = platform.system().lower()
        dict_program = {"mafft": "lg_exePath_mafft",
                        "Rscript": "lg_exePath",
                        "python27": "lg_exePath_python27",
                        "gblocks": "lg_exePath_gb",
                        "iq-tree": "lg_exePath_iq",
                        "MrBayes": "lg_exePath_mb",
                        "compiled PF2": "lg_exePath_PF",
                        "PF2": "lg_exePath_PF",
                        "macse": "lg_exePath_macse",
                        "trimAl": "lg_exePath_trimAl",
                        "tbl2asn": "lg_exePath_ts",
                        "CodonW": "lg_exePath_CodonW"
                        }
        if (program in dict_program) and hasattr(self, dict_program[program]):
            resource = getattr(self, dict_program[program]).downloadRes
        elif hasattr(self, "lg_exePath"):
            resource = self.lg_exePath.downloadRes
        else:
            resource = "Chinese resource"
        if platform_ in dict_url:
            if self.pc_bit in dict_url[platform_]:
                if resource in dict_url[platform_][self.pc_bit]:
                    if program in dict_url[platform_][self.pc_bit][resource]:
                        url = dict_url[platform_][self.pc_bit][resource][program]
        return url

    def zip_waiting(self, text):
        if text != "Unzip finished":
            self.progressDialog = self.factory.myProgressDialog(
                "Please Wait", "%s..."%text, busy=True, parent=self)
            self.progressDialog.show()
        else:
            if hasattr(self, "progressDialog"):
                self.progressDialog.close()

    def plugin_is_installed(self, plugin):
        row = self.dict_name_row[plugin]
        status = self.tableWidget.item(row, 2).text()
        return True if status == "Installed" else False

    def Install_finished(self, text, plugin):
        WorkThread(self.judgePluginInstall, parent=self).start()
        if plugin in ["Rscript", "py27"]:
            QMessageBox.information(
                self, "Settings",
                "<p style='line-height:25px;height:25px'>%s</p>" % text, QMessageBox.Ok)
            if plugin == "Rscript":
                self.on_download_Rscript_button_clicked()
            elif plugin == "py27":
                self.on_download_python27_button_clicked()
        elif plugin == "plot_engine":
            # 需要重启phylosuite
            reply = QMessageBox.information(
                self, "Settings",
                "<p style='line-height:25px;height:25px'>Unzip finished, "
                "do you want to restart PhyloSuite now?</p>",
                QMessageBox.Ok,
                QMessageBox.Cancel,
            )
            if reply == QMessageBox.Ok:
                UpdateAPP().exec_restart()
        else:
            QMessageBox.information(
                self, "Settings",
                "<p style='line-height:25px;height:25px'>%s</p>" % text, QMessageBox.Ok)

    def refreshPython27(self):
        PF2path = self.factory.programIsValid("PF2", mode="tool")
        if PF2path:
            pf_compiled = PF2path + os.sep + "PartitionFinder.exe" if platform.system().lower() == "windows" else \
                PF2path + os.sep + "PartitionFinder"
            if os.path.exists(pf_compiled):
                self.installStatus("python27", "not need")
                return
        status = self.factory.programIsValid("python27")
        self.installStatus("python27", status)

    def judgePluginInstall(self):
        for i in set(["mafft", "tbl2asn", "RscriptPath", "PF2", "gblocks", "iq-tree", "MrBayes", "mpi",
                  "java", "macse", "trimAl", "perl", "HmmCleaner", "CodonW"] + \
                 list(dict_plugin_settings.keys())):
            status = self.factory.programIsValid(i)
            self.installStatus(i, status)
        # plog engine 单独判断
        try:
            import plotly
            import pandas as pd
            import statsmodels.api as sm
            flag = "succeed"
        except:
            # exception = ''.join(
            #     traceback.format_exception(
            #         *sys.exc_info()))
            # print(exception)
            flag = "uninstall"
        self.installStatus("plot_engine", flag)
        self.refreshPython27()  ##python 2.7的状态单独判断

    def refresh_taxonomyCombo(self, settingName=None):
        allItems = self.settings.value("Taxonomy Recognition").keys()
        model = self.comboBox.model()
        self.comboBox.clear()
        for num, i in enumerate(allItems):
            item = QStandardItem(i)
            # 背景颜色
            if num % 2 == 0:
                item.setBackground(QColor(255, 255, 255))
            else:
                item.setBackground(QColor(237, 243, 254))
            item.setToolTip(i)
            model.appendRow(item)
        if settingName in allItems: self.comboBox.setCurrentText(settingName)
        else: self.comboBox.setCurrentIndex(0)

    def refreshTaxonomyTable(self, data):
        header, array = data
        if not hasattr(self, "init_data"): self.init_data = copy.deepcopy(data)
        tableModel = MySettingTableModel(array, header)
        self.tableView_2.setModel(tableModel)
        self.tableView_2.resizeColumnsToContents()
        tableModel.dataChanged.connect(self.depositeTable2Data)
        tableModel.layoutChanged.connect(self.depositeTable2Data)

    def judgeSettings(self, text):
        if not text: return
        if text != "Default taxonomy settings": self.toolButton_4.setEnabled(True)
        else: self.toolButton_4.setEnabled(False)
        allSettings = self.settings.value("Taxonomy Recognition")
        self.refreshTaxonomyTable(allSettings[text])

    def saveTaxonomySettings(self, settings):
        self.settings.setValue("Taxonomy Recognition", settings)

    def setFont(self):
        family = self.lineEdit.text()
        size = int(self.lineEdit_2.text())
        font, ok = QFontDialog.getFont(QFont(family, size), self)
        if ok:
            family_ = font.family()
            size_ = str(font.pointSize())
            self.lineEdit.setText(family_)
            self.lineEdit_2.setText(size_)
            self.qss_file = re.sub(r"^\*{font-family: (.+?); font-size: (\d+)pt;}",
                                   "*{font-family: %s; font-size: %spt;}"%(family_, size_), self.qss_file)
            self.setStyleSheet(self.qss_file)
            self.parent.setStyleSheet(self.qss_file)
            self.style().unpolish(self)
            self.style().polish(self)
            with open(self.thisPath + os.sep + 'style.qss', "w", encoding="utf-8", errors='ignore') as f:
                f.write(self.qss_file)
            font_settings = QSettings()
            font_settings.setValue("font changed", True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    setting = Setting()
    setting.show()
    sys.exit(app.exec_())
