#!/usr/bin/env python
# -*- coding: utf-8 -*-
import multiprocessing
import platform
import re
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from src.factory import Factory, WorkThread
from src.tiger_index import run_index
from uifiles.Ui_Tiger import Ui_Tiger
import inspect
import os
import sys
import traceback
from multiprocessing.pool import ApplyResult

# TODO: test subsets function speed-up

def pool_init(queue):
    # see http://stackoverflow.com/a/3843313/852994
    run_index.queue = queue

class Tiger(QDialog, Ui_Tiger, object):
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    progressSig = pyqtSignal(int)  # 控制进度条
    startButtonStatusSig = pyqtSignal(list)

    def __init__(
            self,
            workPath=None,
            focusSig=None,
            parent=None):
        super(Tiger, self).__init__(parent)
        self.factory = Factory()
        self.parent = parent
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.focusSig = focusSig
        self.setupUi(self)
        self.interrupt = False
        # 保存设置
        self.tiger_settings = QSettings(
            self.thisPath +
            '/settings/tiger_settings.ini',
            QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.tiger_settings.setFallbacksEnabled(False)
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
        # 信号和槽
        self.spinBox_2.valueChanged.connect(lambda : [self.changeCombox(self.comboBox),
                                                      self.changeCombox(self.comboBox_2)])
        self.checkBox_3.toggled.connect(lambda bool_: self.checkBox_4.setChecked(not bool_))
        self.checkBox_4.toggled.connect(lambda bool_: self.checkBox_3.setChecked(not bool_))
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
        self.comboBox_4.setTopText()

    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        fileNames = QFileDialog.getOpenFileNames(
            self, "Input alignment file",
            filter="Fasta Format(*.fa *.fas *.fasta)")
        if fileNames[0]:
            self.input(fileNames[0])

    @pyqtSlot()
    def on_pushButton_22_clicked(self):
        fileName = QFileDialog.getOpenFileName(
            self, "Input reference file",
            filter="Ti Format(*.ti)")
        if fileName[0]:
            base = os.path.basename(fileName[0])
            self.lineEdit_2.setText(base)
            self.lineEdit_2.setToolTip(fileName[0])

    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        """
        Stop
        """
        if self.isRunning():
            reply = QMessageBox.question(
                self,
                "Confirmation",
                "<p style='line-height:25px; height:25px'>Tiger is still running, terminate it?</p>",
                QMessageBox.Yes,
                QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                try:
                    self.worker.stopWork()
                    self.pool.terminate()  # Terminate all processes in the Pool
                    self.pool = None
                    self.interrupt = True
                except:
                    self.pool = None
                    self.interrupt = True
                QMessageBox.information(
                    self,
                    "Tiger",
                    "<p style='line-height:25px; height:25px'>Program has been terminated!</p>")
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton,
                        [self.progressBar],
                        "except",
                        self.dict_args["exportPath"],
                        self.qss_file,
                        self])

    @pyqtSlot()
    def on_pushButton_clicked(self):
        """
        execute program
        """
        if self.comboBox_4.count():
            # 有数据才执行
            self.interrupt = False
            self.dict_args = {}
            self.dict_args["exception_signal"] = self.exception_signal
            self.dict_args["progressSig"] = self.progressSig
            self.dict_args["workPath"] = self.workPath
            self.output_dir_name = self.factory.fetch_output_dir_name(self.dir_action)
            self.exportPath = self.factory.creat_dirs(self.workPath + \
                                                      os.sep + "Tiger_results" + os.sep + self.output_dir_name)
            self.dict_args["exportPath"] = self.exportPath
            ok = self.factory.remove_dir(self.exportPath, parent=self)
            if not ok:
                #提醒是否删除旧结果，如果用户取消，就不执行
                return
            self.dict_args["alignments"] = self.comboBox_4.fetchListsText()
            self.dict_args["reference"] = self.lineEdit_2.toolTip()
            self.dict_args["chunk_n"] = self.spinBox.value()
            self.dict_args["bins_n"] = self.spinBox_2.value()
            self.dict_args["included_bins"] = [self.comboBox.itemText(i) for i in range(self.comboBox.count())
                                                if self.comboBox.model().item(i).checkState() == Qt.Checked]
            self.dict_args["excluded_bins"] = [self.comboBox_2.itemText(i) for i in range(self.comboBox_2.count())
                                              if self.comboBox_2.model().item(i).checkState() == Qt.Checked]
            self.dict_args["unknown_chars"] = self.lineEdit.text()
            self.dict_args["out_fmt"] = self.comboBox_3.currentIndex()
            self.dict_args["mask"] = self.checkBox.isChecked()
            self.dict_args["rate_list_yes"] = self.checkBox_2.isChecked()
            self.dict_args["thread"] = int(self.comboBox_6.currentText())
            self.queue = multiprocessing.Queue()
            self.pool = multiprocessing.get_context("spawn").Pool(processes=self.dict_args["thread"],
                                             initializer=pool_init, initargs=(self.queue,)) #\
                # if platform.system().lower() == "windows" else multiprocessing.Pool(processes=self.dict_args["thread"],
                #                                             initializer=pool_init, initargs=(self.queue,))
            # Check for progress periodically
            self.timer = QTimer()
            self.timer.timeout.connect(self.updateProcess)
            self.timer.start(1)
            self.worker = WorkThread(self.run_command, parent=self)
            self.worker.start()
        else:
            QMessageBox.critical(
                self,
                "Tiger",
                "<p style='line-height:25px; height:25px'>Please input files first!</p>")

    def run_command(self):
        try:
            # 清空文件夹，放在这里方便统一报错
            self.startButtonStatusSig.emit(
                [
                    self.pushButton,
                    self.progressBar,
                    "start",
                    self.dict_args["exportPath"],
                    self.qss_file,
                    self])
            self.dict_file_progress = {os.path.basename(file): 0 for file in self.dict_args["alignments"]}
            # index
            # input_, exportPath, reference_,
            # rate_list_yes, format_, mask,
            # bin_n, excluded_bins, included_bins, split_ = 1
            async_results_index = [self.pool.apply_async(run_index, args=(file,
                                                                          self.dict_args["exportPath"],
                                                                          self.dict_args["reference"],
                                                                          self.dict_args["rate_list_yes"],
                                                                          self.dict_args["out_fmt"],
                                                                          self.dict_args["mask"],
                                                                          self.dict_args["bins_n"],
                                                                          self.dict_args["excluded_bins"],
                                                                          self.dict_args["included_bins"],
                                                                          self.dict_args["chunk_n"])) for
                             num, file in enumerate(self.dict_args["alignments"])]
            self.pool.close()  # 关闭进程池，防止进一步操作。如果所有操作持续挂起，它们将在工作进程终止前完成
            map(ApplyResult.wait, async_results_index)
            [r.get() for r in async_results_index]
            if not self.interrupt:
                self.pool = None
                self.interrupt = False
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
                self.pool = None
                self.interrupt = False
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
                    self.dict_args["exportPath"],
                    self.qss_file,
                    self])
            self.pool = None
            self.interrupt = False

    def changeCombox(self, comboBox):
        currentBin_n = self.spinBox_2.value()
        model = comboBox.model()
        comboBox.clear()
        for num, i in enumerate(range(currentBin_n)):
            item = QStandardItem(str(i + 1))
            item.setCheckState(Qt.Unchecked)
            # 背景颜色
            if num % 2 == 0:
                item.setBackground(QColor(255, 255, 255))
            else:
                item.setBackground(QColor(237, 243, 254))
            item.setToolTip(str(i + 1))
            model.appendRow(item)
        comboBox.setTopText()

    def input(self, list_items=None):
        if list_items:
            self.comboBox_4.refreshInputs(list_items)
        else:
            self.comboBox_4.refreshInputs([])

    def guiSave(self):
        # Save geometry
        self.tiger_settings.setValue('size', self.size())
        # self.tiger_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QComboBox):
                # save combobox selection to registry
                index = obj.currentIndex()
                self.tiger_settings.setValue(name, index)
            if isinstance(obj, QCheckBox):
                state = obj.isChecked()
                self.tiger_settings.setValue(name, state)

    def guiRestore(self):

        # Restore geometry
        self.resize(self.tiger_settings.value('size', QSize(500, 500)))
        self.factory.centerWindow(self)
        # self.move(self.tiger_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                if name in ["comboBox", "comboBox_2"]:
                    obj.setTopText()
                    self.changeCombox(obj)
                elif name == "comboBox_6":
                    cpu_num = multiprocessing.cpu_count()
                    list_cpu = [str(i + 1) for i in range(cpu_num)]
                    index = self.tiger_settings.value(name, "0")
                    model = obj.model()
                    obj.clear()
                    for num, i in enumerate(list_cpu):
                        item = QStandardItem(i)
                        # 背景颜色
                        if num % 2 == 0:
                            item.setBackground(QColor(255, 255, 255))
                        else:
                            item.setBackground(QColor(237, 243, 254))
                        model.appendRow(item)
                    obj.setCurrentIndex(int(index))
                else:
                    index = self.tiger_settings.value(name, "0")
                    obj.setCurrentIndex(int(index))
            if isinstance(obj, QCheckBox):
                value = self.tiger_settings.value(
                    name, obj.isChecked())  # get stored value from registry
                obj.setChecked(
                    self.factory.str2bool(value))  # restore checkbox

    def runProgress(self, num):
        oldValue = self.progressBar.value()
        done_int = int(num)
        if done_int > oldValue:
            self.progressBar.setProperty("value", done_int)
            QCoreApplication.processEvents()

    def updateProcess(self):
        if self.queue.empty(): return
        info = self.queue.get()
        # print(info)
        file, progress = info
        self.dict_file_progress[file] = progress
        total_progress = sum(self.dict_file_progress.values())/len(self.dict_file_progress)
        self.progressSig.emit(total_progress)


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
                "Tiger",
                "<p style='line-height:25px; height:25px'>Tiger is still running, terminate it?</p>",
                QMessageBox.Yes,
                QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                try:
                    self.worker.stopWork()
                    self.pool.terminate()  # Terminate all processes in the Pool
                    self.pool = None
                    self.interrupt = True
                except:
                    self.pool = None
                    self.interrupt = True
            else:
                event.ignore()

    def eventFilter(self, obj, event):
        # modifiers = QApplication.keyboardModifiers()
        name = obj.objectName()
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
                if name == "comboBox_4":
                    files = [i for i in files if
                             os.path.splitext(i)[1].upper() in [".FA", ".FAS", ".FASTA"]]
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
        # return QMainWindow.eventFilter(self, obj, event) #
        # 其他情况会返回系统默认的事件处理方法。
        return super(Tiger, self).eventFilter(obj, event)  # 0

    def isRunning(self):
        '''判断程序是否运行,依赖进程是否存在来判断'''
        return hasattr(self, "pool") and self.pool and not self.interrupt

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = Tiger()
    ui.show()
    sys.exit(app.exec_())