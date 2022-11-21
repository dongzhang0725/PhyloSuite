#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import platform

import re
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from uifiles.Ui_ConvertFmt import Ui_ConverFMT
from src.factory import Factory, WorkThread, Convertfmt
import inspect
import os
import sys
import traceback


class ConvertFMT(QDialog, Ui_ConverFMT, object):
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    progressSig = pyqtSignal(int)  # 控制进度条
    startButtonStatusSig = pyqtSignal(list)
    unalignedSig = pyqtSignal(list)
    ##弹出识别输入文件的信号
    auto_popSig = pyqtSignal(QDialog)

    def __init__(
            self,
            workPath=None,
            focusSig=None,
            autoFiles=None,
            parent=None):
        super(ConvertFMT, self).__init__(parent)
        self.parent = parent
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.focusSig = focusSig
        self.autoFiles = autoFiles
        self.setupUi(self)
        # 保存设置
        self.convertFmt_settings = QSettings(
            self.thisPath +
            '/settings/convertFmt_settings.ini',
            QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.convertFmt_settings.setFallbacksEnabled(False)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        # 恢复用户的设置
        self.guiRestore()
        self.exception_signal.connect(self.popupException)
        self.startButtonStatusSig.connect(self.factory.ctrl_startButton_status)
        self.progressSig.connect(self.runProgress)
        self.comboBox_4.installEventFilter(self)
        self.comboBox_4.lineEdit().autoDetectSig.connect(self.popupAutoDec)  #自动识别可用的输入
        self.unalignedSig.connect(self.popupUnaligns)
        # 给开始按钮添加菜单
        menu = QMenu(self)
        menu.setToolTipsVisible(True)
        self.work_action = QAction(QIcon(":/picture/resourses/work.png"), "", menu)
        self.work_action.triggered.connect(lambda: self.factory.swithWorkPath(self.work_action, parent=self))
        self.dir_action = QAction(QIcon(":/picture/resourses/folder.png"), "Output Dir: ", menu)
        self.dir_action.triggered.connect(lambda: self.factory.set_direct_dir(self.dir_action, self))
        menu.addAction(self.work_action)
        menu.addAction(self.dir_action)
        self.pushButton.toolButton.setMenu(menu)
        self.pushButton.toolButton.menu().installEventFilter(self)
        self.factory.swithWorkPath(self.work_action, init=True, parent=self)  # 初始化一下
        ## brief demo
        country = self.factory.path_settings.value("country", "UK")
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#5-8-1-Brief-example" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#5-8-1-Brief-example"
        self.label_2.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        ##自动弹出识别文件窗口
        self.auto_popSig.connect(self.popupAutoDecSub)

    @pyqtSlot()
    def on_pushButton_clicked(self):
        """
        execute program
        """
        AllItems = self.comboBox_4.fetchListsText()
        if AllItems:
            self.dict_args = {}
            self.dict_args["exception_signal"] = self.exception_signal
            self.dict_args["unaligned_signal"] = self.unalignedSig
            self.dict_args["progressSig"] = self.progressSig
            self.dict_args["files"] = AllItems
            self.dict_args["workPath"] = self.workPath
            self.output_dir_name = self.factory.fetch_output_dir_name(self.dir_action)
            self.dict_args["export_path"] = self.factory.creat_dirs(self.workPath +
                                                os.sep + "convertFmt_results" + os.sep + self.output_dir_name)
            self.dict_args["export_phylip"] = self.checkBox.isChecked()
            self.dict_args["export_nex"] = self.checkBox_2.isChecked()
            self.dict_args["export_nexi"] = self.checkBox_3.isChecked()
            self.dict_args["export_axt"] = self.checkBox_13.isChecked()
            self.dict_args["export_paml"] = self.checkBox_5.isChecked()
            self.dict_args["export_fas"] = self.checkBox_12.isChecked()
            self.dict_args["export_stat"] = self.checkBox_9.isChecked()
            if True not in list(self.dict_args.values()):
                QMessageBox.critical(
                    self,
                    "Convert Sequence Format",
                    "<p style='line-height:25px; height:25px'>Please select output format(s) first!</p>")
                self.checkBox.setChecked(True)
                return
            ok = self.factory.remove_dir(self.dict_args["export_path"], parent=self)
            if not ok:
                #提醒是否删除旧结果，如果用户取消，就不执行
                return
            self.worker = WorkThread(self.run_command, parent=self)
            self.worker.start()
        else:
            QMessageBox.critical(
                self,
                "Convert Sequence Format",
                "<p style='line-height:25px; height:25px'>Please input files first!</p>")

    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        """
        open files
        """
        files = QFileDialog.getOpenFileNames(
            self, "Input Files",
            filter="Supported Format(*.fas *.fasta *.phy *.phylip *.nex *.nxs *.nexus);;")
        if files[0]:
            self.input(files[0])

    def run_command(self):
        try:
            # 先清空文件夹
            time_start = datetime.datetime.now()
            self.startButtonStatusSig.emit(
                [self.pushButton, self.progressBar, "start", self.dict_args["export_path"], self.qss_file, self])
            convertFmt = Convertfmt(**self.dict_args)
            convertFmt.exec_()
            if convertFmt.error_message:
                self.exception_signal.emit(convertFmt.error_message)  # 激发这个信号
                self.startButtonStatusSig.emit(
                    [self.pushButton, self.progressBar, "except", self.dict_args["export_path"], self.qss_file, self])
            elif convertFmt.unaligns:
                self.unalignedSig.emit(convertFmt.unaligns)
                self.startButtonStatusSig.emit(
                    [self.pushButton, self.progressBar, "except", self.dict_args["export_path"], self.qss_file, self])
            else:
                self.startButtonStatusSig.emit(
                    [self.pushButton, self.progressBar, "stop", self.dict_args["export_path"], self.qss_file, self])
            self.focusSig.emit(self.dict_args["export_path"])
            time_end = datetime.datetime.now()
            self.time_used_des = "Start at: %s\nFinish at: %s\nTotal time used: %s\n\n" % (str(time_start), str(time_end),
                                                                                  str(time_end - time_start))
            with open(self.dict_args["export_path"] + os.sep + "summary and citation.txt", "w", encoding="utf-8") as f:
                f.write("If you use PhyloSuite v1.2.3, please cite:\nZhang, D., F. Gao, I. Jakovlić, H. Zou, J. Zhang, W.X. Li, and G.T. Wang, PhyloSuite: An integrated and scalable desktop platform for streamlined molecular sequence data management and evolutionary phylogenetics studies. Molecular Ecology Resources, 2020. 20(1): p. 348–355. DOI: 10.1111/1755-0998.13096.\n\n" + self.time_used_des)
        except BaseException:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号
            self.startButtonStatusSig.emit(
                [self.pushButton, self.progressBar, "except", self.dict_args["export_path"], self.qss_file, self])

    def guiSave(self):
        # Save geometry
        self.convertFmt_settings.setValue('size', self.size())
        # self.convertFmt_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QCheckBox):
                state = obj.isChecked()
                self.convertFmt_settings.setValue(name, state)
            if isinstance(obj, QRadioButton):
                state = obj.isChecked()
                self.convertFmt_settings.setValue(name, state)

    def guiRestore(self):

        # Restore geometry
        size = self.factory.judgeWindowSize(self.convertFmt_settings, 561, 384)
        self.resize(size)
        self.factory.centerWindow(self)
        # self.move(self.convertFmt_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                if self.autoFiles:
                    self.input(self.autoFiles)
                else:
                    self.input([])
            if isinstance(obj, QCheckBox):
                value = self.convertFmt_settings.value(
                    name, "true")  # get stored value from registry
                obj.setChecked(
                    self.factory.str2bool(value))  # restore checkbox
            if isinstance(obj, QRadioButton):
                value = self.convertFmt_settings.value(
                    name, "true")  # get stored value from registry
                obj.setChecked(
                    self.factory.str2bool(value))  # restore checkbox

    def input(self, list_inputs):
        self.comboBox_4.refreshInputs(list_inputs)

    def runProgress(self, num):
        oldValue = self.progressBar.value()
        done_int = int(num)
        if done_int > oldValue:
            self.progressBar.setProperty("value", done_int)
            QCoreApplication.processEvents()

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

    def eventFilter(self, obj, event):
        # modifiers = QApplication.keyboardModifiers()
        if isinstance(
                obj,
                QComboBox):
            if event.type() == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    # must accept the dragEnterEvent or else the dropEvent
                    # can't occur !!!
                    event.accept()
                    return True
            if event.type() == QEvent.Drop:
                files = [u.toLocalFile() for u in event.mimeData().urls()]
                files = [i for i in files if os.path.splitext(i)[1].upper() in
                         [".FAS", ".FASTA", ".PHY", ".PHYLIP", ".NEX", ".NXS", ".NEXUS"]]
                self.input(files)
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
        return super(ConvertFMT, self).eventFilter(obj, event)  # 0

    def popupUnaligns(self, message):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setText(
            "<p style='line-height:25px; height:25px'>Unaligned sequences found, see details</p>")
        msg.setWindowTitle("Warning")
        msg.setDetailedText("Unaligned sequences: " + ",".join(message))
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def popupAutoDec(self, init=False):
        self.init = init
        self.factory.popUpAutoDetect("format conversion", self.workPath, self.auto_popSig, self)

    def popupAutoDecSub(self, popupUI):
        if not popupUI:
            if not self.init:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "<p style='line-height:25px; height:25px'>No available file detected!</p>")
            return
        if not self.init: popupUI.checkBox.setVisible(False)
        if popupUI.exec_() == QDialog.Accepted:
            widget = popupUI.listWidget_framless.itemWidget(popupUI.listWidget_framless.selectedItems()[0])
            autoInputs = widget.autoInputs
            self.input(autoInputs)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = ConvertFMT()
    ui.show()
    sys.exit(app.exec_())