#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from src.factory import Factory, WorkThread
from uifiles.Ui_compareTable import Ui_compareTable
import inspect
import os
import sys
import traceback
import subprocess
import itertools
import re
from collections import OrderedDict
from Bio.Phylo.TreeConstruction import DistanceCalculator
from Bio import AlignIO
import platform


class Alignment(object):

    def run_command(self, commands, popen):  # 子线程run
        # print(commands)
        while True:
            try:
                out_line = popen.stdout.readline().decode("utf-8", errors='ignore')
            except UnicodeDecodeError:
                out_line = popen.stdout.readline().decode("gbk", errors='ignore')
            if out_line == "" and popen.poll() is not None:
                break
            # print(out_line)

    def align(self, inputFile, outfile, mafftPath):
        # 尝试去除cmd窗口
        startupINFO = None
        if platform.system().lower() == "windows":
            startupINFO = subprocess.STARTUPINFO()
            startupINFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupINFO.wShowWindow = subprocess.SW_HIDE
        ch_out = ' --inputorder '
        strategy = ' --auto'
        arg = ""
        commands = mafftPath + arg + strategy + ch_out + '"' + inputFile  + \
            '"' + ' > ' + '"' + outfile + '"'
        self.mafft_popen = subprocess.Popen(
            commands, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=startupINFO, shell=True)
        self.run_command(commands, self.mafft_popen)


class GatherTable(object):

    def __init__(self, list_files, isPairwiseAlign, exportPath, progressSig, mafft_exe, headerRows):
        self.list_files = list_files
        self.dict_files = OrderedDict()
        self.isPairwiseAlign = isPairwiseAlign
        self.exportPath = exportPath
        self.progressSig = progressSig
        self.mafft_exe = mafft_exe
        self.headerRows = headerRows
        self.result = ""
        self.readFiles()
        self.progressSig.emit(5)
        self.gatherDict()
        self.save()
        self.progressSig.emit(100)

    def readFiles(self):
        self.headers = ""
        haveHeader = False
        for i in self.list_files:
            base = os.path.basename(i)
            key = base.split(".")[0]
            dict_i = OrderedDict()
            with open(i, encoding="utf-8", errors='ignore') as f:
                list_lines = f.readlines()
            for num, j in enumerate(list_lines):
                if (num + 1) <= self.headerRows:
                    if not haveHeader:
                        self.headers += j
                    continue
                list_line = j.strip("\n").split(",")
                dict_i[list_line[0]] = list_line[1:]
            self.dict_files[key] = dict_i
            haveHeader = True
        self.input_path = os.path.dirname(
            i) if os.path.dirname(
                i) else '.'

    def gatherDict(self):
        self.list_keys = list(self.dict_files.keys())
        # 几个物种两两比较的组合: [('a', 'b'), ('a', 'c'), ('b', 'c')]
        self.combin = list(itertools.combinations(self.list_keys, 2))
        self.progressSig.emit(5)
        self.addHeader()
        # 找到键最多的字典
        # list_maxKeys = max(*[self.dict_files[i]
        #                      for i in self.list_keys], key=len)
        list_maxKeys = list(set().union(*[list(self.dict_files[i].keys())
                             for i in self.list_keys]))
        #得到最长的列的列数
        list_cols = []
        for i in self.list_keys:
            list_cols.extend(list(self.dict_files[i].values()))
        self.table_col_num = len(max(list_cols, key=len))
        self.complement(list_maxKeys)
        gather = ""
        count = len(list_maxKeys)
        ##以第一个表作为参照，complement那里已经补足了，所以每个表的行数都是一样的
        for num, i in enumerate(self.dict_files[self.list_keys[0]]):
            gather += i + "," + self.gatherItem(i, self.list_keys) + "\n"
            self.progressSig.emit(10 + (num * 89 / count))
        self.result = self.headers + self.species_order + \
            "\n" + gather

    def save(self):
        with open(self.exportPath + os.sep + "comp_results.csv", "w", encoding="utf-8") as f:
            # 一次替换不干净，要一直替换
            cleanResult = self.result + "--: none"
            # r",\=\"[/@]+\"," ; r",\=\"[/@]+\"\n"
            while re.search(r",\=?\"?[/@|/-]+\"?,", cleanResult):
                cleanResult = re.sub(r",\=?\"?[/@|/-]+\"?,", ",,", cleanResult)
            # 某行的最后一个也要替换：,-/-\n
            cleanResult = re.sub(r",\=?\"?[/@|/-]+\"?\n", ",\n", cleanResult)
            cleanResult = cleanResult.replace("@", "--") # 单个物种空白的情况
            f.write(cleanResult)

    def gatherItem(self, key, list_dict):
        # 按列号存
        dict_col_num = OrderedDict()
        for i in list_dict:
            # 每个基因对应那一行
            list_ = self.dict_files[i][key]
            for num, j in enumerate(list_):
                # 将空白项换成@
                j = "@" if j == "" else j
                if num in dict_col_num:
                    dict_col_num[num] += "/" + j
                else:
                    dict_col_num[num] = j
        return_ = ['="' + k + '"' for k in dict_col_num.values()]
        if not self.isPairwiseAlign:
            return ",".join(return_)
        identity = ""
        sum_identity = 0
        NA_num = 0
        # 读取不同的物种组合
        for num, k in enumerate(self.combin):
            #k=('a', 'b')
            seq1 = self.dict_files[k[0]][key][-1]
            seq2 = self.dict_files[k[1]][key][-1]
#             print(key, seq1, seq2)
            if self.is_validated(seq1) and self.is_validated(seq2):
                # 确定是核苷酸序列
                with open(self.exportPath + os.sep + "align.fas", "w", encoding="utf-8") as f:
                    f.write(">seq1\n%s\n" % seq1 + ">seq2\n%s\n" % seq2)
                self.mafftAlign()
                float_identity = self.pairwiseIdentity(
                    self.exportPath + os.sep + 'align_mafft.fas')
                identity += "/%.2f" % float_identity
                sum_identity += float_identity
                # 删掉这2个文件
                os.remove(self.exportPath + os.sep + 'align.fas')
                os.remove(self.exportPath + os.sep + 'align_mafft.fas')
            else:
                identity += "/-"
                NA_num += 1
        differ = num + 1 - NA_num
        aver_identity = "/%.2f" % (sum_identity / differ) if differ else "/-"
        aver_identity = "" if len(self.combin) == 1 else aver_identity #只有2个物种不计算平均
        identity += aver_identity
        return_.append(identity.strip("/"))
        return ",".join(return_)

    def pairwiseIdentity(self, alnFile):
        # 序列成对，生成相似性矩阵
        aln = AlignIO.read(open(alnFile), 'fasta')
        calculator = DistanceCalculator('identity')
        identity = (1 - calculator.get_distance(aln).matrix[1][0]) * 100
        return identity

    def is_validated(self, seq, alphabet=set("ATGCN")):
        # 验证是否为核苷酸序列
        "Checks that a sequence only contains values from an alphabet"
        # 序列为空，也会得到空的set()
        flag = True if (
            not (set(seq.upper()) - alphabet)) and seq != "" else False
        return flag

    def mafftAlign(self):
        # mafft比对
        _input = self.exportPath + os.sep + "align.fas"
        output = self.exportPath + os.sep + "align_mafft.fas"
        align_ = Alignment()
        align_.align(_input, output, self.mafft_exe)
        self.mafft_popen = align_.mafft_popen

    def complement(self, list_maxKeys):
        # 补全表格，使之一致
        for i in list_maxKeys:
            # length = len(list_maxKeys[i])
            for j in self.dict_files:
                if i not in self.dict_files[j]:
                    self.dict_files[j][i] = ["--"] * self.table_col_num

    def addHeader(self):
        # 显示在列上
        listPair = [j[0] + "-" + j[1] for j in self.combin]
        _list = self.headers.split("\n")
        self.column_count = len(_list[0].split(","))
        if self.isPairwiseAlign:
            self.headers = self.headers.strip() + ",Identity\n"
            identityHeader = "/".join(listPair) + "/Average"
            self.species_order = "/".join(self.list_keys) + \
                "," * (self.column_count+1) + identityHeader
        else:
            self.species_order = "/".join(self.list_keys)


class CompareTable(QDialog, Ui_compareTable, object):
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    progressSig = pyqtSignal(int)  # 控制进度条
    startButtonStatusSig = pyqtSignal(list)

    def __init__(
            self,
            autoInputs=None,
            workPath=None,
            focusSig=None,
            MAFFTpath=None,
            parent=None):
        super(CompareTable, self).__init__(parent)
        self.parent = parent
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.mafft_exe = MAFFTpath
        self.setupUi(self)
        self.autoInputs = autoInputs
        self.focusSig = focusSig
        # 保存设置
        self.CompareTable_settings = QSettings(
            self.thisPath +
            '/settings/CompareTable_settings.ini',
            QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.CompareTable_settings.setFallbacksEnabled(False)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        # 恢复用户的设置
        self.guiRestore()
        self.exception_signal.connect(self.popupException)
        self.startButtonStatusSig.connect(self.factory.ctrl_startButton_status)
        self.progressSig.connect(self.runProgress)
        self.listWidget.installEventFilter(self)
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
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#5-14-2-1-Brief-example" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#5-14-2-1-Brief-example"
        self.label_2.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))

    @pyqtSlot()
    def on_pushButton_clicked(self):
        """
        execute program
        """
        self.list_files = [
            self.listWidget.item(i).toolTip() for i in range(self.listWidget.count())]
        if len(self.list_files) >= 2:
            # 有数据才执行
            self.headerRows = self.spinBox.value()
            self.output_dir_name = self.factory.fetch_output_dir_name(self.dir_action)
            self.exportPath = self.factory.creat_dirs(self.workPath +
                                                os.sep + "comp_tbl_results" + os.sep + self.output_dir_name)
            self.ispairwiseAlign = self.checkBox.isChecked()
            ok = self.factory.remove_dir(self.exportPath, parent=self)
            if not ok:
                #提醒是否删除旧结果，如果用户取消，就不执行
                return
            self.worker = WorkThread(self.run_command, parent=self)
            self.worker.start()
        else:
            QMessageBox.critical(
                self,
                "Compare table",
                "<p style='line-height:25px; height:25px'>Please input at least two files!</p>")

    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        """
        open files
        """
        fileNames = QFileDialog.getOpenFileNames(
            self, "Input Files", filter="CSV Format(*.csv);;")
        if fileNames[0]:
            self.input(fileNames[0])

    @pyqtSlot()
    def on_toolButton_T_clicked(self):
        '''
        delete
        '''
        listItems = self.listWidget.selectedItems()
        if not listItems:
            return
        for item in listItems:
            self.listWidget.takeItem(self.listWidget.row(item))

    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        '''
        cancel
        '''
        # ctypes.windll.kernel32.TerminateThread(  # @UndefinedVariable
        #     self.worker.handle, 0)

        self.close()

    def run_command(self):
        try:
            #清空文件夹，放在这里方便统一报错
            time_start = datetime.datetime.now()
            # raise BaseException
            self.startButtonStatusSig.emit(
                [
                    self.pushButton,
                    self.progressBar,
                    "start",
                    self.exportPath,
                    self.qss_file,
                    self])
            self.gatherTable = GatherTable(
                self.list_files, self.ispairwiseAlign, self.exportPath, self.progressSig, self.mafft_exe, self.headerRows)
            self.startButtonStatusSig.emit(
                [
                    self.pushButton,
                    self.progressBar,
                    "stop",
                    self.exportPath,
                    self.qss_file,
                    self])
            self.focusSig.emit(self.exportPath)
            time_end = datetime.datetime.now()
            description = """The sequences were pairwise aligned with MAFFT (Katoh and Standley, 2013) first, then the genetic distances (identity) among sequences were calculated with the “DistanceCalculator” function in Biopython (Cock, et al., 2009) using the “identity” model."""
            mafft_ref = "Katoh, K., Standley, D.M., 2013. MAFFT multiple sequence alignment software version 7: improvements in performance and usability. Mol. Biol. Evol. 30, 772-780."
            biopython_ref = "Cock, P.J., Antao, T., Chang, J.T., Chapman, B.A., Cox, C.J., Dalke, A., Friedberg, I., Hamelryck, T., Kauff, F., Wilczynski, B., et al. (2009). Biopython: freely available Python tools for computational molecular biology and bioinformatics. Bioinformatics 25, 1422-1423."
            self.time_used_des = "Start at: %s\nFinish at: %s\nTotal time used: %s\n\n" % (str(time_start), str(time_end),
                                                                                  str(time_end - time_start))
            ps_cite = "If you use PhyloSuite v1.2.3, please cite:\nZhang, D., F. Gao, I. Jakovlić, H. Zou, J. Zhang, W.X. Li, and G.T. Wang, PhyloSuite: An integrated and scalable desktop platform for streamlined molecular sequence data management and evolutionary phylogenetics studies. Molecular Ecology Resources, 2020. 20(1): p. 348–355. DOI: 10.1111/1755-0998.13096.\n\n"
            text = ps_cite + self.time_used_des if not self.checkBox.isChecked() else description + "\n\n" + ps_cite + "If you use MAFFT, please cite:\n%s\n\nIf you use Biopython, please cite:\n%s\n\n"%(mafft_ref, biopython_ref) + self.time_used_des
            with open(self.exportPath + os.sep + "summary and citation.txt", "w", encoding="utf-8") as f:
                f.write(text)
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
        self.CompareTable_settings.setValue('size', self.size())
        # self.CompareTable_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QListWidget):
                allItems = [
                    obj.item(i).toolTip() for i in range(obj.count())]
                self.CompareTable_settings.setValue(name, allItems)
            if isinstance(obj, QCheckBox):
                state = obj.isChecked()
                self.CompareTable_settings.setValue(name, state)

    def guiRestore(self):

        # Restore geometry
        self.resize(self.factory.judgeWindowSize(self.CompareTable_settings, 652, 483))
        self.factory.centerWindow(self)
        # self.move(self.CompareTable_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QListWidget):
                if self.autoInputs:
                    self.input(self.autoInputs)
                else:
                    values = self.CompareTable_settings.value(name, [])
                    if values:
                        self.input(values)
            if isinstance(obj, QCheckBox):
                value = self.CompareTable_settings.value(
                    name, "true")  # get stored value from registry
                obj.setChecked(
                    self.factory.str2bool(value))  # restore checkbox

    def runProgress(self, num):
        oldValue = self.progressBar.value()
        done_int = int(num)
        if done_int > oldValue:
            self.progressBar.setProperty("value", done_int)
            QCoreApplication.processEvents()

    def popupException(self, exception):
        rgx = re.compile(r'Permission.+?[\'\"](.+\.csv)[\'\"]')
        if rgx.search(exception):
            csvfile = rgx.search(exception).group(1)
            reply = QMessageBox.critical(
                self,
                "Compare table",
                "<p style='line-height:25px; height:25px'>Please close '%s' file first!</p>"%os.path.basename(csvfile),
                QMessageBox.Yes,
                QMessageBox.Cancel)
            if reply == QMessageBox.Yes and platform.system().lower() == "windows":
                os.startfile(csvfile)
        else:
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
                QListWidget):
            if event.type() == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    # must accept the dragEnterEvent or else the dropEvent
                    # can't occur !!!
                    event.accept()
                    return True
            if event.type() == QEvent.Drop:
                files = [u.toLocalFile() for u in event.mimeData().urls()]
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
        # 其他情况会返回系统默认的事件处理方法。
        return super(CompareTable, self).eventFilter(obj, event)  # 0

    def input(self, files):
        self.listWidget.clear()
        for num, i in enumerate(files):
            if not os.path.exists(i):
                continue
            item = QListWidgetItem(os.path.basename(i))
            item.setToolTip(i)
            # 背景颜色
            if num % 2 == 0:
                item.setBackground(QColor(255, 255, 255))
            else:
                item.setBackground(QColor(237, 243, 254))
            self.listWidget.addItem(item)

    # def checkInputPaths(self, files):
    #     for i in files:
    #         state = self.factory.checkPath(i, mode="silence", parent=self, allow_space=True)
    #         if state != True:
    #             illegalTXT, path_text = state
    #             QMessageBox.information(
    #                 self,
    #                 "PhyloSuite",
    #                 "<p style='line-height:25px; height:25px'>There may be some non-standard characters in the path (<span style=\"color:red\">%s</span>),"
    #                 " try to copy the file to a new path and try again. The archcriminal characters in the path are shown in red:<br> \"%s\"</p>" %(illegalTXT, path_text),
    #                 QMessageBox.Ok)
    #             return False
    #     return True