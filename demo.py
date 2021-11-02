from __future__ import unicode_literals

import os

from yaml import dump_all, load, FullLoader
import image.image
import ctypes
import re
import threading
from datetime import datetime
from time import sleep
import serial.tools.list_ports
import sys
import matplotlib
# Make sure that we are using QT5
matplotlib.use('Qt5Agg')

import qtawesome
from numpy import arange, sin, pi
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from ui.mainwindow_ui import Ui_MainWindow
flagConnect = False
logginNum = 0

class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self.compute_initial_figure()
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
    def compute_initial_figure(self):
        pass


class MyStaticMplCanvas(MyMplCanvas):
    """Simple canvas with a sine plot."""
    def compute_initial_figure(self):
        t = arange(0.0, 3.0, 0.01)
        s = sin(2*pi*t)
        self.axes.plot(t, s)

class IctTest(QMainWindow, Ui_MainWindow):
    infoMsgPrint = pyqtSignal(str)
    operMsgPrint = pyqtSignal(str)

    def __init__(self, parent=None):
        super(IctTest, self).__init__(parent)
        self.main_ui = Ui_MainWindow()
        self.main_ui.setupUi(self)
        self.initUI()

    # 界面启动时初始化
    def initUI(self):
        # 增加左上角logo图标
        self.setWindowIcon(QIcon(':/ICT.png'))
        #给工具栏添加带图形按钮
        openfile = QAction(qtawesome.icon('fa.file-text-o',color="green"),"打开文件",self)
        self.main_ui.toolBar.addAction(openfile)
        printfile = QAction(qtawesome.icon('fa.print',color="green"),"打印文件",self)
        self.main_ui.toolBar.addAction(printfile)
        # 设置底部任务栏图标和左上角同步
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")
        self.get_serials_name()#初始化获取系统设备串口连接情况
        # -----------tablewidget表格中自定义下拉填充-----------
        self.main_ui.combox_compress = QComboBox()
        self.main_ui.combox_compress.addItems(['on', 'off'])
        self.main_ui.tableWidget.setCellWidget(0, 1, self.main_ui.combox_compress)
        self.main_ui.combox_interleave = QComboBox()
        self.main_ui.combox_interleave.addItems(['off', 'on'])
        self.main_ui.tableWidget.setCellWidget(1, 1, self.main_ui.combox_interleave)
        self.main_ui.combox_ccnum = QComboBox()
        self.main_ui.combox_ccnum.setEditable(True)  # 设置下拉box可配
        ccnumItems = [str(i) for i in range(15)]
        self.main_ui.combox_ccnum.addItems(ccnumItems)
        self.main_ui.tableWidget.setCellWidget(2, 1, self.main_ui.combox_ccnum)
        self.main_ui.combox_ccnum.currentTextChanged[str].connect(self.carrier_cfg_tablewidget)

        # -------------窗口打印部件槽连接-----------------------
        self.infoMsgPrint.connect(self.information_print)
        self.operMsgPrint.connect(self.operation_print)
        # -------------按钮连接槽函数--------------------------
        self.main_ui.connnect_button.clicked.connect(self.connect)
        self.main_ui.disconnect_button.clicked.connect(self.disconnect)
        self.main_ui.cfgfile_button.clicked.connect(self.cfgfile_button_clicked)
        self.main_ui.btnCfgSend.clicked.connect(self.get_script_cfg)
        self.main_ui.menuhelp.addAction("&About",self.about)
        self.main_ui.pushButton_save.clicked.connect(self.save_dialog)
        self.main_ui.pushButton.clicked.connect(self.cfgByName)
        self.main_ui.pushButtonDelete.clicked.connect(self.delByName)
        self.main_ui.pushButton_3.clicked.connect(self.infoByScriptName)
        self.main_ui.pushButton_download.clicked.connect(self.tftpd_32_open)
        self.main_ui.pushButton_openFile.clicked.connect(self.getFirmwareFile)
        self.main_ui.tableWidget_2.setContextMenuPolicy(Qt.CustomContextMenu) #允许右击产生菜单
        self.main_ui.tableWidget_2.customContextMenuRequested.connect(self.window_rightMenuShow)  # 设置右击tablewidget窗口时弹窗
        self.read_yaml()#读取自定义的脚本
        l = QVBoxLayout(self.main_ui.widget2)
        sc = MyStaticMplCanvas(self.main_ui.widget2, width=5, height=4, dpi=100)
        l.addWidget(sc)

    #右键小弹窗槽函数
    def window_rightMenuShow(self):
        contextMenu = QMenu()
        action1 = contextMenu.addAction('清空')
        action1.triggered.connect(self.click_event1)
        # 菜单显示前,将它移动到鼠标点击的位置
        contextMenu.exec_(QCursor.pos())  # 在鼠标位置显示

    #右击菜单“清空”槽函数
    def click_event1(self):
        self.main_ui.tableWidget_2.clearContents()

    # DFE数量下拉值改变触发的槽函数
    def carrier_cfg_tablewidget(self, cc_num):
        self.main_ui.tableWidget_2.clearContents()
        carrierCfg = self.get_cfg()
        a = int(cc_num)
        for i in range(a):
            chCC = str(i+1)
            item = QTableWidgetItem(qtawesome.icon('fa.magic',color="black"),chCC) #设置qtAwesome图标
            self.main_ui.tableWidget_2.setItem(i, 0, item)
            item = QTableWidgetItem(carrierCfg[0])
            self.main_ui.tableWidget_2.setItem(i, 1, item)
            item = QTableWidgetItem(carrierCfg[3])
            self.main_ui.tableWidget_2.setItem(i, 2, item)
            item = QTableWidgetItem('1')
            self.main_ui.tableWidget_2.setItem(i, 3, item)
            item = QTableWidgetItem('0')
            self.main_ui.tableWidget_2.setItem(i, 4, item)
            item = QTableWidgetItem('0')
            self.main_ui.tableWidget_2.setItem(i, 5, item)
            item = QTableWidgetItem('0')
            self.main_ui.tableWidget_2.setItem(i, 6, item)
        # for i in range(a):
        #     chCC = str(i+1)
        #     item = QTableWidgetItem(chCC)
        #     self.main_ui.tableWidget_2.setItem(i, 0, item)
        #     # -----------生成载波采样率下拉按钮---------------------
        #     self.main_ui.comboBox_msps = QtWidgets.QComboBox()
        #     x = 7.68
        #     listx = []
        #     for j in range(1, 17):
        #         listx.append(str('{0:.2f}'.format(x * j)))
        #     self.main_ui.comboBox_msps.addItems(listx)
        #     self.main_ui.tableWidget_2.setCellWidget(i, 1, self.main_ui.comboBox_msps)
        #     #------------width----------
        #     item = QTableWidgetItem(carrierCfg[3])
        #     self.main_ui.tableWidget_2.setItem(i, 2, item)
        #     #------------生成DFE CH下拉按钮----------------------
        #     self.main_ui.comboBox_dfech = QtWidgets.QComboBox()
        #     listy = [str(k) for k in range(10) ]
        #     self.main_ui.comboBox_dfech.addItems((listy))
        #     self.main_ui.tableWidget_2.setCellWidget(i,3,self.main_ui.comboBox_dfech)
        #     # ------------生成CC ID下拉按钮----------------------
        #     self.main_ui.comboBox_ccid = QtWidgets.QComboBox()
        #     listy = [str(k) for k in range(3) ]
        #     self.main_ui.comboBox_ccid.addItems((listy))
        #     self.main_ui.tableWidget_2.setCellWidget(i,4,self.main_ui.comboBox_ccid)
        #     # ------------生成天线ID下拉按钮----------------------
        #     self.main_ui.comboBox_antid = QtWidgets.QComboBox()
        #     listy = [str(k) for k in range(2) ]
        #     self.main_ui.comboBox_antid.addItems((listy))
        #     self.main_ui.tableWidget_2.setCellWidget(i,5,self.main_ui.comboBox_antid)
        #     # ------------时延---------------------
        #     item = QTableWidgetItem('0')
        #     self.main_ui.tableWidget_2.setItem(i, 6, item)


    #获取UI界面参数进行配置
    def get_script_cfg(self):
        compress=self.main_ui.combox_compress.currentText()
        interleave=self.main_ui.combox_interleave.currentText()
        # 获取ccnum按钮的内容来判断要读取表格的行数
        rowCount = int(self.main_ui.combox_ccnum.currentText())
        data = []
        for i in range(rowCount):
            dictMsg ={}
            chcfg = []
            for j in range(7):
                cellItem = self.main_ui.tableWidget_2.item(i, j).text()
                chcfg.append(cellItem)
            dictMsg['msps']=chcfg[1]
            dictMsg['width']=chcfg[2]
            dictMsg['ch_num'] = chcfg[3]
            dictMsg['ch_cc']=chcfg[4]
            dictMsg['ant_num']=chcfg[5]
            dictMsg['offset'] =chcfg[6]
            data.append(dictMsg)
        sendData = {"compress":compress,"interleave":interleave,"ch_num":rowCount,"data":data}
        self.ser_cfg_send(sendData)
        # combox_list_content = self.main_ui.tableWidget_2.cellWidget(1,1).currentText()
        # combox_list_content1 = self.main_ui.tableWidget_2.cellWidget(0, 1).currentText()


    # 配置下发
    def ser_cfg_send(self,dictMsg):
        cpriConfigMsg = f"cpri reset\ncpri compress {dictMsg['compress']}\ncpri interleave {dictMsg['interleave']}\n"
        # 获取ccnum按钮的内容来判断要读取表格的行数
        rowCount = dictMsg['ch_num']
        data = dictMsg['data']
        for i in range(rowCount):
            addcc = f"addcc   {data[i]['msps']}    {data[i]['width']}       {data[i]['ch_num']}            {data[i]['ch_cc']}             {data[i]['ant_num']}           {data[i]['offset']}\n"
            cpriConfigMsg = cpriConfigMsg + addcc
        cpri_dfe_enable = 'cpri enable\ndfe enable\n'
        filename = datetime.now().strftime('%Y%m%d%H%M%S') + '.config'
        cpriConfigMsg = f'echo -e "{cpriConfigMsg}{cpri_dfe_enable}" >>/lib/firmware/{filename}'
        commond = f"dfe -f /lib/firmware/{filename}"
        self.seial_msgs_send(cpriConfigMsg)
        self.main_ui.plainTextEdit.clear()
        sleep(0.2)
        self.seial_msgs_send(commond)

    # 获取界面参数返回值
    def get_cfg(self):
        # msps = self.main_ui.comboBox_msps.currentText()
        compressCfg = self.main_ui.combox_compress.currentText()
        interleaveCfg = self.main_ui.combox_interleave.currentText()
        widthCfg = {'on': '8', 'off': '16'}
        width = widthCfg[compressCfg]
        list_resp = ['7.68', compressCfg, interleaveCfg, width]
        return list_resp

    #填写保存界面
    def save_dialog(self):
        self.saveDialog = QDialog()
        self.saveDialog.resize(250,40)
        self.saveDialog.setWindowTitle("保存配置名")
        self.saveDialog.setWindowIcon(QIcon("./image/ICT.ico"))
        self.saveDialog.okbtn = QPushButton(qtawesome.icon("fa.save",color="blue"),"保存")
        self.saveDialog.lineEdit = QLineEdit()
        layout = QFormLayout(self.saveDialog)
        layout.addRow(self.saveDialog.lineEdit,self.saveDialog.okbtn)
        self.saveDialog.okbtn.clicked.connect(self.save_cfg)
        self.saveDialog.exec_()

    #获取当前配置并保存至config.yaml配置文件
    def save_cfg(self):
        fileName = self.saveDialog.lineEdit.text()
        if fileName:
            compress=self.main_ui.combox_compress.currentText()
            interleave=self.main_ui.combox_interleave.currentText()
            # 获取ccnum按钮的内容来判断要读取表格的行数
            ccnum = int(self.main_ui.combox_ccnum.currentText())
            data_list = [] #存放DFE载波具体信息
            for i in range(ccnum):
                chcfg = []
                for j in range(7):
                    cellItem = self.main_ui.tableWidget_2.item(i, j).text()
                    chcfg.append(cellItem)
                data = {"ch_cc":chcfg[4],
                        "msps":chcfg[1],
                        "width":chcfg[2],
                        "ch_num":chcfg[3],
                        "ant_num":chcfg[5],
                        "offset":chcfg[6]
                        }
                data_list.append(data)
            saveData = {
            "compress": compress,
            "interleave": interleave,
            "ch_num":ccnum,
            "data": data_list
            }
            self.dictScript[fileName] = saveData
            self.write_yaml(self.dictScript)#将文件名和配置信息写入yaml文件中
            self.saveDialog.close()
        else:
            QMessageBox.information(self.saveDialog,"提示","配置名不能为空")

    #导入配置生成对应的yaml文件
    def write_yaml(self,dictData):
        with open("./config/testCases.yaml", encoding='utf-8', mode='w') as f:
            try:
                dump_all(documents=[dictData], stream=f, allow_unicode=True)
            except Exception as e:
                QMessageBox.information(self,"错误提示",e)
        self.main_ui.comboBox_2.clear()
        self.read_yaml()

    #读取yaml文件并返回
    def read_yaml(self):
        with open(f"./config/testCases.yaml", encoding='utf-8') as f:
            data = load(f.read(), Loader=FullLoader)
            self.dictScript = data
        boxList = []
        for k in self.dictScript.keys():
            boxList.append(k)
        self.main_ui.comboBox_2.addItems(boxList)

    #根据脚本名下发配置
    def cfgByName(self):
        try:
            scriptName = self.main_ui.comboBox_2.currentText()
            data = self.dictScript[scriptName]
            self.ser_cfg_send(data)
        except:
            self.operMsgPrint.emit("当前不存在脚本")

    #根据脚本名删除配置
    def delByName(self):
        try:
            scriptName = self.main_ui.comboBox_2.currentText()
            del self.dictScript[scriptName] #删除键值对
            self.write_yaml(self.dictScript)#重新写入yaml配置文件
        except:
            self.operMsgPrint.emit("当前不存在脚本")

    #根据脚本查看
    def infoByScriptName(self):
        try:
            scriptName = self.main_ui.comboBox_2.currentText()
            data = self.dictScript[scriptName]

            self.cfgInfoDialog = QDialog()
            self.cfgInfoDialog.setWindowTitle("配置详情")
            self.cfgInfoDialog.setWindowIcon(qtawesome.icon('fa.magic',color="black"))
            layout = QHBoxLayout(self.cfgInfoDialog)
            self.model = QStandardItemModel(2,2)
            self.model.setHorizontalHeaderLabels(["AxC id","Msgs"])
            for row in range(2):
                for column in range(2):
                    item = QStandardItem("row %s ,column %s"%(row,column))
                    self.model.setItem(row,column,item)
            self.tableView = QTableView()
            self.tableView.setModel(self.model)
            layout.addWidget(self.tableView)
            self.cfgInfoDialog.exec_()
        except:
            self.operMsgPrint.emit("当前不存在脚本")

    # 获取当前设备连接的COM列表
    def get_serials_name(self):
        ports_get = list(serial.tools.list_ports.comports())
        port_list = []
        if len(ports_get) == 0:
            self.operMsgPrint.emit("错误提示,找不到串口\n")
        else:
            for i in range(0, len(ports_get)):
                port = (ports_get[i])
                port_list.append(port[0])
            port_list.sort()
            self.main_ui.comboBox.addItems(port_list)

    # 打开tftpd程序
    def tftpd_32_open(self):
        try:
            tftpath = os.path.dirname(os.path.realpath(__file__))
            app = "tftpd32.exe"
            tftpath = f"{tftpath}\config\{app}"
            open_app(tftpath)
        except:
            pass

    #打开文件夹填充至lineEdit_2
    def getFirmwareFile(self):
        directory = QFileDialog.getExistingDirectory(self,"选取文件夹","./")
        self.main_ui.lineEdit_2.setText(directory)

    # 连接按钮槽函数
    def connect(self):
        self.serialThread = threading.Thread(target=self.serial_connect)
        self.serialThread.setDaemon(True)  # 设置守护进程
        self.serialThread.start()

    # 断开连接槽函数
    def disconnect(self):
        global flagConnect
        self.main_ui.connnect_button.setEnabled(True)  # 设置连接按钮可点击
        flagConnect = False
        try:
            if self.serialThread.isAlive():
                self.serialSingle.close()
                self.operMsgPrint.emit(f"{self.main_ui.comboBox.currentText()}串口已经断开")
        except:
            self.operMsgPrint.emit("请先配置连接")

    # 串口连接
    def serial_connect(self):
        global flagConnect
        try:
            self.serialSingle = serial.Serial(self.main_ui.comboBox.currentText(), 115200, timeout=0.5)
            self.operMsgPrint.emit(f"{self.main_ui.comboBox.currentText()}串口已经连接")
            flagConnect = True
            self.main_ui.connnect_button.setEnabled(False)  # 设置连接按钮不可点击
            while flagConnect:
                data = self.recv(self.serialSingle)
                if data != b'':
                    try:
                        serialMsg = str(data, encoding='utf-8')
                        self.infoMsgPrint.emit(serialMsg)
                        self.check_in(serialMsg)
                    except:
                        pass
        except:
            self.operMsgPrint.emit("注意：串口被占用或者不存在\n")

    # 匹配关键字进行登陆操作
    def check_in(self, strMsg):
        global logginNum
        strRegex1 = re.compile('login|success')
        mo1 = strRegex1.search(strMsg)
        if mo1.group() == 'login':
            self.logThread = threading.Thread(target=self.logging)
            self.logThread.setDaemon(True)
            self.logThread.start()
            logginNum += 1
        if mo1.group() == 'success' and logginNum != 0: #判断loggingNum不为0，防止启动时打印也会提示脚本下发成功
            self.operMsgPrint.emit("提示: 脚本下发成功")

    # 进行串口登录操作，登陆完清除面板内容
    def logging(self):
        msgSend = ['root', 'ict']
        for i in msgSend:
            self.seial_msgs_send(i)
            sleep(2)
        self.main_ui.plainTextEdit.clear()
        self.cfgfile_button_clicked()
        self.operMsgPrint.emit("提示:芯片启动完成，可以进行配置")

    # 实现串口已连接的serial监听，返回byte数据
    def recv(self, serial_id):
        while flagConnect:
            try:
                data = serial_id.read_all()
                return data
            except:
                pass

    # 串口信息打印
    def information_print(self, mypstr):
        self.main_ui.plainTextEdit.appendPlainText(mypstr.strip())

    # 操作信息打印
    def operation_print(self, mypstr):
        currenTime = self.getCurrenTime()
        self.main_ui.textEdit_2.append(currenTime + mypstr)

    # 实现给已连接串口发送字符串数据
    def cfgfile_button_clicked(self):
        if flagConnect == True:
            msgSend = self.main_ui.lineEdit_2.text() + '\n'
            self.serialSingle.write(bytes(msgSend, encoding='utf-8'))
        else:
            self.operMsgPrint.emit("串口未连接！")

    # 实现给已连接串口发送字符串数据
    def seial_msgs_send(self, msgStr):
        if flagConnect == True:
            msgSend = msgStr + '\n'
            self.serialSingle.write(bytes(msgSend, encoding='utf-8'))
        else:
            self.operMsgPrint.emit("串口未连接！")

    # 返回当前时间年月日时分秒
    def getCurrenTime(self):
        localtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S ')
        return localtime

    #软件版权信息
    def about(self):
        QMessageBox.about(self, "About",
                                    """Copyright 2021 @创芯慧联 zhangbingxue"""
                                )

def open_app(app_dir):
    os.startfile(app_dir)

if __name__ == "__main__":
    myapp = QApplication(sys.argv)
    Main_Ui = IctTest()
    Main_Ui.show()
    sys.exit(myapp.exec_())
