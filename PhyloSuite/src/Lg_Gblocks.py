#!/usr/bin/env python
# -*- coding: utf-8 -*-
import signal
from collections import OrderedDict

import datetime
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from src.factory import Factory, WorkThread, Parsefmt, Convertfmt
from uifiles.Ui_gblocks import Ui_Gblocks
import inspect
import os
import sys
import re
import traceback
import subprocess
import shutil
import platform


class Gblocks(QDialog, Ui_Gblocks, object):
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    progressSig = pyqtSignal(int)  # 控制进度条
    startButtonStatusSig = pyqtSignal(list)
    logGuiSig = pyqtSignal(str)
    workflow_progress = pyqtSignal(int)
    workflow_finished = pyqtSignal(str)
    auto_parSig = pyqtSignal()
    gblocks_exception = pyqtSignal(str)  # 定义所有类都可以使用的信号
    # 用于flowchart自动popup combobox等操作
    showSig = pyqtSignal(QDialog)
    closeSig = pyqtSignal(str, str)
    # 用于输入文件后判断用
    ui_closeSig = pyqtSignal(str)
    ##弹出识别输入文件的信号
    auto_popSig = pyqtSignal(QDialog)

    def __init__(
            self,
            autoInputs=None,
            workPath=None,
            focusSig=None,
            gb_exe=None,
            workflow=False,
            parent=None):
        super(Gblocks, self).__init__(parent)
        self.parent = parent
        self.function_name = "Gblocks"
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.focusSig = focusSig if focusSig else pyqtSignal(
            str)  # 为了方便workflow
        self.workflow = workflow
        self.gb_exe = gb_exe
        self.autoInputs = autoInputs
        self.interrupt = False
        self.setupUi(self)
        # 保存设置
        if not workflow:
            self.gblocks_settings = QSettings(
                self.thisPath + '/settings/gblocks_settings.ini', QSettings.IniFormat)
        else:
            self.gblocks_settings = QSettings(
                self.thisPath + '/settings/workflow_settings.ini', QSettings.IniFormat)
            self.gblocks_settings.beginGroup("Workflow")
            self.gblocks_settings.beginGroup("temporary")
            self.gblocks_settings.beginGroup('Gblocks')
        # File only, no fallback to registry or or.
        self.gblocks_settings.setFallbacksEnabled(False)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        # 恢复用户的设置
        self.guiRestore()
        # 判断程序的版本
        self.version = "0.91b"
        # version_worker = WorkThread(
        #     lambda : self.factory.get_version("Gblocks", self),
        #     parent=self)
        # version_worker.start()
        #
        self.log_gui = self.gui4Log()
        self.exception_signal.connect(self.popupException)
        self.startButtonStatusSig.connect(self.factory.ctrl_startButton_status)
        self.gblocks_exception.connect(self.popup_Gblocks_exception)
        self.progressSig.connect(self.runProgress)
        self.logGuiSig.connect(self.addText2Log)
        self.comboBox_4.installEventFilter(self)
        self.comboBox_4.lineEdit().autoDetectSig.connect(
            self.popupAutoDec)  # 自动识别可用的输入
        # self.comboBox_4.itemRemovedSig.connect(self.auto_parFromfile)
        self.comboBox_2.currentIndexChanged[str].connect(self.comboLink)
        reg_ex = QRegExp(".{,5}")
        validator = QRegExpValidator(reg_ex, self.lineEdit_3)
        self.lineEdit_3.setValidator(validator)
        self.auto_parSig.connect(self.auto_parFromfile)
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
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#5-6-1-Brief-example" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#5-6-1-Brief-example"
        self.label_7.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        ##自动弹出识别文件窗口
        self.auto_popSig.connect(self.popupAutoDecSub)

    @pyqtSlot()
    def on_pushButton_clicked(self):
        """
        execute program
        """
        if self.isFileIn():
            # 创建输出文件夹
            self.output_dir_name = self.factory.fetch_output_dir_name(self.dir_action)
            self.exportPath = self.factory.creat_dirs(self.workPath +
                                                    os.sep + "Gblocks_results" + os.sep + self.output_dir_name)
            self.interrupt = False
            ok = self.factory.remove_dir(
                self.exportPath, parent=self)  # 第二次运行的时候要清空
            if not ok:
                # 提醒是否删除旧结果，如果用户取消，就不执行
                return
            self.collect_args()
            self.textEdit_log.clear()  # 清空log
            self.worker = WorkThread(self.run_command, parent=self)
            self.worker.start()
        else:
            QMessageBox.critical(
                self,
                "Gblocks",
                "<p style='line-height:25px; height:25px'>Please input files first!</p>")

    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        """
        open files
        """
        fileNames = QFileDialog.getOpenFileNames(
            self, "Input Files", filter="NBRF/PIR Format(*.pir);;Fasta Format(*.fas *.fasta *.fsa);;")
        if fileNames[0]:
            self.input(fileNames[0])

    @pyqtSlot()
    def on_pushButton_9_clicked(self):
        """
        show log
        """
        self.log_gui.show()

    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        """
        Stop
        """
        if self.isRunning():
            if not self.workflow:
                reply = QMessageBox.question(
                    self,
                    "Confirmation",
                    "<p style='line-height:25px; height:25px'>Gblocks is still running, terminate it?</p>",
                    QMessageBox.Yes,
                    QMessageBox.Cancel)
            else:
                reply = QMessageBox.Yes
            if reply == QMessageBox.Yes:
                try:
                    self.worker.stopWork()
                    if platform.system().lower() in ["windows", "darwin"]:
                        self.gb_popen.kill()
                    else:
                        os.killpg(os.getpgid(self.gb_popen.pid), signal.SIGTERM)
                    self.gb_popen = None
                    self.interrupt = True
                except:
                    self.gb_popen = None
                    self.interrupt = True
                if not self.workflow:
                    QMessageBox.information(
                        self,
                        "Gblocks",
                        "<p style='line-height:25px; height:25px'>Program has been terminated!</p>")
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton,
                        self.progressBar,
                        "except",
                        self.exportPath,
                        self.qss_file,
                        self])

    def run_command(self):
        try:
            time_start = datetime.datetime.now()
            self.startButtonStatusSig.emit(
                [
                    self.pushButton,
                    self.progressBar,
                    "start",
                    self.exportPath,
                    self.qss_file,
                    self])
            # if not self.workflow:
            self.input_files = []
            for j in self.files:
                shutil.copy(j, self.exportPath)
                self.input_files.append(os.path.basename(j))
            os.chdir(self.exportPath)
            # self.input_files = os.listdir(self.exportPath)
            for num, self.input_file in enumerate(self.input_files):
                if self.seq_num_differ and (self.workflow or self.runAnyway):
                    with open(self.input_file, encoding="utf-8", errors='ignore') as f:
                        content = f.read()
                        self.seq_num = content.count(">")
                    self.auto_parFromfile()
                    # self.auto_parSig.emit()
                    self.collect_args()  # 参数刷新了
                commands = "\"{self.gb_exe}\" \"{self.input_file}\" -t={self.t} -b1={self.b1} -b2={self.b2} -b3={self.b3} -b4={self.b4} -b5={self.b5}{self.b6} -s={self.s} -p={self.p} -v={self.v} -n={self.n} -u={self.u} -k={self.k} -d={self.d} -e={self.e}".format(
                    self=self)
                # print(os.path.basename(self.input_file), commands)
                self.run_code(commands)
                self.progressSig.emit((num + 1) * 100 / len(self.input_files))
                self.workflow_progress.emit(
                    (num + 1) * 100 / len(self.input_files))
                if self.interrupt:
                    return
            # 将gb后缀放到前面
            for j in os.listdir(self.exportPath):
                name, ext = os.path.splitext(j)
                if ext.endswith(self.e):
                    # 将ext的后缀放到前面
                    if not os.path.exists(self.exportPath + os.sep + name + self.e + ".fasta"):
                        os.rename(
                            self.exportPath + os.sep + j,
                            self.exportPath + os.sep + name + self.e + ".fasta")
                    else:
                        try:
                            os.remove(self.exportPath + os.sep + j)
                        except:
                            pass
                if self.interrupt:
                    break
            time_end = datetime.datetime.now()
            self.time_used = str(time_end - time_start)
            self.time_used_des = "Start at: %s\nFinish at: %s\nTotal time used: %s\n\n" % (str(time_start), str(time_end),
                                                                                           self.time_used)
            with open(self.exportPath + os.sep + "summary and citation.txt", "w", encoding="utf-8") as f:
                f.write(self.description +
                        "\n\nIf you use PhyloSuite v1.2.3, please cite:\nZhang, D., F. Gao, I. Jakovlić, H. Zou, J. Zhang, W.X. Li, and G.T. Wang, PhyloSuite: An integrated and scalable desktop platform for streamlined molecular sequence data management and evolutionary phylogenetics studies. Molecular Ecology Resources, 2020. 20(1): p. 348–355. DOI: 10.1111/1755-0998.13096.\n"
                        "If you use Gblocks, please cite:\n" + self.reference + "\n\n" + self.time_used_des)
            if not self.interrupt:
                if self.workflow:
                    # work flow跑的
                    self.startButtonStatusSig.emit(
                        [
                            self.pushButton,
                            self.progressBar,
                            "workflow stop",
                            self.exportPath,
                            self.qss_file,
                            self])
                    self.workflow_finished.emit("finished")
                    return
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton,
                        self.progressBar,
                        "stop",
                        self.exportPath,
                        self.qss_file,
                        self])
                self.focusSig.emit(self.exportPath)
            else:
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton,
                        self.progressBar,
                        "except",
                        self.exportPath,
                        self.qss_file,
                        self])
        except BaseException:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号
            self.startButtonStatusSig.emit(
                [
                    self.pushButton,
                    self.progressBar,
                    "except",
                    self.exportPath,
                    self.qss_file,
                    self])

    def guiSave(self):
        # Save geometry
        self.gblocks_settings.setValue('size', self.size())
        # self.gblocks_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QComboBox):
                # save combobox selection to registry
                if name != "comboBox_4":
                    text = obj.currentText()
                    if text:
                        allItems = [
                            obj.itemText(i) for i in range(obj.count())]
                        allItems.remove(text)
                        sortItems = [text] + allItems
                        self.gblocks_settings.setValue(name, sortItems)
            if isinstance(obj, QRadioButton):
                state = obj.isChecked()
                self.gblocks_settings.setValue(name, state)
            if isinstance(obj, QLineEdit):
                text = obj.text()
                self.gblocks_settings.setValue(name, text)
            if isinstance(obj, QSpinBox):
                value = obj.value()
                self.gblocks_settings.setValue(name, value)

    def guiRestore(self):

        # Restore geometry
        size = self.factory.judgeWindowSize(self.gblocks_settings, 809, 582)
        self.resize(size)
        self.factory.centerWindow(self)
        # self.move(self.gblocks_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                if name not in ["comboBox_10", "comboBox_2"]:
                    allItems = [obj.itemText(i) for i in range(obj.count())]
                    values = self.gblocks_settings.value(name, allItems)
                    if name == "comboBox_4":
                        if not self.workflow:
                            if self.autoInputs:
                                self.input(self.autoInputs)
                            else:
                                self.input(values)
                        else:
                            self.input([])
                    else:
                        model = obj.model()
                        obj.clear()
                        for num, i in enumerate(values):
                            item = QStandardItem(i)
                            # 背景颜色
                            if num % 2 == 0:
                                item.setBackground(QColor(255, 255, 255))
                            else:
                                item.setBackground(QColor(237, 243, 254))
                            model.appendRow(item)
            if isinstance(obj, QRadioButton):
                value = self.gblocks_settings.value(
                    name, "true")  # get stored value from registry
                obj.setChecked(
                    self.factory.str2bool(value))  # restore checkbox
            if isinstance(obj, QLineEdit):
                value = self.gblocks_settings.value(
                    name, "_gb")  # get stored value from registry
                obj.setText(value)
            if isinstance(obj, QSpinBox):
                value = self.gblocks_settings.value(
                    name)  # get stored value from registry
                if value:
                    obj.setValue(int(value))
        if self.radioButton_2.isChecked():
            self.comboBox_13.setEnabled(True)
        elif self.radioButton.isChecked() or self.radioButton_3.isChecked():
            self.comboBox_13.setEnabled(False)

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
        self.log_gui.close()  # 关闭子窗口
        self.closeSig.emit("Gblocks", self.fetchWorkflowSetting())
        # 取消选中文字
        self.radioButton.setFocus()
        self.spinBox_2.lineEdit().deselect()
        self.spinBox_3.lineEdit().deselect()
        # 断开showSig和closeSig的槽函数连接
        try:
            self.showSig.disconnect()
        except:
            pass
        try:
            self.closeSig.disconnect()
        except:
            pass
        if self.workflow:
            self.ui_closeSig.emit("Gblocks")
            # 自动跑的时候不杀掉程序
            return
        if self.isRunning():
            # print(self.isRunning())
            reply = QMessageBox.question(
                self,
                "Gblocks",
                "<p style='line-height:25px; height:25px'>Gblocks is still running, terminate it?</p>",
                QMessageBox.Yes,
                QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                try:
                    self.worker.stopWork()
                    if platform.system().lower() in ["windows", "darwin"]:
                        self.gb_popen.kill()
                    else:
                        os.killpg(os.getpgid(self.gb_popen.pid), signal.SIGTERM)
                    self.gb_popen = None
                    self.interrupt = True
                except:
                    self.gb_popen = None
                    self.interrupt = True
            else:
                event.ignore()

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
                pick_files = [i for i in files if os.path.splitext(
                    i)[1].upper() in [".FASTA", ".FAS", ".PIR", ".NBRF"]]
                if pick_files:
                    self.input(files)
                else:
                    QMessageBox.warning(
                        self,
                        "Gblocks",
                        "<p style='line-height:25px; height:25px'>Only files in fasta, nbrf and pir formats are allowed!</p>")
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
        return super(Gblocks, self).eventFilter(obj, event)  # 0

    def input(self, infiles):
        self.comboBox_4.refreshInputs([])  # 先刷新一个空的
        dict_taxon_num = {}
        self.seq_num_differ = False  # 序列数目相同就是false
        self.runAnyway = False
        self.comboBox_10.setDisabled(False)
        self.comboBox_2.setDisabled(False)
        new_infiles = []  # 预防有时候有些文件无效
        for i in infiles:
            if not os.path.exists(i):
                continue
            with open(i, encoding="utf-8", errors='ignore') as f:
                content = f.read()
                self.seq_num = content.count(">")
                if self.seq_num == 0:
                    self.popup_Gblocks_exception(
                        "The file %s is not in fasta format!" % (os.path.basename(i)))
                    self.comboBox_4.refreshInputs([])
                    return
                try:
                    if re.search(r"(?m)^\n(?!\>)", content):
                        # 序列内部有空行
                        content = re.sub(r"(?m)^\n(?!\>)", "", content)
                        with open(i, "w", encoding="utf-8") as f1:
                            # 重新保存一下该文件
                            f1.write(content)
                    else:
                        # 多了一个\r的情况
                        with open(i, "w", encoding="utf-8") as f1:
                            # 重新保存一下该文件
                            f1.write(content)
                except:
                    pass
                dict_taxon_num.setdefault(
                    self.seq_num, []).append(os.path.basename(i))
            new_infiles.append(i)
        if not new_infiles:  # 如果没有有效的文件
            return
        if len(dict_taxon_num) > 1:
            self.seq_num_differ = True
        # 物种数目一样,如果是workflow方式，就直接都用最低配置
        if len(dict_taxon_num) == 1 or self.workflow:
            self.auto_parFromfile()
        else:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setText(
                'Input files contain different numbers of sequences (which implies that some genes are missing), '
                'execute Gblocks with most relaxed parameters to retain as much data as possible?')
            msg.setWindowTitle("Gblocks")
            list_detail = ["Seqs  |  Files"] + [str(i).ljust(6) + "|  " + str(dict_taxon_num[i]) for i in
                                                dict_taxon_num]
            msg.setDetailedText("\n".join(list_detail))
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            if msg.exec_() == QMessageBox.Yes:
                self.comboBox_10.setDisabled(True)
                self.comboBox_2.setDisabled(True)
                self.runAnyway = True
                self.auto_parFromfile()
            else:
                return
        # 输入序列
        self.comboBox_4.refreshInputs(infiles)

    def comboLink(self, text):
        if text:  # 有时候清空combobox会报错
            list_first_opt = []
            for i in range(int(text) + 1):
                if i >= self.seq_num // 2 + 1:
                    list_first_opt.append(str(i))
            self.combobox_refresh(self.comboBox_10, list_first_opt)
            # self.comboBox_10.setCurrentIndex(0)

    def run_code(self, commands):
        startupINFO = None
        if platform.system().lower() == "windows":
            startupINFO = subprocess.STARTUPINFO()
            startupINFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupINFO.wShowWindow = subprocess.SW_HIDE
            self.gb_popen = subprocess.Popen(
                commands, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=startupINFO)
        else:
            self.gb_popen = subprocess.Popen(
                commands, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=startupINFO,
                shell=True, preexec_fn=os.setsid)
        self.factory.emitCommands(self.logGuiSig, commands)
        is_error = False  ##判断是否出了error
        while True:
            QApplication.processEvents()
            if self.isRunning():
                try:
                    out_line = self.gb_popen.stdout.readline().decode("utf-8", errors='ignore')
                except UnicodeDecodeError:
                    out_line = self.gb_popen.stdout.readline().decode("gbk", errors='ignore')
                if out_line == "" and self.gb_popen.poll() is not None:
                    break
                self.logGuiSig.emit(out_line.strip())
                if "Execution terminated" in out_line:
                    is_error = True
            else:
                break
        if is_error:
            self.interrupt = True
            self.gblocks_exception.emit(
                "Error happened! Click <span style='font-weight:600; color:#ff0000;'>Show log</span> to see detail!")
        self.gb_popen = None

    def addText2Log(self, text):
        if re.search(r"\w+", text):
            self.textEdit_log.append(text)
            with open(self.exportPath + os.sep + "PhyloSuite_Gblocks.log", "a", errors='ignore') as f:
                f.write(text + "\n")

    def gui4Log(self):
        dialog = QDialog(self)
        dialog.resize(800, 500)
        dialog.setWindowTitle("Log")
        gridLayout = QGridLayout(dialog)
        horizontalLayout_2 = QHBoxLayout()
        label = QLabel(dialog)
        label.setText("Log of Gblocks:")
        horizontalLayout_2.addWidget(label)
        spacerItem = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        horizontalLayout_2.addItem(spacerItem)
        toolButton = QToolButton(dialog)
        icon2 = QIcon()
        icon2.addPixmap(
            QPixmap(":/picture/resourses/interface-controls-text-wrap-512.png"))
        toolButton.setIcon(icon2)
        toolButton.setCheckable(True)
        toolButton.setToolTip("Use Wraps")
        toolButton.clicked.connect(self.setWordWrap)
        toolButton.setChecked(True)
        horizontalLayout_2.addWidget(toolButton)
        pushButton = QPushButton("Save to file", dialog)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/Save-icon.png"))
        pushButton.setIcon(icon)
        pushButton_2 = QPushButton("Close", dialog)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/if_Delete_1493279.png"))
        pushButton_2.setIcon(icon)
        self.textEdit_log = QTextEdit(dialog)
        self.textEdit_log.setReadOnly(True)
        gridLayout.addLayout(horizontalLayout_2, 0, 0, 1, 2)
        gridLayout.addWidget(self.textEdit_log, 1, 0, 1, 2)
        gridLayout.addWidget(pushButton, 2, 0, 1, 1)
        gridLayout.addWidget(pushButton_2, 2, 1, 1, 1)
        pushButton.clicked.connect(self.save_log_to_file)
        pushButton_2.clicked.connect(dialog.close)
        dialog.setWindowFlags(
            dialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
        return dialog

    def setWordWrap(self):
        button = self.sender()
        if button.isChecked():
            button.setChecked(True)
            self.textEdit_log.setLineWrapMode(QTextEdit.WidgetWidth)
        else:
            button.setChecked(False)
            self.textEdit_log.setLineWrapMode(QTextEdit.NoWrap)

    def save_log_to_file(self):
        content = self.textEdit_log.toPlainText()
        fileName = QFileDialog.getSaveFileName(
            self, "Gblocks", "log", "text Format(*.txt)")
        if fileName[0]:
            with open(fileName[0], "w", encoding="utf-8") as f:
                f.write(content)

    def collect_args(self):
        self.files = self.comboBox_4.fetchListsText()
        dict_abbre = {"None": "n",
                      "With Half": "h",
                      "All": "a",
                      "Yes": "y",
                      "No": "n",
                      "Save": "y",
                      "Don't Save": "n",
                      "Save Text": "t",
                      "Save Short": "s"}
        if self.radioButton.isChecked():
            self.t = "d"
        elif self.radioButton_2.isChecked():
            self.t = "p"
        elif self.radioButton_3.isChecked():
            self.t = "c"
        self.b1 = self.comboBox_10.currentText()
        self.b2 = self.comboBox_2.currentText()
        self.b3 = str(self.spinBox_2.value())
        self.b4 = str(self.spinBox_3.value())
        self.b5 = dict_abbre[self.comboBox_5.currentText()]
        self.b6 = " -b6=%s" % dict_abbre[
            self.comboBox_13.currentText()] if self.t == "p" else ""
        self.s = dict_abbre[self.comboBox_6.currentText()]
        self.p = dict_abbre[self.comboBox_12.currentText()]
        self.v = str(self.spinBox.value())
        self.n = dict_abbre[self.comboBox_7.currentText()]
        self.u = dict_abbre[self.comboBox_8.currentText()]
        self.k = dict_abbre[self.comboBox_11.currentText()]
        self.d = dict_abbre[self.comboBox_9.currentText()]
        self.e = self.lineEdit_3.text()
        prefix = "Ambiguously aligned fragments of %d alignments were removed in batches" % self.comboBox_4.count(
        ) if self.comboBox_4.count() > 1 else "Ambiguously aligned fragments of 1 alignment was removed"
        self.description = '''%s using Gblocks %s (Talavera and Castresana, 2007) with the following parameter settings: minimum number of sequences for a conserved/flank position (%s/%s), maximum number of contiguous non-conserved positions (%s), minimum length of a block (%s), allowed gap positions (%s).''' % (
            prefix, self.version, self.b1, self.b2, self.b3, self.b4, self.comboBox_5.currentText().lower())
        self.reference = "Talavera, G., Castresana, J., 2007. Improvement of phylogenies after removing divergent and ambiguously aligned blocks from protein sequence alignments. Syst. Biol. 56, 564-577."

    def auto_parFromfile(self):
        list_second_opt = []  # 设置第二个选项
        self.seq_range_num = self.seq_num + 1  # 必须加1，参数才会正确
        for j in range(self.seq_range_num):
            if j >= self.seq_num // 2 + 1:
                list_second_opt.append(str(j))
        self.combobox_refresh(self.comboBox_2, list_second_opt)
        # self.comboBox_2.setCurrentIndex(0)
        list_first_opt = []  # 设置第一个选项
        for k in range(int(self.comboBox_2.currentText()) + 1):
            if k >= self.seq_num // 2 + 1:
                list_first_opt.append(str(k))
        self.combobox_refresh(self.comboBox_10, list_first_opt)

    def check_MSA(self, files):
        self.unaligns = []
        self.dict_genes_alignments = OrderedDict()
        parsefmt = Parsefmt("")
        for num, eachFile in enumerate(files):
            geneName = os.path.splitext(os.path.basename(eachFile))[0]
            dict_taxon = parsefmt.readfile(eachFile)
            if self.factory.is_aligned(dict_taxon):
                self.dict_genes_alignments[geneName] = dict_taxon
            else:
                self.unaligned = True
                self.unaligns.append(geneName)
        # 补足数据
        dict_warning_data = OrderedDict()
        dict_maxTaxa = []
        for k in self.dict_genes_alignments:
            list_taxon = list(self.dict_genes_alignments[k].keys())
            dict_maxTaxa.extend(list_taxon)
        list_set_dict_maxTaxa = list(set(dict_maxTaxa))
        self.seq_num = len(list_set_dict_maxTaxa)
        self.auto_parFromfile()
        for i in list_set_dict_maxTaxa:
            lossingGene = []
            for j in self.dict_genes_alignments:
                if i not in self.dict_genes_alignments[j]:
                    keys = list(self.dict_genes_alignments[j].keys())
                    alignmentLenth = len(
                        self.dict_genes_alignments[j][keys[0]])
                    self.dict_genes_alignments[j][i] = "?" * alignmentLenth
                    lossingGene.append(j)
            if lossingGene:
                dict_warning_data[i] = lossingGene
        # 覆盖以前的文件
        self.input_files = []
        convertfmt = Convertfmt(
            **{"export_path": self.exportPath, "export_fas": True})
        for name in self.dict_genes_alignments:
            convertfmt.generate_each(self.dict_genes_alignments[name], name)
            self.input_files.append(convertfmt.f6)
        # 生成报错信息
        if dict_warning_data:
            max_len_taxa = len(max(list(dict_warning_data), key=len))
            # 要大于species的占位符
            max_len_taxa = max_len_taxa if max_len_taxa > 7 else 7
            list_detail = ["Species".ljust(max_len_taxa) + " |Missing genes"] + [
                str(i).ljust(max_len_taxa) + " |" + str(dict_warning_data[i]) for i in dict_warning_data]
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setText(
                "<p style='line-height:25px; height:25px'>Missing genes are replaced with '?' (see details or 'missing_genes.txt')</p>")
            msg.setWindowTitle("Warning")
            msg.setDetailedText("\n".join(list_detail))
            msg.setStandardButtons(QMessageBox.Ok)
            with open(self.exportPath + os.sep + "missing_genes.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(list_detail))
            msg.exec_()
            # if msg.exec_() == 1024:  # QDialog.Accepted:
            #     if self.workflow:
            #         ##work flow跑的
            #         self.startButtonStatusSig.emit(
            #             [
            #                 self.pushButton,
            #                 self.progressBar,
            #                 "workflow stop",
            #                 self.exportPath,
            #                 self.qss_file,
            #                 self])
            #         self.workflow_finished.emit("finished")
            #         return
            #     self.startButtonStatusSig.emit(
            #         [self.pushButton, self.progressBar, "stop", self.exportPath, self.qss_file, self])
            #     self.focusSig.emit(self.exportPath)

    def combobox_refresh(self, widget, list_items):
        model = widget.model()
        widget.clear()
        for num, i in enumerate(list_items):
            item = QStandardItem(i)
            # 背景颜色
            if num % 2 == 0:
                item.setBackground(QColor(255, 255, 255))
            else:
                item.setBackground(QColor(237, 243, 254))
            model.appendRow(item)
        widget.setCurrentIndex(0)

    def isRunning(self):
        '''判断程序是否运行,依赖进程是否存在来判断'''
        return hasattr(self, "gb_popen") and self.gb_popen and not self.interrupt

    def popup_Gblocks_exception(self, text):
        QMessageBox.information(
            self,
            "Gblocks",
            "<p style='line-height:25px; height:25px'>%s</p>" % text)
        if "Show log" in text:
            self.on_pushButton_9_clicked()

    def popupAutoDec(self, init=False):
        self.init = init
        self.factory.popUpAutoDetect("Gblocks", self.workPath, self.auto_popSig, self)

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
            widget = popupUI.listWidget_framless.itemWidget(
                popupUI.listWidget_framless.selectedItems()[0])
            autoInputs = widget.autoInputs
            self.input(autoInputs)

    def fetchWorkflowSetting(self):
        '''* Data type
          * Minimum Number Of Sequences For A Conserved Position:
          * Minimum Number Of Sequences For A Flank Position:
          * Maximum Number Of Contiguous Nonconserved Positions:
          * Minimum Length Of A Block:
          * Allowed Gap Positions:'''
        settings = '''<p class="title">***Gblocks***</p>'''
        if self.radioButton.isChecked():
            data_type = "Nucleotide"
        elif self.radioButton_2.isChecked():
            data_type = "Protein"
        elif self.radioButton_3.isChecked():
            data_type = "Codons"
        settings += '<p>Data type: <a href="self.Gblocks_exe factory.highlightWidgets(x.radioButton,' \
                    'x.radioButton_2,x.radioButton_3)">%s</a></p>' % data_type
        conserve_pos = self.comboBox_10.currentText()
        if conserve_pos:
            settings += '<p>Minimum Number Of Sequences For A Conserved Position: <a href="self.Gblocks_exe ' \
                        'comboBox_10.showPopup() factory.highlightWidgets(x.comboBox_10)">%s</a></p>' % conserve_pos
        else:
            settings += '<p>Minimum Number Of Sequences For A Conserved Position: <span style="font-weight:600; color:green;">auto detect when loading files</span></p>'
        flank_pos = self.comboBox_2.currentText()
        if flank_pos:
            settings += '<p>Minimum Number Of Sequences For A Conserved Position: <a href="self.Gblocks_exe ' \
                        'comboBox_2.showPopup() factory.highlightWidgets(x.comboBox_2)">%s</a></p>' % flank_pos
        else:
            settings += '<p>Minimum Number Of Sequences For A Flank Position: <span style="font-weight:600; color:green;">auto detect when loading files</span></p>'
        max_pos = self.spinBox_2.value()
        settings += '<p>Maximum Number Of Contiguous Nonconserved Positions: ' \
                    '<a href="self.Gblocks_exe spinBox_2.setFocus() spinBox_2.selectAll()' \
                    ' factory.highlightWidgets(x.spinBox_2)">%s</a></p>' % max_pos
        min_block = self.spinBox_3.value()
        settings += '<p>Minimum Length Of A Block: <a href="self.Gblocks_exe spinBox_3.setFocus() spinBox_3.selectAll()' \
                    ' factory.highlightWidgets(x.spinBox_3)">%s</a></p>' % min_block
        allow_gap = self.comboBox_5.currentText()
        settings += '<p>Allowed Gap Positions: <a href="self.Gblocks_exe ' \
                    'comboBox_5.showPopup() factory.highlightWidgets(x.comboBox_5)">%s</a></p>' % allow_gap
        return settings

    def showEvent(self, event):
        QTimer.singleShot(100, lambda: self.showSig.emit(self))
        # self.showSig.emit(self)

    def isFileIn(self):
        return self.comboBox_4.count()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = Gblocks()
    ui.show()
    sys.exit(app.exec_())
