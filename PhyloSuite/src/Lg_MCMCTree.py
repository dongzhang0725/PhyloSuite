import datetime
import glob
import multiprocessing
import platform
import random
import re
import shutil
import signal
import traceback
import queue
import time
from io import StringIO
import arviz as az
from PyQt5 import QtWidgets, QtCore
import itertools

from src.Lg_settings import Setting
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from ete3 import NCBITaxa, TextFace
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from scipy import stats
import pandas as pd
import subprocess
from statsmodels.tsa.stattools import acf

import numpy as np
# from src.Lg_Baseml import Baseml
# from uifiles.Ui_baseml import Ui_Baseml
from src.CustomWidget import MyTaxTableModel
from src.CustomWidget import DetectPopupGui
from src.factory import Factory, WorkThread, Parsefmt, Convertfmt
import inspect
import os
import sys
from uifiles.Ui_mcmctree import Ui_MCMCTreeGUI
from uifiles.Ui_configuration import Ui_configuration
from uifiles.Ui_MCMCTracer import Ui_MCMCTracer
from multiprocessing.pool import ApplyResult
from multiprocessing import Manager
if platform.system().lower() == "windows":
    import pyr8s.parse as pyr8sp

'''
关于模型里面的gamma：
model, alpha, ncatG are used to specify the nucleotide substitution model. These are the same
variables as used in baseml.ctl. If alpha ≠ 0, the program will assume a gamma-rates model, while
alpha = 0 means that the model of one rate for all sites will be used.
关于提速：
For large alignments, calculation of the likelihood function during the MCMC is computationally
expensive, and estimation of divergence times is very slow. Thorne et al.[8] suggested using an approximate
method to calculate the likelihood that improves the speed of the MCMC dramatically. 即 usedata=2或3



'''

factory = Factory()
def MF2PAML(mf_model):
    '''
    将modelfinder选出来的最优模型替换为PAML支持的模型名字
    Returns
    -------

    '''
    dict_ = {"12.12": "UNREST",
             "DCMut": "dayhoff-dcmut",
             "JTT": "jones",
             "JTTDCMut": "jones-dcmut",
             "mtREV": "mtREV24"}
    return dict_[mf_model] if mf_model in dict_ else mf_model

def replace_ctl(ctl_file, rgx_old, new):
    with open(ctl_file, errors='ignore') as f:
        ctl_content = f.read()
    with open(ctl_file, "w", errors='ignore') as f:
        f.write(re.sub(rgx_old, new, ctl_content, re.I))

def change_ctl_gamma(gamma_num, gamma_alpha, ctl_file):
    if gamma_num:
        replace_ctl(ctl_file,
                         r"ncatG\s*=\s*\d+",
                         f"ncatG = {gamma_num}")
        replace_ctl(ctl_file,
                         r"alpha\s*=\s*\d+\.?\d*",
                         f"alpha = {gamma_alpha}")
    else:
        # 没有gamma
        replace_ctl(ctl_file,
                         r"(?m)^\s+ncatG\s*=\s*\d+.*$",
                         f"")
        replace_ctl(ctl_file,
                         r"alpha\s*=\s*\d+\.?\d*",
                         f"alpha = 0")

def run_code(popen_=None, log2="", log_prefix="", queque=None, runPath=None):
    # popen = popen_ if popen_ else self.mcmctree_popen
    flag = os.path.basename(runPath)
    if popen_.args:
        run.queue.put(("log", f"{flag}: Current command: {popen_.args}"))
    popen = popen_
    is_error = False  ##判断是否出了error
    error_text = ""
    if queque is None:
        queque = queue.Queue() if platform.system().lower() == "windows" else multiprocessing.Manager().Queue()
    while True:
        QApplication.processEvents()
        if popen.stdin and (not popen.stdin.closed):
            # mcmctree有时候报错会等待输入，造成程序一直hold，所以需要关闭stdin
            popen.stdin.flush()
            popen.stdin.close()
        # if self.isRunning():
        try:
            out_line = popen.stdout.readline().decode("utf-8", errors="ignore")
        except UnicodeDecodeError:
            out_line = popen.stdout.readline().decode("gbk", errors="ignore")
        # queque.put(("log", f"{flag}: {out_line.strip()}"))
        if out_line == "" and popen.poll() is not None:
            break
        if log2:
            with open(log2, "a", errors="ignore") as f:
                f.write(out_line)
        if log_prefix:
            queque.put(("log", f"{flag}: ### {log_prefix} ### {out_line.strip()}"))
        else:
            queque.put(("log", f"{flag}: {out_line.strip()}"))
        if re.search(r"ERROR", out_line, re.IGNORECASE) and ("multifurcating".upper() in out_line.upper()):
            is_error = True
            error_text = "multifurcating"
            break
        elif re.search(r"ERROR", out_line, re.IGNORECASE) and ("routine returned error" not in out_line):
            is_error = True
            error_text = "Error happened! Click <span style='font-weight:600; color:#ff0000;'>Show log</span> to see detail!"
            break
        elif re.search(r"BAD CPU TYPE", out_line, re.IGNORECASE):
            is_error = True
            error_text = "PAML is incompatible with your current CPU type. To proceed, please follow the manual " \
                         "configuration guide available at https://github.com/abacus-gene/paml/wiki/Installation. " \
                         "or enable the current PAML version using " \
                         "<a href='https://support.apple.com/en-us/102527'>Rosetta</a>."
            break
        elif (not log2) and \
                ("Summarizing MCMC samples" in out_line) and \
                ("mcmc_pre1.txt" in os.listdir(runPath)):
            break
    if is_error:
        # self.interrupt = True
        queque.put(("error", error_text))
    # run.queue.put(("prog", "finished"))
    queque.put(("log", f"{flag} --- Done!"))
    queque.put(("popen finished", popen.pid))
    # run.queue.put(("log", f"{flag} --- Done!"))
    # run.queue.put(("popen finished", popen.pid))

def run(dict_args, command, runPath, ctl_file, mode="start"):
    def generate_IQ3_hessian(flag, runPath, dict_args):
        iq_input_file = f"{runPath}{os.sep}seq_for_IQ3.fas"
        # alignment
        with open(iq_input_file, "w", errors="ignore") as f:
            f.write("".join([f">{name}\n{seq}\n" for name, seq in dict_args["dict_seq"].items()]))
        # 树
        with open(f"{runPath}{os.sep}calibrate_tree_for_IQ3.nwk", "w", errors="ignore") as f:
            f.write(dict_args["calibrate_tree_text"])
        mix_model = "MIX+" if dict_args['mix_models'] else ""
        # 自动选模型，然后计算hessian matrix
        iq3_cmd = f"\"{dict_args['MF_path']}\" -s seq_for_IQ3.fas -te calibrate_tree_for_IQ3.nwk " \
                  f"-m {mix_model}MF {dict_args['mf_threads']}" \
                  f" --dating mcmctree --prefix IQ3"
        run.queue.put((
            "log", f"\n{flag}: &&&&&&&& Step 1. Run \"IQ-TREE\" to generate the Hessian matrix...... &&&&&&&&\n"))
        run.queue.put((
            "log", iq3_cmd))
        IQ_popen = factory.init_popen(iq3_cmd, stdin_=True)
        run.queue.put(("popen", IQ_popen.pid))
        run_code(popen_=IQ_popen, queque=run.queue, runPath=runPath)
        ctl_file = f"{runPath}{os.sep}mcmctree.ctl"
        replace_ctl(ctl_file,
            r"usedata\s*=\s*\d+",
            "usedata = 2 IQ3.mcmctree.hessian")
    os.chdir(runPath)
    flag = os.path.basename(runPath)
    # 将PAML加到环境变量
    if "mcmctreeEXE" in dict_args:
        os.environ["PATH"] = os.path.dirname(dict_args["mcmctreeEXE"]) + os.pathsep + os.environ["PATH"]
    if mode == "start":
        run.queue.put(("prog", "")) # 启动进度条
        if dict_args["model"] == "AUTO":
            # 自动选模型
            run.queue.put(("log", f"\n{flag}: &&&&&&&& Running \"MoldelFinder\" to select the best-fit evolutionary model...... &&&&&&&&\n"))
            mf_input_file = f"{runPath}{os.sep}seq_for_MF.fas"
            with open(mf_input_file, "w", errors="ignore") as f:
                f.write("".join([f">{name}\n{seq}\n" for name,seq in dict_args["dict_seq"].items()]))
            # 选codon的时候怎么办？
            DNA_models = ["JC69", "K80", "F81", "HKY", "TN93", "GTR"] if dict_args["use_data"] not in \
                            ["no data (prior)", "seq like (exact likelihood) SLOW"] else ["JC69", "K80", "F81", "HKY"]
            models = ",".join(DNA_models) \
                if dict_args["seq_type"] in ["DNA", "RNA"] else \
                ",".join(["Dayhoff", "DCMut", "JTT", "JTTDCMut", "LG", "mtART",
                          "mtMAM", "mtREV", "mtZOA", "WAG"])
            MF_command = f"\"{dict_args['MF_path']}\" -s seq_for_MF.fas " \
                         f"-mset {models} -mrate G {dict_args['mf_threads']} -pre ModelFinder"
            run.queue.put(("log", "%s: %sCommands%s\n%s\n%s" % (flag, "=" * 45, "=" * 45, MF_command, "=" * 98)))
            mcmctree_popen = factory.init_popen(MF_command, stdin_=True)
            run.queue.put(("popen", mcmctree_popen.pid))
            run_code(popen_=mcmctree_popen, queque=run.queue, runPath=runPath)
            # if dict_args["interrupt"]:
            #     dict_args["end_run"]()
            #     return
            # 找到最优模型
            model_file = glob.glob(f"{runPath}/*.iqtree")
            if model_file:
                model_file = model_file[0]
            # else:
            #     dict_args["interrupt"] = True
            #     dict_args["end_run"]()
            #     return
            f = Factory().read_file(model_file)
            content = f.read()
            f.close()
            rgx_model = re.compile(r"Best-fit model according to.+?\: (.+)")
            rgx_model2 = re.compile(r"Model of substitution: (.+)")
            best_model = rgx_model.search(content).group(1) if rgx_model.search(content) \
                else rgx_model2.search(content).group(1)
            model_split = best_model.split("+")
            current_model = MF2PAML(model_split[0])
            if len(model_split) == 3:
                gamma = model_split[2]
            elif len(model_split) == 2:
                gamma = model_split[1]
            else:
                gamma = ""
            gamma_num = int(gamma.lstrip("G")) if gamma.lstrip("G").isnumeric() else None
            gamma_alpha = re.search(r"Gamma shape alpha: (.+)", content).group(1) if \
                re.search(r"Gamma shape alpha: (.+)", content) else None
            flag = True
        elif dict_args["model"] != "IQ-AUTO":
            # 获取当前model的值
            current_model = dict_args["model"]
            gamma_num = dict_args["gamma_num"]
            gamma_alpha = dict_args["gamma_alpha"]
            flag = True
        else:
            # IQTREE 计算hessian matrix的模式
            flag = False
        if flag:
            model_value = str(dict_args["model_value"][current_model.upper()])
            # 跑之前替换好模型
            if dict_args["seq_type"] == "PROTEIN":
                # 氨基酸序列的第一步是先用0生成CTL文件
                replace_ctl(ctl_file,
                                 r"model\s*=\s*\d+",
                                 "model = 2")
            else:
                replace_ctl(ctl_file,
                                 r"model\s*=\s*\d+",
                                 f"model = {model_value}")
            change_ctl_gamma(gamma_num, gamma_alpha, ctl_file)
        run.queue.put(("log", f"%s: %sCommands%s\n%s\n%s" % (flag, "=" * 45, "=" * 45, command, "=" * 98)))
        if dict_args["use_data"] in ["no data (prior)", "seq like (exact likelihood) SLOW"]:
            # usedata 0或1的时候，不用执行复杂步骤。该模式下，model肯定是enabled
            # 核苷酸序列：usedata=1时，直接可以调用0-4模型;并且该模式下面，用户不可能选到其它模型
            # 氨基酸序列：
            mcmctree_popen = factory.init_popen(command, stdin_=True)
            run.queue.put(("popen", mcmctree_popen.pid))
            run_code(popen_=mcmctree_popen, queque=run.queue, runPath=runPath)
        elif dict_args["seq_type"] in ["DNA", "RNA"]:
            # 核苷酸序列，此时用户选择的是 usedata=2
            # usedata=3，然后usedata=2模式，可以用0-8模型；
            # 流程是先用usedata=3生成out.BV，然后用usedata=2 out.BV来执行程序
            if dict_args["hessian_program"] == "Baseml":
                replace_ctl(ctl_file,
                            r"usedata\s*=\s*\d+",
                            "usedata = 3")
                mcmctree_popen = factory.init_popen(command, stdin_=True)
                run.queue.put(("log", f"\n{flag}: &&&&&&&& Step 1. Run \"usedata=3\" to generate the Hessian matrix...... &&&&&&&&\n"))
                run.queue.put(("popen", mcmctree_popen.pid))
                run_code(popen_=mcmctree_popen, queque=run.queue, runPath=runPath)
                replace_ctl(ctl_file,
                            r"usedata\s*=\s*\d+",
                            "usedata = 2 out.BV")
            elif dict_args["hessian_program"] == "IQ-TREE":
                generate_IQ3_hessian(flag, runPath, dict_args)
            mcmctree_popen = factory.init_popen(command, stdin_=True)
            run.queue.put(("log",
                           f"\n{flag}: &&&&&&&& Step 2. Running MCMCTREE with the generated Hessian matrix...... &&&&&&&&\n"))
            run.queue.put(("popen", mcmctree_popen.pid))
            run_code(popen_=mcmctree_popen, queque=run.queue, runPath=runPath)
        else:
            # 氨基酸序列，此时用户选择的是 usedata=2
            if dict_args["hessian_program"]=="Baseml":
                dat_folder = os.path.dirname(os.path.dirname(dict_args["mcmctreeEXE"]))
                dat_file = os.path.join(dat_folder, "dat", "jones.dat")
                # 解决jones.dat找不到的报错
                shutil.copy(dat_file, runPath)
                replace_ctl(ctl_file,
                            r"usedata\s*=\s*\d+",
                            "usedata = 3")
                mcmctree_popen = factory.init_popen(command, stdin_=True)
                run.queue.put(("log", f"\n{flag}: &&&&&&&& Step 1. Preparing to run \"codeml\" to generate the Hessian matrix...... &&&&&&&&\n"))
                run.queue.put(("popen", mcmctree_popen.pid))
                run_code(popen_=mcmctree_popen, queque=run.queue, runPath=runPath)
                # 获取所有tmp*.ctl文件
                gamma = f"fix_alpha = 0\nalpha = {gamma_alpha}\nncatG = {gamma_num}" if gamma_num \
                    else "fix_alpha = 1\nalpha = 0"
                ctl_files = glob.glob(f"{runPath}{os.sep}tmp*.ctl")
                modified_content = f'''model = 2 * 2: Empirical
aaRatefile = {model_value}
{gamma}
Small_Diff = 0.1e-6
getSE = 2
method = 1'''
                # print(ctl_files)
                for ctl_file in ctl_files:
                    # 对tmp.ctl文件内容进行修改
                    with open(ctl_file, 'r', errors='ignore') as f:
                        ctl_content = f.read()
                        # print(ctl_content)
                    start_index = ctl_content.find("seqtype = 2")
                    if start_index != -1:
                        end_index = ctl_content.find('\n', start_index)
                        if end_index != -1:
                            modified_ctl_content = f'''{ctl_content[:end_index]}\n{modified_content}'''
                    # print(modified_ctl_content)
                    with open(ctl_file, 'w', errors='ignore') as f:
                        f.write(modified_ctl_content)
                    # 复制.dat文件到当前路径
                    dat_file = os.path.join(dat_folder, "dat", model_value)
                    shutil.copy(dat_file, runPath)
                    # 更新commands为codeml运行所需
                    codeml_command = f"codeml {ctl_file}"
                    run.queue.put(("log", "%s: %sCommands%s\n%s\n%s" % (flag, "=" * 45, "=" * 45, codeml_command, "=" * 98)))
                    mcmctree_popen = factory.init_popen(codeml_command, stdin_=True)
                    run.queue.put(("log", f"\n{flag}: &&&&&&&& Step 2. Running \"codeml\" to Generate the Hessian matrix...... &&&&&&&&\n"))
                    run.queue.put(("popen", mcmctree_popen.pid))
                    run_code(popen_=mcmctree_popen, queque=run.queue, runPath=runPath)
                    # if dict_args["interrupt"]:
                    #     break
                    # 读取生成的rst2内容写进out.BV
                    rst2_path = os.path.join(runPath, "rst2")
                    if rst2_path:
                        with open(rst2_path, 'r', errors='ignore') as f:
                            rst2_content = f.read()
                        in_BV_path = os.path.join(runPath, "out.BV")
                        with open(in_BV_path, "a", errors='ignore') as f:
                            f.write(f'''\n\n{rst2_content}''')
                # if dict_args["interrupt"]:
                #     dict_args["end_run"]()
                #     return
                # 再跑一次mcmctree
                # mcmc_ctl_path = os.path.join(runPath, "mcmctree.ctl")
                # with open(mcmc_ctl_path, 'r', errors='ignore') as f:
                #     ctl_content = f.read()
                # modified_ctl_content = ctl_content.replace("usedata = 3", "usedata = 2")
                # with open(mcmc_ctl_path, 'w', errors='ignore') as f:
                #     f.write(modified_ctl_content)
                # 更新commands
                ctl_file = f"{runPath}{os.sep}mcmctree.ctl"
                replace_ctl(ctl_file,
                                 r"usedata\s*=\s*\d+",
                                 "usedata = 2 out.BV")
            elif dict_args["hessian_program"] == "IQ-TREE":
                generate_IQ3_hessian(flag, runPath, dict_args)
            run.queue.put(("log", "%s: %sCommands%s\n%s\n%s" % (flag, "=" * 45, "=" * 45, command, "=" * 98)))
            mcmctree_popen = factory.init_popen(command, stdin_=True)
            run.queue.put(("log", f"\n{flag}: &&&&&&&& Step 3. Running MCMCTREE with the generated Hessian matrix...... &&&&&&&&\n"))
            run.queue.put(("popen", mcmctree_popen.pid))
            run_code(popen_=mcmctree_popen, queque=run.queue, runPath=runPath)
    elif mode == "continue":
        run.queue.put(("prog", "")) # 启动进度条
        run.queue.put(("log", f"\n{flag}&&&&&&&& Resuming MCMCTREE analysis...... &&&&&&&&\n"))
        mcmctree_continue_popen = factory.init_popen(command, stdin_=True)
        run.queue.put(("popen", mcmctree_continue_popen.pid))
        run_code(popen_=mcmctree_continue_popen, queque=run.queue, runPath=runPath)
    elif mode == "summarize":
        run.queue.put(("log", f"\n{flag}&&&&&&&& Summarizing MCMCTREE analysis...... &&&&&&&&\n"))
        mcmctree_summarize_popen = factory.init_popen(command, stdin_=True)
        run.queue.put(("popen", mcmctree_summarize_popen.pid))
        run_code(popen_=mcmctree_summarize_popen, queque=run.queue, runPath=runPath)
        if flag != "repeat1":
            # 确保有2个重复的时候，只有repeat2会弹窗提示结束
            run.queue.put(("summarize finished", mcmctree_summarize_popen.pid))
    elif mode == "r8s":
        run.queue.put(("log", f"\n{flag}&&&&&&&& r8s analysis...... &&&&&&&&\n"))
        run.queue.put(("log", f"COMMAND: {command}"))
        r8s_popen = factory.init_popen(command)
        run.queue.put(("popen", r8s_popen.pid))
        run_code(popen_=r8s_popen, queque=run.queue, runPath=runPath)
    # mcmtree 会自动生成树文件，所以可以不要
    # mcmcout_path = os.path.join(runPath, "mcmc.out.txt")
    # if os.path.exists(mcmcout_path):
    #     with open(mcmcout_path, "r") as f:
    #         file_text = f.read()
    #         #species_tree = re.search(r'Species(.*?)];', file_text, re.DOTALL)
    #         time_tree = re.search(r'\n\(.*?:.*?\);\n', file_text, re.DOTALL)
    #         #velocity_tree = re.search(r'\(.*?}];', file_text, re.DOTALL)
    # if time_tree:
    #     # match_txt = time_tree.group(0)
    #     # print(f"Match found {match_txt}")
    #     with open("time_tree.txt", "w") as tt:
    #         tt.write(time_tree.group(0))

def pool_init(queue):
    run.queue = queue

class CaptureOutput(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        # 将捕获的输出按行分割并添加到列表中
        self.extend(self._stringio.getvalue().splitlines())
        # 释放内存
        del self._stringio
        # 恢复原始的标准输出
        sys.stdout = self._stdout

class CenterAlignDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignCenter

class ProgressDialog(QDialog):
    def __init__(self, max_value, title="loading...", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFixedSize(300, 80)

        layout = QVBoxLayout(self)

        self.label = QLabel("loading files...")
        self.progress = QProgressBar()
        self.progress.setRange(0, max_value)

        layout.addWidget(self.label)
        layout.addWidget(self.progress)

    def update_progress(self, value):
        self.progress.setValue(value)
        QApplication.processEvents()

class MCMCTracer(QMainWindow,Ui_MCMCTracer,object):
    showSig = pyqtSignal(QDialog)
    closeSig = pyqtSignal(str, str)
    exception_signal = pyqtSignal(str)
    progDialogSig = pyqtSignal(QProgressDialog, float)

    def __init__(
            self,
            workPath=None,
            focusSig=None,
            autoInputs=None,
            parent=None,
            resultsPath=None):
        super(MCMCTracer, self).__init__(parent)
        self.factory = Factory()
        self.fileNames = []
        # mcT = MCMCTree()
        self.figureEst = Figure()
        self.figureTra = Figure()
        self.figureCon = Figure()
        self.figureDist = Figure()
        self.figureESS = Figure()
        self.setupUi(self)
        self.figureCanvasEst = FigureCanvas(self.figureEst)
        self.figureCanvasEst.setAcceptDrops(True)
        self.figureCanvasTra = FigureCanvas(self.figureTra)
        self.figureCanvasTra.setAcceptDrops(True)
        self.figureCanvasCon = FigureCanvas(self.figureCon)
        self.figureCanvasCon.setAcceptDrops(True)
        self.verticalLayout_3.replaceWidget(self.widget1, self.figureCanvasEst)
        self.verticalLayout_5.replaceWidget(self.widget2, self.figureCanvasTra)
        self.gridLayout_5.replaceWidget(self.widget3, self.figureCanvasCon)
        self.figureCanvasDist = FigureCanvas(self.figureDist)
        self.verticalLayout_11.replaceWidget(self.widget4, self.figureCanvasDist)
        self.figureCanvasESS = FigureCanvas(self.figureESS)
        self.verticalLayout_12.replaceWidget(self.widget6, self.figureCanvasESS)
        self.files_list = []
        self.dataframes = []
        self.run_data = {}
        self.workPath = workPath
        self.samplesNum = None
        self.tableWidget1.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidget2.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidget3.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget1.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget1.setAcceptDrops(True)
        self.tableWidget1.installEventFilter(self)
        self.figureCanvasEst.installEventFilter(self)
        # self.tableWidget1.currentItemChanged.connect(self.udpate)
        # self.tableWidget2.currentItemChanged.connect(self.udpate)
        self.tableWidget1.itemSelectionChanged.connect(self.on_selections_changed)
        self.pushButton_color_1.clicked.connect(self.changeEstColor)
        self.pushButton_color_2.clicked.connect(self.changeTraColor)
        # self.pushButton_color_4.clicked.connect(self.change_ess_color)
        self.comboBox_bin.currentTextChanged.connect(self.changeEstBins)
        self.checkBox.stateChanged.connect(self.updatePlotBasedOnCheckbox)
        self.radioButton.toggled.connect(self.change_radiobutton)

        # 表格自适应内容
        self.tableWidget1.cellChanged.connect(lambda row, col:
                                              [self.tableWidget1.resizeRowToContents(row),
                                               self.tableWidget1.resizeColumnToContents(col)])
        self.tableWidget2.cellChanged.connect(lambda row, col:
                                      [self.tableWidget2.resizeRowToContents(row),
                                       self.tableWidget2.resizeColumnToContents(col)])
        self.tableWidget3.cellChanged.connect(lambda row, col:
                                              [self.tableWidget3.resizeRowToContents(row),
                                               self.tableWidget3.resizeColumnToContents(col)])
        self.tableWidget4.cellChanged.connect(lambda row, col:
                                              [self.tableWidget4.resizeRowToContents(row),
                                               self.tableWidget4.resizeColumnToContents(col)])
        # 应用委托到表格
        delegate = CenterAlignDelegate()
        self.tableWidget1.setItemDelegate(delegate)
        self.tableWidget2.setItemDelegate(delegate)
        self.tableWidget3.setItemDelegate(delegate)
        self.tableWidget4.setItemDelegate(delegate)

        self.tb1row = 0
        self.tb2row = 0
        self.bins = int(self.comboBox_bin.currentText())
        self.estColor = 'paleturquoise'
        self.traColor = 'royalblue'
        self.essColor = 'darkturquoise'
        self.postColor = 'deepskyblue'
        # Restore geometry
        self.resize(QSize(1200, 1000))
        self.factory.centerWindow(self)
        self.progDialogSig.connect(self.factory.runProgressDialog)
        self.splitter.setStretchFactor(0, 4)
        self.splitter.setStretchFactor(1, 6)
        self.splitter_2.setStretchFactor(0, 5)
        self.splitter_2.setStretchFactor(1, 5)
        self.pushButton_2.installEventFilter(self)
        self.tableWidget1.installEventFilter(self)
        self.tableWidget2.installEventFilter(self)
        self.tableWidget3.installEventFilter(self)
        self.exception_signal.connect(self.popupException)
        if autoInputs:
            self.input(autoInputs, use_folder_name=True)

    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        f_paths, _ = QFileDialog.getOpenFileNames(self, "Select Files")
        if f_paths:  # f_paths 是一个包含文件路径的列表
            # 将选中的文件路径添加到 files_list 中
            self.files_list.extend(f_paths)
            # print(self.files_list)

            # 调用 input 函数并传入更新后的文件列表
            self.input(self.files_list)
        '''f_path = filedialog.askopenfilename()
        if f_path:  # f_path 是一个包含路径的元组，f_path[0] 是文件的完整路径
            # 如果路径存在，将其存入列表
            self.files_list.append(f_path)
            print(self.files_list)
            self.input(self.files_list)'''

    @pyqtSlot()
    def on_pushButton_clicked(self):
        self.chooseConvergenceFoler()

    # @pyqtSlot()
    # def on_pushButton_5_clicked(self):
    #     active_canvas = None
    #     canvas_attributes = ['figureCanvasTra', 'figureCanvasEst', 'figureCanvasESS', 'figureCanvasDist']  # Add all your canvas attribute names
    #
    #     for canvas_attr in canvas_attributes:
    #         if hasattr(self, canvas_attr):
    #             canvas = getattr(self, canvas_attr)
    #             if canvas.isVisible():
    #                 active_canvas = canvas
    #                 print(f"yes,{active_canvas}")
    #     if not active_canvas:
    #         QtWidgets.QMessageBox.warning(self, "Warning", "No plot found to save!")
    #         return
    #     fig = active_canvas.figure
    #     if not fig.axes:
    #         QtWidgets.QMessageBox.warning(self, "Warning", "No plot content to save!")
    #         return
    #     # Create a dialog to let user select DPI and format
    #     dialog = QtWidgets.QDialog(self)
    #     dialog.setWindowTitle("Save Plot Options")
    #     layout = QtWidgets.QVBoxLayout()
    #
    #     # DPI selection
    #     dpi_label = QtWidgets.QLabel("DPI (Resolution):")
    #     dpi_spinbox = QtWidgets.QSpinBox()
    #     dpi_spinbox.setRange(72, 1200)
    #     dpi_spinbox.setValue(300)
    #     dpi_layout = QtWidgets.QHBoxLayout()
    #     dpi_layout.addWidget(dpi_label)
    #     dpi_layout.addWidget(dpi_spinbox)
    #
    #     # Format selection
    #     format_label = QtWidgets.QLabel("File Format:")
    #     format_combo = QtWidgets.QComboBox()
    #     format_combo.addItems(["PDF (.pdf)", "JPEG (.jpg)", "PNG (.png)", "SVG (.svg)"])
    #
    #     # Buttons
    #     button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
    #     button_box.accepted.connect(dialog.accept)
    #     button_box.rejected.connect(dialog.reject)
    #
    #     # Add widgets to layout
    #     layout.addLayout(dpi_layout)
    #     layout.addWidget(format_label)
    #     layout.addWidget(format_combo)
    #     layout.addWidget(button_box)
    #     dialog.setLayout(layout)
    #
    #     if dialog.exec_() != QtWidgets.QDialog.Accepted:
    #         return
    #
    #     # Get user selections
    #     dpi = dpi_spinbox.value()
    #     format_map = {
    #         0: ('pdf', 'PDF Files (*.pdf)'),
    #         1: ('jpg', 'JPEG Files (*.jpg)'),
    #         2: ('png', 'PNG Files (*.png)'),
    #         3: ('svg', 'SVG Files (*.svg)')
    #     }
    #     format_idx = format_combo.currentIndex()
    #     file_ext, file_filter = format_map[format_idx]
    #
    #     # Get save path
    #     default_name = f"plot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
    #     file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
    #         None,
    #         "Save Plot As",
    #         default_name,
    #         file_filter
    #     )
    #
    #     if not file_path:
    #         return
    #
    #     # Ensure correct file extension
    #     if not file_path.lower().endswith(f'.{file_ext}'):
    #         file_path += f'.{file_ext}'
    #
    #     # Save the figure
    #     try:
    #         fig.savefig(file_path, dpi=dpi, bbox_inches='tight')
    #         QtWidgets.QMessageBox.information(self, "Success", f"Plot saved successfully to:\n{file_path}")
    #     except Exception as e:
    #         QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save plot:\n{str(e)}")

    @pyqtSlot()
    def on_pushButton_5_clicked(self):
        """保存第一个画布组"""
        success, params = self.save_active_canvas(
            ['figureCanvasTra', 'figureCanvasEst', 'figureCanvasESS', 'figureCanvasDist', 'figureCanvasCon'])
        if success:
            fig, file_path, dpi = params
            try:
                fig.savefig(file_path, dpi=dpi, bbox_inches='tight')
                QtWidgets.QMessageBox.information(self, "Success", f"Plot saved successfully to:\n{file_path}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save plot:\n{str(e)}")

    def save_active_canvas(self, canvas_attributes):
        """通用保存画布方法"""
        active_canvas = None

        for canvas_attr in canvas_attributes:
            if hasattr(self, canvas_attr):
                canvas = getattr(self, canvas_attr)
                if canvas.isVisible():
                    active_canvas = canvas
                    break

        if not active_canvas:
            QtWidgets.QMessageBox.warning(self, "Warning", "No plot found to save!")
            return False, None

        fig = active_canvas.figure
        if not fig.axes:
            QtWidgets.QMessageBox.warning(self, "Warning", "No plot content to save!")
            return False, None

        # 创建保存选项对话框
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Save Plot Options")
        layout = QtWidgets.QVBoxLayout()

        # DPI选择
        dpi_label = QtWidgets.QLabel("DPI (Resolution):")
        dpi_spinbox = QtWidgets.QSpinBox()
        dpi_spinbox.setRange(72, 1200)
        dpi_spinbox.setValue(300)
        dpi_layout = QtWidgets.QHBoxLayout()
        dpi_layout.addWidget(dpi_label)
        dpi_layout.addWidget(dpi_spinbox)

        # 格式选择
        format_label = QtWidgets.QLabel("File Format:")
        format_combo = QtWidgets.QComboBox()
        format_combo.addItems(["PDF (.pdf)", "JPEG (.jpg)", "PNG (.png)", "SVG (.svg)"])

        # 按钮
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        # 添加控件到布局
        layout.addLayout(dpi_layout)
        layout.addWidget(format_label)
        layout.addWidget(format_combo)
        layout.addWidget(button_box)
        dialog.setLayout(layout)

        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return False, None

        # 获取用户选择
        dpi = dpi_spinbox.value()
        format_map = {
            0: ('pdf', 'PDF Files (*.pdf)'),
            1: ('jpg', 'JPEG Files (*.jpg)'),
            2: ('png', 'PNG Files (*.png)'),
            3: ('svg', 'SVG Files (*.svg)')
        }
        format_idx = format_combo.currentIndex()
        file_ext, file_filter = format_map[format_idx]

        # 获取保存路径
        default_name = f"plot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Plot As",
            default_name,
            file_filter
        )

        if not file_path:
            return False, None

        # 确保正确的文件扩展名
        if not file_path.lower().endswith(f'.{file_ext}'):
            file_path += f'.{file_ext}'

        return True, (fig, file_path, dpi)
    # def input(self, files):
    #     # 输入文件填入表格
    #     # self.files_list = []
    #     self.tableWidget1.setRowCount(len(files))
    #     self.dataframes = []
    #     for row, file in enumerate(files):
    #         base = os.path.basename(file)
    #         # self.files_list.append(base)
    #         item = QTableWidgetItem(base)
    #         item.setToolTip(os.path.abspath(file))
    #         item.setTextAlignment(Qt.AlignCenter)
    #         self.tableWidget1.setItem(row, 0, item)
    #         df = pd.read_csv(file, sep='\t')
    #         self.dataframes.append(df)
    #
    #         self.first_column_name = df.columns[0]
    #         self.states_value = df[self.first_column_name].max()
    #         item_states = QTableWidgetItem(f"{self.states_value}")
    #         item_states.setTextAlignment(Qt.AlignCenter)
    #         self.tableWidget1.setItem(row, 1, item_states)
    #
    #         sample_frequency = df['Gen'].iloc[-1] - df['Gen'].iloc[-2]
    #         item_samfrq = QTableWidgetItem(f"{sample_frequency}")
    #         item_samfrq.setTextAlignment(Qt.AlignCenter)
    #         self.tableWidget1.setItem(row, 2, item_samfrq)
    #         if row % 2 == 1:
    #             color = QColor(202, 202, 202)
    #             item.setBackground(color)
    #             item_states.setBackground(color)
    #             item_samfrq.setBackground(color)
    #     # print("导入数据结束:", datetime.datetime.now())
    #     self.tableWidget1.setCurrentCell(0, 0)
    #     self.tableWidget2.setCurrentCell(0, 0)
    #     self.dis_Traces(0)
    #     ini_column = self.tableWidget2.item(self.tb2row, 0).text()
    #     self.dis_summary(0, ini_column)
    #     # self.draw_Tra(0, self.first_column_name, ini_column, self.traColor)
    #     # self.draw_Est(0, ini_column, self.estColor, self.bins)
    #     self.tableWidget1.currentItemChanged.connect(self.udpate)
    #     self.tableWidget2.currentItemChanged.connect(self.udpate)

    def parse_data(self, files, use_folder_name=False):
        try:
            self.dataframes = []
            self.cached_data = {}  # 缓存每个文件的数据分析结果
            self.table1_data = {}
            total = len(files)
            list_names = []
            for row, file in enumerate(files):
                base = os.path.basename(file) if not use_folder_name else os.path.basename(os.path.dirname(file))
                new_name, list_names = self.factory.numbered_Name(list_names,
                    base, omit=True, suffix="_")
                list_names.append(new_name)
                df = pd.read_csv(file, sep='\t')
                if df.empty:
                    continue
                self.dataframes.append(df)
                first_column_name = df.columns[0]
                states_value = df[first_column_name].max()
                sample_frequency = df['Gen'].iloc[-1] - df['Gen'].iloc[-2]
                self.table1_data[new_name] = [os.path.abspath(file), states_value, sample_frequency]
                # ▶ 提前计算并缓存所有变量的统计量
                analysis_result = {}
                total_col = len(df.columns[1:])
                for i, col in enumerate(df.columns[1:]):
                    data = df[col].astype(float)
                    arviz_idata = az.convert_to_inference_data({col: data.to_numpy()[None, :]})
                    arviz_summary = az.summary(arviz_idata)

                    analysis_result[col] = {
                        "mean": data.mean(),
                        "median": data.median(),
                        "min": data.min(),
                        "max": data.max(),
                        "ci": az.hdi(data.to_numpy(), hdi_prob=0.95),
                        "ess_bulk": arviz_summary.loc[col, "ess_bulk"],
                        "ess_tail": arviz_summary.loc[col, "ess_tail"]
                    }
                    # 列进度 (在文件内部计算时)
                    inner_prop = i / total_col
                    self.progDialogSig.emit(self.progressDialog, int(((row + inner_prop) / total) * 80))
                self.cached_data[row] = analysis_result
        except:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号

    def display_data(self):
        if not self.table1_data:
            QMessageBox.information(
                self,
                "MDGUI",
                "<p style='line-height:25px; height:25px'>No MCMC samples found in the input files!</p>")
            return
        for row, (base, lists) in enumerate(self.table1_data.items()):
            filepath, states_value, sample_frequency = lists
            item = QTableWidgetItem(base)
            item.setToolTip(filepath)
            item.setTextAlignment(Qt.AlignCenter)
            self.tableWidget1.setItem(row, 0, item)  #
            item_states = QTableWidgetItem(f"{states_value}")
            item_states.setTextAlignment(Qt.AlignCenter)
            self.tableWidget1.setItem(row, 1, item_states)  #
            item_samfrq = QTableWidgetItem(f"{sample_frequency}")
            item_samfrq.setTextAlignment(Qt.AlignCenter)
            self.tableWidget1.setItem(row, 2, item_samfrq)

        self.factory.runProgressDialog(self.progressDialog, 90)
        self.tableWidget1.setCurrentCell(0, 0)
        self.tableWidget2.setCurrentCell(0, 0)
        self.dis_Traces(0)
        self.factory.runProgressDialog(self.progressDialog, 95)
        ini_column = self.tableWidget2.item(self.tb2row, 0).text()
        self.plot_dist(0, ini_column, self.estColor, self.bins)
        self.plot_ess_evolution(0, ini_column, self.essColor)
        self.plot_posterior_dist(0, ini_column, self.postColor)
        self.plot_trace_dynamic(0, ini_column, self.traColor)
        self.dis_summary(0, ini_column)
        self.tableWidget1.currentItemChanged.connect(self.udpate)
        self.tableWidget2.currentItemChanged.connect(self.udpate)
        self.factory.runProgressDialog(self.progressDialog, 100)

    def input(self, files, use_folder_name=False):
        if not files:
            return
        self.tableWidget1.setRowCount(len(files))
        self.dataframes = []
        self.cached_data = {}  # 缓存每个文件的数据分析结果

        # dialog = ProgressDialog(max_value=len(files), parent=self)
        self.progressDialog = self.factory.myProgressDialog(
            "Please Wait", "Loading data...",
            parent=self)
        self.progressDialog.show()
        Worker = WorkThread(lambda : self.parse_data(files, use_folder_name), parent=self)
        self.progressDialog.canceled.connect(lambda: [Worker.stopWork(),
                                            self.progressDialog.close()])
        Worker.finished.connect(lambda : [self.display_data(),
                                             self.progressDialog.close()])
        Worker.start()

    def read_mcmc(self):
        self.dataframes = []
        for file in self.files_list:
            base = os.path.basename(file)
            df = pd.read_csv(base, sep='\t')
            self.dataframes.append(df)

    def save_cached_data(self, filepath="cached_data_output.txt"):
        with open(filepath, "w", encoding="utf-8") as f:
            for row_index, analysis in self.cached_data.items():
                f.write(f"=== Row {row_index} ===\n")
                for param_name, stats in analysis.items():
                    f.write(f"[{param_name}]\n")
                    f.write(f"  Mean:     {stats['mean']:.6f}\n")
                    f.write(f"  Median:   {stats['median']:.6f}\n")
                    f.write(f"  Min:      {stats['min']:.6f}\n")
                    f.write(f"  Max:      {stats['max']:.6f}\n")
                    f.write(f"  95% CI:   [{stats['ci'][0]:.6f}, {stats['ci'][1]:.6f}]\n")
                    f.write(f"  ESS bulk: {stats['ess_bulk']:.2f}\n")
                    f.write(f"  ESS tail: {stats['ess_tail']:.2f}\n")
                    f.write("\n")
                f.write("\n")

    def on_selections_changed(self):
        # 获取当前选中的行
        selected_items = self.tableWidget1.selectedItems()
        selected_rows = list(set(item.row() for item in selected_items))
        # 如果选中了两行，调用 draw_boxline 函数
        if len(selected_rows) == 2:
            row1, row2 = selected_rows
            # 获取所需的列名称 (假设第0列是列名)
            column_name = self.tableWidget2.item(self.tb2row, 0).text()
            # 调用 draw_boxline 函数
            self.draw_boxline(row1, row2, column_name, self.estColor)

    def udpate_basedon_selection(self):
        index_wid1 = self.tableWidget1.currentRow()
        index_wid2 = self.tableWidget2.currentRow()
        if index_wid1 == -1 or index_wid2 == -1:
            return None, None
        return index_wid1, index_wid2

    def udpate(self):
        self.tb1row, self.tb2row = self.udpate_basedon_selection()

        if self.tb1row is not None and self.tb2row is not None:
            # TODO: 已经展示过的，跳过这部分
            column_name = self.tableWidget2.item(self.tb2row, 0).text()
            self.dis_Traces(self.tb1row)
            self.dis_summary(self.tb1row, column_name)
            self.plot_trace_dynamic(self.tb1row, column_name, self.traColor)
            # self.draw_Est(self.tb1row, column_name, self.estColor, self.bins)
            self.plot_dist(self.tb1row, column_name, self.estColor, self.bins)
            self.plot_ess_evolution(self.tb1row, column_name, self.essColor)
            self.plot_posterior_dist(self.tb1row, column_name, self.postColor)
        else:
            QMessageBox.warning(self, "Warning", "No file is imported!")

    def dis_Traces(self, num):
        if not num in self.cached_data:
            return
        cache = self.cached_data[num]
        column_names = list(cache.keys())  # 原来是 cache["columns"] 错误地引用了不存在的 key

        self.tableWidget2.setRowCount(len(column_names))

        for row, col_name in enumerate(column_names):
            stats = cache[col_name]
            mean_value = stats["mean"]
            ess_value = stats["ess_bulk"]

            item_name = QTableWidgetItem(col_name)
            self.tableWidget2.setItem(row, 0, item_name)

            item_mean = QTableWidgetItem(f"{mean_value:.6f}")
            item_mean.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # 左对齐，垂直居中
            self.tableWidget2.setItem(row, 1, item_mean)

            item_ess = QTableWidgetItem(f"{ess_value:.1f}")
            if ess_value < 200:
                # 或者字体标红（任选其一）
                item_ess.setForeground(QBrush(QColor("red")))
            self.tableWidget2.setItem(row, 2, item_ess)

        self.tableWidget2.resizeColumnsToContents()
        self.tableWidget2.setColumnWidth(1, min(self.tableWidget2.columnWidth(1), 90))  # 限制最大200

    def dis_summary(self, num, series):
        if not num in self.cached_data:
            return
        stats = self.cached_data[num][series]

        item_mean = QTableWidgetItem(f"{stats['mean']:.6f}")
        item_median = QTableWidgetItem(f"{stats['median']:.6f}")
        item_min_max = QTableWidgetItem(f"[{stats['min']:.6f}, {stats['max']:.6f}]")
        ci = stats["ci"]
        item_ci = QTableWidgetItem(f"[{ci[0]:.6f}, {ci[1]:.6f}]")
        item_essbulk = QTableWidgetItem(f"{stats['ess_bulk']:.1f}")
        item_esstail = QTableWidgetItem(f"{stats['ess_tail']:.1f}")

        items = [item_mean, item_median, item_min_max, item_ci, item_essbulk, item_esstail]
        for row, item in enumerate(items):
            self.tableWidget3.setItem(row, 1, item)
            # if row % 2 == 1:
            #     item.setBackground(QColor(202, 202, 202))

    def get_ess_values(self, data_array, varname="param"):
        # 不重复从 df 中提取数据，只传 data
        idata = az.convert_to_inference_data({varname: data_array[None, :]})
        summary_df = az.summary(idata, var_names=[varname], round_to=None)
        ess_bulk = summary_df.loc[varname, "ess_bulk"]
        ess_tail = summary_df.loc[varname, "ess_tail"]
        return ess_bulk, ess_tail

    def cal_all_ess(self, num, columns):
        df = self.dataframes[num]
        data_dict = {col: df[col].values[None, :] for col in columns}
        idata = az.convert_to_inference_data(data_dict)
        summary_df = az.summary(idata, var_names=list(columns))
        return summary_df["ess_bulk"].to_dict()

    # def cal_CI(self, num, series):
    #     df = self.dataframes[num]
    #     data = df[series]
    #     mean = data.mean()
    #     sem = stats.sem(data)  # 标准误差
    #     # 计算95%置信区间
    #     confidence_interval = stats.t.interval(0.95, len(data) - 1, loc=mean, scale=sem)
    #     lower_bound = confidence_interval[0]
    #     upper_bound = confidence_interval[1]
    #     return [lower_bound, upper_bound]

    # def cal_CI_arviz(self, num, series):
    #     df = self.dataframes[num]
    #     data = df[series]
    #     data_array = np.vstack([data.values, data.values])  # shape: (2, n_samples)
    #     hdi = az.hdi(data_array, hdi_prob=0.95)
    #     return [hdi[0], hdi[1]]

    def cal_CI_arviz(self, data_array):
        # 不重复从 df 中提取数据，只传 data
        data_stacked = np.vstack([data_array, data_array])  # shape: (2, n_samples)
        hdi = az.hdi(data_stacked, hdi_prob=0.95)
        return hdi[0], hdi[1]

    def change_ess_color(self):
        essColor = QColorDialog.getColor(initial=Qt.white, parent=self)
        column_name = self.tableWidget2.item(self.tb2row, 0).text()
        self.essColor = essColor.name()
        if essColor.isValid():
            self.pushButton_color_4.setText(essColor.name())
            self.pushButton_color_4.setStyleSheet(f"background-color: {essColor.name()}")
            self.plot_ess_evolution(self.tb1row, column_name, self.essColor)

    def change_post_color(self):
        postColor = QColorDialog.getColor(initial=Qt.white, parent=self)
        column_name = self.tableWidget2.item(self.tb2row, 0).text()
        self.postColor = postColor.name()
        if postColor.isValid():
            self.pushButton_color_3.setText(postColor.name())
            self.pushButton_color_3.setStyleSheet(f"background-color: {postColor.name()}")
            self.plot_posterior_dist(self.tb1row, column_name, self.postColor)

    def changeEstColor(self):
        estColor = QColorDialog.getColor(initial=Qt.white, parent=self)
        column_name = self.tableWidget2.item(self.tb2row, 0).text()
        self.estColor = estColor.name()
        if estColor.isValid():
            # Set the button's text and background color to the selected color
            self.pushButton_color_1.setText(estColor.name())
            self.pushButton_color_1.setStyleSheet(f"background-color: {estColor.name()}")
            self.plot_dist(self.tb1row, column_name, self.estColor, self.bins)

    def changeEstBins(self):
        self.bins = int(self.comboBox_bin.currentText())
        column_name = self.tableWidget2.item(self.tb2row, 0).text()
        self.plot_dist(self.tb1row, column_name, self.estColor, self.bins)

    def changeTraColor(self):
        traColor = QColorDialog.getColor(initial=Qt.white, parent=self)
        column_name = self.tableWidget2.item(self.tb2row, 0).text()
        self.traColor = traColor.name()
        if traColor.isValid():
            # Set the button's text and background color to the selected color
            self.pushButton_color_2.setText(traColor.name())
            self.pushButton_color_2.setStyleSheet(f"background-color: {traColor.name()}")
            self.plot_trace_dynamic(self.tb1row, column_name, self.traColor)
            # self.draw_boxline()

    def draw_Est(self, num, series, color, binnum):
        df = self.dataframes[num]
        data = df[series]
        self.figureEst.clear()
        ax = self.figureEst.add_subplot(111)
        #histogram
        ax.hist(data, bins=binnum, color=color, edgecolor='black')  # You can adjust 'bins' for more or fewer intervals
        ax.set_xlabel("Value Intervals")
        ax.set_ylabel("Frequency")
        ax.set_title(f"Histogram of {series}")
        self.figureCanvasEst.draw_idle()

    def plot_trace_dynamic(self, num, series, color):
        if (num+1) > len(self.dataframes):
            return
        df = self.dataframes[num]
        data = df[series].values

        # 清除画布
        self.figureCanvasTra.figure.clear()
        ax = self.figureCanvasTra.figure.add_subplot(111)  # 单一面板

        # 转换为ArviZ格式（模拟2链）
        idata = az.from_dict(
            posterior={series: np.vstack([data, data])},  # shape: (2, n_samples)
            coords={"chain": [0, 1]},
            dims={series: ["chain", "draw"]}
        )
        if self.checkBox.isChecked():
            # 折线图模式
            for chain in [0, 1]:
                ax.plot(
                    idata.posterior[series].sel(chain=chain),
                    color=color,
                    linewidth=1,
                    alpha=0.7,
                )
        else:
            # 点图模式
            for chain in [0, 1]:
                ax.scatter(
                    range(len(data)),
                    idata.posterior[series].sel(chain=chain),
                    color=color,
                    s=5,
                    alpha=0.6,
                )

        ax.set_title(f'Trace Plot: {series}', fontsize=12)
        ax.set_xlabel('Iteration')
        ax.set_ylabel('Parameter Value')
        ax.grid(True, alpha=0.3)
        ax.legend()
        self.figureCanvasTra.figure.tight_layout()
        self.figureCanvasTra.draw_idle()

    def plot_posterior_dist(self, num, series, color):
        if (num+1) > len(self.dataframes):
            return
        df = self.dataframes[num]
        data = df[series].values
        # 清除并准备画布
        self.figureCanvasDist.figure.clear()
        ax = self.figureCanvasDist.figure.add_subplot(111)
        idata = az.from_dict(posterior={series: np.vstack([data, data])})
        # 绘制后验分布
        az.plot_posterior(
            idata,
            var_names=[series],
            color=color,
            point_estimate='mean',
            round_to=4,
            ax=ax,
            hdi_prob=0.95,
            textsize=10  # 控制统计量文本大小
        )
        # 自定义美化
        ax.set_title(f'Posterior Distribution: {series}',
                     fontsize=12, pad=12)
        ax.set_xlabel('Parameter Value', fontsize=11)
        ax.grid(True, alpha=0.3, linestyle=':')
        # 调整坐标轴字体
        ax.tick_params(axis='both', labelsize=9)
        # 自动调整布局防止溢出
        self.figureCanvasDist.figure.tight_layout(pad=2.0)
        self.figureCanvasDist.draw_idle()

    def plot_ess_evolution(self, num, series, color):
        if (num+1) > len(self.dataframes):
            return
        df = self.dataframes[num]
        data = df[series].values

        posterior = {series: np.vstack([data, data])}  # shape: (2, n_samples)
        idata = az.from_dict(posterior=posterior)
        # 清除现有图形
        self.figureCanvasESS.figure.clear()
        ax = self.figureCanvasESS.figure.add_subplot(111)
        plt.rcParams.update({
            'font.size': 10,  # 全局字体大小
            'axes.titlesize': 12,  # 标题大小
            'axes.labelsize': 11,  # 坐标轴标签大小
            'xtick.labelsize': 9,  # X轴刻度标签大小
            'ytick.labelsize': 9,  # Y轴刻度标签大小
            'legend.fontsize': 10  # 图例字体大小
        })
        az.plot_ess(
            idata,
            kind="evolution",
            ax=ax
        )
        ax.set_title(f'ESS Evolution: {series}', fontsize=10)
        ax.set_xlabel('Iteration')
        ax.set_ylabel('Effective Sample Size')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left')
        self.figureCanvasESS.draw_idle()

    def plot_dist(self, num, series, color, binnum):
        if (num+1) > len(self.dataframes):
            return
        df = self.dataframes[num]
        data = df[series].values
        # 清除现有图形
        self.figureCanvasEst.figure.clear()
        ax = self.figureCanvasEst.figure.add_subplot(111)
        az.plot_dist(
            data,
            kind='hist',
            color=color,
            hist_kwargs={
                'bins': binnum,  # 分箱数在此处传递
                'alpha': 0.7,
                'edgecolor': 'white',
                'density': True  # 确保与KDE尺度一致
            },
            ax=ax
        )

        # 计算并标注95% HDI
        hdi = az.hdi(data, hdi_prob=0.95)
        if self.radioButton.isChecked():
            ax.axvline(hdi[0], color='red', linestyle='--', label='95% HDI')
            ax.axvline(hdi[1], color='red', linestyle='--')
            ax.axvspan(hdi[0], hdi[1], color='red', alpha=0.1)
        else:
            pass
        # 添加统计标注
        stats_text = (f"Mean = {np.mean(data):.4f}\n"
                      f"Median = {np.median(data):.4f}\n"
                      f"95% HDI = [{hdi[0]:.4f}, {hdi[1]:.4f}]")
        ax.text(0.02, 0.95, stats_text,
                transform=ax.transAxes,
                verticalalignment='top',
                bbox=dict(facecolor='white', alpha=0.8))

        # 美化图形
        ax.set_title(f'Posterior Distribution: {series}', fontsize=12)
        ax.set_xlabel('Parameter Value')
        ax.set_ylabel('Density')
        ax.xaxis.set_major_locator(MaxNLocator(6))
        ax.legend(loc='upper right')

        # 刷新画布
        self.figureCanvasEst.draw_idle()

    def change_radiobutton(self):
        column_name = self.tableWidget2.item(self.tb2row, 0).text()
        # self.draw_Est(self.tb1row, "t_n8", self.estColor, self.bins)
        self.plot_dist(self.tb1row, column_name, self.estColor, self.bins)

    def updatePlotBasedOnCheckbox(self):
        column_name = self.tableWidget2.item(self.tb2row, 0).text()
        # Call draw_Tra with the necessary parameters
        self.plot_trace_dynamic(self.tb1row, column_name, self.estColor)

    # def draw_Tra(self, num, enu, series, color):
    #     # 获取数据
    #     df = self.dataframes[num]
    #     states = df[enu]  # 假设 'state' 是 df 中的一列
    #     data = df[series]
    #
    #     self.figureTra.clear()
    #     #创建子图
    #     ax = self.figureTra.add_subplot(111)
    #     # ax.scatter(states, data, s=0.5)
    #     if self.checkBox.isChecked():
    #         ax.plot(states, data, linewidth=0.5, color=color)
    #     else:
    #         ax.scatter(states, data, s=0.5, color=color)
    #     ax.set_xlabel('State')
    #     ax.set_ylabel(series)
    #     self.figureCanvasTra.draw_idle()

    def draw_boxline(self, num1, num2, series, color):
        df1 = self.dataframes[num1]
        df2 = self.dataframes[num2]
        data1 = df1[series]
        data2 = df2[series]
        self.figureEst.clear()
        ax = self.figureEst.add_subplot(111)
        # 绘制箱线图
        boxplot = ax.boxplot([data1, data2], patch_artist=True,
                             boxprops=dict(facecolor=color, linewidth=1.0),  # Increase the linewidth for boxes
                             medianprops=dict(color='black', linewidth=1.0),  # Make the median line thicker
                             whiskerprops=dict(color='black', linewidth=0.5),  # Make the whiskers thicker
                             capprops=dict(color='black', linewidth=0.5),
                             showfliers=False)  # Make the caps thicker
        # Remove fliers (the points)
        # for flier in boxplot['fliers']:
        #     flier.set(marker='', alpha=0)  # Remove fliers by setting marker to an empty string
        ax.set_xticklabels(['Data1', 'Data2'])
        ax.set_ylabel(series)

        # Set the title of the plot
        ax.set_title(f'Boxplot of {series}')

        self.figureCanvasEst.draw_idle()

    def chooseConvergenceFoler(self):
        self.resultsPath = self.workPath + os.sep + "MDGUI_results"
        folder_list = [f for f in os.listdir(self.resultsPath) if os.path.isdir(os.path.join(self.resultsPath, f))]
        self.convergenceFolerGui(folder_list)

    def convergenceFolerGui(self, folder_list):
        self.convergence_dialog = QDialog(self)
        self.convergence_dialog.setWindowTitle("Choose Folder")
        self.gridLayout = QGridLayout(self.convergence_dialog)
        self.horizontalLayout = QHBoxLayout()
        self.label = QLabel("Available inputs prepared for convergence checking in workplace:", self.convergence_dialog)
        self.horizontalLayout.addWidget(self.label)
        spacerItem = QSpacerItem(153, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 2)
        qss = '''QListView::item{height:30px;}
            QListView::item{background:white;}
            QListView::item:hover{background: #E5F3FF;}
            QListView::item:selected:active{background: #CDE8FF;}'''  # 灰色：#F2F2F2，#EBEBEB
        self.listWidget_framless = QListWidget(self.convergence_dialog)
        self.listWidget_framless.setSelectionMode(QListWidget.MultiSelection)  # 允许多选
        self.listWidget_framless.setStyleSheet(qss)
        self.gridLayout.addWidget(self.listWidget_framless, 1, 0, 1, 2)

        self.item_to_path = {}  # 存储项到路径的映射
        folder_icon = QIcon(":/picture/resourses/folder.png")
        # 反转folder_list
        for index, folder_path in enumerate(reversed(folder_list)):
            folder_name = os.path.basename(folder_path)
            item = QListWidgetItem(folder_name)
            item.setIcon(folder_icon)
            if index % 2 == 0:
                item.setBackground(QColor("#F0F0F0"))
            else:
                item.setBackground(QColor("#FFFFFF"))
            self.listWidget_framless.addItem(item)
            self.item_to_path[item.text()] = folder_path

        self.pushButton = QPushButton("Ok", self.convergence_dialog)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/btn_ok.png"), QIcon.Normal, QIcon.Off)
        self.pushButton.setIcon(icon)
        self.gridLayout.addWidget(self.pushButton, 2, 0, 1, 1)
        self.pushButton.setEnabled(False)  # 初始状态下禁用OK按钮
        self.pushButton_2 = QPushButton("No, thanks", self.convergence_dialog)
        icon1 = QIcon()
        icon1.addPixmap(QPixmap(":/picture/resourses/btn_close.png"), QIcon.Normal, QIcon.Off)
        self.pushButton_2.setIcon(icon1)
        self.gridLayout.addWidget(self.pushButton_2, 2, 1, 1, 1)
        self.pushButton.clicked.connect(lambda : [self.onOkClicked(), self.convergence_dialog.close()])
        self.pushButton_2.clicked.connect(self.convergence_dialog.close)
        self.listWidget_framless.itemSelectionChanged.connect(self.updateOkButtonState)
        self.convergence_dialog.exec_()

    def updateOkButtonState(self):
        selected_items = self.listWidget_framless.selectedItems()
        if len(selected_items) > 0:
            self.pushButton.setEnabled(True)
            # self.listWidget_framless.blockSignals(True)
            # while len(selected_items) > 1:
            #     item = selected_items.pop(0)
            #     item.setSelected(False)
            # self.listWidget_framless.blockSignals(False)
            # 启用按钮仅当选择了一个项目时
        # self.pushButton.setEnabled(len(selected_items) == 1)

    def onOkClicked(self):
        selected_items = self.listWidget_framless.selectedItems()
        selected_paths = [os.path.join(self.resultsPath, item.text()).replace("\\", "/")
                          for item in selected_items]

        if len(selected_paths) == 1:
            self.single_folder_selected(selected_paths[0])
        else:
            QMessageBox.warning(self, "multiple selection!", "Select one folder!")
            # self.multi_folders_selected(selected_paths)
        self.convergence_dialog.close()

    def single_folder_selected(self, folder_path):
        # print(f"Selected folder: {folder_path}")
        repeat_dirs = [
            os.path.join(folder_path, d)
            for d in os.listdir(folder_path)
            if os.path.isdir(os.path.join(folder_path, d)) and d.startswith("repeat")
        ]
        if len(repeat_dirs) < 2:
            QMessageBox.warning(self, "Warning",
                                f"Folder '{os.path.basename(folder_path)}' contains less than 2 repeat directories.")
            return
        repeat_combinations = list(itertools.combinations(sorted(repeat_dirs), 2))
        self.tableWidget.clear()
        self.tableWidget.setRowCount(len(repeat_combinations))
        self.tableWidget.setHorizontalHeaderLabels(["repeat* vs. repeat*"])
        self.repeat_data = {}
        for repeat in repeat_dirs:
            repeat_name = os.path.basename(repeat)
            summarization_file = os.path.join(repeat, "summarization.out.txt").replace("\\", "/")
            ctl_file = os.path.join(repeat, "mcmctree.ctl").replace("\\", "/")
            seed_file = os.path.join(repeat, "SeedUsed").replace("\\", "/")
            seed_value = ''
            if os.path.exists(seed_file):
                with open(seed_file, 'r') as f:
                    content = f.read()
                    seed_value = content
                    # match = re.search(r"seed\s*=\s*(-?\d+)", content)
                    # if match:
                    #     seed_value = match.group(1)
            posterior_means = []
            if os.path.exists(summarization_file):
                with open(summarization_file, 'r') as f:
                    content = f.read()
                    matches = re.finditer(
                        r"t_n\d+\s+([\d.]+)\s+\(\s*[\d.]+\s*,\s*[\d.]+\s*\)\s+\(\s*[\d.]+\s*,\s*[\d.]+\s*\)",
                        content
                    )
                    posterior_means = [float(m.group(1)) for m in matches]
            self.run_data[repeat] = {
                'name': repeat_name,
                'seed': seed_value,
                'posterior_means': posterior_means,
            }
        # print(self.run_data)
        for row, (repeat1_path, repeat2_path) in enumerate(repeat_combinations):
            repeat1 = os.path.basename(repeat1_path)
            repeat2 = os.path.basename(repeat2_path)
            combo_item = QTableWidgetItem(f"{repeat1} vs. {repeat2}")
            combo_item.setData(Qt.UserRole, (repeat1_path, repeat2_path))
            combo_item.setData(Qt.UserRole + 1, "repeat")
            self.tableWidget.setItem(row, 0, combo_item)
        self.tableWidget.setSelectionBehavior(QTableWidget.SelectRows)
        self.tableWidget.cellClicked.connect(self.update_run_comparison)
        # 默认显示第一个组合
        if repeat_combinations:
            self.tableWidget.setCurrentCell(0, 0)
            self.update_run_comparison(0, 0)

    def multi_folders_selected(self, folder_paths):
        # print(folder_paths)
        valid_folders = []
        for folder_path in folder_paths:
            summarization_file = os.path.join(folder_path, "summarization.ctl")
            seed_file = os.path.join(folder_path, "SeedUsed")
            if not (os.path.exists(summarization_file) and os.path.exists(seed_file)):
                QMessageBox.warning(self, "Warning",
                                    f"Folder '{os.path.basename(folder_path)}' does not contain required result files!")
                continue

            valid_folders.append(folder_path)
        folder_combinations = list(itertools.combinations(valid_folders, 2))
        # print(valid_folders)
        self.tableWidget.clear()
        self.tableWidget.setRowCount(len(folder_combinations))
        self.tableWidget.setHorizontalHeaderLabels(["Summarization Combinations"])
        self.folder_data = {}
        for folder_path in valid_folders:
            folder_name = os.path.basename(folder_path)
            summarization_file = os.path.join(folder_path, "summarization.out.txt")
            seed_file = os.path.join(folder_path, "SeedUsed")
            seed_value = ""
            if os.path.exists(seed_file):
                with open(seed_file, 'r') as f:
                    seed_value = f.read().strip()
            posterior_means = []
            if os.path.exists(summarization_file):
                with open(summarization_file, 'r') as f:
                    content = f.read()
                    matches = re.finditer(
                        r"t_n\d+\s+([\d.]+)\s+\(\s*[\d.]+\s*,\s*[\d.]+\s*\)\s+\(\s*[\d.]+\s*,\s*[\d.]+\s*\)",  # 根据实际文件格式调整正则表达式
                        content
                    )
                    posterior_means = [float(m.group(1)) for m in matches]

            self.folder_data[folder_path] = {
                'name': folder_name,
                'seed': seed_value,
                'posterior_means': posterior_means,
            }
        for row, (folder1_path, folder2_path) in enumerate(folder_combinations):
            folder1_name = os.path.basename(folder1_path)
            folder2_name = os.path.basename(folder2_path)
            combo_item = QTableWidgetItem(f"{folder1_name} & {folder2_name}")
            combo_item.setData(Qt.UserRole, (folder1_path, folder2_path))
            combo_item.setData(Qt.UserRole + 1, "folder")
            self.tableWidget.setItem(row, 0, combo_item)
        self.tableWidget.setSelectionBehavior(QTableWidget.SelectRows)
        self.tableWidget.cellClicked.connect(self.update_run_comparison)
        if folder_combinations:
            self.tableWidget.setCurrentCell(0, 0)
            self.update_run_comparison(0, 0)

    def update_run_comparison(self, row, col):
        combo_item = self.tableWidget.item(row, 0)
        path1, path2 = combo_item.data(Qt.UserRole)
        data_type = combo_item.data(Qt.UserRole + 1)
        if data_type == "repeat":
            run1_data = self.run_data[path1]
            run2_data = self.run_data[path2]
            name1 = run1_data['name']
            name2 = run2_data['name']
            seed1 = run1_data['seed']
            seed2 = run2_data['seed']
            means1 = run1_data['posterior_means']
            means2 = run2_data['posterior_means']
            # print(means1)
            # print(means2)
        elif data_type == "folder":
            folder1_data = self.folder_data[path1]
            folder2_data = self.folder_data[path2]
            name1 = folder1_data['name']
            name2 = folder2_data['name']
            seed1 = folder1_data['seed']
            seed2 = folder2_data['seed']
            means1 = folder1_data['posterior_means']
            means2 = folder2_data['posterior_means']

        self.tableWidget4.clear()

        self.tableWidget4.setItem(0, 0, QTableWidgetItem(name1))
        self.tableWidget4.setItem(0, 1, QTableWidgetItem(seed1))
        self.tableWidget4.setItem(0, 2, QTableWidgetItem(str(means1)))

        self.tableWidget4.setItem(1, 0, QTableWidgetItem(name2))
        self.tableWidget4.setItem(1, 1, QTableWidgetItem(seed2))
        self.tableWidget4.setItem(1, 2, QTableWidgetItem(str(means2)))
        self.tableWidget4.setHorizontalHeaderLabels(["Files", "Seed", "Posterior mean times"])
        self.draw_convergence(
            means1,
            means2,
            name1,
            name2
        )

    def draw_convergence(self, data1, data2, base1, base2):
        #
        self.figureCon.clear()
        # Create a subplot on the figure canvas
        ax = self.figureCon.add_subplot(111)
        # Plot the data
        ax.scatter(data1, data2)
        ax.plot([0, 1], [0, 1], transform=ax.transAxes, color='black')

        # Set the labelsre
        ax.set_xlabel(f'Posterior mean times from {base1}')
        ax.set_ylabel(f'Posterior mean times from {base2}')

        # Redraw the canvas to update the plot
        self.figureCanvasCon.draw_idle()

    def eventFilter(self, obj, event):
        # modifiers = QApplication.keyboardModifiers()
        name = obj.objectName()
        if isinstance(obj, QTableWidget) or isinstance(obj, QPushButton):
            if event.type() == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    event.accept()
                    return True
            # if event.type() == QEvent.Drop:
            #     files = [u.toLocalFile() for u in event.mimeData().urls()]
            #     file = files[0]
            #     print(files)
            #     self.input(files)
            #     # self.input(file_f)
            #     return True
            if event.type() == QEvent.Drop:
                new_files = [u.toLocalFile() for u in event.mimeData().urls()]
                self.files_list.extend(new_files)
                # print("Current files list:", self.files_list)
                # 传入完整的文件列表
                self.input(self.files_list)
                return True

        if isinstance(
                obj,
                FigureCanvas):
            if event.type() == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    # must accept the dragEnterEvent or else the dropEvent
                    # can't occur !!!
                    event.accept()
                    return True
            if event.type() == QEvent.Drop:
                new_files = [u.toLocalFile() for u in event.mimeData().urls()]
                self.files_list.extend(new_files)
                # print("Current files list:", self.files_list)
                # 传入完整的文件列表
                self.input(self.files_list)
                return True

        return super(MCMCTracer, self).eventFilter(obj, event)

    def popupException(self, exception):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setText(
            'The program encountered an unforeseen problem, please report the bug at <a href="https://github.com/dongzhang0725/PhyloSuite/issues">https://github.com/dongzhang0725/PhyloSuite/issues</a> or send an email with the detailed traceback to dongzhang0725@gmail.com')
        msg.setWindowTitle("Error")
        msg.setDetailedText(exception)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()


class MCMCTree(QDialog,Ui_MCMCTreeGUI,object):
    showSig = pyqtSignal(QDialog)
    closeSig = pyqtSignal(str, str)
    logGuiSig = pyqtSignal(str)
    startButtonStatusSig = pyqtSignal(list)
    mcmctree_exception = pyqtSignal(str)
    workflow_progress = pyqtSignal(int)
    workflow_finished = pyqtSignal(str)
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    progressSig = pyqtSignal(int)  # 控制进度条
    ##弹出识别输入文件的信号
    auto_popSig = pyqtSignal(QDialog)
    sum_dialog_popSig = pyqtSignal()

    def __init__(
            self,
            workPath=None,
            focusSig=None,
            mcmctreeEXE=None,
            basemlEXE=None,
            r8sEXE=None,
            autoInputs=None,
            workflow=False,
            parent=None):
        super(MCMCTree, self).__init__(parent)
        #self.Baseml = Baseml
        self.Ui_configuration = Ui_configuration
        self.parent = parent
        self.function_name = "MDGUI"
        self.factory = Factory()
        #self.main = MyMainWindow()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.focusSig = focusSig
        self.workflow = workflow
        self.mcmctreeEXE = mcmctreeEXE
        self.basemlEXE = basemlEXE
        self.r8sEXE = r8sEXE
        self.seqFileName = ''
        self.treeFileName = ''
        self.seq_type = ''
        self.rootCal = ''
        self.version = ""
        self.setupUi(self)
        self.MCMCTree_settings = QSettings(
           self.thisPath + '/settings/MCMCTree_settings.ini', QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.MCMCTree_settings.setFallbacksEnabled(False)
        self.qss_file = self.factory.set_qss(self)
        # 恢复用户的设置
        self.guiRestore()
        # 判断程序的版本 TODO
        ## 自动导入树和MSA文件
        if autoInputs:
            trees, alns = autoInputs
            if trees:
                self.input(trees[0], 4)
            if alns:
                self.input(alns[0], 3)
        # 槽函数
        self.exception_signal.connect(self.popupException)
        self.startButtonStatusSig.connect(self.factory.ctrl_startButton_status)
        self.logGuiSig.connect(self.addText2Log)
        self.progressSig.connect(self.runProgress)
        self.sum_dialog_popSig.connect(self.sum_dialog)
        self.lineEdit_2.deleteFile.clicked.connect(
            self.clear_lineEdit)  # 删除了内容，也要把tooltip删掉
        self.lineEdit_2.autoDetectSig.connect(self.popupAutoDec)
        self.lineEdit.deleteFile.clicked.connect(
            self.clear_lineEdit)
        self.lineEdit.autoDetectSig.connect(self.popupAutoDec)
        self.comboBox.currentIndexChanged[str].connect(self.ctrlModel)
        self.comboBox_3.activated.connect(self.usedata_changed)
        self.usedata_changed()
        self.comboBox_14.activated.connect(self.ctl_models)
        self.ctl_models(self.comboBox_14.currentIndex())
        #self.comboBox_3.currentTextChanged[str].connect(self.ctrlUsedata)
        #self.ctrlUsedata()
        # self.ctrlITOL()
        # self.comboBox_3.currentIndexChanged[str].connect(self.ctl_usedata)
        # self.ctrlUsedata(self.comboBox_3.currentText())
        # self.ctrlModel(self.comboBox.currentText()) # 理论上该功能会在guiRestore里面触发
        self.mcmctree_exception.connect(self.popup_log_exception)
        self.comboBox.currentTextChanged.connect(self.judgeIQTREEinstalled)
        self.comboBox_14.currentTextChanged.connect(self.judgeIQTREEinstalled)
        # 触发信号
        self.comboBox.currentTextChanged.emit(self.comboBox.currentText())
        self.comboBox_14.currentTextChanged.emit(self.comboBox_14.currentText())
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
        # self.pushButton_8.clicked.connect(self.chooseConvergenceFoler)
        self.factory.swithWorkPath(self.work_action, init=True, parent=self)  # 初始化一下
        self.lineEdit.installEventFilter(self)
        self.lineEdit_2.installEventFilter(self)
        self.comboBox_10.setTopText()
        self.comboBox_3.setEnabled(True)
        self.log_gui = self.gui4Log()
        #self.temporary_tree = None
        #self.text_gui = self.gui4Text()
        ##自动弹出识别文件窗口
        self.auto_popSig.connect(self.popupAutoDecSub)
        # 判断mcmctree和r8s插件是否安装
        self.tabWidgetMCMC.currentChanged.connect(self.judge_plugin_install)
        self.judge_plugin_install(self.tabWidgetMCMC.currentIndex())
        #给结束按钮添加菜单
        menu2 = QMenu(self)
        menu2.setToolTipsVisible(True)
        action_infer = QAction(QIcon(":/picture/resourses/if_Delete_1493279.png"),
                               "Stop the run and infer the time tree",
                               menu2,
                               triggered=self.viewResultsEarly)
        menu2.addAction(action_infer)
        self.pushButton_2.toolButton.setMenu(menu2)
        self.pushButton_2.toolButton.menu().installEventFilter(self)
        if platform.system().lower() == "windows":
            self.spinBox_2.setVisible(False)
            self.label_35.setVisible(False)
            self.checkBox_5.setVisible(False)
            self.checkBox_7.setVisible(False)
            self.checkBox_8.setVisible(False)
            self.checkBox_6.setVisible(False)
            self.label_37.setVisible(False)
            self.comboBox_12.setVisible(False)
            self.label_38.setVisible(False)
            self.doubleSpinBox_16.setVisible(False)
            self.label_39.setVisible(False)
            self.doubleSpinBox_17.setVisible(False)
            self.checkBox_3.setVisible(False)
            self.checkBox_9.setVisible(False)
            self.checkBox_10.setVisible(False)
        ## brief demo
        country = self.factory.path_settings.value("country", "UK")
        url = "https://github.com/abacus-gene/paml/wiki/MCMCtree" if \
            country == "China" else "https://github.com/abacus-gene/paml/wiki/MCMCtree"
        self.label_25.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        self.ctl_template = None
        self.popens = []
        self.reference = "1. Yang Z. PAML 4: phylogenetic analysis by maximum likelihood. " \
                         "Mol Biol Evol. 2007;24:1586–91.\n" \
                         "2. dos Reis, M. and Yang Z. (2011) Approximate likelihood calculation " \
                         "on a phylogeny for Bayesian estimation of divergence times. " \
                         "Molecular Biology and Evolution 28:2161–2172. \n" \
                         "3. Huerta-Cepas J, Serra F, Bork P. ETE 3: reconstruction, analysis, " \
                         "and visualization of phylogenomic data[J]. Molecular biology and evolution, " \
                         "2016, 33(6): 1635-1638. \n" \
                         "4. T.K.F. Wong, N. Ly-Trong, H. Ren, H. Banos, A.J. Roger, E. Susko, C. Bielow, " \
                         "N. De Maio, N. Goldman, M.W. Hahn, G. Huttley, R. Lanfear, B.Q. Minh (2025) " \
                         "IQ-TREE 3: Phylogenomic Inference Software using Complex Evolutionary Models. " \
                         "Submitted, https://doi.org/10.32942/X2P62N"
        self.r8s_reference = "Sanderson, M. J. (2003). r8s: inferring absolute rates of molecular evolution " \
                              "and divergence times in the absence of a molecular clock. Bioinformatics, " \
                              "19(2), 301-302."
        self.dict_args = {}

    def input(self, file, which):
        base = os.path.basename(file)
        if which == 4:
            self.lineEdit.setText(base)
            self.lineEdit.setToolTip(os.path.abspath(file))
            self.treeFileName = file
            # 为了适配所有情况，2个好处：
            # 1. 用户输入树以后不使用calibration功能，直接开始分析，也可以执行在树文件顶部加上数量信息的功能
            # 2. 当遇到多歧树，用户选择自动处理多歧树并重新运行时，比较方便
            self.tree_with_tipdate = self.factory.read_tree(file, refine_name=True, parent=self)
            self.get_nood_calibration(self.tree_with_tipdate)
            self.species_matching(4)
        if which == 3:
            self.lineEdit_2.setText(base)
            self.lineEdit_2.setToolTip(os.path.abspath(file))
            self.seqFileName = file
            if self.seqFileName:
                parsefmt = Parsefmt()
                self.dict_seq = parsefmt.readfile(file)
                self.seq_type = parsefmt.which_pattern(self.dict_seq, file)
                if self.seq_type == "PROTEIN":
                    self.comboBox_2.setCurrentText("AAs")
                elif self.seq_type in ["DNA", "RNA"]:
                    self.comboBox_2.setCurrentText("nucleotides")
                if not (os.path.splitext(self.seqFileName)[1].upper() in [".PAML", ".PML"]):
                    convertfmt = Convertfmt(
                        **{"export_path": os.path.dirname(self.seqFileName), "files": [self.seqFileName], "export_paml": True})
                    convertfmt.exec_()
                    self.seqFileName = convertfmt.f4
                    base = os.path.basename(self.seqFileName)
                    self.lineEdit_2.setText(base)
                    # print(base)
            # 判断序列类型，方便多处使用
            # parsefmt = Parsefmt()
            # self.dict_seq = parsefmt.readfile(file)
            # self.seq_type = parsefmt.which_pattern(self.dict_seq, file)
            # if self.seq_type == "PROTEIN":
            #     self.comboBox_2.setCurrentText("AAs")
            # elif self.seq_type in ["DNA", "RNA"]:
            #     self.comboBox_2.setCurrentText("nucleotides")
            # if

    @pyqtSlot()
    def on_pushButton_4_clicked(self):
        fileName = QFileDialog.getOpenFileName(
            self, "Input tre file", filter="Newick Format(*.nwk *.newick *.tre *.trees);;")
        if fileName[0]:
            self.treeFileName = fileName[0]
            self.input(self.treeFileName, 4)

    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        fileName = QFileDialog.getOpenFileName(
            self, "Input alignment file",
            filter="Supported Format(*.fas *.fasta *.phy *.phylip *.nex *.nxs *.nexus *.pml *.PAML *.aln);;")
        if fileName[0]:
            self.seqFileName = fileName[0]
            self.input(self.seqFileName, 3)

    # @pyqtSlot()
    # def on_pushButton_15_clicked(self):
    #     is_consist = self.consistency_checking()
    #     if not is_consist:
    #         return
    #     s_Values, ds_Values = self.getParas()
    #     # print(f"s_Values:{s_Values}")
    #     # print(f"ds_Values:{ds_Values}")
    #     self.ctl_generater(treefile=self.treeFileName)

    @pyqtSlot()
    def on_pushButton_6_clicked(self):
        """
        show log
        """
        self.log_gui.show()

    @pyqtSlot()
    def on_pushButton_7_clicked(self):
        is_file_in = self.confirm_input()
        if not is_file_in:
            return
        self.gui4Text()
        # tree_path = self.lineEdit.toolTip()
        # seq_path = self.lineEdit_2.toolTip()
        # if tree_path:
        #     if seq_path:
        #         self.gui4Text()
        #     else:
        #         QMessageBox.warning(self, "no file", "No seqfile file is imported, please input the seqfile!")
        # else:
        #     QMessageBox.warning(self, "no file", "No treefile file is imported, please input the treefile!")

    @pyqtSlot()
    def on_pushButton_5_clicked(self, rerun=False):
        """
        execute program
        """
        if self.tabWidgetMCMC.tabText(self.tabWidgetMCMC.currentIndex()) == "r8s":
            if platform.system().lower() != "windows":
                self.version = ""
                version_worker = WorkThread(
                    lambda : self.factory.get_version("r8s", self),
                    parent=self)
                version_worker.start()
            else:
                self.version = "Pyr8s"
            # 有数据才执行
            self.interrupt = False  # 如果是终止以后重新运行要刷新
            self.textEdit_log.clear()  # 清空log
            self.error_has_shown = False
            if platform.system().lower() != "windows":
                self.list_pids = []
                self.queue = multiprocessing.Queue() if platform.system().lower() == "windows" else multiprocessing.Manager().Queue()
                self.pool = multiprocessing.get_context("spawn").Pool(
                    processes=1, initializer=pool_init, initargs=(self.queue,)
                )
                # Check for progress periodically
                self.timer = QTimer()
                self.timer.timeout.connect(self.updateProcess)
                self.timer.start(1)
            self.worker = WorkThread(lambda : self.run_command_r8s(), parent=self)
            self.worker.start()
            if platform.system().lower() != "windows":
                self.on_pushButton_6_clicked()
        else:
            isok = self.judge_root_node()
            if not isok:
                return
            self.chains = int(self.comboBox_8.currentText()) # self.spinBox.value()
            self.exe_repeat = self.checkBox_11.isChecked()
            is_consist = self.consistency_checking()
            if is_consist:
                # 有数据才执行
                self.interrupt = False  # 如果是终止以后重新运行要刷新
                self.textEdit_log.clear()  # 清空log
                self.error_has_shown = False
                self.list_pids = []
                self.queue = multiprocessing.Queue() if platform.system().lower() == "windows" else multiprocessing.Manager().Queue()
                # self.queue = Manager().Queue()  # 安全跨进程,防止MAC报错
                if self.exe_repeat:
                    if self.chains%2==0:
                        threads = self.chains
                    else:
                        threads = self.chains-1
                else:
                    threads = self.chains
                self.pool = multiprocessing.get_context("spawn").Pool(
                    processes=threads, initializer=pool_init, initargs=(self.queue,)
                )
                # Check for progress periodically
                self.timer = QTimer()
                self.timer.timeout.connect(self.updateProcess)
                self.timer.start(1)
                self.worker = WorkThread(lambda : self.run_command(rerun=rerun), parent=self)
                self.worker.start()
                self.on_pushButton_6_clicked()

    @pyqtSlot()
    def on_pushButton_2_clicked(self, silence=False, keep_run_state=False):
        """
        Stop
        """
        if self.isRunning():
            if (not silence) and (not self.workflow):
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
                    self.pool.terminate()  # Terminate all processes in the Pool
                    ## 删除subprocess
                    if platform.system().lower() == "windows":
                        for pid in self.list_pids: os.popen('taskkill /F /T /PID %s' % pid)
                    else:
                        for pid in self.list_pids: os.killpg(os.getpgid(pid), signal.SIGTERM)
                    self.pool = None
                    self.interrupt = True
                except:
                    self.pool = None
                    self.interrupt = True
                if (not silence) and (not self.workflow):
                    QMessageBox.information(
                        self,
                        "MDGUI",
                        "<p style='line-height:25px; height:25px'>Program has been terminated!</p>")
                if keep_run_state:
                    return True
                if hasattr(self, "has_previous_run") and self.has_previous_run:
                    for hpr in self.has_previous_run:
                        self.startButtonStatusSig.emit(
                            [
                                self.pushButton_5,
                                self.progressBar,
                                "except",
                                hpr,
                                self.qss_file,
                                self])
                if hasattr(self, "exportPath"):
                    self.startButtonStatusSig.emit(
                        [
                            self.pushButton_5,
                            self.progressBar,
                            "except",
                            self.exportPath,
                            self.qss_file,
                            self])
            return True
        else:
            return False

    @pyqtSlot()
    def on_pushButton_clicked(self):
        """
        add calibration
        """
        # 判断用户是否导入了树，没有就弹框提示
        # 如果是无根树提醒用户
        # set_NCBI_db = self.factory.checkNCBIdb(self)
        # if set_NCBI_db:
        #     self.updateTaxonomyDB()
        #     return
        if hasattr(self, "tree_with_tipdate"):
            self.handle_tree_text(self.tree_with_tipdate, mode="calibration").show(name="MCMCTREE-ETE", parent=self)
            #print(self.handle_tree_text(self.tree_with_tipdate, mode="calibration").write())
            self.get_nood_calibration(self.tree_with_tipdate)
        else:
            QMessageBox.information(self, "MDGUI",
                                    "Please input tree first!")

    @pyqtSlot()
    def on_pushButton_12_clicked(self):
        """
        preview r8s configuration
        """
        tree_path = self.lineEdit.toolTip()
        seq_path = self.lineEdit_2.toolTip()
        if tree_path:
            self.gui4Text()
            # if seq_path:
            #     self.gui4Text()
            # else:
            #     QMessageBox.warning(self, "no file", "No seqfile file is imported, please input the seqfile!")
        else:
            QMessageBox.warning(self, "no file", "No treefile file is imported, please input the treefile!")

    @pyqtSlot()
    def on_pushButton_13_clicked(self):
        """
        Generate configuration file and run in Linux system
        """
        fileName = QFileDialog.getSaveFileName(
            self, "MDGUI", "r8s_data_cmd", "text Format(*.txt)")
        if fileName[0]:
            self.prepare_for_run_r8s(file=fileName[0])
            QMessageBox.information(
                self,
                "MDGUI",
                "<p style='line-height:25px; height:25px'>File saved successfully!</p>"
                "After moving 'r8s_data_cmd.txt' to your Linux system, navigate to its directory in the terminal, "
                "then run the command: <br><br>"
                f"<span style=\" font-weight:600; color:#ff0000;\">r8s{' -b' if self.batch_process else ''} -f r8s_data_cmd.txt</span><br><br>"
                "Note: ensure that r8s is in your environment path")

    @pyqtSlot()
    def on_pushButton_continue_clicked(self):
        """
        continue
        1. rename mcmc.txt to others
        2. setting burin as 0
        3. checkpoint = 2
        4. summarize: 把所有sample合并以后再去summarize？ 这一步是通过mcmc.txt去summarize吗？
        5. 读取seed，赋予给新的ctl
        """
        if self.isRunning():
            QMessageBox.information(
                self,
                "MDGUI",
                "<p style='line-height:25px; height:25px'>MCMCTREE is running!</p>")
            return
        resultsPath = None
        ##choose work folder
        if os.path.exists(self.workPath + os.sep + "MDGUI_results"):
            list_result_dirs = sorted([i for i in os.listdir(self.workPath + os.sep + "MDGUI_results")
                                       if os.path.isdir(self.workPath + os.sep + "MDGUI_results" + os.sep + i)],
                                      key=lambda x: os.path.getmtime(self.workPath + os.sep + "MDGUI_results" + os.sep + x), reverse=True)
            if list_result_dirs:
                item, ok = QInputDialog.getItem(self, "Choose previous results",
                                                "Previous results:", list_result_dirs, 0, False)
                if ok and item:
                    resultsPath = self.workPath + os.sep + "MDGUI_results" + os.sep + item
        else:
            QMessageBox.information(
                self,
                "MDGUI",
                "<p style='line-height:25px; height:25px'>No previous MCMCTREE analysis found in %s!</p>"%os.path.normpath(self.workPath))
            return
        self.exportPath = resultsPath
        self.has_previous_run = self.havePreviousRun(resultsPath)
        if self.has_previous_run:
            self.i, ok = QInputDialog.getInt(self,
                                        "Specify sample to run", "Additional sample:", 10000, 0, 999999999, 1000)
            if ok:
                # commands = []
                # for runPath in has_previous_run:
                #     # self.refresh_analysis(resultsPath)
                #     ctl_path = self.ctl_addition(runPath)
                #     self.mcmc_addition(runPath)
                #     self.replace_ctl(ctl_path,
                #                      r"(?i)nsample\s*=\s*\d+",
                #                      f"nsample = {i}")
                #     self.replace_ctl(ctl_path,
                #                      r"(?i)burnin\s*=\s*\d+",
                #                      "burnin = 0")
                #     self.replace_ctl(ctl_path,
                #                      r"(?i)checkpoint\s*=\s*\d+",
                #                      "checkpoint = 2")
                #     seed = self.fetch_seed(runPath)
                #     self.replace_ctl(ctl_path,
                #                      r"(?i)seed\s*=\s*-?\d+",
                #                      f"seed = {seed}")
                #     # self.logGuiSig.emit("\n&&&&&&&& Resume MCMCTREE analysis...... &&&&&&&&\n")
                #     commands.append(f"{self.mcmctreeEXE} {ctl_path}")
                #     # self.mcmctree_popen = self.factory.init_popen(cmd)
                #     # self.worker = WorkThread(self.run_command_continue, parent=self)
                #     # self.worker.start()
                #     # self.on_pushButton_6_clicked()
                # if commands:
                self.interrupt = False  # 如果是终止以后重新运行要刷新
                self.error_has_shown = False
                self.list_pids = []
                # self.continue_queue = multiprocessing.Queue()
                self.queue = multiprocessing.Queue() if platform.system().lower() == "windows" else multiprocessing.Manager().Queue()
                self.pool = multiprocessing.get_context("spawn").Pool(
                    processes=len(self.has_previous_run), initializer=pool_init,
                    initargs=(self.queue,)
                )
                # Check for progress periodically
                self.timer = QTimer()
                self.timer.timeout.connect(self.updateProcess)
                self.timer.start(1)
                self.worker = WorkThread(lambda : self.run_command_continue(self.has_previous_run,resultsPath), parent=self)
                self.worker.start()
                self.on_pushButton_6_clicked()
        else:
            QMessageBox.information(
                self,
                "MDGUI",
                "<p style='line-height:25px; height:25px'>No checkpoint file found in %s, please rerun the analysis!</p>"%resultsPath)

    @pyqtSlot()
    def on_pushButton_9_clicked(self, use_prog_bar=False, sum_silence=False,
                                mode="direct click"):
        '''
        summarize
        1. 未运行程序，直接打开以前的结果进行summarize
        2. 运行mcmctree，正常结束/或续跑结束后统一summarize
        3. 运行mcmctree的过程中summarize看看结果

        mode:
        direct click
        summarize during run
        stop run and summarize
        run finished following summarize

        Parameters
        ----------
        silence
        self.use_prog_bar: 程序正常运行完的最后一步

        Returns
        -------

        '''
        self.summarize_silence = sum_silence
        self.use_prog_bar = use_prog_bar
        self.summarize_mode = mode
        if self.isRunning() and (mode=="direct click"):
            self.summarize_mode = "summarize during run"
        if (not self.isRunning()) and (mode=="direct click"):
            ## 判断结果文件夹是否存在
            if os.path.exists(self.workPath + os.sep + "MDGUI_results"):
                ## 打开文件选择对话框，允许用户选择文件夹
                resultsPath = QFileDialog.getExistingDirectory(
                    self,
                    "Choose MCMCTREE results folder",
                    self.workPath + os.sep + "MDGUI_results",
                    QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
                )

                ## 检查用户是否选择了有效路径
                if resultsPath:
                    self.exportPath = resultsPath
                else:
                    return
            else:
                QMessageBox.information(
                    self,
                    "MDGUI",
                    "<p style='line-height:25px; height:25px'>No MCMCTREE results found in %s!</p>" % os.path.normpath(
                        self.workPath)
                )
                return
        if (not self.use_prog_bar) and (mode != "stop run and summarize"):
            # stop run and summarize 模式是在进程里面执行这个函数的，所以会报错，以信号槽形式执行
            self.sum_dialog_popSig.emit()

        self.interrupt = False  # 如果是终止以后重新运行要刷新
        self.error_has_shown = False
        self.list_pids = [] if not hasattr(self, "list_pids") else self.list_pids
        mcmc_results_ = [(None, glob.glob(f"{self.exportPath}{os.sep}run*"))]
        if not mcmc_results_[0][1]:
            repeat1Paths = glob.glob(f"{self.exportPath}{os.sep}repeat1{os.sep}run*")
            repeat2Paths = glob.glob(f"{self.exportPath}{os.sep}repeat2{os.sep}run*")
            mcmc_results_ = [("repeat1", repeat1Paths), ("repeat2", repeat2Paths)]
        if not hasattr(self, "queue"):
            self.queue = multiprocessing.Queue() if platform.system().lower() == "windows" else multiprocessing.Manager().Queue()
        self.sum_pool = multiprocessing.get_context("spawn").Pool(
            processes=len(mcmc_results_), initializer=pool_init, initargs=(self.queue,)
        )
        # Check for progress periodically
        self.sum_timer = QTimer()
        self.sum_timer.timeout.connect(self.updateProcess) #(lambda : self.updateProcess(mode="summarize"))
        self.sum_timer.start(1)
        self.sum_worker = WorkThread(lambda : self.summarize_fun(mcmc_results=mcmc_results_), parent=self)
        self.sum_worker.start()

    @pyqtSlot()
    def on_pushButton_8_clicked(self):
        self.progressDialog = self.factory.myProgressDialog(
            "Please Wait", "Prepare data for MCMCTacer...",
            busy=True,
            parent=self)
        self.progressDialog.show()
        Worker = WorkThread(self.prepare_for_mcmctracer, parent=self)
        self.progressDialog.canceled.connect(lambda: [Worker.stopWork(),
                                                      self.progressDialog.close()])
        Worker.finished.connect(lambda: [self.openMCMCtracer(),
                                            self.progressDialog.close()])
        Worker.start()

    def prepare_for_mcmctracer(self):
        if hasattr(self, "exportPath"):
            repeatPaths = glob.glob(f"{self.exportPath}{os.sep}repeat*")
            runPaths = glob.glob(f"{self.exportPath}{os.sep}run*")
            self.mcmc_file_paths = []
            if runPaths:
                for rpath in runPaths:
                    if "mcmc.txt" in os.listdir(rpath):
                        mcmc_file_path = os.path.join(rpath, "mcmc.txt").replace("\\", "/")
                        self.mcmc_file_paths.append(mcmc_file_path)
            elif repeatPaths:
                for repeatPath in repeatPaths:
                    all_mcmc = []
                    rPaths = glob.glob(f"{repeatPath}{os.sep}run*")
                    mcmcs = None
                    for rpath in rPaths:
                        all_mcmc_name, mcmcs = self.mcmc_agg(rpath, filename=None)
                        all_mcmc.extend(mcmcs[1:])
                    if not mcmcs:
                        continue
                    all_mcmc.insert(0, mcmcs[0])
                    if all_mcmc:
                        all_mcmc_path = f"{repeatPath}{os.sep}all_mcmc_runs.txt"
                        with open(all_mcmc_path, "w", errors="ignore") as f:
                            f.write("".join(all_mcmc))
                        self.mcmc_file_paths.append(all_mcmc_path)

    def openMCMCtracer(self):
        if hasattr(self, "mcmc_file_paths") and self.mcmc_file_paths:
            self.MCMCTracer = MCMCTracer(workPath=self.workPath,
                focusSig=self.focusSig,
                parent=self,
                resultsPath=None)
            self.MCMCTracer.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | self.MCMCTracer.windowFlags())
            self.MCMCTracer.input(self.mcmc_file_paths, use_folder_name=True)
            self.MCMCTracer.show()
        else:
            QMessageBox.warning(self, "Warning", "None of the paths contain MCMC samples. "
                                                 "We will open MCMCTracer window for you to import files.")
            self.MCMCTracer = MCMCTracer(workPath=self.workPath,
                focusSig=self.focusSig,
                parent=self)
            self.MCMCTracer.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | self.MCMCTracer.windowFlags())
            self.MCMCTracer.show()

    def summarize_fun(self, mcmc_results=None):
        try:
            commands = []
            for rep, rPaths in mcmc_results:
                all_mcmc = []
                for rpath in rPaths:
                    all_mcmc_name, mcmcs = self.mcmc_agg(rpath)
                    if not mcmcs:
                        continue
                    all_mcmc.extend(mcmcs[1:])
                if not mcmcs:
                    continue
                all_mcmc.insert(0, mcmcs[0])
                all_mcmc_path = f"{self.exportPath}{os.sep}{rep+os.sep if rep else ''}all_mcmc_runs.txt"
                with open(all_mcmc_path, "w", errors="ignore") as f:
                    f.write("".join(all_mcmc))
                sum_ctl = f"{self.exportPath}{os.sep}{rep+os.sep if rep else ''}summarization.ctl"
                self.ctl_file = f"{rpath}{os.sep}mcmctree.ctl"
                shutil.copyfile(self.ctl_file, sum_ctl)
                self.replace_ctl(sum_ctl,
                                 r"(?i)mcmcfile\s*=\s*[^\n]+",
                                 f"mcmcfile = all_mcmc_runs.txt")
                self.replace_ctl(sum_ctl,
                                 r"(?i)outfile\s*=\s*[^\n]+",
                                 f"outfile = summarization.out.txt")
                self.replace_ctl(sum_ctl,
                                 r"(?i)print\s*=\s*-?\d+",
                                 f"print = -1")
                # seed = self.fetch_seed(rpath)
                self.replace_ctl(sum_ctl,
                                 r"(?i)seed\s*=\s*-?\d+",
                                 f"seed = -1")
                self.replace_ctl(sum_ctl,
                                 r"(?i)burnin\s*=\s*\d+",
                                 f"burnin = 0")
                # copy input file
                alignment = self.fetchCTLvalue(sum_ctl, r"(?i)seqfile\s*=\s*(\S+)")
                shutil.copyfile(f"{rpath}{os.sep}{alignment}", f"{self.exportPath}{os.sep}{rep+os.sep if rep else ''}{alignment}")
                tree = self.fetchCTLvalue(sum_ctl, r"(?i)treefile\s*=\s*(\S+)")
                shutil.copyfile(f"{rpath}{os.sep}{tree}", f"{self.exportPath}{os.sep}{rep+os.sep if rep else ''}{tree}")
                sum_cmd = f"{self.mcmctreeEXE} {sum_ctl}"
                commands.append((sum_cmd,f"{self.exportPath}{os.sep+rep if rep else ''}",sum_ctl))
            if commands:
                async_results = [self.sum_pool.apply_async(run, args=({}, command, runPath,
                                                                      ctl_file, "summarize")) for
                                 command,runPath,ctl_file in commands]
                # async_results = [self.sum_pool.apply_async(sum_run, args=(command, runPath)) for
                #                  command,runPath,ctl_file in commands]
                self.sum_pool.close()  # 关闭进程池，防止进一步操作。如果所有操作持续挂起，它们将在工作进程终止前完成
                map(ApplyResult.wait, async_results)
                lst_results = [r.get() for r in async_results]
                self.sum_pool.join()  # 等待所有进程结束
                time_tree = f"{self.exportPath}{os.sep}repeat1{os.sep}FigTree.tre"
                if os.path.exists(time_tree):
                    shutil.copy(time_tree, self.exportPath)
            else:
                raise ValueError("No MCMC samples found!")
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
            self.sum_pool = None

    def species_matching(self, which):
        if which == 4:
            # tree_path = self.lineEdit.toolTip()
            # tre = self.factory.read_tree(tree_path, parent=self)
            species_count = len(self.tree_with_tipdate)
            self.label_5.setText(str(species_count))
            # species_count = tre.count_terminals()

    # def partition_matching(self, which):
    #     if which == 3:
    #         seq_path = self.lineEdit_2.toolTip()
    #         with open(seq_path, 'r') as file:
    #             lines = file.readlines()
    #             if not lines[1].split():
    #                 return
    #             first_species = lines[1].split()[0]
    #             print(first_species)
    #             ndata_count = sum([1 for line in lines if line.strip().startswith(first_species)])
    #             print(ndata_count)
    #             self.spinBox.setValue(ndata_count)

    def rename_file(self, filePath, oldName, newName):
        # print("rename")
        out_file_path = os.path.join(filePath, oldName)
        in_file_path = os.path.join(filePath, newName)
        if os.path.exists(out_file_path):
            os.rename(out_file_path, in_file_path)

    # def modify_usedata(self):
    #     ctl_file_path = os.path.join(self.exportPath, "mcmctree.ctl")
    #     with open(ctl_file_path, 'r', errors='ignore') as f:
    #         ctl_content = f.read()
    #     modified_ctl_content = ctl_content.replace("usedata = 3", "usedata = 2")
    #     with open(ctl_file_path, 'w', errors='ignore') as f:
    #         f.write(modified_ctl_content)

    def ctrlModel(self, text):
        if text == "AUTO":
            return
        if (text in ["JC69", "K80", "F81", "F84", "HKY", "T92", "TN93", "GTR", "UNREST", "REVu", "UNRESTu"]) and \
                (self.seq_type == "PROTEIN"):
            QMessageBox.information(self, "MDGUI", "PhyloSuite detected that your data is "
                                                      "comprised of amino acid sequences. "
                                                      "You cannot select a nucleotide model!")
            self.sender().setCurrentText("AUTO")
            return
        elif (text in ["cpREV10", "cpREV64", "dayhoff", "dayhoff-dcmut", "g1974a", "g1974c", "g1974p", "g1974v",
                       "grantham", "jones", "jones-dcmut", "lg", "miyata", "mtART", "mtmam", "mtREV24", "MtZoa",
                       "wag"]) and \
                (self.seq_type in ["DNA", "RNA"]):
            QMessageBox.information(self, "MDGUI", "PhyloSuite detected that your data is "
                                                      "comprised of nucleotide sequences. "
                                                      "You cannot select a protein model!")
            self.comboBox.setCurrentText("AUTO")
            return
        # 与usedata联动判断
        self.usedata_changed()

    def confirm_input(self):
        tree_path = self.lineEdit.toolTip()
        seq_path = self.lineEdit_2.toolTip()
        if not tree_path:
            QMessageBox.warning(self, "no file", "No tree file file is imported!")
            return False
        if not seq_path:
            QMessageBox.warning(self, "no file", "No alignment file is imported!")
            return False
        return tree_path, seq_path

    def consistency_checking(self):
        is_file_in = self.confirm_input()
        if not is_file_in:
            return
        tree_path, seq_path = is_file_in
        # tree_path = self.lineEdit.toolTip()
        # seq_path = self.lineEdit_2.toolTip()
        # if tree_path:
        # tre = self.factory.read_tree(tree_path, parent=self)
        tre_species = set([leaf.name for leaf in self.tree_with_tipdate.iter_leaves()])
        tre_species_count = len(tre_species)
        # else:
        #     QMessageBox.warning(self, "no file", "No treefile file is imported, please input the treefile!")
        # if seq_path:
        if not hasattr(self, "dict_seq"):
            parsefmt = Parsefmt()
            self.dict_seq = parsefmt.readfile(seq_path)
        seq_species = set(self.dict_seq.keys())
        seq_species_count = len(seq_species)
            # print(seq_species)
            # print(seq_species_count)
        if seq_species == tre_species:
            if seq_species_count == tre_species_count:
                pass
                #QMessageBox.information(self, "consistency check", "The species are the same in both files.")
        else:
            # print(seq_species)
            # print(tre_species)
            # print(seq_species == tre_species)
            QMessageBox.warning(self, "different", "Different species, re-import files!")
            return False
        # else:
        #     QMessageBox.warning(self, "no file", "No sequence file is imported, please input the seqfile!")
        #     return False
        return True

    # def updateProcess(self):
    #     """
    #     Check the status of running processes and update the UI.
    #     """
    #     try:
    #         while not self.queue.empty():
    #             message = self.queue.get_nowait()
    #             self.textEdit_log.append(message)
    #     except Exception as e:
    #         print(f"Error updating process: {e}")
    # def run_times_command(self):
    #     for i in range(min(self.run_times, 5)):
    #         popen = self.factory.init_popen(self.commands)
    #         self.popens.append(popen)
    #         # 创建线程并绑定到对应的命令
    #         worker = WorkThread(lambda p=popen: self.run_command(p), parent=self)
    #         self.workers.append(worker)
    #         worker.start()
    #     for worker in self.workers:
    #         worker.finished.connect(self.check_threads_finished)

    def run_command(self, rerun=False):
        try:
            self.output_dir_name = self.factory.fetch_output_dir_name(self.dir_action)
            self.exportPath = self.factory.creat_dirs(self.workPath +
                                                 os.sep + "MDGUI_results" + os.sep + self.output_dir_name) if \
                not rerun else self.exportPath
            self.time_start = datetime.datetime.now()
            self.startButtonStatusSig.emit(
                [
                    self.pushButton_5,
                    self.progressBar,
                    "start",
                    self.exportPath,
                    self.qss_file,
                    self])
            seeds = random.sample(range(2147483647), self.chains)
            # print(seeds)
            if self.exe_repeat:
                # 保证repeat
                self.chains = 2 if self.chains==1 else self.chains
                repeat = [(1 if (i+1)*2 <= self.chains else 2, i) for i in range(self.chains)]
                if len(repeat)%2 == 1:
                    # 如果核心数是单数，删掉最后的run，确保2个重复的run的数量一样
                    repeat.pop()
                command_list = [self.prepare_for_run(fold_suffix=f"repeat{rep}/run{i+1}", seed=seeds[i])
                                for rep,i in repeat]
            else:
                command_list = [self.prepare_for_run(fold_suffix=f"run{i+1}", seed=seeds[i])
                                for i in range(self.chains)]
            async_results = [self.pool.apply_async(run, args=(self.dict_args, command, runPath, ctl_file)) for
                             command,runPath,ctl_file in command_list]
            self.pool.close() # 关闭进程池，防止进一步操作。如果所有操作持续挂起，它们将在工作进程终止前完成
            map(ApplyResult.wait, async_results)
            lst_results = [r.get() for r in async_results]
            self.pool.join()  # 等待所有进程结束
            if not self.error_has_shown:
                self.end_run(silence=True)
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

    def run_command_r8s(self, cfg=None):
        try:
            self.output_dir_name = self.factory.fetch_output_dir_name(self.dir_action)
            self.exportPath = self.factory.creat_dirs(self.workPath +
                                                      os.sep + "MDGUI_results" + os.sep + self.output_dir_name)
            self.time_start = datetime.datetime.now()
            self.startButtonStatusSig.emit(
                [
                    self.pushButton_5,
                    self.progressBar,
                    "start",
                    self.exportPath,
                    self.qss_file,
                    self])
            # 存树
            with open(f"{self.exportPath}{os.sep}tree_with_r8s_mark.nwk", "w", errors="ignore") as f:
                f.write(self.tree_with_tipdate.write(format=3,
                                         no_replace=True).replace("NoName", ""))
            r8s_cmd_data_file = f"{self.exportPath}{os.sep}r8s_cmd_data.txt"
            if not cfg:
                self.prepare_for_run_r8s(file=r8s_cmd_data_file)
            else:
                with open(r8s_cmd_data_file, "w", errors="ignore") as f:
                    f.write(cfg)
            if platform.system().lower() != "windows":
                command_list = [f"echo 'quit;' | {self.r8sEXE}{' -b' if self.batch_process else ''} -f {r8s_cmd_data_file}"]
                # 修改
                async_results = [self.pool.apply_async(run, args=("", command, self.exportPath, "", "r8s")) for
                                 command in command_list]
                self.pool.close()  # 关闭进程池，防止进一步操作。如果所有操作持续挂起，它们将在工作进程终止前完成
                map(ApplyResult.wait, async_results)
                lst_results = [r.get() for r in async_results]
                self.pool.join()  # 等待所有进程结束
                # 获取并生成时间树和速率树
                text = self.textEdit_log.toPlainText()
                rgx_chrono = re.compile(r"(?sm)\[TREE DESCRIPTION of tree[^\]]+\][^;]+?tree [^\(]+(\([^;]+;)")
                if rgx_chrono.search(text):
                    chronogram = rgx_chrono.search(text).group(1)
                    with open(f"{self.exportPath}{os.sep}chronogram.nwk", 'w', errors="ignore") as file:
                        file.write(chronogram)
                rgx_rate = re.compile(r"(?sm)\[RATO DESCRIPTION of tree[^\]]+\][^;]+?tree [^\(]+(\([^;]+;)")
                if rgx_rate.search(text):
                    ratogram = rgx_rate.search(text).group(1)
                    with open(f"{self.exportPath}{os.sep}ratogram.nwk", 'w', errors="ignore") as file:
                        file.write(ratogram)
            else:
                with CaptureOutput() as output:
                    a = pyr8sp.from_file_nexus(r8s_cmd_data_file)
                    a.run()
                self.logGuiSig.emit("\n".join(output))
                with open(f"{self.exportPath}{os.sep}chronogram.nwk", 'w', errors="ignore") as file:
                    file.write(a.results.chronogram.as_string(schema='newick').replace("[&R] ", ""))
                with open(f"{self.exportPath}{os.sep}ratogram.nwk", 'w', errors="ignore") as file:
                    file.write(a.results.ratogram.as_string(schema='newick').replace("[&R] ", ""))
                with open(f"{self.exportPath}{os.sep}age_rates.csv", 'w', errors="ignore") as file:
                    table = a.results.table
                    for i in range(table['n']):
                        file.write(str(table['Node'][i]) + ',')
                        file.write(str(table['Age'][i]) + ',')
                        file.write(str(table['Rate'][i]) + '\n')
            time_end = datetime.datetime.now()
            self.time_used = str(time_end - self.time_start)
            self.time_used_des = "Start at: %s\nFinish at: %s\nTotal time used: %s\n\n" % (str(self.time_start), str(time_end),
                                                                                           self.time_used)
            tool = f"r8s v{self.version} (Sanderson et al., 2003)" if self.version != "Pyr8s" \
                            else "Pyr8s (https://github.com/iTaxoTools/pyr8s)"
            self.description = f"Molecular dating analyses were conducted using {tool} " \
                           f"with {self.r8s_algorithm} algorithm and {self.r8s_method} method."
            with open(self.exportPath + os.sep + "summary and citation.txt", "w", encoding="utf-8") as f:
                f.write(self.description +
                        f"\n\nIf you use PhyloSuite v2, please cite:\n{self.factory.get_PS_citation()}\n\n"
                        "If you use r8s, please cite:\n" + self.r8s_reference + "\n\n" + self.time_used_des)
            self.pool = None
            # self.interrupt = False
            if (not self.interrupt) and (not self.error_has_shown):
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
                # self.pool = None
                # self.interrupt = False
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

    def run_command_continue(self, runPaths, resultsPath):
        try:
            self.time_start = datetime.datetime.now()
            self.startButtonStatusSig.emit(
                [
                    self.pushButton_5,
                    self.progressBar,
                    "start",
                    resultsPath,
                    self.qss_file,
                    self])
            commands = []
            for runPath in runPaths:
                ctl_path = self.ctl_addition(runPath)
                self.mcmc_addition(runPath)
                self.replace_ctl(ctl_path,
                                 r"(?i)nsample\s*=\s*\d+",
                                 f"nsample = {self.i}")
                self.replace_ctl(ctl_path,
                                 r"(?i)burnin\s*=\s*\d+",
                                 "burnin = 0")
                # self.replace_ctl(ctl_path,
                #                  r"(?i)checkpoint\s*=\s*\d+",
                #                  "checkpoint = 2")
                self.auto_checkpoint(ctl_path, resume=True)
                seed = self.fetch_seed(runPath)
                self.replace_ctl(ctl_path,
                                 r"(?i)seed\s*=\s*-?\d+",
                                 f"seed = {seed}")
                # self.logGuiSig.emit("\n&&&&&&&& Resume MCMCTREE analysis...... &&&&&&&&\n")
                commands.append((f"{self.mcmctreeEXE} {ctl_path}",runPath,ctl_path))
            if commands:
                # self.run_code()
                async_results = [self.pool.apply_async(run, args=({}, command, runPath, ctl_file, "continue")) for
                                 command,runPath,ctl_file in commands]
                self.pool.close()  # 关闭进程池，防止进一步操作。如果所有操作持续挂起，它们将在工作进程终止前完成
                map(ApplyResult.wait, async_results)
                lst_results = [r.get() for r in async_results]
                self.pool.join()  # 等待所有进程结束
                # if not self.error_has_shown:
                # 已经弹窗报错，点击弹窗以后，进度条又会被启动，可能是因为其它run在弹窗的时候还没运行，点击弹窗又运行了。
                # 等所有东西都输出以后再弹窗更好？有时候捕获error，还会启动去运行end_run,怎么办？
                if not self.error_has_shown:
                    self.end_run(silence=True)
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
                    resultsPath,
                    self.qss_file,
                    self])
            self.pool = None
            self.interrupt = False

    def end_run(self,
                use_prog_bar=False,
                silence=False,
                sum_silence=False,
                runpaths=None,
                sum_mode="run finished following summarize"):
        # runpaths = glob.glob(f"{self.exportPath}{os.sep}run*") if not runpaths else runpaths
        self.on_pushButton_9_clicked(use_prog_bar=use_prog_bar,
                                     sum_silence=sum_silence,
                                     # rpath=runpaths,
                                     mode=sum_mode)
        time_end = datetime.datetime.now()
        self.time_used = str(time_end - self.time_start)
        self.time_used_des = "Start at: %s\nFinish at: " \
                             "%s\nTotal time used: %s\n\n" % (str(self.time_start),
                                                              str(time_end),
                                                              self.time_used)
        # 加上version信息
        with open(self.exportPath + os.sep + "PhyloSuite_MCMCTREE.log") as f:
            content = f.read()
        rgx_version = re.compile(r"(?im)MCMCTREE.+?(\d+\.\d+\.\d+)")
        if rgx_version.search(content):
            self.version = rgx_version.search(content).group(1)
        else:
            self.version = ""
        if self.comboBox_14.currentIndex() == 0:
            IQ_model = " and IQ-TREE (for best-fit model selection and Hessian matrix calculation) (Thomas Wong et al., 2025)"
        elif (self.comboBox.currentText() == "AUTO"):
            IQ_model = " and IQ-TREE (for best-fit model selection) (Thomas Wong et al., 2025)"
        else:
            IQ_model = ""
        self.description = f"Molecular dating analyses were conducted using MCMCTREE v{self.version} " \
                           f"(Yang, 2007; dos Reis et al., 2011) with the help of ETE3 (Huerta-Cepas et al., 2016){IQ_model}."
        with open(self.exportPath + os.sep + "summary and citation.txt", "w", encoding="utf-8") as f:
            f.write(self.description +
                    f"\n\nIf you use PhyloSuite v2, please cite:\n{self.factory.get_PS_citation()}\n\n"
                    "If you use MCMCTREE, please cite:\n" + self.reference + "\n\n" + self.time_used_des)
        self.pool = None
        # self.interrupt = False
        if silence:
            return
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
            # self.pool = None
            # self.interrupt = False
        if not self.workflow:
            self.focusSig.emit(self.exportPath)

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
                if name == "comboBox_10":
                    item_state = {self.comboBox_10.itemText(i): True if
                                self.comboBox_10.model().item(i).checkState() == Qt.Checked else False
                                  for i in range(self.comboBox_10.count())}
                    self.MCMCTree_settings.setValue(name, item_state)
                else:
                    index = obj.currentIndex()
                    self.MCMCTree_settings.setValue(name, index)
            elif isinstance(obj, QCheckBox):
                state = obj.isChecked()
                self.MCMCTree_settings.setValue(name, state)
            elif isinstance(obj,QSpinBox):
                int_ = obj.value()
                self.MCMCTree_settings.setValue(name, int_)
            elif isinstance(obj, QDoubleSpinBox):
                float_ = obj.value()
                self.MCMCTree_settings.setValue(name, float_)

    def guiRestore(self):

        # Restore geometry
        self.resize(self.MCMCTree_settings.value('size', QSize(1300, 700)))
        self.factory.centerWindow(self)
        # self.move(self.MCMCTree_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                obj.installEventFilter(self)  # 安装事件过滤器，为了取消滚轮事件
                if name == "comboBox":
                    ini_models = ["AUTO", "***Default***", "JC69", "K80", "F81", "F84", "HKY", "T92", "TN93", "GTR", "UNREST",
                                  "REVu", "UNRESTu",
                                  "***AAs***", "cpREV10", "cpREV64", "dayhoff", "dayhoff-dcmut", "g1974a", "g1974c",
                                  "g1974p", "g1974v",
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
                    obj.model().item(1).setSelectable(False)
                    obj.model().item(13).setSelectable(False)
                elif name == "comboBox_8":
                    cpu_num = multiprocessing.cpu_count()
                    list_cpu = [str(i + 1) for i in range(cpu_num)]
                    index = self.MCMCTree_settings.value(name, "3")
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
                elif name == "comboBox_10":
                    init_state = {"CHRONOGRAM": True, "CLADOGRAM": False, "PHYLOGRAM": False, "RATOGRAM": True,
                                  "CHRONO_DESCRIPTION": True, "PHYLO_DESCRIPTION": False,
                                  "RATO_DESCRIPTION": True, "TREE_DESCRIPTION": False,
                                  "MARG_DESCRIPTION": False,
                                  "ID_DESCRIPTION": False, "TRACE": False, "TRACEPHY": False,
                                  "NODE_INFO": False}
                    dict_state = self.MCMCTree_settings.value(name, init_state)
                    model = self.comboBox_10.model()
                    self.comboBox_10.clear()
                    for num, (item_, state) in enumerate(dict_state.items()):
                        item = QStandardItem(item_)
                        item.setCheckState(Qt.Unchecked if not state else Qt.Checked)
                        # 背景颜色
                        if num % 2 == 0:
                            item.setBackground(QColor(255, 255, 255))
                        else:
                            item.setBackground(QColor(237, 243, 254))
                        item.setToolTip(item_)
                        model.appendRow(item)
                    self.comboBox_10.setTopText()
                elif name == "comboBox_11":
                    if platform.system().lower() != "windows":
                        model = obj.model()
                        obj.clear()
                        item = QStandardItem("TN")
                        item.setToolTip("TN")
                        model.appendRow(item)
                    else:
                        model = obj.model()
                        obj.clear()
                        item = QStandardItem("POWELL")
                        item.setToolTip(item_)
                        model.appendRow(item)
                elif name == "comboBox_9":
                    index = self.MCMCTree_settings.value(name, "0")
                    if platform.system().lower() != "windows":
                        for num, i in enumerate(["LF (Langley-Fitch)",
                                                 "PL (penalized likelihood)"]):
                            model = obj.model()
                            obj.clear()
                            item = QStandardItem(i)
                            # 背景颜色
                            if num % 2 == 0:
                                item.setBackground(QColor(255, 255, 255))
                            else:
                                item.setBackground(QColor(237, 243, 254))
                            item.setToolTip(i)
                            model.appendRow(item)
                    else:
                        model = obj.model()
                        obj.clear()
                        item = QStandardItem("NPRS")
                        item.setToolTip("NPRS")
                        model.appendRow(item)
                    obj.setCurrentIndex(int(index))
                else:
                    ini_index = "2" if name=="comboBox_3" else "0"
                    allItems = [obj.itemText(i) for i in range(obj.count())]
                    index = self.MCMCTree_settings.value(name, ini_index)
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
            elif isinstance(obj, QCheckBox):
                value = self.MCMCTree_settings.value(
                    name, "no setting")  # get stored value from registry
                if value != "no setting":
                    obj.setChecked(
                        self.factory.str2bool(value))  # restore checkbox
            elif isinstance(obj, QSpinBox):
                obj.installEventFilter(self)  # 安装事件过滤器，为了取消滚轮事件
                ini_int_ = obj.value()
                int_ = self.MCMCTree_settings.value(name, ini_int_)
                obj.setValue(int(int_))
            elif isinstance(obj, QDoubleSpinBox):
                obj.installEventFilter(self)  # 安装事件过滤器，为了取消滚轮事件
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
        if self.isRunning():
            reply = QMessageBox.question(
                self,
                "Confirmation",
                "<p style='line-height:25px; height:25px'>MCMCTree is still running, terminate it?</p>",
                QMessageBox.Yes,
                QMessageBox.Cancel)
        else:
            reply = QMessageBox.Yes
        if reply == QMessageBox.Yes:
            self.on_pushButton_2_clicked(silence=True)

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
            self, "MDGUI", "log", "text Format(*.txt)")
        if fileName[0]:
            with open(fileName[0], "w", encoding="utf-8") as f:
                f.write(content)

    def get_nood_calibration(self, ete_tree):
        root = ete_tree.get_tree_root()
        root_calibration = False
        if hasattr(root, "name") and root.name:
            if re.search(r">|<|B.*\(|U.*\(|L.*\(|G.*\(|SN.*\(|ST.*", root.name):
                root_has_calibration = True
            # print(root.name)
            self.rootCal = root.name
        else:
            print("nocal")

    def generate_template(self):
        def generate_ctl(seqfile, treefile):
            # 全部换成大写，方便兼容各种情况
            self.model_value = {'AUTO': 0,
                                'JC69': 0,
                                'K80': 1,
                                'F81': 2,
                                'F84': 3,
                                'HKY': 4,
                                'T92': 5,
                                'TN93': 6,
                                'GTR': 7,
                                'UNREST': 8,
                                '12.12': 8,
                                'REVU': 9,
                                'UNRESTU': 10,
                                'CPREV10': 'cpREV10.dat',
                                'CPREV64': 'cpREV64.dat',
                                'DAYHOFF': 'dayhoff.dat',
                                'DAYHOFF-DCMUT': 'dayhoff-dcmut.dat',
                                'G1974A': 'g1974a.dat',
                                'G1974C': 'g1974c.dat',
                                'G1974P': 'g1974p.dat',
                                'G1974V': 'g1974v.dat',
                                'GRANTHAM': 'grantham.dat',
                                'JONES': 'jones.dat',
                                'JONES-DCMUT': 'jones-dcmut.dat',
                                'LG': 'lg.dat',
                                'MIYATA': 'miyata.dat',
                                'MTART': 'mtART.dat',
                                'MTMAM': 'mtmam.dat',
                                'MTREV24': 'mtREV24.dat',
                                'MTZOA': 'MtZoa.dat',
                                'WAG': 'wag.dat'}
            # self.usedata_value = {'no data': 0, 'seq like': 1, 'normal approximation': 2, 'out.BV': 3}
            seqtype_value = {'nucleotides': 0, 'codons': 1, 'AAs': 2}
            #checkpoint_value = {'save': 1, 'resume': 2, 'nothing': 0}
            cleandata_value = {'YES': 1, 'NO': 0}
            BDparas_value = {'conditional':'c', 'multiplicative':'m'}
            clock_value = {'global clock': 1, 'independent rates': 2, 'correlated rates': 3}
            print_value = {'no mcmc sample': 0, 'except branch rates': 1, 'everything': 2}
            tipdate = f"\n       TipDate = 1 100 * TipDate (1) & time unit" if self.checkBox_13.isChecked() else ""
            rootage = f"\n       RootAge = >{self.doubleSpinBox.value()}<{self.doubleSpinBox_19.value()}" if \
                self.checkBox_14.isChecked() else ""
            models = f'''\n         model = {self.model_value[self.comboBox.currentText().upper()]} *
         alpha = {self.doubleSpinBox_6.value()} *
         ncatG = {self.spinBox_21.value()} *
     cleandata = {1 if self.checkBox_15.isChecked() else 0} *
   kappa_gamma = {self.doubleSpinBox_2.value()} {self.doubleSpinBox_7.value()} *
   alpha_gamma = {self.doubleSpinBox_14.value()} {self.doubleSpinBox_15.value()} *\n''' if self.comboBox.isEnabled() \
                else ""

            self.ctl_template = f'''          seed = -1
       seqfile = {seqfile}
      treefile = {treefile}
      mcmcfile = mcmc.txt
       outfile = mcmc.out.txt
       
         ndata = 1 *
       seqtype = {seqtype_value[self.comboBox_2.currentText()]} *
       usedata = {self.comboBox_3.currentIndex()} *
         clock = {clock_value[self.comboBox_4.currentText()]} *{models}{tipdate}{rootage}
       BDparas = {self.doubleSpinBox_3.value()} {self.doubleSpinBox_4.value()} {self.doubleSpinBox_5.value()} {BDparas_value[self.comboBox_13.currentText()]}*
   
   rgene_gamma = {self.doubleSpinBox_8.value()} {self.doubleSpinBox_9.value()} {self.doubleSpinBox_10.value()} *
  sigma2_gamma = {self.doubleSpinBox_11.value()} {self.doubleSpinBox_12.value()} {self.doubleSpinBox_13.value()} *
  
         print = {print_value[self.comboBox_7.currentText()]} *
        burnin = {int((self.spinBox_19.value() *
                   self.spinBox_20.value() *
                   self.spinBox_18.value())/100)} *
      sampfreq = {self.spinBox_19.value()} *
       nsample = {self.spinBox_20.value()} *
    checkpoint = 1 {10000 / 
                    (self.spinBox_20.value() *
                     self.spinBox_19.value())} mcmctree.ckpt *
'''
            return self.ctl_template
        seqfile = os.path.basename(self.seqFileName) if self.seqFileName else ""
        treefile = "calibration_tree.nwk"
        ctl_template = generate_ctl(seqfile, treefile)
        return ctl_template

    def setWordWrap_preview(self):
        button = self.sender()
        if button.isChecked():
            button.setChecked(True)
            self.configuration_ui.textEdit.setLineWrapMode(QTextEdit.WidgetWidth)
        else:
            button.setChecked(False)
            self.configuration_ui.textEdit.setLineWrapMode(QTextEdit.NoWrap)

    def gui4Text(self):
        self.configuration_dialog = QtWidgets.QDialog(self)
        self.configuration_ui = self.Ui_configuration()
        self.configuration_ui.setupUi(self.configuration_dialog)
        self.configuration_ui.toolButton.clicked.connect(self.setWordWrap_preview)
        self.configuration_ui.toolButton.setChecked(True)
        templtate = self.prepare_for_run_r8s() if self.tabWidgetMCMC.tabText(self.tabWidgetMCMC.currentIndex()) == "r8s" \
            else self.generate_template()
        self.configuration_ui.textEdit.setPlainText(templtate)
        self.configuration_ui.pushButton.clicked.connect(lambda : [self.on_pushButton_6_clicked(),
                                                                   self.on_textChanged_run(),
                                                                   self.configuration_dialog.close()]) # 待改进
        self.configuration_ui.pushButton_2.clicked.connect(self.configuration_dialog.close)
        self.configuration_dialog.setWindowFlags(
            self.configuration_dialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.configuration_dialog.show()

    # def ctrlUsedata(self):
    #     if self.comboBox_3.currentText() == 'approximate likelihood FAST':
    #         for i in [self.label_11, self.comboBox, self.label_26, self.comboBox_5,
    #                   self.label_18, self.spinBox_8, self.spinBox_9,
    #                   self.label_19, self.spinBox_10, self.spinBox_11,
    #                   self.label_16, self.spinBox_21, self.label_15, self.doubleSpinBox_6]:
    #             i.setEnabled(False)
    #     elif self.comboBox_3.currentText() == 'out.BV (in.BV)':
    #         for i in [self.label_11, self.comboBox, self.label_26, self.comboBox_5]:
    #             i.setEnabled(True)
    #         for n in [self.label_18, self.spinBox_8, self.spinBox_9,
    #                   self.label_19, self.spinBox_10, self.spinBox_11,
    #                   self.label_16, self.spinBox_21, self.label_15, self.doubleSpinBox_6]:
    #             n.setEnabled(False)
    #     elif (self.comboBox_3.currentText() == 'no data (prior)' or
    #           self.comboBox_3.currentText() == 'seq like (exact likelihood) SLOW'):
    #         for i in [self.label_11, self.comboBox, self.label_26, self.comboBox_5,
    #                   self.label_18, self.spinBox_8, self.spinBox_9,
    #                   self.label_19, self.spinBox_10, self.spinBox_11,
    #                   self.label_16, self.spinBox_21, self.label_15, self.doubleSpinBox_6]:
    #             i.setEnabled(True)

    '''def ctrlITOL(self):
        if not self.checkBox6.isChecked():
            for i in [self.checkBox, self.checkBox_2, self.checkBox_3,
                      self.checkBox_4, self.checkBox_5]:
                i.setEnabled(False)
        else:
            for i in [self.checkBox, self.checkBox_2, self.checkBox_3,
                      self.checkBox_4, self.checkBox_5]:
                i.setEnabled(True)'''

    def on_textChanged_run(self, rerun=False):
        # 当文本编辑框文本更改
        self.temporary_text = self.configuration_ui.textEdit.toPlainText()
        if self.tabWidgetMCMC.tabText(self.tabWidgetMCMC.currentIndex()) == "r8s":
            # 有数据才执行
            self.interrupt = False  # 如果是终止以后重新运行要刷新
            self.textEdit_log.clear()  # 清空log
            self.error_has_shown = False
            if platform.system().lower() != "windows":
                self.list_pids = []
                self.queue = multiprocessing.Queue() if platform.system().lower() == "windows" else multiprocessing.Manager().Queue()
                self.pool = multiprocessing.get_context("spawn").Pool(
                    processes=1, initializer=pool_init, initargs=(self.queue,)
                )
                # Check for progress periodically
                self.timer = QTimer()
                self.timer.timeout.connect(self.updateProcess)
                self.timer.start(1)
            self.worker = WorkThread(lambda : self.run_command_r8s(cfg=self.temporary_text), parent=self)
            self.worker.start()
            # self.on_pushButton_6_clicked()
        else:
            # 这一步需要调整，可以到最后报错的时候来检查看是不是不一致
            self.chains = int(self.comboBox_8.currentText())  #  self.spinBox.value()
            self.exe_repeat = self.checkBox_11.isChecked()
            is_consist = self.consistency_checking()
            if is_consist:
                # 有数据才执行
                self.interrupt = False  # 如果是终止以后重新运行要刷新
                self.textEdit_log.clear()  # 清空log
                self.error_has_shown = False
                self.list_pids = []
                self.queue = multiprocessing.Queue() if platform.system().lower() == "windows" else multiprocessing.Manager().Queue()
                if self.exe_repeat:
                    if self.chains%2==0:
                        threads = self.chains
                    else:
                        threads = self.chains-1
                else:
                    threads = self.chains
                self.pool = multiprocessing.get_context("spawn").Pool(
                    processes=threads, initializer=pool_init, initargs=(self.queue,)
                )
                # Check for progress periodically
                self.timer = QTimer()
                self.timer.timeout.connect(self.updateProcess)
                self.timer.start(1)
                self.worker = WorkThread(lambda : self.run_command(rerun=rerun), parent=self)
                self.worker.start()
                self.on_pushButton_6_clicked()

    def gui4Log(self):
        dialog = QDialog(self)
        dialog.resize(1200, 700)
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
        toolButton.setChecked(False)
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
        self.textEdit_log.setLineWrapMode(QTextEdit.NoWrap)
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

    def ctl_generater(self, file_path=None, treefile=None, seed=None):
        if file_path:
            if hasattr(self, "temporary_text"):
                mcmctree_ctl = self.temporary_text
            else:
                mcmctree_ctl = self.generate_template()
            if seed is not None:
                # 修改种子值
                mcmctree_ctl = re.sub(r"(?m)^\s*seed\s*=\s*-?\d+.*", f"          seed = {seed}", mcmctree_ctl)
            with open(file_path, "w", errors="ignore") as f:
                f.write(mcmctree_ctl)
        else:
            options = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
            directory = QFileDialog.getExistingDirectory(self, "Choose folder", options=options)
            if directory:
                if hasattr(self, "temporary_text"):
                    mcmctree_ctl = self.temporary_text
                else:
                    mcmctree_ctl = self.generate_template()
                file_path = f"{directory}{os.sep}mcmctree.ctl"
                if os.path.exists(file_path):
                    reply = QMessageBox.question(self, "File Exists", f"The file {file_path} already exists. Do you want to overwrite it？",
                                                 QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        if seed is not None:
                            # 修改种子值
                            mcmctree_ctl = re.sub(r"(?m)^\s*seed\s*=\s*-?\d+.*", f"          seed = {seed}", mcmctree_ctl)
                        with open(file_path, "w", errors="ignore") as f:
                            f.write(mcmctree_ctl)
                        QMessageBox.information(self, "File Created", "The file has been created successfully.")
                else:
                    if seed is not None:
                        # print(seed)
                        # 修改种子值
                        mcmctree_ctl = re.sub(r"(?m)^\s*seed\s*=\s*-?\d+.*", f"          seed = {seed}", mcmctree_ctl)
                        # print(mcmctree_ctl)
                    with open(file_path, "w", errors="ignore") as f:
                        f.write(mcmctree_ctl)

    def auto_checkpoint(self, ctl_file, resume=False):
        # with open(ctl_file, errors="ignore") as f:
        #     ctl_content = f.read()
        # sampfreq = int(re.search(r"(?i)sampfreq\s*=\s*(\d+)", ctl_content).group(1)) if (
        #     re.search(r"(?i)sampfreq\s*=\s*(\d+)", ctl_content)) else None
        # nsample = int(re.search(r"(?i)nsample\s*=\s*(\d+)", ctl_content).group(1)) if (
        #     re.search(r"(?i)nsample\s*=\s*(\d+)", ctl_content)) else None
        sampfreq = self.fetchCTLvalue(ctl_file, r"(?i)sampfreq\s*=\s*(\d+)")
        nsample = self.fetchCTLvalue(ctl_file, r"(?i)nsample\s*=\s*(\d+)")
        if sampfreq and nsample:
            sampfreq = float(sampfreq)
            nsample = float(nsample)
            prob = 10000 / (nsample * sampfreq)
            rep_ = r"checkpoint = \1 %s \3"%prob if not resume else r"checkpoint = 2 %s \3"%prob
            self.replace_ctl(ctl_file,
                             r"(?i)checkpoint\s*=\s*(\d+)\s*(\S+)\s*(\S+)",
                             rep_
                             )

    def prepare_for_run(self, fold_suffix=None, seed=-1):
        # MF线程选择
        self.mf_threads = " -nt %s" % self.comboBox_8.currentText()
        self.burin_prop = self.spinBox_18.value() / 100
        runPath = self.factory.creat_dirs(f"{self.exportPath}{os.sep}{fold_suffix}")
        # self.refresh_analysis(exportPath)
        shutil.copy(self.seqFileName, runPath + os.sep + os.path.basename(self.seqFileName))
        species_count = len(self.tree_with_tipdate)
        species_tree = f"{species_count} 1"
        treefile = f"{runPath}{os.sep}calibration_tree.nwk"
        tre_text = self.handle_tree_text(self.tree_with_tipdate)
        # print(self.tree_with_tipdate.name)
        # print("Tree:", self.tree_with_tipdate.get_ascii(show_internal=True))
        # print("Tree text:", tre_text)
        # 在树里面设置的rootage，write另存的时候会丢失，这里补齐
        calibrate_tree_text = re.sub(r"\)\s*;", f"){self.tree_with_tipdate.name};", tre_text)
        self.use_data = self.comboBox_3.currentText()
        self.gamma_num = self.spinBox_21.value()
        self.gamma_alpha = self.doubleSpinBox_6.value()
        self.model = self.comboBox.currentText()
        self.MF_path = self.factory.programIsValid("iq-tree", mode="tool")
        self.dict_args["MF_path"] = self.MF_path
        with open(treefile, "w", errors="ignore") as f:
            f.write(f"{species_tree}\n{calibrate_tree_text}")
        ctl_file = f"{runPath}{os.sep}mcmctree.ctl"
        self.ctl_generater(ctl_file, treefile=treefile, seed=seed)
        # self.replace_ctl(ctl_file,r"seed\s*=\s*-?\d+",
        #                  f"seed = {seed}")
        cmds = f"{self.mcmctreeEXE} {ctl_file}"
        # self.replace_ctl(ctl_file,r"seed\s*=\s*-?\d+",
        #                  f"seed = {seed}")
        self.dict_args["model"] = self.model if self.comboBox.isEnabled() else "IQ-AUTO"
        self.dict_args["dict_seq"] = self.dict_seq
        self.dict_args["seq_type"] = self.seq_type
        self.dict_args["mf_threads"] = self.mf_threads
        # self.dict_args["run_code"] = self.run_code
        # self.dict_args["MF2PAML"] = self.MF2PAML
        self.dict_args["gamma_num"] = self.gamma_num
        self.dict_args["gamma_alpha"] = self.gamma_alpha
        self.dict_args["model_value"] = self.model_value
        # self.dict_args["replace_ctl"] = self.replace_ctl
        # self.dict_args["change_ctl_gamma"] = self.change_ctl_gamma
        self.dict_args["use_data"] = self.use_data
        self.dict_args["mcmctreeEXE"] = self.mcmctreeEXE
        self.dict_args["hessian_program"] = self.comboBox_14.currentText().split()[0]
        self.dict_args["mix_models"] = self.checkBox_12.isChecked()
        self.dict_args["calibrate_tree_text"] = calibrate_tree_text
        # 设置checkpoint
        self.auto_checkpoint(ctl_file)
        return cmds, runPath, ctl_file

    def prepare_for_run_r8s(self, file=None):
        self.batch_process = self.checkBox_10.isChecked()
        tre_text, mrca, cal, con, fix, unfix = self.handle_r8s_tree()
        list_cmd_lines = ["#nexus\n"]
        # trees
        list_cmd_lines.append(f"begin trees;\ntree tre_for_r8s = {tre_text}\nend;\n\nbegin r8s;\n\n")
        # mrca+age
        if mrca:
            list_cmd_lines.append(mrca+"\n")
        if cal and (platform.system().lower() != "windows"):
            list_cmd_lines.append(cal+"\n")
        if con:
            list_cmd_lines.append(con+"\n")
        if fix:
            list_cmd_lines.append(fix+"\n")
        if unfix:
            list_cmd_lines.append(unfix+"\n")
        # blformat
        lengths = self.comboBox_6.currentText().split()[0]
        if not hasattr(self, "dict_seq"):
            parsefmt = Parsefmt()
            self.dict_seq = parsefmt.readfile(self.seqFileName)
        nsites = len(self.dict_seq.popitem()[1])
        list_cmd_lines.append(f"BLFORMAT lengths={lengths} nsites={nsites} "
                              f"ultrametric={'yes' if self.checkBox.isChecked() else 'no'} "
                              f"round={'yes' if self.checkBox_2.isChecked() else 'no'};\n")
        # describe
        plots = ";\n".join([f"DESCRIBE plot={self.comboBox_10.itemText(i)}" for i in range(self.comboBox_10.count())
                            if self.comboBox_10.model().item(i).checkState()==Qt.Checked]) + ";\n"
        list_cmd_lines.append(plots)
        # divtime
        self.r8s_method = self.comboBox_9.currentText().split()[0]
        self.r8s_algorithm = self.comboBox_11.currentText()
        cvnum_cmd = f"cvnum={self.spinBox_2.value()} " if self.spinBox_2.isVisible() else ''
        confidence_cmd = f"confidence={'yes' if self.checkBox_5.isChecked() else 'no'} " if self.checkBox_5.isVisible() else ''
        fossilconstrained_cmd = f"fossilconstrained={'yes' if self.checkBox_7.isChecked() else 'no'} " if self.checkBox_7.isVisible() else ''
        fossilfixed_cmd = f"fossilfixed={'yes' if self.checkBox_8.isChecked() else 'no'} " if self.checkBox_8.isVisible() else ''
        crossv_cmd = f"crossv={'yes' if self.checkBox_6.isChecked() else 'no'}" if self.checkBox_6.isVisible() else ''
        list_cmd_lines.append(f"DIVTIME method={self.r8s_method} algorithm={self.r8s_algorithm} "
                              f"{cvnum_cmd}"
                              f"{confidence_cmd}"
                              f"{fossilconstrained_cmd}"
                              f"{fossilfixed_cmd}"
                              f"{crossv_cmd}"
                              f";\n")
        # collapse
        if self.checkBox_4.isChecked():
            list_cmd_lines.append(f"COLLAPSE;\n")
        # cleartrees
        if self.checkBox_3.isChecked() and self.checkBox_3.isChecked():
            list_cmd_lines.append(f"CLEARTREES;\n")
        # shownamed
        if self.checkBox_9.isChecked() and self.checkBox_9.isChecked():
            list_cmd_lines.append(f"SHOWNAMED;\n")
        # set
        self.label_37.setVisible(False)
        # new
        rate_cmd = f"rates={self.comboBox_12.currentText()} " if self.comboBox_12.isVisible() else ""
        shape_cmd = f"shape={self.doubleSpinBox_16.value()} " if self.doubleSpinBox_16.isVisible() else ""
        smoothing_cmd = f"smoothing={self.doubleSpinBox_17.value()} " if self.doubleSpinBox_17.isVisible() else ""
        list_cmd_lines.append(f"SET {rate_cmd}"
                              f"{shape_cmd}"
                              f"{smoothing_cmd}"
                              f"num_time_guesses={self.doubleSpinBox_18.value()}"
                              f";\n")
        # end
        list_cmd_lines.append("\n\nend;")
        data_cmd = "".join(list_cmd_lines)
        if file:
            with open(file, "w", errors="ignore") as f:
                f.write(data_cmd)
        return data_cmd

    def handle_r8s_tree(self):
        '''
        读取r8s树，用于设置mrca、calibrate、constrain、fixage、unfixage
        4种标记方式，标记在树的内部节点上面：
            cal[age]
            con[minage~maxage]
            fix[age]
            unfix[age]
        Parameters
        ----------
        tree

        Returns
        -------

        '''
        mrca_lines = []
        cal_lines = []
        con_lines = []
        fix_lines = []
        unfix_lines = []
        for node in self.tree_with_tipdate.traverse():
            if node.is_leaf():
                continue
            if node.name.startswith("cal"):
                if re.search(r"cal\[(\d+\.?\d*)\]", node.name):
                    age = re.search(r"cal\[(\d+.?\d*)\]", node.name).group(1)
                    mrca_name = f"mrca{len(mrca_lines)+1}"
                    mrca_lines.append(f"MRCA {mrca_name} {' '.join(node.get_leaf_names())};")
                    cal_lines.append(f"CALIBRATE taxon={mrca_name} age={age};")
            elif node.name.startswith("con"):
                if re.search(r"con\[(\d*\.?\d*)\~(\d*\.?\d*)\]", node.name):
                    minage, maxage = re.search(r"con\[(\d*\.?\d*)\~(\d*\.?\d*)\]", node.name).groups()
                    mrca_name = f"mrca{len(mrca_lines)+1}"
                    mrca_lines.append(f"MRCA {mrca_name} {' '.join(node.get_leaf_names())};")
                    if minage:
                        con_lines.append(f"CONSTRAIN taxon={mrca_name} min_age={minage};")
                    if maxage:
                        con_lines.append(f"CONSTRAIN taxon={mrca_name} max_age={maxage};")
            elif node.name.startswith("fix"):
                if re.search(r"fix\[(\d+\.?\d*)\]", node.name):
                    age = re.search(r"fix\[(\d+.?\d*)\]", node.name).group(1)
                    mrca_name = f"mrca{len(mrca_lines)+1}"
                    mrca_lines.append(f"MRCA {mrca_name} {' '.join(node.get_leaf_names())};")
                    fix_lines.append(f"FIXAGE taxon={mrca_name} age={age};")
            elif node.name.startswith("unfix"):
                if re.search(r"unfix\[(\d+\.?\d*)\]", node.name):
                    age = re.search(r"unfix\[(\d+.?\d*)\]", node.name).group(1)
                    mrca_name = f"mrca{len(mrca_lines)+1}"
                    mrca_lines.append(f"MRCA {mrca_name} {' '.join(node.get_leaf_names())};")
                    unfix_lines.append(f"UNFIXAGE taxon={mrca_name} age={age};")
        return self.tree_with_tipdate.write(format=5), "\n".join(mrca_lines), "\n".join(cal_lines), \
                "\n".join(con_lines), "\n".join(fix_lines), "\n".join(unfix_lines)

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
                if file_f:
                    self.input(file_f, which=which)
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

        if (isinstance(obj, QDoubleSpinBox) or isinstance(obj, QSpinBox) or isinstance(obj, QComboBox)) and event.type()==QEvent.Wheel:
            return True  # 过滤掉滚轮事件

        # return QMainWindow.eventFilter(self, obj, event) #
        # 其他情况会返回系统默认的事件处理方法。
        return super(MCMCTree, self).eventFilter(obj, event)  # 0

    def isRunning(self):
        '''判断程序是否运行,依赖进程是否存在来判断'''
        return hasattr(self, "pool") and self.pool and not self.interrupt

    def addText2Log(self, text):
        if re.search(r"\w+", text):
            self.textEdit_log.append(text)
            with open(self.exportPath + os.sep + "PhyloSuite_MCMCTREE.log", "a", errors='ignore') as f:
                f.write(text + "\n")

    # def calibration_tree(self):
    #     if self.exportPath:
    #         file_path = os.path.join(self.exportPath, 'Figtree.tre')
    #         if os.path.isfile(file_path):
    #             mtre = toytree.tree(file_path)
    #             tv = treeview.TreeViewer(tree='tree.newick', meta='meta.csv')
    #         else:
    #             QMessageBox.warning(self, "No file", "There is no Figtree.tre file!")
    #             return False

    def popupException(self, exception):
        msg = QMessageBox(self)
        if hasattr(self, "progressDialog"):
            self.progressDialog.close()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(
            'The program encountered an unforeseen problem, please report the bug at <a href="https://github.com/dongzhang0725/PhyloSuite/issues">https://github.com/dongzhang0725/PhyloSuite/issues</a> or send an email with the detailed traceback to dongzhang0725@gmail.com')
        msg.setWindowTitle("Error")
        msg.setDetailedText(exception)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

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

    def clear_lineEdit(self):
        sender = self.sender()
        lineEdit = sender.parent()
        lineEdit.setText("")
        lineEdit.setToolTip("")

    def popupAutoDec(self, init=False):
        self.init = init
        self.factory.popUpAutoDetect(
            "MDGUI", self.workPath, self.auto_popSig, self)

    def chooseConvergenceFoler(self):
        self.resultsPath = self.workPath + os.sep + "MDGUI_results"
        folder_list = [f for f in os.listdir(self.resultsPath) if os.path.isdir(os.path.join(self.resultsPath, f))]
        self.convergenceFolerGui(folder_list)

    def convergenceFolerGui(self, folder_list):
        self.convergence_dialog = QDialog(self)
        self.convergence_dialog.setWindowTitle("Choose Folder")
        self.gridLayout = QGridLayout(self.convergence_dialog)
        self.horizontalLayout = QHBoxLayout()
        self.label = QLabel("Available inputs prepared for convergence checking in workplace:", self.convergence_dialog)
        self.horizontalLayout.addWidget(self.label)
        spacerItem = QSpacerItem(153, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 2)
        qss = '''QListView::item{height:30px;}
            QListView::item{background:white;}
            QListView::item:hover{background: #E5F3FF;}
            QListView::item:selected:active{background: #CDE8FF;}'''  # 灰色：#F2F2F2，#EBEBEB
        self.listWidget_framless = QListWidget(self.convergence_dialog)
        self.listWidget_framless.setSelectionMode(QListWidget.MultiSelection)  # 允许多选
        self.listWidget_framless.setStyleSheet(qss)
        self.gridLayout.addWidget(self.listWidget_framless, 1, 0, 1, 2)

        self.item_to_path = {}  # 存储项到路径的映射
        folder_icon = QIcon(":/picture/resourses/folder.png")
        # 反转folder_list
        for index, folder_path in enumerate(reversed(folder_list)):
            folder_name = os.path.basename(folder_path)
            item = QListWidgetItem(folder_name)
            item.setIcon(folder_icon)
            if index % 2 == 0:
                item.setBackground(QColor("#F0F0F0"))
            else:
                item.setBackground(QColor("#FFFFFF"))
            self.listWidget_framless.addItem(item)
            self.item_to_path[item.text()] = folder_path

        self.pushButton = QPushButton("Ok", self.convergence_dialog)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/btn_ok.png"), QIcon.Normal, QIcon.Off)
        self.pushButton.setIcon(icon)
        self.gridLayout.addWidget(self.pushButton, 2, 0, 1, 1)
        self.pushButton.setEnabled(False)  # 初始状态下禁用OK按钮
        self.pushButton_2 = QPushButton("No, thanks", self.convergence_dialog)
        icon1 = QIcon()
        icon1.addPixmap(QPixmap(":/picture/resourses/btn_close.png"), QIcon.Normal, QIcon.Off)
        self.pushButton_2.setIcon(icon1)
        self.gridLayout.addWidget(self.pushButton_2, 2, 1, 1, 1)
        self.pushButton.clicked.connect(self.onOkClicked)
        self.pushButton_2.clicked.connect(self.convergence_dialog.close)
        self.listWidget_framless.itemSelectionChanged.connect(self.updateOkButtonState)
        self.convergence_dialog.exec_()
        # self.convergence_dialog.show()

    def updateOkButtonState(self):
        selected_items = self.listWidget_framless.selectedItems()
        if len(selected_items) > 2:
            # 取消之前的选择，使总数不超过两个
            self.listWidget_framless.blockSignals(True)
            while len(selected_items) > 2:
                item = selected_items.pop(0)
                item.setSelected(False)
            self.listWidget_framless.blockSignals(False)
        self.pushButton.setEnabled(len(selected_items) == 2)

    def onOkClicked(self):
        selected_items = self.listWidget_framless.selectedItems()

        if len(selected_items) != 2:
            QMessageBox.warning(self, "Warning", "请选择两个文件夹")
            return
        # 绝对路径
        selected_paths = [
            os.path.join(self.resultsPath, item.text()).replace("\\", "/")
            for item in selected_items
        ]
        # print("Selected paths:", selected_paths)
        mcmc_data1 = []
        mcmc_data2 = []
        # 获取每个文件夹中mcmc.out.txt路径
        mcmc_files = [os.path.join(folder, "mcmc.out.txt").replace("\\", "/") for folder in selected_paths]
        # print("Seed files:", mcmc_files)
        for index, mcmc_file in enumerate(mcmc_files):
            # print(f"Checking existence of: {mcmc_file}")
            if os.path.exists(mcmc_file):
                with open(mcmc_file, 'r') as file:
                    seed_content = file.read()
                    pattern = r"Posterior mean.*?\nt_n\d+\s+([\d.]+)\s+\(\s*([\d.]+)\s*,\s*([\d.]+)\s*\)\s+\(\s*([\d.]+)\s*,\s*([\d.]+)\s*\)"
                    matches = re.search(pattern, seed_content, re.DOTALL)
                    if matches:
                        numbers = matches.groups()
                        # print(f"Matched numbers from {mcmc_file}: {numbers}")
                        if index == 0:
                            mcmc_data1.extend(map(float, numbers))
                        elif index == 1:
                            mcmc_data2.extend(map(float, numbers))

                        # self.draw_convergence(mcmc_data1, mcmc_data2)
            else:
                print(f"mcmc.out.txt is not exist or fragmentary!")
        mcmc_data1 = sorted(mcmc_data1)
        mcmc_data2 = sorted(mcmc_data2)
        self.draw_convergence(mcmc_data1, mcmc_data2)

    def readSeedFiles(self, seed_files):
        seed_contents = []
        for seed_file in seed_files:
            if os.path.exists(seed_file):
                with open(seed_file, 'r') as file:
                    seed_contents.append(file.read())
            else:
                QMessageBox.warning(self, "Warning", f"文件 {seed_file} 不存在")
        return seed_contents

    def draw_convergence(self, data1, data2):
        dialog = QDialog()
        dialog.setWindowTitle('Convergence check')
        figure = plt.figure()
        canvas = FigureCanvas(figure)
        layout = QVBoxLayout()
        layout.addWidget(canvas)
        dialog.setLayout(layout)
        # 轴对象
        ax = figure.add_subplot(111)
        ax.scatter(data1, data2)
        ax.plot([0, 1], [0, 1], transform=ax.transAxes, color='black')
        ax.set_xlabel('Posterior mean times from run 1')
        ax.set_ylabel('Posterior mean times from run 2')
        canvas.draw_idle()
        dialog.exec_()
        # fig = plt.figure()
        # fig.canvas.manager.set_window_title('Convergence check')
        # # 散点图
        # plt.scatter(data1, data2)
        # # 对角线
        # plt.plot([0, 1], [0, 1], transform=plt.gca().transAxes, color='black')
        # plt.xlabel('Posterior mean times from run 1')
        # plt.ylabel('Posterior mean times from run 2')
        # plt.show()

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
            autoPartFindPath = widget.autoInputs
            if autoPartFindPath:
                trees, msa = autoPartFindPath
                if msa:
                    self.progressDialog = self.factory.myProgressDialog(
                        "Please Wait", "Converting format...", busy=True, parent=self)
                    self.progressDialog.show()
                    self.convertfmt = Convertfmt(**{"export_path": os.path.dirname(msa[0]), "files": [msa[0]],
                                                    "export_paml": True,
                                                    "exception_signal": self.exception_signal})
                    gbWorker = WorkThread(
                        lambda: self.convertfmt.exec_(),
                        parent=self)
                    gbWorker.finished.connect(
                        lambda: [self.progressDialog.close(), self.input(self.convertfmt.f4, 3)])
                    gbWorker.start()
                if trees:
                    self.input(trees[0], 4)

    def popup_log_exception(self, text):
        if text == "multifurcating":
            self.handle_multifurcating()
        else:
            QMessageBox.critical(
                self,
                "MDGUI",
                "<p style='line-height:25px; height:25px'>%s</p>" % text)
            if "Show log" in text:
                self.on_pushButton_6_clicked()
        self.startButtonStatusSig.emit(
            [
                self.pushButton_5,
                self.progressBar,
                "except",
                self.exportPath,
                self.qss_file,
                self])

    def handle_multifurcating(self):
        if hasattr(self, "multifurcating_box") and self.multifurcating_box.isVisible():
            return
        self.multifurcating_box = QMessageBox(self)
        self.multifurcating_box.setIcon(QMessageBox.Question)
        self.multifurcating_box.setWindowTitle('MCMCTREE!')
        self.multifurcating_box.setText("<p style='line-height:25px; height:25px'>Multifurcating tree found! There are two options:<br>"
                    "1. If you forgot to root the tree, you can choose \""
                    "<span style='font-weight:600; color:#ff0000;'>Root the tree</span>\" button, "
                    "right click the node that you want to root, then select \"Set as outgroup\". <br>"
                    "2. If you want to resolve the multifurcation, and rerun MCMCTREE, you "
                    "can select \"<span style='font-weight:600; color:#ff0000;'>Resolve and rerun</span>\" button "
                    "to direct PhyloSuite to use the \"resolve_polytomy\" function of ETE3.</p>")
        self.multifurcating_box.setStandardButtons(QMessageBox.Yes|QMessageBox.Close|QMessageBox.Reset)
        buttonY = self.multifurcating_box.button(QMessageBox.Yes)
        buttonY.setText('Resolve and rerun')
        buttonR = self.multifurcating_box.button(QMessageBox.Reset)
        buttonR.setText('Root the tree')
        self.multifurcating_box.resize(1000, 800)
        self.multifurcating_box.exec_()
        if self.multifurcating_box.clickedButton() == buttonY:
            # self.on_pushButton_2_clicked(silence=True)
            self.factory.remove_dir_directly(self.exportPath)
            self.tree_with_tipdate.resolve_polytomy()
            self.on_pushButton_5_clicked(rerun=True)
        elif self.multifurcating_box.clickedButton() == buttonR:
            self.on_pushButton_clicked()

    def handle_tree_text(self, ete_tree, mode="generate"):
        for node in ete_tree.traverse():
            if not node.is_leaf():
                if 'name' in node.features:
                    node_bound = re.search(r">|<|B.*\(|U.*\(|L.*\(|G.*\(|SN.*\(|ST.*\(|cal.*\[|con.*\[|fix.*\[|unfix.*\[", node.name)
                    if node_bound:
                        if re.search(r"cal.*\[|con.*\[|fix.*\[|unfix.*\[", node_bound.group(0)):
                            pass
                        else:
                            if not node.name.startswith("'"):
                                node.name = f"'{node.name}"
                            if not node.name.endswith("'"):
                                node.name = f"{node.name}'"
                        if mode == "calibration":
                            text = node.name
                            # 避免重复添加face
                            setattr(node.faces, "branch-top", {})
                            node.add_face(TextFace(text), column=0, position="branch-top")
                    else:
                        # 删掉除校准点以外的节点名字，保持树纯净
                        node.name = ''

        return ete_tree.write(format=8, no_replace=True).replace("NoName", "") if mode=="generate" else ete_tree

    def judgeIQTREEinstalled(self, text):
        flag = False
        if self.sender() == self.comboBox:
            if text == "AUTO":
                flag = True
        if self.sender() == self.comboBox_14:
            if text.startswith("IQ-TREE"):
                flag = True
        if flag:
            IQpath = self.factory.programIsValid("iq-tree", mode="tool")
            if not IQpath:
                reply = QMessageBox.information(
                    self,
                    "Information",
                    "<p style='line-height:25px; height:25px'>Please install IQ-TREE "
                    "<span style='font-weight:600; color:#ff0000;'>v3</span> (for model selection and "
                    "generation of Hessian matrix) first!</p>",
                    QMessageBox.Ok,
                    QMessageBox.Cancel)
                if reply == QMessageBox.Ok:
                    self.setting = Setting(self.parent)
                    self.setting.display_table(self.setting.listWidget.item(1))
                    # 隐藏？按钮
                    self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
                    self.setting.exec_()
            elif self.sender() == self.comboBox_14:
                self.IQworker = WorkThread(lambda : self.judgeIQversion_slot(IQpath), parent=self)
                self.IQworker.finished.connect(self.judgeIQversion)
                self.IQworker.start()

    def judgeIQversion_slot(self, IQpath):
        self.IQversion = self.factory.get_version("IQ-TREE", parent=self, mode=IQpath)

    def judgeIQversion(self):
        if not self.IQversion.startswith("3"):
            QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>IQ-TREE "
                "<span style='font-weight:600; color:#ff0000;'>v3</span> is mandatory for "
                "generation of Hessian matrix! Please reinstall IQ-TREE v3.x!</p>",
                QMessageBox.Ok)
            self.comboBox_14.setCurrentIndex(1)
            self.ctl_models(1)

    def replace_ctl(self, ctl_file, rgx_old, new):
        with open(ctl_file, errors='ignore') as f:
            ctl_content = f.read()
        with open(ctl_file, "w", errors='ignore') as f:
            f.write(re.sub(rgx_old, new, ctl_content, re.I))

    def MF2PAML(self, mf_model):
        '''
        将modelfinder选出来的最优模型替换为PAML支持的模型名字
        Returns
        -------

        '''
        dict_ = {"12.12": "UNREST",
                 "DCMut": "dayhoff-dcmut",
                 "JTT": "jones",
                 "JTTDCMut": "jones-dcmut",
                 "mtREV": "mtREV24"}
        return dict_[mf_model] if mf_model in dict_ else mf_model

    def change_ctl_gamma(self, gamma_num, gamma_alpha):
        if gamma_num:
            self.replace_ctl(self.ctl_file,
                             r"ncatG\s*=\s*\d+",
                             f"ncatG = {gamma_num}")
            self.replace_ctl(self.ctl_file,
                             r"alpha\s*=\s*\d+\.?\d*",
                             f"alpha = {gamma_alpha}")
        else:
            # 没有gamma
            self.replace_ctl(self.ctl_file,
                             r"(?m)^\s+ncatG\s*=\s*\d+.*$",
                             f"")
            self.replace_ctl(self.ctl_file,
                             r"alpha\s*=\s*\d+\.?\d*",
                             f"alpha = 0")

    def fetchCTLvalue(self, ctl_file, rgx):
        '''
        Parameters
        ----------
        ctl_file
        rgx：如 r"usedata\s*=\s*(\d+)"

        Returns
        -------

        '''
        with open(ctl_file, errors='ignore') as f:
            ctl_content = f.read()
        return re.search(rgx, ctl_content).group(1) if re.search(rgx, ctl_content) else None

    def count_mcmc_sample(self, filename):
        '''
        实测最高效的方法：https://gist.github.com/zed/0ac760859e614cd03652
        Parameters
        ----------
        filename

        Returns
        -------

        '''
        with open(filename) as f:
            for line_number, _ in enumerate(f):
                pass
        return line_number

    def count_sample(self, path):
        mcmc_ = f"{path}{os.sep}mcmc.txt"
        mcmc_pre = f"{path}{os.sep}mcmc_pre.txt"
        if not os.path.exists(mcmc_):
            return
        sample = self.count_mcmc_sample(mcmc_pre) if os.path.exists(mcmc_pre) else 0
        return sample + self.count_mcmc_sample(mcmc_)

    def havePreviousRun(self, path=None):
        if not path:
            return None
        # have_ckp, have_mcmc = False, False
        runPaths = glob.glob(f"{path}{os.sep}repeat*{os.sep}run*")
        if not runPaths:
            runPaths = glob.glob(f"{path}{os.sep}run*")
        if not runPaths:
            return None
        have_ckp = glob.glob(f"{runPaths[0]}{os.sep}*.CKPT")
        have_mcmc = (glob.glob(f"{runPaths[0]}{os.sep}mcmc.txt") +
                     glob.glob(f"{runPaths[0]}{os.sep}mcmc_pre*.txt"))
        return runPaths if (have_ckp and have_mcmc) else None

    def mcmc_addition(self, path):
        list_names = glob.glob(f"{path}{os.sep}mcmc_pre*.txt")
        list_names = [os.path.basename(i).rstrip(".txt") for i in list_names]
        suffix = "_pre"
        new_name, list_names = self.factory.numbered_Name(list_names,
                                                          "mcmc",
                                                          omit=False,
                                                          suffix=suffix)
        pre_mcmc = f"{path}{os.sep}{new_name}.txt"
        mcmc = f"{path}{os.sep}mcmc.txt"
        if not os.path.exists(mcmc):
            return
        # if os.path.exists(pre_mcmc):
        #     with open(mcmc, errors="ignore") as f:
        #         mcmc_content = f.readlines()
        #     mcmc_content = re.sub(r"^[^\n]+?\n", "", mcmc_content)
        #     with open(pre_mcmc, "a", errors="ignore") as f:
        #         f.write(mcmc_content)
        else:
            os.rename(mcmc, pre_mcmc)

    # def burin(self, list_lines, prop):
    #     # 不用自己burin，mcmctree会在跑的时候自己burin掉不要的sample，也就是存到文件里面的sample都是burin后的
    #     total_len = len(list_lines)
    #     burin_lines = int(total_len * prop)
    #     list_new = list_lines[burin_lines: ]
    #     list_new.insert(0, list_lines[0])
    #     return list_new

    def mcmc_agg(self, path, filename="mcmc_for_sum.txt"):
        list_pre_mcmc = glob.glob(f"{path}{os.sep}mcmc_pre*.txt")
        mcmc = f"{path}{os.sep}mcmc.txt"
        list_all_mcmc = []
        def drop_incomplete(list_lines):
            ncol = list_lines[0].count("\t")
            while list_lines[-1].count("\t") < ncol:
                list_lines.pop()
            return list_lines
        for num, pre_mcmc in enumerate(list_pre_mcmc):
            with open(pre_mcmc, errors="ignore") as f:
                # mcmc_content = f.read().rstrip("\n")
                list_lines = f.readlines()
                if list_lines:
                    list_lines = drop_incomplete(list_lines)
                else:
                    continue
            if num != 0:
                # mcmc_content = re.sub(r"^[^\n]+?\n", "", mcmc_content)
                list_lines = list_lines[1:]
            list_all_mcmc.extend(list_lines)
        if os.path.exists(mcmc):
            with open(mcmc, errors="ignore") as f:
                # mcmc_content = f.read()
                list_lines = f.readlines()
                if list_lines:
                    list_lines = drop_incomplete(list_lines)
            if list_pre_mcmc:
                # mcmc_content = re.sub(r"^[^\n]+?\n", "", mcmc_content)
                if list_lines:
                    list_lines = list_lines[1:]
            list_all_mcmc.extend(list_lines)
        # list_all_mcmc = self.burin(list_all_mcmc, self.burin_prop)
        # print(path)
        if filename:
            with open(f"{path}{os.sep}{filename}", "w", errors="ignore") as f:
                f.write("".join(list_all_mcmc))
        return filename, list_all_mcmc

    def fetch_seed(self, path):
        seed_file = f"{path}{os.sep}SeedUsed"
        if os.path.exists(seed_file):
            with open(seed_file, errors="ignore") as f:
                content = f.read()
            return int(content)
        ctl_file = f"{path}{os.sep}mcmctree.ctl"
        if os.path.exists(ctl_file):
            with open(ctl_file, errors="ignore") as f:
                content = f.read()
            match = re.search(r"(?m)^\s*seed\s*=\s*(-?\d+)", content)
            if match:
                return int(match.group(1))
        else:
            QMessageBox.warning(self, "Warning", "No seed data!")

    def ctl_addition(self, path):
        list_names = glob.glob(f"{path}{os.sep}mcmctree_continue*.ctl")
        list_names = [os.path.basename(i).rstrip(".ctl") for i in list_names]
        suffix = "_continue"
        new_name, list_names = self.factory.numbered_Name(list_names,
                                                          "mcmctree",
                                                          omit=False,
                                                          suffix=suffix)
        ctl_cont = f"{path}{os.sep}{new_name}.ctl"
        ctl = f"{path}{os.sep}mcmctree.ctl"
        if not os.path.exists(ctl):
            return
        else:
            shutil.copyfile(ctl, ctl_cont)
            return ctl_cont

    def viewResultsEarly(self):
        if self.tabWidgetMCMC.tabText(self.tabWidgetMCMC.currentIndex()) == "r8s":
            QMessageBox.information(
                self,
                "MDGUI",
                "<p style='line-height:25px; height:25px'>Only MCMCtree can use this "
                "function!</p>")
            return
        ok = self.on_pushButton_2_clicked(silence=True) #先结束线程
        if not ok:
            return
        if not self.workflow:
            QMessageBox.information(
                self,
                "MDGUI",
                "<p style='line-height:25px; height:25px'>If the results are not converged, "
                "you can continue the analysis via \"Continue Previous Analysis\" button!</p>")
        self.progressDialog = self.factory.myProgressDialog(
            "Please Wait", "summarizing mcmc...", busy=True, parent=self)
        self.progressDialog.show()
        QApplication.processEvents()

        # self.interrupt = False  # 如果是终止以后重新运行要刷新
        # self.error_has_shown = False
        # self.list_pids = []
        # self.queue = multiprocessing.Queue()
        # rPaths = glob.glob(f"{self.exportPath}{os.sep}run*")
        # self.sum_pool = multiprocessing.get_context("spawn").Pool(
        #     processes=len(rPaths), initializer=pool_init, initargs=(self.queue,)
        # )
        # # Check for progress periodically
        # self.timer = QTimer()
        # self.timer.timeout.connect(self.updateProcess)
        # self.timer.start(1)
        self.worker = WorkThread(lambda : self.end_run(use_prog_bar=False,
                                                       silence=True,
                                                       sum_silence=False,
                                                       sum_mode="stop run and summarize"
                                                       ),
                                 parent=self)
        self.worker.start()
        # self.worker = WorkThread(
        #     lambda : self.end_run(stop_infer=True), parent=self)
        # self.worker.finished.connect(self.progressDialog.close)
        # self.worker.start()

    def refresh_analysis(self, resultsPath):
        self.exportPath = resultsPath
        self.ctl_file = f"{self.exportPath}{os.sep}mcmctree.ctl"
        os.chdir(self.exportPath)

    def updateProcess(self):
        queque = self.queue
        if queque.empty():
            return
        info = queque.get()
        if info[0] == "log":
            message = info[1]
            self.logGuiSig.emit(message)
        elif info[0] == "prog":
            if not self.interrupt:
                self.progressSig.emit(99999)
        elif info[0] == "popen":
            self.list_pids.append(info[1])
        elif info[0] == "error":
            self.on_pushButton_2_clicked(silence=True) #杀掉进程
            if not self.error_has_shown:
                self.error_has_shown = True
                error_text = info[1]
                self.mcmctree_exception.emit(error_text)
            if hasattr(self, "progressDialog"):
                self.progressDialog.close()
        elif info[0] == "popen finished":
            self.interrupt = False
            if info[1] in self.list_pids:
                self.list_pids.remove(info[1])
        elif info[0] == "summarize finished":
            # mode:
            #         direct click
            #         summarize during run
            #         stop run and summarize
            #         run finished following summarize
            self.sum_pool = None
            if hasattr(self, "progressDialog"):
                self.progressDialog.close()
            self.focusSig.emit(self.exportPath)
            if self.summarize_mode in ["direct click",
                                       "summarize during run",
                                       "stop run and summarize"]:
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton_5,
                        self.progressBar,
                        "popupDialog stop",
                        self.exportPath,
                        self.qss_file,
                        self])
            else:
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton_5,
                        self.progressBar,
                        "stop",
                        self.exportPath,
                        self.qss_file,
                        self])

    def judge_plugin_install(self, index):
        text = self.tabWidgetMCMC.tabText(index)
        # print(text, self.r8sEXE, self.mcmctreeEXE)
        if (text == "r8s") and \
            (not self.r8sEXE) and \
            (platform.system().lower() != "windows"):
            self.close()
            reply = QMessageBox.information(
                    self,
                    "Information",
                    "<p style='line-height:25px; height:25px'>Please install r8s first!</p>",
                    QMessageBox.Ok,
                    QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.parent.setting = Setting(self.parent)
                self.parent.setting.display_table(self.parent.setting.listWidget.item(1))
                # 隐藏？按钮
                self.parent.setting.setWindowFlags(self.parent.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
                self.parent.setting.exec_()
        if (text == "MCMCTree") and (not self.mcmctreeEXE):
            reply = QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>Please install PAML first!</p>",
                QMessageBox.Ok,
                QMessageBox.Cancel)
            self.close()
            if reply == QMessageBox.Ok:
                self.parent.setting = Setting(self.parent)
                self.parent.setting.display_table(self.parent.setting.listWidget.item(1))
                # 隐藏？按钮
                self.parent.setting.setWindowFlags(self.parent.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
                self.parent.setting.exec_()

    def usedata_changed(self):
        model = self.comboBox.currentText()
        usedata = self.comboBox_3.currentText()
        if (model in ["T92", "TN93", "GTR", "UNREST", "REVu", "UNRESTu", "cpREV10", "cpREV64", "dayhoff",
                      "dayhoff-dcmut", "g1974a", "g1974c", "g1974p", "g1974v",
                      "grantham", "jones", "jones-dcmut", "lg", "miyata", "mtART", "mtmam", "mtREV24", "MtZoa",
                      "wag"]) and \
                (usedata in ["no data (prior)", "seq like (exact likelihood) SLOW"]):
            if self.sender() == self.comboBox:
                QMessageBox.information(
                    self,
                    "MDGUI",
                    f"<p style='line-height:25px; height:25px'>The \"{model}\" substitution model is incompatible "
                    f"with the \"no data (prior)\" and \"seq like (exact likelihood) SLOW\" usedata options, we will "
                    "automatically switch \"usedata\" to <span style='font-weight:600; color:#ff0000;'>"
                    "\"approximate likelihood FAST\""
                    "</span>"
                    "</p>")
                self.comboBox_3.setCurrentIndex(2)
            elif self.sender() == self.comboBox_3:
                QMessageBox.information(
                    self,
                    "MDGUI",
                    f"<p style='line-height:25px; height:25px'>The \"{model}\" substitution model is incompatible "
                    "with the \"no data (prior)\" and \"seq like (exact likelihood) SLOW\" usedata parameter, we will "
                    "automatically switch \"model\" to <span style='font-weight:600; color:#ff0000;'>"
                    "\"AUTO\""
                    "</span>"
                    "</p>")
                self.comboBox.setCurrentText("AUTO")
        if self.comboBox_3.currentText() == "approximate likelihood FAST":
            self.label_27.setEnabled(True)
            self.comboBox_14.setEnabled(True)
        else:
            self.label_27.setEnabled(False)
            self.comboBox_14.setEnabled(False)
        self.ctl_models(self.comboBox_14.currentIndex())

    def sum_dialog(self):
        self.progressDialog = self.factory.myProgressDialog(
            "Please Wait", "summarizing mcmc...", busy=True, parent=self)
        self.progressDialog.show()
        QApplication.processEvents()

    def ctl_models(self, int_):
        if (int(int_) == 0) and self.comboBox_14.isEnabled():
            self.checkBox_12.setEnabled(True)
        else:
            self.checkBox_12.setEnabled(False)
        if self.comboBox_14.isEnabled() and (self.comboBox_14.currentIndex() == 0):
            # 自带的model参数
            for i in [self.label_11, self.comboBox, self.checkBox_15, self.label_15, self.doubleSpinBox_6,
                      self.label_16,
                      self.spinBox_21, self.label_18, self.doubleSpinBox_2, self.doubleSpinBox_7, self.label_19,
                      self.doubleSpinBox_14, self.doubleSpinBox_15]:
                i.setEnabled(False)
        else:
            for i in [self.label_11, self.comboBox, self.checkBox_15, self.label_15, self.doubleSpinBox_6,
                      self.label_16,
                      self.spinBox_21, self.label_18, self.doubleSpinBox_2, self.doubleSpinBox_7, self.label_19,
                      self.doubleSpinBox_14, self.doubleSpinBox_15]:
                i.setEnabled(True)

    def judge_root_node(self):
        root = self.tree_with_tipdate.get_tree_root()
        if len(self.tree_with_tipdate.children) > 2:
            # 无根树
            msg = QMessageBox(QMessageBox.Warning, "Error",
                "The tree is unrooted. Since MCMCtree requires a rooted tree, we will open the tree for you to root.\n"
                "Please select a node, right-click to open the context menu, and choose the 'Set as outgroup (root tree)' option.",
                QMessageBox.Ok | QMessageBox.Ignore,
                self
                )
            # 修改按钮文字
            msg.button(QMessageBox.Ok).setText("Root Now")
            msg.button(QMessageBox.Ignore).setText("Ignore Warning")
            reply = msg.exec_()
            if reply == QMessageBox.Ok:
                self.on_pushButton_clicked()
                return
        # print(root)
        if self.checkBox_14.isChecked():
            return True
        root_calibration = False
        if hasattr(root, "name") and root.name:
            if re.search(r">|<|B.*\(|U.*\(|L.*\(|G.*\(|SN.*\(|ST.*", root.name):
                root_calibration = True
        if not root_calibration:
            msg = QMessageBox(QMessageBox.Warning, "Error",
                "The root node lacks fossil calibration information, but MCMCtree requires it to be set. You have two options:\n"
                "1. Click \"Set RootAge in Interface\", then check the \"RootAge\" option in the interface and set the "
                "age range using the two spin boxes. \n"
                "2. Click \"Add Calibration in Tree\", then select the node, right-click to open the context menu, and choose \"Add calibration\". "
                "Then switch to the MCMCtree root node tab to set the calibration.",
                QMessageBox.Ok | QMessageBox.Ignore,
                self
                )
            # 修改按钮文字
            msg.button(QMessageBox.Ok).setText("Add Calibration in Tree")
            msg.button(QMessageBox.Ignore).setText("Set RootAge in Interface")
            reply = msg.exec_()
            if reply==QMessageBox.Ok:
                self.on_pushButton_clicked()
            return
        return True


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = MCMCTree()
    ui.gui4Text()
    ui.show()
    sys.exit(app.exec_())
