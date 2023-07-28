import datetime
import multiprocessing
import platform
import re
import shutil
import signal
import traceback


from PyQt5 import QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from ete3 import NCBITaxa, TextFace
from src.Lg_Baseml import Baseml
from uifiles.Ui_baseml import Ui_Baseml
from src.CustomWidget import MyTaxTableModel

from src.factory import Factory, WorkThread
import inspect
import os
import sys
from uifiles.Ui_mcmctree import Ui_MCMCTree

class MCMCTree(QDialog,Ui_MCMCTree,object):
    showSig = pyqtSignal(QDialog)
    closeSig = pyqtSignal(str, str)
    logGuiSig = pyqtSignal(str)
    startButtonStatusSig = pyqtSignal(list)
    mcmctree_exception = pyqtSignal(str)
    workflow_progress = pyqtSignal(int)
    workflow_finished = pyqtSignal(str)
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    progressSig = pyqtSignal(int)  # 控制进度条

    def __init__(
            self,
            workPath=None,
            focusSig=None,
            mcmctreeEXE=None,
            basemlEXE=None,
            autoInputs=None,
            workflow=False,
            parent=None):
        super(MCMCTree, self).__init__(parent)
        #self.Baseml = Baseml
        self.parent = parent
        self.function_name = "MCMCTree"
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.focusSig = focusSig
        self.workflow = workflow
        self.mcmctreeEXE = mcmctreeEXE
        self.basemlEXE = basemlEXE
        self.seqFileName = ''
        self.treeFileName = ''
        self.setupUi(self)
        self.MCMCTree_settings = QSettings(
           self.thisPath + '/settings/MCMCTree_settings.ini', QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.MCMCTree_settings.setFallbacksEnabled(False)
        self.qss_file = self.factory.set_qss(self)
        # 恢复用户的设置
        self.guiRestore()
        ## 自动导入树和MSA文件
        if autoInputs:
            trees, alns = autoInputs
            self.input(trees[0], 4)
            self.input(alns[0], 3)
        # 槽函数
        self.startButtonStatusSig.connect(self.factory.ctrl_startButton_status)
        self.logGuiSig.connect(self.addText2Log)
        self.progressSig.connect(self.runProgress)
        # 给开始按钮添加菜单
        menu = QMenu(self)
        menu.setToolTipsVisible(True)
        self.work_action = QAction(QIcon(":/picture/resourses/work.png"), "", menu)
        self.work_action.triggered.connect(lambda: self.factory.swithWorkPath(self.work_action, parent=self))
        self.dir_action = QAction(QIcon(":/picture/resourses/folder.png"), "Output Dir: ", menu)
        self.dir_action.triggered.connect(lambda: self.factory.set_direct_dir(self.dir_action, self))
        menu.addAction(self.work_action)
        menu.addAction(self.dir_action)
        self.pushButton_5.toolButton.setMenu(menu)
        self.pushButton_5.toolButton.menu().installEventFilter(self)
        self.factory.swithWorkPath(self.work_action, init=True, parent=self)  # 初始化一下
        self.lineEdit.installEventFilter(self)
        self.lineEdit_2.installEventFilter(self)
        self.log_gui = self.gui4Log()
        #self.temporary_tree = None
        #self.text_gui = self.gui4Text()
        ## brief demo
        country = self.factory.path_settings.value("country", "UK")
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#5-12-1-Brief-example" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#5-12-1-Brief-example"
        self.label_25.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))

    def input(self, file, which):
        base = os.path.basename(file)
        if which == 4:
            self.lineEdit.setText(base)
            self.lineEdit.setToolTip(os.path.abspath(file))
            self.treeFileName = file
        if which == 3:
            self.lineEdit_2.setText(base)
            self.lineEdit_2.setToolTip(os.path.abspath(file))
            self.seqFileName = file
        """tre = self.factory.read_tree(file)
        list_leaves = tre.get_leaf_names()
        self.init_table(list_leaves)"""

    @pyqtSlot()
    def on_pushButton_4_clicked(self):
        fileName = QFileDialog.getOpenFileName(
            self, "Input tre file", filter="Newick Format(*.nwk *.newick *.tre *.trees);;")
        if fileName[0]:
            self.treeFileName = fileName[0]
            self.input(self.treeFileName, 4)
            self.species_matching(4)

    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        fileName = QFileDialog.getOpenFileName(
            self, "Input alignment file", filter="Phylip Format(*.txt);;")
        if fileName[0]:
            self.seqFileName = fileName[0]
            self.input(self.seqFileName, 3)
        self.codon_matching(3)

    @pyqtSlot()
    def on_pushButton_15_clicked(self):
        self.consistency_checking()
        s_Values, ds_Values = self.getParas()
        print(f"s_Values:{s_Values}")
        print(f"ds_Values:{ds_Values}")
        self.ctl_generater(treefile=self.treeFileName)

    @pyqtSlot()
    def on_pushButton_6_clicked(self):
        """
        show log
        """
        self.log_gui.show()

    @pyqtSlot()
    def on_pushButton_7_clicked(self):
        self.gui4Text().show()

    @pyqtSlot()
    def on_pushButton_8_clicked(self):
        self.on_baseml_triggered()
    """@pyqtSlot()
    def on_pushButton_8_clicked(self):
        self.consistency_checking()"""

    @pyqtSlot()
    def on_pushButton_5_clicked(self):
        """
        execute program
        """
        self.commands = self.prepare_for_run()
        self.consistency_checking()
        print(self.commands)
        self.check_usedata()
        if self.commands:
            # 有数据才执行
            self.interrupt = False  # 如果是终止以后重新运行要刷新
            self.textEdit_log.clear()  # 清空log
            self.mcmctree_popen = self.factory.init_popen(self.commands)
            self.factory.emitCommands(self.logGuiSig, self.commands)
            self.worker = WorkThread(self.run_command, parent=self)
            self.worker.start()

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
                    "<p style='line-height:25px; height:25px'>MCMCTree is still running, terminate it?</p>",
                    QMessageBox.Yes,
                    QMessageBox.Cancel)
            else:
                reply = QMessageBox.Yes
            if reply == QMessageBox.Yes:
                try:
                    self.worker.stopWork()
                    if platform.system().lower() in ["windows", "darwin"]:
                        self.mcmctree_popen.kill()
                    else:
                        os.killpg(os.getpgid(self.mcmctree_popen.pid), signal.SIGTERM)
                    self.mcmctree_popen = None
                    self.interrupt = True
                except:
                    self.mcmctree_popen = None
                    self.interrupt = True
                if not self.workflow:
                    QMessageBox.information(
                        self,
                        "MCMCTree",
                        "<p style='line-height:25px; height:25px'>Program has been terminated!</p>")
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton,
                        self.progressBar,
                        "except",
                        self.exportPath,
                        self.qss_file,
                        self])

    @pyqtSlot()
    def on_pushButton_clicked(self):
        """
        add calibration
        """
        # 判断用户是否导入了树，没有就弹框提示
        # 如果是无根树提醒用户
        set_NCBI_db = self.factory.checkNCBIdb(self)
        if set_NCBI_db:
            self.updateTaxonomyDB()
            return
        if hasattr(self, "tree_with_tipdate"):
            tre = self.factory.read_tree(self.tree_with_tipdate, parent=self)
        else:
            tree_path = self.lineEdit.toolTip()
            tre = self.factory.read_tree(tree_path, parent=self)
        if tre:
            for node in tre.traverse():
                if 'name' in node.features:
                    # node_bound = re.search(r">(\d*\.\d{2})+<(\d*\.\d{2})|"
                    #                        r">(\d*\.\d{2})|"
                    #                        r"<(\d*\.\d{2})|"
                    #                        r"B\((\d*\.\d{2}),(\d*\.\d{2})(?:,(\d*\.\d{3}),(\d*\.\d{3}))?\)|"
                    #                        r"L\((\d*\.\d{2})(?:,(\d*\.\d),(\d*\.\d),(\d*\.\d{3}))?\)|"
                    #                        r"U\((\d*\.\d{2})(?:,(\d*\.\d{3}))?\)"
                    #                        , node.name)
                    node_bound = re.search(r">|<|B.*\(|U.*\(|L.*\(", node.name)
                    if node_bound:
                        if not node.name.startswith("'"):
                            node.name = f"'{node.name}"
                        if not node.name.endswith("'"):
                            node.name = f"{node.name}'"
                        text = node.name
                        node.add_face(TextFace(text), column=0, position="branch-top")
            tre.show(name="MCMCTREE-ETE", parent=self)
        #nwk_string = tre.write(format=5)
        #print(nwk_string)
        """else:
            QMessageBox.warning(self, "no file", "No tree file is imported. Please import a file.")"""

    """def on_baseml_triggered(self):
        #filePath, workPath = self.fetchWorkPath(mode="all")
        basemlEXE = self.factory.programIsValid("PAML", mode="tool")
        self.Baseml = Baseml(focusSig=self.focusSig,
                             basemlEXE=basemlEXE,
                             parent=self)
        self.Baseml.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint |self.Baseml.windowFlags())
        self.Baseml.show()"""


    def species_matching(self, which):
        if which == 4:
            tree_path = self.lineEdit.toolTip()
            tre = self.factory.read_tree(tree_path, parent=self)
            species_count = len(tre)
            self.label_5.setText(str(species_count))

    def codon_matching(self, which):
        if which == 3:
            seq_path = self.lineEdit_2.toolTip()
            with open(seq_path, 'r') as file:
                lines = file.readlines()
                first_species = lines[1].split()[0]
                print(first_species)
                ndata_count = sum([1 for line in lines if line.strip().startswith(first_species)])
                print(ndata_count)
                self.spinBox.setValue(ndata_count)

    def consistency_checking(self):
        tree_path = self.lineEdit.toolTip()
        seq_path = self.lineEdit_2.toolTip()
        if tree_path:
            tre = self.factory.read_tree(tree_path, parent=self)
            tre_species = set([leaf.name for leaf in tre.iter_leaves()])
            tre_species_count = len(tre_species)
        else:
            QMessageBox.warning(self, "no file", "No treefile file is imported, please input the treefile!")
        if seq_path:
            seq_species = set()
            with open(seq_path, 'r') as file:
                for line in file:
                    if line.strip():
                        match = re.search(r'[a-z]+', line)
                        if match:
                            species_name = match.group()
                            seq_species.add(species_name)
            seq_species_count = len(seq_species)
            #print(seq_species)
            #print(seq_species_count)
            #print(tre_species)
            #print(tre_species_count)
            if seq_species == tre_species:
                if seq_species_count == tre_species_count:
                    pass
                    #QMessageBox.information(self, "consistency check", "The species are the same in both files.")
            else:
                QMessageBox.warning(self, "different", "Different species, re-import files!")
        else:
            QMessageBox.warning(self, "no file", "No sequence file is imported, please input the seqfile!")

    def rename_file(self, filePath, oldName, newName):
        out_file_path = os.path.join(filePath, oldName)
        in_file_path = os.path.join(filePath, newName)
        if os.path.exists(out_file_path):
            os.rename(out_file_path, in_file_path)

    def check_usedata(self):
        usedata_value = {'no data': 0, 'seq like': 1, 'normal approximation': 2, 'out.BV': 3}
        current_usedata = self.comboBox_3.currentText()

        if usedata_value.get(current_usedata, -1) == 2:
            options = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
            directory = QFileDialog.getExistingDirectory(self, "Choose folder", options=options)
            if directory:
                self.exportPath = directory
                QMessageBox.information(self, "Export Path Updated", f"The export path has been updated to: {directory}")
                self.rename_file(self.exportPath, "out.BV", "in.BV")


    def run_command(self):
        try:
            time_start = datetime.datetime.now()
            self.startButtonStatusSig.emit(
                [
                    self.pushButton_5,
                    self.progressBar,
                    "start",
                    self.exportPath,
                    self.qss_file,
                    self])
            print(111)
            self.run_code()
            time_end = datetime.datetime.now()
            self.time_used = str(time_end - time_start)
            self.time_used_des = "Start at: %s\nFinish at: %s\nTotal time used: %s\n\n" % (str(time_start), str(time_end),
                                                                                           self.time_used)
            # 加上version信息
            with open(self.exportPath + os.sep + "PhyloSuite_MCMCTREE.log") as f:
                content = f.read()
            rgx_version = re.compile(r"-+\s+MCMCTREE.+?(\d+\.\d+\.\d+)")
            if rgx_version.search(content):
                self.version = rgx_version.search(content).group(1)
            else:
                self.version = ""
            self.description = self.description.replace("$version$", self.version)
            with open(self.exportPath + os.sep + "summary and citation.txt", "w", encoding="utf-8") as f:
                f.write(self.description +
                        f"\n\nIf you use PhyloSuite v1.2.3 v1.2.3, please cite:\n{self.factory.get_PS_citation()}\n\n"
                        "If you use PartitionFinder 2, please cite:\n" + self.reference + "\n\n" + self.time_used_des)
            if not self.interrupt:
                if self.workflow:
                    # work flow跑的
                    self.startButtonStatusSig.emit(
                        [
                            self.pushButton_5,
                            self.progressBar,
                            "workflow stop",
                            self.exportPath,
                            self.qss_file,
                            self])
                    self.workflow_finished.emit("finished")
                    return
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton_5,
                        self.progressBar,
                        "stop",
                        self.exportPath,
                        self.qss_file,
                        self])
            else:
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton_5,
                        self.progressBar,
                        "except",
                        self.exportPath,
                        self.qss_file,
                        self])
            if not self.workflow:
                self.focusSig.emit(self.exportPath)
        except BaseException:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号
            self.startButtonStatusSig.emit(
                [
                    self.pushButton_5,
                    self.progressBar,
                    "except",
                    self.exportPath,
                    self.qss_file,
                    self])

    def run_code(self):
        is_error = False  ##判断是否出了error
        error_text = ""
        self.progressSig.emit(99999)
        while True:
            QApplication.processEvents()
            if self.isRunning():
                try:
                    out_line = self.mcmctree_popen.stdout.readline().decode("utf-8", errors="ignore")
                except UnicodeDecodeError:
                    out_line = self.mcmctree_popen.stdout.readline().decode("gbk", errors="ignore")
                if out_line == "" and self.mcmctree_popen.poll() is not None:
                    break
                self.logGuiSig.emit(out_line.strip())
                if re.search(r"^ERROR", out_line):
                    is_error = True
                    error_text = "Error happened! Click <span style='font-weight:600; color:#ff0000;'>Show log</span> to see detail!"
            else:
                break
        if is_error:
            self.interrupt = True
            self.mcmctree_exception.emit(error_text)
        self.mcmctree_popen = None

    def showText(self, lst):
        self.tableView_2.setRowCount(len(lst))
        self.tableView_2.setColumnCount(1)
        for i in range(len(lst)):
            item = QTableWidgetItem(lst[i])
            self.tableView_2.setItem(i, 0, item)

    def guiSave(self):
        # Save geometry
        self.MCMCTree_settings.setValue('size', self.size())
        # self.MCMCTree_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QComboBox):
                # save combobox selection to registry
                index = obj.currentIndex()
                self.MCMCTree_settings.setValue(name, index)
            # if isinstance(obj, QCheckBox):
            #     state = obj.isChecked()
            #     self.MCMCTree_settings.setValue(name, state)
            elif isinstance(obj,QSpinBox):
                int_ = obj.value()
                self.MCMCTree_settings.setValue(name, int_)
            elif isinstance(obj, QDoubleSpinBox):
                float_ = obj.value()
                self.MCMCTree_settings.setValue(name, float_)

    def guiRestore(self):

        # Restore geometry
        self.resize(self.MCMCTree_settings.value('size', QSize(1000, 750)))
        self.factory.centerWindow(self)
        # self.move(self.MCMCTree_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                if name == "comboBox":
                    ini_models = ["***Default***", "JC69", "K80", "F81", "F84", "HKY85", "T92", "TN93", "GTR", "UNREST",
                                  "REVu", "UNRESTu",
                                  "***AAs***", "cpREV10", "cpREV64", "dayhoff", "dayhoff-dcmut", "g1975a", "g1975c",
                                  "g1975p", "g1975v",
                                  "grantham", "jones", "jones-dcmut", "lg", "miyata", "mtART", "mtmam", "mtREV24", "MtZoa",
                                  "wag"]
                    index = self.MCMCTree_settings.value(name, "0")
                    model = obj.model()
                    for num, i in enumerate(ini_models):
                        item = QStandardItem(i)
                        # 背景颜色
                        if "*" in i:
                            item.setBackground(QColor(245, 105, 87))
                            item.setForeground(QColor("white"))
                        elif num % 2 == 0:
                            item.setBackground(QColor(255, 255, 255))
                        else:
                            item.setBackground(QColor(237, 243, 254))
                        model.appendRow(item)
                    obj.setCurrentIndex(int(index))
                    obj.model().item(0).setSelectable(False)
                    obj.model().item(12).setSelectable(False)
                    default_index = ini_models.index("JC69")
                    obj.setCurrentIndex(default_index)
                else:
                    allItems = [obj.itemText(i) for i in range(obj.count())]
                    index = self.MCMCTree_settings.value(name, "0")
                    model = obj.model()
                    obj.clear()
                    for num, i in enumerate(allItems):
                        item = QStandardItem(i)
                        # 背景颜色
                        if num % 2 == 0:
                            item.setBackground(QColor(255, 255, 255))
                        else:
                            item.setBackground(QColor(237, 243, 254))
                        model.appendRow(item)
                    obj.setCurrentIndex(int(index))
            # elif isinstance(obj, QCheckBox):
            #     value = self.MCMCTree_settings.value(
            #         name, "no setting")  # get stored value from registry
            #     if value != "no setting":
            #         obj.setChecked(
            #             self.factory.str2bool(value))  # restore checkbox
            elif isinstance(obj, QSpinBox):
                ini_int_ = obj.value()
                int_ = self.MCMCTree_settings.value(name, ini_int_)
                obj.setValue(int(int_))
            elif isinstance(obj, QDoubleSpinBox):
                ini_float_ = obj.value()
                float_ = self.MCMCTree_settings.value(name, ini_float_)
                obj.setValue(float(float_))

            """elif isinstance(obj, QLineEdit):
                    if name == "lineEdit_5" and self.autoInputs:
                        self.input(self.autoInputs, obj)"""


    def closeEvent(self, event):
        self.guiSave()
        # self.log_gui.close()  # 关闭子窗口
        # 断开showSig和closeSig的槽函数连接
        try:
            self.showSig.disconnect()
        except:
            pass
        try:
            self.closeSig.disconnect()
        except:
            pass

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
            self, "MCMCTree", "log", "text Format(*.txt)")
        if fileName[0]:
            with open(fileName[0], "w", encoding="utf-8") as f:
                f.write(content)

    def gui4Text(self):
        para_s, para_ds = self.getParas()
        """param_indices = {
            'model': {'JC69': 0, 'K80': 1, 'F81': 2, 'F84': 3, 'HKY85': 4}
        }"""

        items_list = [("seed", para_s[13], "-", "-"),
                      ("ndata", para_s[0], "-", "-"),
                      ("seqtype", self.comboBox_2.currentText(), "-", "-"),
                      ("usedata", self.comboBox_3.currentText(), "-", "-"),
                      ("clock", self.comboBox_4.currentText(), "-", "-"),
                      ("RootAge <", para_ds[0], "-", "-"),
                      ("model", self.comboBox.currentText(), "-", "-"),
                      ("alpha", para_ds[4], "-", "-"),
                      ("ncatG", para_s[12], "-", "-"),
                      ("cleandata", self.comboBox_5.currentText(), "-", "-"),
                      ("BDparas", para_ds[1], para_ds[2], para_ds[3]),
                      ("kappa_gamma", para_s[14], para_s[15], "-"),
                      ("alpha_gamma", para_s[1], para_s[2], "-"),
                      ("rgene_gamma", para_s[3], para_s[4], para_s[5]),
                      ("sigma2_gamma", para_s[6], para_s[7], para_s[8]),
                      ("print", self.comboBox_7.currentText(), "-", "-"),
                      ("burnin", para_s[9], "-", "-"),
                      ("samefreq", para_s[10], "-", "-"),
                      ("nsample", para_s[11], "-", "-")]
        dialog = QDialog(self)
        dialog.resize(800, 500)
        dialog.setWindowTitle("Preview configurations")
        model = QStandardItemModel()

        for row, item in enumerate(items_list):
            name_item = QStandardItem(item[0])
            param_item = QStandardItem(str(item[1]))
            param_item_rd = QStandardItem(str(item[2]))
            param_item_th = QStandardItem(str(item[3]))
            model.setItem(row, 0, name_item)
            model.setItem(row, 1, param_item)
            model.setItem(row, 2, param_item_rd)
            model.setItem(row, 3, param_item_th)

        verticalLayout_2 = QVBoxLayout(dialog)
        groupBox = QGroupBox("Configuration", dialog)
        verticalLayout = QVBoxLayout(groupBox)
        tableView = QTableView(groupBox)
        tableView.setModel(model)
        tableView.setColumnWidth(0, 150)  # 第一列宽度为 200
        tableView.setColumnWidth(1, 150)  # 第二列宽度为 100
        tableView.setColumnWidth(2, 150)  # 第三列宽度为 100
        tableView.setColumnWidth(3, 150)
        verticalLayout.addWidget(tableView)
        verticalLayout_2.addWidget(groupBox)
        gridLayout = QGridLayout()
        #pushButton_2 = QPushButton("Save", dialog)
        #gridLayout.addWidget(pushButton_2, 0, 0, 1, 1)
        pushButton = QPushButton("OK", dialog)
        gridLayout.addWidget(pushButton, 0, 1, 1, 1)
        verticalLayout_2.addLayout(gridLayout)
        pushButton.clicked.connect(dialog.close)
        #pushButton.clicked.connect(lambda: self.updateParas(model))
        dialog.setWindowFlags(
            dialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
        return dialog

    def updateParas(self, model):
        para_s, para_ds = self.getParas()
        for row in range(model.rowCount()):
            param_item = model.item(row, 1)
            if param_item:
                para_s[row] = float(param_item.text())
        return para_s, para_ds

    def gui4Log(self):
        dialog = QDialog(self)
        dialog.resize(800, 500)
        dialog.setWindowTitle("Log")
        gridLayout = QGridLayout(dialog)
        horizontalLayout_2 = QHBoxLayout()
        label = QLabel(dialog)
        label.setText("Log of MCMCTree:")
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

    def getParas(self):
        s_Values = []
        ds_Values = []
        for name, obj in inspect.getmembers(self):
            if isinstance(obj,QSpinBox):
                s_Values.append(obj.value())
            elif isinstance(obj,QDoubleSpinBox):
                ds_Values.append(obj.value())
        return s_Values, ds_Values

    def ctl_generater(self, file_path=None, treefile=None):
        def generate_ctl(seqfile, treefile):
            s_Values, ds_Values = self.getParas()
            param_indices = {
                'seed': 13,
                'ndata': 0,
                'seqtype': {'nucleotides': 0, 'codons': 1, 'AAs': 2},
                'usedata': {'no data': 0, 'seq like': 1, 'normal approximation': 2, 'out.BV': 3},
                'clock': {'global clock': 1, 'independent rates': 2, 'correlated rates': 3},
                'RootAge': 0,
                'model': {'JC69': 0, 'K80': 1, 'F81': 2, 'F84': 3, 'HKY85': 4, 'T92': 5,
                          'TN93': 6, 'GTR': 7, 'UNREST': 8, 'REVu': 9, 'UNRESTu': 10,
                          "cpREV10":'cpREV10' , "cpREV64":'cpREV64', "dayhoff":'dayhoff', "dayhoff-dcmut":'dayhoff-dcmut',
                          "g1975a":'g1975a', "g1975c":'g1975c',"g1975p":'g1975p', "":'g1975v',"grantham":'grantham',
                          "jones":'jones', "jones-dcmut":'jones-dcmut', "lg":'lg', "miyata":'miyata',"mtART":'mtART',
                          "mtmam":'mtmam', "mtREV24":'mtREV24', "MtZoa":'MtZoa',"wag":'wag'},
                'alpha': 4,
                'ncatG': 12,
                'cleandata': {'yes': 1, 'no': 0},
                'BDparas': (1, 2, 3),
                'kappa_gamma': (14, 15),
                'alpha_gamma': (1, 2),
                'rgene_gamma': (3, 4, 5),
                'sigma2_gamma': (6, 7, 8),
                'print': {'no mcmc sample': 0, 'except branch rates': 1, 'everything': 2},
                'burnin': 9,
                'sampfreq': 10,
                'nsample': 11
            }
            model_value = {'JC69': 0, 'K80': 1, 'F81': 2, 'F84': 3, 'HKY85': 4, 'T92': 5,
                          'TN93': 6, 'GTR': 7, 'UNREST': 8, 'REVu': 9, 'UNRESTu': 10,
                          "cpREV10":'cpREV10' , "cpREV64":'cpREV64', "dayhoff":'dayhoff', "dayhoff-dcmut":'dayhoff-dcmut',
                          "g1975a":'g1975a', "g1975c":'g1975c',"g1975p":'g1975p', "":'g1975v',"grantham":'grantham',
                          "jones":'jones', "jones-dcmut":'jones-dcmut', "lg":'lg', "miyata":'miyata',"mtART":'mtART',
                          "mtmam":'mtmam', "mtREV24":'mtREV24', "MtZoa":'MtZoa',"wag":'wag'}
            usedata_value = {'no data': 0, 'seq like': 1, 'normal approximation': 2, 'out.BV': 3}
            seqtype_value = {'nucleotides': 0, 'codons': 1, 'AAs': 2}
            cleandata_value = {'YES': 1, 'NO': 0}
            clock_value = {'global clock': 1, 'independent rates': 2, 'correlated rates': 3}
            print_value = {'no mcmc sample': 0, 'except branch rates': 1, 'everything': 2}

            ctl_template = '''          seed = {seed}
       seqfile = {seqfile}
      treefile = {treefile}
      mcmcfile = mcmc.txt
       outfile = out.txt

         ndata = {ndata}  *
       seqtype = {seqtype}  *
       usedata = {usedata}  *
         clock = {clock}  *
       RootAge = '<{RootAge}'  *

         model = {model}  *
         alpha = {alpha}  *
         ncatG = {ncatG}  *

     cleandata = {cleandata}  *

       BDparas = {BDparas}  *
   kappa_gamma = {kappa_gamma}  *
   alpha_gamma = {alpha_gamma}  *

   rgene_gamma = {rgene_gamma}  *
  sigma2_gamma = {sigma2_gamma}  *

         print = {print}  *
        burnin = {burnin}  *
      sampfreq = {sampfreq}  *
       nsample = {nsample}  *

*** Note: Make your window wider (100 columns) before running the program.'''

            ctl_values = {
                'seqfile': seqfile,
                'treefile': treefile,
                'seed': s_Values[param_indices['seed']],
                'ndata': s_Values[param_indices['ndata']],
                'seqtype': self.comboBox_2.currentText(),
                'usedata': self.comboBox_3.currentText(),
                'clock': self.comboBox_4.currentText(),
                'RootAge': ds_Values[param_indices['RootAge']],
                'model': self.comboBox.currentText(),
                'alpha': ds_Values[param_indices['alpha']],
                'ncatG': s_Values[param_indices['ncatG']],
                'cleandata': self.comboBox_5.currentText(),
                'BDparas': ' '.join(str(ds_Values[idx]) for idx in param_indices['BDparas']),
                'kappa_gamma': ' '.join(str(s_Values[idx]) for idx in param_indices['kappa_gamma']),
                'alpha_gamma': ' '.join(str(s_Values[idx]) for idx in param_indices['alpha_gamma']),
                'rgene_gamma': ' '.join(str(s_Values[idx]) for idx in param_indices['rgene_gamma']),
                'sigma2_gamma': ' '.join(str(s_Values[idx]) for idx in param_indices['sigma2_gamma']),
                'print': self.comboBox_7.currentText(),
                'burnin': s_Values[param_indices['burnin']],
                'sampfreq': s_Values[param_indices['sampfreq']],
                'nsample': s_Values[param_indices['nsample']]
            }
            ctl_values['model'] = model_value[ctl_values['model']]
            ctl_values['seqtype'] = seqtype_value[ctl_values['seqtype']]
            ctl_values['usedata'] = usedata_value[ctl_values['usedata']]
            ctl_values['cleandata'] = cleandata_value[ctl_values['cleandata']]
            ctl_values['clock'] = clock_value[ctl_values['clock']]
            ctl_values['print'] = print_value[ctl_values['print']]
            return ctl_template.format(**ctl_values)
        seqfile = os.path.basename(self.seqFileName) if self.seqFileName else ""
        if hasattr(self, "tree_with_tipdate"):
            treefile = "calibration_tree.nwk" if treefile else ""
        else:
            treefile = os.path.basename(treefile) if treefile else ""
        if file_path:
            mcmctree_ctl = generate_ctl(seqfile, treefile)
            with open(file_path, "w", errors="ignore") as f:
                f.write(mcmctree_ctl)
        else:
            options = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
            directory = QFileDialog.getExistingDirectory(self, "Choose folder", options=options)
            if directory:
                mcmctree_ctl = generate_ctl(seqfile, treefile)
                file_path = f"{directory}{os.sep}mcmctree.ctl"
                if os.path.exists(file_path):
                    reply = QMessageBox.question(self, "File Exists", f"The file {file_path} already exists. Do you want to overwrite it？",
                                                 QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        with open(file_path, "w", errors="ignore") as f:
                            f.write(mcmctree_ctl)
                        QMessageBox.information(self, "File Created", "The file has been created successfully.")
                else:
                    with open(file_path, "w", errors="ignore") as f:
                        f.write(mcmctree_ctl)


    def prepare_for_run(self):
        if not self.seqFileName:
            #QMessageBox.warning(self, "No File", "No sequence file is imported. Please import a file.")
            return
        self.output_dir_name = self.factory.fetch_output_dir_name(self.dir_action)
        self.exportPath = self.factory.creat_dirs(self.workPath +
                                                  os.sep + "MCMCTREE_results" + os.sep + self.output_dir_name)
        shutil.copy(self.seqFileName, self.exportPath + os.sep + os.path.basename(self.seqFileName))
        if hasattr(self, "tree_with_tipdate"):
            tre = self.factory.read_tree(self.tree_with_tipdate, parent=self)
            species_count = len(tre)
            species_tree = f"{species_count} 1"
            treefile = self.exportPath + os.sep + "calibration_tree.nwk"
            with open(treefile, "w", errors="ignore") as f:
                f.write(f"{species_tree}\n{self.tree_with_tipdate}")
            print(f"{species_tree}\n{self.tree_with_tipdate}")
        else:
            treefile = self.exportPath + os.sep + os.path.basename(self.treeFileName)
            shutil.copy(self.treeFileName, treefile)
        self.basemlEXE = os.path.join(os.path.dirname(self.mcmctreeEXE), "baseml.exe")
        shutil.copy(self.basemlEXE, os.path.join(self.exportPath, "baseml.exe"))
        """basemlEXE = os.path.join(os.path.dirname(self.mcmctreeEXE), "baseml.exe")
        baseml_path_to_copy = os.path.join(self.exportPath, "baseml.exe")
        if os.path.exists(basemlEXE):
            shutil.copy(basemlEXE, baseml_path_to_copy)"""
        ctl_file = f"{self.exportPath}{os.sep}mcmctree.ctl"
        self.ctl_generater(ctl_file, treefile=treefile)
        os.chdir(self.exportPath)
        cmds = f"{self.mcmctreeEXE} {ctl_file}"
        return cmds

    def eventFilter(self, obj, event):
        # modifiers = QApplication.keyboardModifiers()
        name = obj.objectName()
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
                file_f = files[0]
                which = 3 if name == 'lineEdit_2' else 4
                self.input(file_f, which=which)
                if which == 4:
                    self.species_matching(4)
                if which == 3:
                    self.codon_matching(3)
                return True
        if (event.type() == QEvent.Show) and (obj == self.pushButton_5.toolButton.menu()):
            if re.search(r"\d+_\d+_\d+\-\d+_\d+_\d+",
                         self.dir_action.text()) or self.dir_action.text() == "Output Dir: ":
                self.factory.sync_dir(self.dir_action)  ##同步文件夹名字
            menu_x_pos = self.pushButton_5.toolButton.menu().pos().x()
            menu_width = self.pushButton_5.toolButton.menu().size().width()
            button_width = self.pushButton_5.toolButton.size().width()
            pos = QPoint(menu_x_pos - menu_width + button_width,
                         self.pushButton_5.toolButton.menu().pos().y())
            self.pushButton_5.toolButton.menu().move(pos)
            return True
        # return QMainWindow.eventFilter(self, obj, event) #
        # 其他情况会返回系统默认的事件处理方法。
        return super(MCMCTree, self).eventFilter(obj, event)  # 0

    def isRunning(self):
        '''判断程序是否运行,依赖进程是否存在来判断'''
        return hasattr(self, "mcmctree_popen") and self.mcmctree_popen and not self.interrupt

    def addText2Log(self, text):
        if re.search(r"\w+", text):
            self.textEdit_log.append(text)
            with open(self.exportPath + os.sep + "PhyloSuite_MCMCTREE.log", "a", errors='ignore') as f:
                f.write(text + "\n")

    def runProgress(self, num):
        if num == 99999:
            self.progressBar.setMaximum(0)
            self.progressBar.setMinimum(0)
        else:
            oldValue = self.progressBar.value()
            done_int = int(num)
            if done_int > oldValue:
                self.progressBar.setProperty("value", done_int)
                QCoreApplication.processEvents()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = MCMCTree()
    ui.show()
    sys.exit(app.exec_())
