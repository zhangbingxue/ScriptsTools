import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class MainWindow(QMainWindow):
    count=0
    def __init__(self,parent=None):
        super(MainWindow, self).__init__(parent)
        #实例化Qmidarea区域
        self.mdi=QMdiArea()
        #设置为中间控件
        self.setCentralWidget(self.mdi)

        #实例化菜单栏
        bar=self.menuBar()
        #添加主菜单
        file=bar.addMenu('File')
        #添加子菜单
        file.addAction('New')
        file.addAction('cascade')
        file.addAction('Tiled')

        #点击QAction绑定自定义的槽函数（传递有值【QAction】）
        file.triggered[QAction].connect(self.windowaction)
        #设置主窗口的标题
        self.setWindowTitle("MDI demo")
    def windowaction(self,q):
        print('Triggered')

        if q.text()=='New':
            #子窗口增加一个
            MainWindow.count=MainWindow.count+1

            #实例化多文档界面对象
            sub=QMdiSubWindow()
            #向sub内添加内部控件
            sub.setWidget(QTextEdit())
            #设置新建子窗口的标题
            sub.setWindowTitle('subWindow'+str(MainWindow.count))

            #将子窗口添加到Mdi区域
            self.mdi.addSubWindow(sub)

            #子窗口显示
            sub.show()
        if q.text()=='cascade':
            #cascadeSubWindows()：安排子窗口在Mdi区域级联显示
            self.mdi.cascadeSubWindows()
        if q.text()=='Tiled':
            #tileSubWindow():安排子窗口在Mdi区域平铺显示
            self.mdi.tileSubWindow()
if __name__ == '__main__':
    app=QApplication(sys.argv)
    demo=MainWindow()
    demo.show()
    sys.exit(app.exec_())