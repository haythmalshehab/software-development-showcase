#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import *
from PyQt4.QtCore import *

import os
import sys
import serial
import _winreg
import threading
import time
import datetime
from ui_viewerSecond import Ui_MainWindow

import pyqtgraph as pg

# Styling of graphWidget.plot
pg.setConfigOption('background', 'k')  # Plot background -> black
# Predefined colors to use in plot's curves
COLORS = {
    'red': (214, 39, 40),
    'blue': (31, 119, 180),
    'cyan': (23, 190, 207),
    'green': (44, 160, 44),
    'yellow': (188, 189, 34),
    'wisteria': (142, 68, 173),
    'emerald': (46, 204, 113),
    'sunflower': (241, 196, 15)
}

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


class graphWidget(QtGui.QWidget):
    """"""

    def __init__(self, parent=None):
        """Creates canvas, ROIs, curves and area for mask testing;
        Connects self.mouseMoved to PlotWidget.Scene signal"""
        super(graphWidget, self).__init__(parent)
        self.canvas = pg.PlotWidget()
        self.p = self.canvas.plotItem
        self.p.showGrid(1, 1)
        self.roi_t = None
        self.roi_b = None
        self.c_t = self.p.plot()
        self.c_b = self.p.plot()
        self.area = pg.FillBetweenItem(None, None, brush=COLORS['wisteria'])
        self.p.addItem(self.area)

        self.vb = self.p.vb
        self.p.scene().sigMouseMoved.connect(self.mouseMoved)
        self.layoutVertical = QtGui.QVBoxLayout(self)
        self.layoutVertical.addWidget(self.canvas)

    def initROI(self, top, bottom):
        """ Clears current points of ROIs, creates new ROIs, adds them to PlotWidget;
        Connects ROIs to multiple functions

        Params:
            top - list of points (point: [x, y]) for top side of mask
            bottom - list of points (point: [x, y]) for bottom side of mask"""
        try:
            self.roi_t.clearPoints()
            self.roi_b.clearPoints()
        except AttributeError:
            pass
        self.roi_t = pg.PolyLineROI(top, closed=False, removable=True, pen=COLORS['emerald'])
        self.roi_b = pg.PolyLineROI(bottom, closed=False, removable=True, pen=COLORS['sunflower'])
        self.p.addItem(self.roi_t)
        self.p.addItem(self.roi_b)
        self.roi_t.sigRegionChangeFinished.connect(self.createTopCurve)
        self.roi_b.sigRegionChangeFinished.connect(self.createBottomCurve)
        self.roi_t.sigRemoveRequested.connect(self.roi_t.clearPoints)
        self.roi_b.sigRemoveRequested.connect(self.roi_b.clearPoints)
        self.roi_t.sigRemoveRequested.connect(self.clearTopPoints)
        self.roi_b.sigRemoveRequested.connect(self.clearBottomPoints)

    def mouseMoved(self, evt):
        """Send mouse position when mouseMoved

        Params
            evt - event received from PlotWidget.Scene"""
        pos = evt
        if self.p.sceneBoundingRect().contains(pos):
            mousePoint = self.vb.mapSceneToView(pos)
            self.emit(QtCore.SIGNAL('MouseMove(int,QString)'), int(mousePoint.x()), str(round(mousePoint.y(), 2)))

    def createTopCurve(self, evt):
        """Creates curve from 'top' ROI

        Params
            evt - event received from ROI"""
        try:
            self.c_t.clear()
        except AttributeError:
            pass
        x = [p[0] for p in self.roi_t.lastState['points']]
        y = [p[1] for p in self.roi_t.lastState['points']]
        self.c_t = self.p.plot({'x': x, 'y': y}, pen=COLORS['emerald'])
        self.updateArea()

    def createBottomCurve(self, evt):
        """Creates curve from 'bottom' ROI

        Params
            evt - event received from ROI"""
        try:
            self.c_b.clear()
        except AttributeError:
            pass
        x = [p[0] for p in self.roi_b.lastState['points']]
        y = [p[1] for p in self.roi_b.lastState['points']]
        self.c_b = self.p.plot({'x': x, 'y': y}, pen=COLORS['sunflower'])
        self.updateArea()

    def clearCurves(self):
        """Clears curves ('top' and 'bottom')"""
        try:
            self.c_t.clear()
            self.c_b.clear()
        except AttributeError:
            pass

    def clearTopPoints(self):
        """Sends signal to clear points of MWindow.points_t which refer to 'top' ROI"""
        self.emit(QtCore.SIGNAL('clearTopPoints()'))

    def clearBottomPoints(self):
        """Sends signal to clear points of MWindow.points_b which refer to 'bottom' ROI"""
        self.emit(QtCore.SIGNAL('clearBottomPoints()'))

    def updateArea(self):
        """Sets curves ('top' and 'bottom') to graphWidget.area for updating it"""
        self.area.setCurves(self.c_t, self.c_b)

    def updateTopLimit(self, x_pos):
        """Updates 'top' ROI"""
        try:
            self.c_t.clear()
        except AttributeError:
            pass
        x = [p[0] for p in self.roi_t.lastState['points']]
        y = [p[1] for p in self.roi_t.lastState['points']]
        x_sorted = sorted(x)
        try:
            if x_pos < x_sorted[0]:
                x.append(x_pos)
                y.append(y[0])
            elif x_pos > x_sorted[-1]:
                x.append(x_pos)
                y.append(y[-1])
            else:
                pass
        except IndexError:
            x.append(x_pos)
            y.append(y[0])
        self.c_t = self.p.plot({'x': x, 'y': y})
        self.updateArea()

    def updateBottomLimit(self, x_pos):
        """Updates 'bottom' ROI"""
        try:
            self.c_b.clear()
        except AttributeError:
            pass
        x = [p[0] for p in self.roi_b.lastState['points']]
        y = [p[1] for p in self.roi_b.lastState['points']]
        x_sorted = sorted(x)
        try:
            if x_pos < x_sorted[0]:
                x.append(x_pos)
                y.append(y[0])
            elif x_pos > x_sorted[-1]:
                x.append(x_pos)
                y.append(y[-1])
            else:
                pass
        except IndexError:
            x.append(x_pos)
            y.append(y[0])
        self.c_b = self.p.plot({'x': x, 'y': y})
        self.updateArea()


# main window
class MWindow(QtGui.QMainWindow, Ui_MainWindow):
    """"""

    def __init__(self):
        super(QMainWindow, self).__init__()
        self.setupUi(self)
        self.fail_states = []
        self.unit_mode = None
        self.data_index = None
        self.readable_mode = None
        self.acquisition = True
        #
        self.serial = serial.Serial()#UART
        self.FLAG = False
        self.send_timer = QtCore.QTimer()  # timer
        self.time_timer = QtCore.QTimer()  # timer
        # 0- read file, 1 - read COM port
        self.mode = 0
        # thread
        self.alive = threading.Event()
        self.thread = None
        # file
        self.i = 0
        self.f = None  # file object
        self.path_file = ''  # path
        #
        self.f_pause = False
        #
        # data for plot
        self.mass_plot = []  #
        #
        self.error_range = False  #
        #
        self.mass_time = []
        #
        self.mass_ac_voltage_t = []
        self.mass_ac_voltage = []  #
        self.mass_ac_voltage_x = []  #
        #
        self.mass_dc_voltage_t = []  #
        self.mass_dc_voltage = []  #
        self.mass_dc_voltage_x = []  #
        #
        self.mass_ac_current_t = []  #
        self.mass_ac_current = []  #
        self.mass_ac_current_x = []  #
        #
        self.mass_dc_current_t = []  #
        self.mass_dc_current = []  #
        self.mass_dc_current_x = []  #
        #
        self.mass_resistance_t = []  #
        self.mass_resistance = []  #
        self.mass_resistance_x = []  #
        #
        self.mass_test_continuity_t = []  #
        self.mass_test_continuity = []  #
        self.mass_test_continuity_x = []  #
        #
        self.mass_logic_level_t = []  #
        self.mass_logic_level = []  #
        self.mass_logic_level_x = []  #
        # points for limits
        self.points_t = []
        self.points_b = []
        # time
        self.first_time = ''
        self.last_time = ''
        #
        self.last_period = False  #
        self.period = 50
        self.replay_speed = 500  # ms
        self.f_first = True  # firsf plot settings
        self.log_file = None  # log file *.csv
        # OpenDialog
        self.dialogTXT = QtGui.QFileDialog()
        self.dialogTXT.setNameFilter("Data files (*.txt *.csv)")
        self.dialogTXT.setViewMode(QtGui.QFileDialog.Detail)
        # MessageBox Error
        self.msgBoxError = QMessageBox()
        self.msgBoxError.setWindowTitle("Error")
        self.msgBoxError.setIcon(QMessageBox.Critical)
        # Info box
        self.msgBox = QtGui.QMessageBox()
        self.msgBox.setWindowTitle(_fromUtf8("Message"))
        # self.msgBox.setWindowIcon(icon)
        self.msgBox.setIcon(QMessageBox.Question)
        self.msgBox.addButton(QtGui.QPushButton(_fromUtf8('Yes')), QtGui.QMessageBox.YesRole)
        self.msgBox.addButton(QtGui.QPushButton(_fromUtf8('No')), QtGui.QMessageBox.NoRole)
        # Font
        self.Bfont = QtGui.QFont()
        self.Bfont.setBold(True)
        # graph1
        self.matplotlibWidget = graphWidget(self)  # graph
        self.groupBox.setLayout(self.matplotlibWidget.layoutVertical)  #
        QtCore.QObject.connect(self.pushButton, QtCore.SIGNAL("clicked()"), self.selectFile)  # select file
        QtCore.QObject.connect(self.pushButton_2, QtCore.SIGNAL("clicked()"), self.start)  # start read file
        QtCore.QObject.connect(self.pushButton_3, QtCore.SIGNAL("clicked()"), self.connectUart)  # connect UART
        QtCore.QObject.connect(self.pushButton_4, QtCore.SIGNAL("clicked()"), self.stop)  # start read file
        QtCore.QObject.connect(self.pushButton_5, QtCore.SIGNAL("clicked()"), self.restart)  # restart
        QtCore.QObject.connect(self.pushButton_8, QtCore.SIGNAL("clicked()"), self.reset)  # reset
        QtCore.QObject.connect(self.pushButton_6, QtCore.SIGNAL("clicked()"), self.plus)  # plus
        QtCore.QObject.connect(self.pushButton_7, QtCore.SIGNAL("clicked()"), self.minus)  # minus
        QtCore.QObject.connect(self.send_timer, QtCore.SIGNAL("timeout()"), self.checkTimer)  #
        QtCore.QObject.connect(self.time_timer, QtCore.SIGNAL("timeout()"), self.checkTimeTimer)  #
        QtCore.QObject.connect(self, QtCore.SIGNAL("OutputData(QString,QString,QString,QString)"), self.viewData)  #
        QtCore.QObject.connect(self.comboBox, QtCore.SIGNAL("currentIndexChanged(int)"), self.selectFrequency)  #
        QtCore.QObject.connect(self.comboBox_2, QtCore.SIGNAL("currentIndexChanged(int)"), self.selectOutput)  #
        QtCore.QObject.connect(self.matplotlibWidget, QtCore.SIGNAL("MouseMove(int,QString)"), self.mouseMove)  #
        QtCore.QObject.connect(self.matplotlibWidget, QtCore.SIGNAL("MouseLeave"), self.mouseLeave)  #
        QtCore.QObject.connect(self.exportButton, QtCore.SIGNAL("clicked()"), self.exportLimits)
        QtCore.QObject.connect(self.importButton, QtCore.SIGNAL("clicked()"), self.importLimits)
        self.matplotlibWidget.p.mouseClickEvent = self.mouseClickEvent
        QtCore.QObject.connect(self.matplotlibWidget, QtCore.SIGNAL('clearTopPoints()'), self.clearTopPoints)
        QtCore.QObject.connect(self.matplotlibWidget, QtCore.SIGNAL('clearBottomPoints()'), self.clearBottomPoints)
        QtCore.QObject.connect(self.powerSaveButton, QtCore.SIGNAL("clicked()"), self.powerSaveMode)
        QtCore.QObject.connect(self.pauseAcqButton, QtCore.SIGNAL("clicked()"), self.pauseAcquisition)
        QtCore.QObject.connect(self.resumeAcqButton, QtCore.SIGNAL("clicked()"), self.resumeAcquisition)
        QtCore.QObject.connect(self, QtCore.SIGNAL("MaskData(QString)"), self.saveMaskTesting)
        # self.matplotlibWidget.spos.on_changed(self.update)
        # menu and action
        self.menubar = QtGui.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 900, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menu = QtGui.QMenu(self.menubar)
        self.menu.setObjectName(_fromUtf8("menu"))
        self.setMenuBar(self.menubar)
        self.action_Exit = QtGui.QAction(self)
        self.action_Exit.setObjectName(_fromUtf8("action_Exit"))
        self.menu.addAction(self.action_Exit)
        self.menubar.addAction(self.menu.menuAction())
        self.menu.setTitle("File")
        self.action_Exit.setText("Exit")
        QtCore.QObject.connect(self.action_Exit, QtCore.SIGNAL("triggered()"), self,
                               QtCore.SLOT("close()"))  # close event
        # activate function
        self.activate()
        self.loadPorts()

    def pauseAcquisition(self):
        """Pauses (hides) plot"""
        self.acquisition = False
        self.pauseAcqButton.setEnabled(False)
        self.resumeAcqButton.setEnabled(True)

    def resumeAcquisition(self):
        """Resumes (shows) plot"""
        self.acquisition = True
        self.resumeAcqButton.setEnabled(False)
        self.pauseAcqButton.setEnabled(True)

    def topCurveEq(self, x):
        """Returns y at x position of graphWidget.PlotWidget's 'top' ROI's curve"""
        self.points_t.sort(key=lambda point: point[0])
        curve_y = None
        for i, _ in enumerate(self.points_t):
            try:
                if self.points_t[i][0] < x < self.points_t[i + 1][0]:
                    k = (
                        (self.points_t[i + 1][1] - self.points_t[i][1]) / (
                            self.points_t[i + 1][0] - self.points_t[i][0]))
                    b = self.points_t[i + 1][1] - self.points_t[i + 1][0] * k
                    curve_y = k * x + b
                elif self.points_t[i][0] == x:
                    curve_y = self.points_t[i][1]
                else:
                    pass
            except IndexError:
                pass
        return curve_y

    def bottomCurveEq(self, x):
        """Returns y at x position of graphWidget.PlotWidget's 'bottom' ROI's curve"""
        self.points_b.sort(key=lambda point: point[0])
        curve_y = None
        for i, _ in enumerate(self.points_b):
            try:
                if self.points_b[i][0] < x < self.points_b[i + 1][0]:
                    k = (
                        (self.points_b[i + 1][1] - self.points_b[i][1]) / (
                            self.points_b[i + 1][0] - self.points_b[i][0]))
                    b = self.points_b[i + 1][1] - self.points_b[i + 1][0] * k
                    curve_y = k * x + b
                elif self.points_b[i][0] == x:
                    curve_y = self.points_b[i][1]
                else:
                    pass
            except IndexError:
                pass
        return curve_y

    def mouseClickEvent(self, ev):
        """Implementation of mouseClickEvent
        Allows to create new ROI points for mask

        Params
            ev - event received after mouse click on graphWidget.PlotWidget.Scene"""
        success = False
        if self.matplotlibWidget.p.sceneBoundingRect().contains(ev._scenePos) and ev._button == 1:
            mousePoint = self.matplotlibWidget.vb.mapSceneToView(ev._scenePos)
            if self.upperLimitButton.isChecked():
                if self.bottomCurveEq(mousePoint.x()):
                    print mousePoint.x(), mousePoint.y()
                    print self.bottomCurveEq(mousePoint.x())
                    if self.bottomCurveEq(mousePoint.x()) < mousePoint.y():
                        self.points_t.append([mousePoint.x(), mousePoint.y()])
                        success = True
                    else:
                        self.msgBoxError.setText(_fromUtf8("Your mask is corrupted [Overlap]!!!"))
                        self.msgBoxError.setVisible(True)
                else:
                    self.points_t.append([mousePoint.x(), mousePoint.y()])
                    success = True
            elif self.lowerLimitButton.isChecked():
                if self.topCurveEq(mousePoint.x()):
                    print mousePoint.x(), mousePoint.y()
                    print self.topCurveEq(mousePoint.x())
                    if self.topCurveEq(mousePoint.x()) > mousePoint.y():
                        self.points_b.append([mousePoint.x(), mousePoint.y()])
                        success = True
                    else:
                        self.msgBoxError.setText(_fromUtf8("Your mask is corrupted [Overlap]!!!"))
                        self.msgBoxError.setVisible(True)
                else:
                    self.points_b.append([mousePoint.x(), mousePoint.y()])
                    success = True
            if success:
                self.points_t.sort(key=lambda point: point[0])
                self.points_b.sort(key=lambda point: point[0])
                self.matplotlibWidget.initROI(self.points_t, self.points_b)
                self.matplotlibWidget.createTopCurve(None)
                self.matplotlibWidget.createBottomCurve(None)
                self.matplotlibWidget.updateArea()

    def clearTopPoints(self):
        """Clears list which refer to graphWidget.PlotWidget's 'top' ROI"""
        self.points_t = []

    def clearBottomPoints(self):
        """Clears list which refer to graphWidget.PlotWidget's 'bottom' ROI"""
        self.points_b = []

    def activate(self):
        # self.setMinimumSize(QtCore.QSize(1100, 700))#minimum size
        # self.setMaximumSize(QtCore.QSize(1200, 800))#maximum size
        self.label_1000 = QtGui.QLabel(self)
        self.label_1000.setMinimumSize(QtCore.QSize(85, 20))  #
        self.label_1000.setMaximumSize(QtCore.QSize(85, 20))
        self.label_1000.setFont(self.Bfont)
        self.statusbar.addWidget(self.label_1000)  # statusbar label
        self.label_1000.setText('')
        #
        self.matplotlibWidget.p.setLabel('left', '')
        self.matplotlibWidget.p.setLabel('bottom', '')
        #
        # initial range of plot
        self.comboBox_4.addItem(_fromUtf8("-1V:+1V"))
        self.comboBox_4.addItem(_fromUtf8("-5V:+5V"))
        self.comboBox_4.addItem(_fromUtf8("-12V:+12V"))
        self.comboBox_4.setCurrentIndex(0)  #
        #
        # txt = u'\u00B1'
        # self.label_8.setText(txt + '1V')
        #
        self.StartThread()  # start thread

    def loadPorts(self):
        """Loads available com ports from OS"""
        index = 0
        self.comboBox_3.clear()
        mass = self.ScanPortFromReg()
        nn = len(mass)
        if nn == 0:
            self.comboBox_3.setEnabled(False)
            self.msgBoxError.setText(_fromUtf8("The system doesn't have the serial ports!"))
            self.msgBoxError.setVisible(True)
            return
        for n in range(nn):
            try:
                self.comboBox_3.addItem(str(mass[n]))
            except:
                pass
        self.comboBox_3.setCurrentIndex(index)

    def getTime(self):
        """Returns two timestamps (utc, ti)"""
        utc = datetime.datetime.utcnow()
        iso = utc.isoformat()  # t = time.time()
        ind = iso.find('.')
        ti = ''
        if ind != -1:
            ti = iso[:ind + 2] + '+10:00'
        else:
            print iso
            ti = iso + '.0+10:00'
        return [utc, ti]

    def ScanPortFromReg(self):
        """Returns available ports from Windows registry"""
        available = []
        try:
            explorer = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "Hardware\\Devicemap\\serialcomm")
        except:
            return available
        i = 0
        while 1:
            try:
                name, value, type = _winreg.EnumValue(explorer, i)
                available.append(value)
                i = i + 1
            except WindowsError:
                break
        _winreg.CloseKey(explorer)
        available.sort()
        return available

    def mouseLeave(self):
        self.label_31.setText('---')
        self.label_30.setText('---')

    # mouse move signal
    def mouseMove(self, x_pos, y_pos):
        """Changes text in UI if mouse moved on graphWidget.PlotWidget

        Params
            x_pos - x position of mouse on Plot
            y_pos - y position of mouse on Plot"""
        try:
            if x_pos == 0:
                pass
            else:
                self.label_30.setText('<sample ' + str(x_pos) + ' , ' + y_pos + ' >')
                self.label_31.setText('<' + self.mass_time[x_pos] + ' , ' + y_pos + ' >')

        except:
            pass

    def initSendtoUART(self):
        """Sends to UART the type of output"""
        out = self.comboBox_2.currentIndex()
        value = ''
        if out == 0:
            value = 'a'
        elif out == 1:
            value = 'b'
        elif out == 2:
            value = 'c'
        elif out == 3:
            value = 'd'
        elif out == 4:
            value = 'e'
        elif out == 5:
            value = 'f'
        elif out == 6:
            value = 'g'
        else:
            pass
        try:
            self.serial.write(value)
        except:
            pass

    def connectUart(self):
        """Reads data from UART"""
        if self.pushButton_3.isChecked():
            try:
                self.stop()  # close data from file
                self.serial.port = str(self.comboBox_3.currentText())
                self.serial.baudrate = 115200
                self.serial.bytesize = serial.EIGHTBITS
                self.serial.parity = serial.PARITY_NONE
                self.serial.stopbits = serial.STOPBITS_ONE
                self.serial.timeout = None  # default = 0.2
                self.serial.open()
                # send type of reading
                self.initSendtoUART()
                #
                self.FLAG = True
                self.mode = 1  # read from UART
                self.log_file = open(time.strftime("%Y%m%d_%H-%M-%S") + '.csv', "wb+")  # always new file
                #
                self.pushButton_3.setText(_fromUtf8("Disconnect"))
                self.resumeAcqButton.setEnabled(False)
                self.label_1000.setText(_fromUtf8(str(self.comboBox_3.currentText())))
                self.pushButton_2.setEnabled(False)  # disable "Start"
                self.pushButton_4.setEnabled(False)  # disable "Stop"
                self.pushButton_5.setEnabled(False)  # disable "Restart"
                self.pushButton.setEnabled(False)  #
                self.comboBox.setEnabled(False)  #
                self.first_time = self.getTime()[1]
                self.time_timer.start(100)  # 100 ms
            except:
                self.stop()
                self.pushButton_3.setChecked(False)  #
                self.serial.close()  #
                self.log_file.close()  # close log
                self.pushButton_3.setText(_fromUtf8("Connect"))
                self.label_1000.setText(_fromUtf8("Disconnected"))
                self.msgBoxError.setText(_fromUtf8("Error!"))
                self.msgBoxError.setVisible(True)
                self.pushButton_2.setEnabled(True)  # enable "Start"
                self.pushButton_4.setEnabled(True)  # enable "Stop"
                self.pushButton_5.setEnabled(True)  # enable "Restart"
                self.pushButton.setEnabled(True)  #
                self.comboBox.setEnabled(True)  #
                self.time_timer.stop()
                return
        else:
            self.stop()
            self.serial.close()
            self.log_file.close()  # close log
            self.FLAG = False
            self.pushButton_3.setText(_fromUtf8("Connect"))
            self.label_1000.setText(_fromUtf8("Disconnected"))
            self.pushButton_2.setEnabled(True)  # enable "Start"
            self.pushButton_4.setEnabled(True)  # enable "Stop"
            self.pushButton_5.setEnabled(True)  # enable "Restart"
            self.pushButton.setEnabled(True)  #
            self.comboBox.setEnabled(True)  #
            self.time_timer.stop()

    def selectFile(self):
        """Select data file"""
        self.dialogTXT.setDirectory(os.getcwd())
        if self.dialogTXT.exec_():
            pp = self.dialogTXT.selectedFiles()
            self.path_file = pp[0]  #
            ff = unicode(pp[0]).encode('CP1251')
            tokens1 = ff.split("/")  #
            p1 = len(tokens1[len(tokens1) - 1]) + 1  #
            l = len(ff) - p1  #
            tt = ff[:l]  #
            tokens = pp[0].split("/")
            p = tokens[len(tokens) - 1]
            self.lineEdit.setText(p)

    def selectFrequency(self):
        """Select frequency in ms"""
        fr = self.comboBox.currentIndex()
        line = ''
        if fr == 0:
            self.replay_speed = 500
            line = 'S1!'
        elif fr == 1:
            self.replay_speed = 1000
            line = 'S2!'
        elif fr == 2:
            self.replay_speed = 2000
            line = 'S4!'
        elif fr == 3:
            self.replay_speed = 5000
            line = 'S10!'
        elif fr == 4:
            self.replay_speed = 10000
            line = 'S20!'
        elif fr == 5:
            self.replay_speed = 60000
            line = 'S120!'
        elif fr == 6:
            self.replay_speed = 120000
            line = 'S240!'
        elif fr == 7:
            self.replay_speed = 300000
            line = 'S600!'
        elif fr == 8:
            self.replay_speed = 600000
            line = 'S1200!'
        else:
            self.replay_speed = 1000
            line = 'S2!'
        try:
            self.serial.write(line)
        except:
            pass

    def selectOutput(self):
        """Select type of output"""
        out = self.comboBox_2.currentIndex()
        self.comboBox_4.clear()
        if out == 0:
            self.label_2.setText('AC Voltage')
            self.label_15.setText('V')
            self.label_8.setText('')
            self.comboBox_4.addItem(_fromUtf8("-1V:+1V"))
            self.comboBox_4.addItem(_fromUtf8("-5V:+5V"))
            self.comboBox_4.addItem(_fromUtf8("-12V:+12V"))
            self.comboBox_4.setCurrentIndex(0)  #
        elif out == 1:
            self.label_2.setText('DC Voltage')
            self.label_15.setText('V')
            self.label_8.setText('')
            self.comboBox_4.addItem(_fromUtf8("-1V:+1V"))
            self.comboBox_4.addItem(_fromUtf8("-5V:+5V"))
            self.comboBox_4.addItem(_fromUtf8("-12V:+12V"))
            self.comboBox_4.setCurrentIndex(0)  #
        elif out == 2:
            self.label_2.setText('AC Current')
            self.label_15.setText('A')
            self.label_8.setText('')
            self.comboBox_4.addItem(_fromUtf8("-200mA:+200mA"))
            self.comboBox_4.addItem(_fromUtf8("-10mA:+10mA"))
            self.comboBox_4.setCurrentIndex(0)  #
        elif out == 3:
            self.label_2.setText('DC Current')
            self.label_15.setText('A')
            self.label_8.setText('')
            self.comboBox_4.addItem(_fromUtf8("-200mA:+200mA"))
            self.comboBox_4.addItem(_fromUtf8("-10mA:+10mA"))
            self.comboBox_4.setCurrentIndex(0)  #
        elif out == 4:
            self.label_2.setText('Resistance')
            self.label_15.setText('Ohm')
            self.label_8.setText('')
            txt = u'\u03A9'
            self.comboBox_4.addItem(_fromUtf8('0 - 1k' + txt))
            self.comboBox_4.addItem(_fromUtf8('0 - 1M' + txt))
            self.comboBox_4.setCurrentIndex(0)  #
        elif out == 5:
            self.label_2.setText('Continuity')
            self.label_15.setText('')
            self.label_8.setText('')
            self.comboBox_4.addItem(_fromUtf8('---'))
            self.comboBox_4.setCurrentIndex(0)  #
        elif out == 6:
            self.label_2.setText('Logic Level')
            self.label_15.setText('')
            self.label_8.setText('')
            self.comboBox_4.addItem(_fromUtf8('---'))
            self.comboBox_4.setCurrentIndex(0)  #
        else:
            pass
        self.resetPlot(False)
        # send to UART message
        self.initSendtoUART()

    # timer
    def checkTimer(self):
        self.FLAG = True

    # time timer
    def checkTimeTimer(self):
        """Changes current time in UI"""
        self.label_28.setText(self.first_time + ' / ' + self.getTime()[1])

    def reset(self):
        """Sends reset command to UART"""
        self.msgBox.setText(_fromUtf8('Are you sure you want to reset?'))
        reply = self.msgBox.exec_()
        if reply == 0:
            # reset
            try:
                self.serial.write('r')
            except:
                pass
        else:
            pass

    def plus(self):
        """Sends plus command to UART"""
        try:
            self.serial.write('+')
        except:
            pass

    def minus(self):
        """Sends minus command to UART"""
        try:
            self.serial.write('-')
        except:
            pass

    def powerSaveMode(self):
        """Sends p (power save) command to UART"""
        try:
            self.serial.write('p')
        except:
            pass

    # restart
    def restart(self):
        self.msgBox.setText(_fromUtf8('Are you sure you want to restart?'))
        reply = self.msgBox.exec_()
        if reply == 0:
            # restart
            self.stop()
            self.start()
        else:
            pass

    # start (reading dummy data)
    def start(self):
        if self.pushButton_2.text() == _fromUtf8("Start"):
            if self.f_pause:
                self.mode = 0
                self.send_timer.start(self.replay_speed)  # 1000,200,100 ms
                self.FLAG = True
                self.pushButton_2.setText(_fromUtf8("Pause"))
                self.f_pause = False
            else:
                if self.path_file == '':
                    self.msgBoxError.setText(_fromUtf8("You didn't select the data file!"))
                    self.msgBoxError.setVisible(True)
                    return
                else:
                    try:
                        self.f = open(self.path_file, "rb")  #
                        if self.mode != 0:
                            self.log_file = open(time.strftime("%Y%m%d_%H-%M-%S") + '.csv', "wb+")  # open log file
                        self.send_timer.start(self.replay_speed)  # 1000,200,100 ms
                        self.FLAG = True
                        self.pushButton_3.setEnabled(False)  # disable "Connect"
                        #
                        self.pushButton_2.setText(_fromUtf8("Pause"))
                        self.f_pause = False
                        self.mode = 0
                        #
                        self.first_time = self.getTime()[1]
                        self.time_timer.start(100)  # 100 ms
                    except:
                        self.msgBoxError.setText(_fromUtf8("Error opening file!"))
                        self.msgBoxError.setVisible(True)
                        self.pushButton_3.setEnabled(True)
                        self.pushButton_2.setText(_fromUtf8("Start"))
                        self.time_timer.stop()
                        try:
                            self.log_file.close()
                        except:
                            pass
                        return
        else:
            self.pushButton_2.setText(_fromUtf8("Start"))
            self.FLAG = False
            self.f_pause = True
            self.time_timer.stop()
            try:
                self.send_timer.stop()
            except:
                pass

    # stop read file
    def stop(self):
        self.FLAG = False
        try:
            self.send_timer.stop()
        except:
            pass
        #
        try:
            self.time_timer.stop()
        except:
            pass
        #
        self.label_11.setText(_fromUtf8('Normal'))
        self.mass_plot = []  #
        self.mass_ac_voltage = []  #
        self.mass_ac_voltage_x = []  #
        self.mass_dc_voltage = []  #
        self.mass_dc_voltage_x = []  #
        self.mass_ac_current = []  #
        self.mass_ac_current_x = []  #
        self.mass_dc_current = []  #
        self.mass_dc_current_x = []  #
        self.mass_resistance = []  #
        self.mass_resistance_x = []  #
        self.mass_test_continuity = []  #
        self.mass_test_continuity_x = []  #
        self.mass_logic_level = []  #
        self.mass_logic_level_x = []  #
        #
        self.pushButton_3.setEnabled(True)  # enable "Connect"
        self.f_pause = False
        self.pushButton_2.setText(_fromUtf8("Start"))
        self.matplotlibWidget.p.clear()  # clear plot view
        self.matplotlibWidget.area = pg.FillBetweenItem(None, None, brush=COLORS['wisteria'])
        self.matplotlibWidget.p.addItem(self.matplotlibWidget.area)
        self.matplotlibWidget.initROI(self.points_t, self.points_b)
        '''self.matplotlibWidget.p.addItem(self.matplotlibWidget.roi_t)
        self.matplotlibWidget.p.addItem(self.matplotlibWidget.roi)'''
        try:
            self.log_file.close()
        except:
            pass

    # def update(self,val):
    #    #print 'hello'
    #    pos = self.matplotlibWidget.spos.val
    #    self.matplotlibWidget.axes.axis([pos-10,pos+10,0,50])
    #    self.matplotlibWidget.canvas.draw()
    #    self.canvas.draw()

    # plotting and set multimeter
    def viewData(self, num, mode, val, rang_):
        """Plots data

        Params
            num - x position
            mode - or unit (ex. a or v for AC Voltage)
            val - y
            rang_ - limit for y"""
        #
        rang = str(rang_).strip('\r\n')
        mode = str(mode).lower()
        s = True
        try:
            num = int(num)
        except ValueError:
            s = False

        curve = None
        if s:
            if self.data_index >= 0:
                if num < self.data_index or num == 0:
                    self.resetPlot(True)
            if self.unit_mode != mode:
                self.resetPlot(False)

            self.unit_mode = mode
        #
        if self.acquisition and s:
            # digital v,dv,c,dc,r,t,l
            if mode == 'v' or mode == 'a':
                self.label_2.setText('AC Voltage')
                self.label_15.setText('V')
                self.label_7.setText(str(round(float(val), 2)))  # Voltage
                # range check
                txt = u'\u00B1'
                if rang == '12':
                    self.label_8.setText(txt + '12V')
                    if -12 <= float(val) <= 12:
                        pass
                    else:
                        self.error_range = True
                elif rang == '5':
                    self.label_8.setText(txt + '5V')
                    if -5 <= float(val) <= 5:
                        pass
                    else:
                        self.error_range = True
                elif rang == '1':
                    self.label_8.setText(txt + '1V')
                    if -1 <= float(val) <= 1:
                        pass
                    else:
                        self.error_range = True
                if self.error_range:
                    self.label_11.setText(_fromUtf8('<span style="color: red">OVER LIMIT</span>'))
                    self.error_range = False
                else:
                    self.label_11.setText(_fromUtf8('Normal'))
                self.mass_ac_voltage.append(float(val))
                self.mass_ac_voltage_x.append(int(num))
                #
                self.mass_ac_voltage_t.append(self.getTime()[0])
                self.mass_dc_voltage_t = []
                self.mass_dc_voltage = []
                self.mass_dc_voltage_x = []
                self.mass_ac_current_t = []
                self.mass_ac_current = []
                self.mass_ac_current_x = []
                self.mass_dc_current_t = []
                self.mass_dc_current = []
                self.mass_dc_current_x = []
                self.mass_resistance_t = []
                self.mass_resistance = []
                self.mass_resistance_x = []
                self.mass_test_continuity_t = []
                self.mass_test_continuity = []  #
                self.mass_test_continuity_x = []  #
                self.mass_logic_level_t = []
                self.mass_logic_level = []  #
                self.mass_logic_level_x = []  #
            elif mode == 'dv' or mode == 'b':
                self.label_2.setText('DC Voltage')
                self.label_15.setText('V')
                self.label_7.setText(str(round(float(val), 2)))  # Voltage
                txt = u'\u00B1'
                if rang == '12':
                    self.label_8.setText(txt + '12V')
                    if -12 <= float(val) <= 12:
                        pass
                    else:
                        self.error_range = True
                elif rang == '5':
                    self.label_8.setText(txt + '5V')
                    if -5 <= float(val) <= 5:
                        pass
                    else:
                        self.error_range = True
                elif rang == '1':
                    self.label_8.setText(txt + '1V')
                    if -1 <= float(val) <= 1:
                        pass
                    else:
                        self.error_range = True
                if self.error_range:
                    self.label_11.setText(_fromUtf8('<span style="color: red">OVER LIMIT</span>'))
                    self.error_range = False
                else:
                    self.label_11.setText(_fromUtf8('Normal'))
                self.mass_dc_voltage.append(float(val))
                self.mass_dc_voltage_x.append(int(num))
                #
                self.mass_dc_voltage_t.append(self.getTime()[0])
                self.mass_ac_voltage_t = []
                self.mass_ac_voltage = []
                self.mass_ac_voltage_x = []
                self.mass_ac_current_t = []
                self.mass_ac_current = []
                self.mass_ac_current_x = []
                self.mass_dc_current_t = []
                self.mass_dc_current = []
                self.mass_dc_current_x = []
                self.mass_resistance_t = []
                self.mass_resistance = []
                self.mass_resistance_x = []
                self.mass_test_continuity_t = []
                self.mass_test_continuity = []  #
                self.mass_test_continuity_x = []  #
                self.mass_logic_level_t = []
                self.mass_logic_level = []  #
                self.mass_logic_level_x = []  #
            elif mode == 'c' or mode == 'c':
                self.label_2.setText('AC Current')
                self.label_15.setText('A')
                self.label_7.setText(str(round(float(val), 2)))  # Current
                txt = u'\u00B1'
                if rang == '10':
                    self.label_8.setText(txt + '10mA')
                    if -10 <= float(val) < 10:
                        pass
                    else:
                        self.error_range = True
                elif rang == '200':
                    self.label_8.setText(txt + '200mA')
                    if -200 <= float(val) <= 200:
                        pass
                    else:
                        self.error_range = True
                if self.error_range:
                    self.label_11.setText(_fromUtf8('<span style="color: red">OVER LIMIT</span>'))
                    self.error_range = False
                else:
                    self.label_11.setText(_fromUtf8('Normal'))
                self.mass_ac_current.append(float(val))
                self.mass_ac_current_x.append(int(num))
                #
                self.mass_ac_current_t.append(self.getTime()[0])
                self.mass_dc_current_t = []
                self.mass_dc_current = []
                self.mass_dc_current_x = []
                self.mass_dc_voltage_t = []
                self.mass_dc_voltage = []
                self.mass_dc_voltage_x = []
                self.mass_ac_voltage_t = []
                self.mass_ac_voltage = []
                self.mass_ac_voltage_x = []
                self.mass_resistance_t = []
                self.mass_resistance = []
                self.mass_resistance_x = []
                self.mass_test_continuity_t = []
                self.mass_test_continuity = []  #
                self.mass_test_continuity_x = []  #
                self.mass_logic_level_t = []
                self.mass_logic_level = []  #
                self.mass_logic_level_x = []  #
            elif mode == 'dc' or mode == 'd':
                self.label_2.setText('DC Current')
                self.label_15.setText('A')
                self.label_7.setText(str(round(float(val), 2)))  # Current
                txt = u'\u00B1'
                if rang == '10':
                    self.label_8.setText(txt + '10mA')
                    if -10 <= float(val) < 10:
                        pass
                    else:
                        self.error_range = True
                elif rang == '200':
                    self.label_8.setText(txt + '200mA')
                    if -200 <= float(val) <= 200:
                        pass
                    else:
                        self.error_range = True
                if self.error_range:
                    self.label_11.setText(_fromUtf8('<span style="color: red">OVER LIMIT</span>'))
                    self.error_range = False
                else:
                    self.label_11.setText(_fromUtf8('Normal'))
                self.mass_dc_current.append(float(val))
                self.mass_dc_current_x.append(int(num))
                #
                self.mass_dc_current_t.append(self.getTime()[0])
                self.mass_ac_current_t = []
                self.mass_ac_current = []
                self.mass_ac_current_x = []
                self.mass_ac_voltage_t = []
                self.mass_ac_voltage = []
                self.mass_ac_voltage_x = []
                self.mass_dc_voltage_t = []
                self.mass_dc_voltage = []
                self.mass_dc_voltage_x = []
                self.mass_resistance_t = []
                self.mass_resistance = []
                self.mass_resistance_x = []
                self.mass_test_continuity_t = []
                self.mass_test_continuity = []  #
                self.mass_test_continuity_x = []  #
                self.mass_logic_level_t = []
                self.mass_logic_level = []  #
                self.mass_logic_level_x = []  #
            elif mode == 'r' or mode == 'e':
                self.label_2.setText('Resistance')
                self.label_15.setText('Ohm')
                self.label_7.setText(str(round(float(val), 2)))  # Resistance
                txt = u'\u03A9'
                if rang == '1':
                    self.label_8.setText('0 - 1K' + txt)
                    if 0 <= float(val) <= 1000:
                        pass
                    else:
                        self.error_range = True
                elif rang == '10':
                    self.label_8.setText('0 - 10K' + txt)
                    if 0 <= float(val) <= 10000:
                        pass
                    else:
                        self.error_range = True
                elif rang == '100':
                    self.label_8.setText('0 - 100K' + txt)
                    if 0 <= float(val) <= 100000:
                        pass
                    else:
                        self.error_range = True
                elif rang == '1000':
                    self.label_8.setText('0 - 1M' + txt)
                    if 0 < float(val) <= 1000000:
                        pass
                    else:
                        self.error_range = True
                if self.error_range:
                    self.label_11.setText(_fromUtf8('<span style="color: red">OVER LIMIT</span>'))
                    self.error_range = False
                else:
                    self.label_11.setText(_fromUtf8('Normal'))
                self.mass_resistance.append(float(val))
                self.mass_resistance_x.append(int(num))
                #
                self.mass_resistance_t.append(self.getTime()[0])
                self.mass_ac_current_t = []
                self.mass_ac_current = []
                self.mass_ac_current_x = []
                self.mass_dc_current_t = []
                self.mass_dc_current = []
                self.mass_dc_current_x = []
                self.mass_ac_voltage_t = []
                self.mass_ac_voltage = []
                self.mass_ac_voltage_x = []
                self.mass_dc_voltage_t = []
                self.mass_dc_voltage = []
                self.mass_dc_voltage_x = []
                self.mass_test_continuity_t = []
                self.mass_test_continuity = []  #
                self.mass_test_continuity_x = []  #
                self.mass_logic_level_t = []
                self.mass_logic_level = []  #
                self.mass_logic_level_x = []  #
            elif mode == 't' or mode == 'f':
                self.label_2.setText('Continuity')
                self.label_15.setText('')
                self.label_8.setText('')
                if int(val) == 0:
                    self.label_7.setText('LOW')
                elif int(val) == 1:
                    self.label_7.setText('HIGH')
                else:
                    pass
                self.label_11.setText(_fromUtf8('Normal'))
                self.mass_test_continuity_t.append(self.getTime()[0])
                self.mass_test_continuity.append(float(val))
                self.mass_test_continuity_x.append(int(num))
                self.mass_ac_current_t = []
                self.mass_ac_current = []
                self.mass_ac_current_x = []
                self.mass_dc_current_t = []
                self.mass_dc_current = []
                self.mass_dc_current_x = []
                self.mass_ac_voltage_t = []
                self.mass_ac_voltage = []
                self.mass_ac_voltage_x = []
                self.mass_dc_voltage_t = []
                self.mass_dc_voltage = []
                self.mass_dc_voltage_x = []
                self.mass_resistance_t = []
                self.mass_resistance = []
                self.mass_resistance_x = []
                self.mass_logic_level_t = []
                self.mass_logic_level = []  #
                self.mass_logic_level_x = []  #
            elif mode == 'l' or mode == 'g':
                self.label_2.setText('Logic Level')
                self.label_15.setText('')
                self.label_8.setText('')
                # FIX FIX FIX
                if int(val) == 0:
                    self.label_7.setText('LOW')
                elif int(val) == 1:
                    self.label_7.setText('HIGH')
                else:
                    pass
                self.label_11.setText(_fromUtf8('Normal'))
                self.mass_logic_level_t.append(self.getTime()[0])
                self.mass_logic_level.append(float(val))
                self.mass_logic_level_x.append(int(num))
                self.mass_ac_current_t = []
                self.mass_ac_current = []
                self.mass_ac_current_x = []
                self.mass_dc_current_t = []
                self.mass_dc_current = []
                self.mass_dc_current_x = []
                self.mass_ac_voltage_t = []
                self.mass_ac_voltage = []
                self.mass_ac_voltage_x = []
                self.mass_dc_voltage_t = []
                self.mass_dc_voltage = []
                self.mass_dc_voltage_x = []
                self.mass_resistance_t = []
                self.mass_resistance = []
                self.mass_resistance_x = []
                self.mass_test_continuity_t = []
                self.mass_test_continuity = []  #
                self.mass_test_continuity_x = []  #
            else:
                pass

            if self.mode == 1:
                self.mass_time.append(self.getTime()[1])
                line = str(num) + ',' + str(mode) + ',' + str(val) + ',' + str(rang) + ',' + self.getTime()[1] + '\r\n'
                self.log_file.write(line)  # write log file

            self.matplotlibWidget.p.setLabel('left', '')
            self.matplotlibWidget.p.setLabel('bottom', '')
            # plotting
            if len(self.mass_ac_voltage) != 0:
                curve = self.matplotlibWidget.p.plot(self.mass_ac_voltage_x, self.mass_ac_voltage,
                                                     pen=COLORS['red'])  # ,label='Voltage,V')
                self.matplotlibWidget.p.setLabel('left', 'V')
                self.matplotlibWidget.p.setLabel('bottom', 'deciseconds')
            elif len(self.mass_dc_voltage) != 0:
                curve = self.matplotlibWidget.p.plot(self.mass_dc_voltage_x, self.mass_dc_voltage,
                                                     pen=COLORS['red'])  # ,label='Voltage,V')
                self.matplotlibWidget.p.setLabel('left', 'V')
                self.matplotlibWidget.p.setLabel('bottom', 'deciseconds')
            elif len(self.mass_ac_current) != 0:
                curve = self.matplotlibWidget.p.plot(self.mass_ac_current_x, self.mass_ac_current,
                                                     pen=COLORS['green'])  # ,label='Current,A')
                self.matplotlibWidget.p.setLabel('left', 'A')
                self.matplotlibWidget.p.setLabel('bottom', 'deciseconds')
            elif len(self.mass_dc_current) != 0:
                curve = self.matplotlibWidget.p.plot(self.mass_dc_current_x, self.mass_dc_current,
                                                     pen=COLORS['green'])  # ,label='Current,A')
                self.matplotlibWidget.p.setLabel('left', 'A')
                self.matplotlibWidget.p.setLabel('bottom', 'deciseconds')
            elif len(self.mass_resistance) != 0:
                curve = self.matplotlibWidget.p.plot(self.mass_resistance_x, self.mass_resistance,
                                                     pen=COLORS['blue'])  # ,label='Resistance, Om')
                self.matplotlibWidget.p.setLabel('left', 'Ohm')
                self.matplotlibWidget.p.setLabel('bottom', 'deciseconds')
            elif len(self.mass_test_continuity) != 0:
                curve = self.matplotlibWidget.p.plot(self.mass_test_continuity_x, self.mass_test_continuity,
                                                     pen=COLORS['cyan'])  # ,label='Resistance, Om')
                self.matplotlibWidget.p.setLabel('left', 'TEST')
                self.matplotlibWidget.p.setLabel('bottom', 'deciseconds')
            elif len(self.mass_logic_level) != 0:
                t = self.mass_logic_level_t[-1]
                curve = self.matplotlibWidget.p.plot(self.mass_logic_level_x, self.mass_logic_level,
                                                     pen=COLORS['yellow'])  # ,label='Resistance, Om')
                self.matplotlibWidget.p.setLabel('left', 'HIGH, LOW')
                self.matplotlibWidget.p.setLabel('bottom', 'deciseconds')
            else:
                pass
            try:
                if curve:
                    self.matplotlibWidget.updateTopLimit(curve.xData[-1])
                    self.matplotlibWidget.updateBottomLimit(curve.xData[-1])
            except BaseException:
                pass
            try:
                if curve:
                    self.data_index = int(curve.xData[-1])
                    if self.matplotlibWidget.roi_t and self.matplotlibWidget.roi_b:
                        if not ((self.topCurveEq(float(curve.xData[-1])) >= curve.yData[-1]) and (
                                    curve.yData[-1] >= self.bottomCurveEq(float(curve.xData[-1])))):
                            self.label_12.setText(_fromUtf8('<span style="color: red">FAIL</span>'))
                            try:
                                if str(float(curve.xData[-2])) == self.fail_states[-1]:
                                    record = '%s - %s' % (self.fail_states[-1], str(float(curve.xData[-1])))
                                    self.fail_states.pop()
                                    self.fail_states.append(record)
                                elif str(float(curve.xData[-2])) == self.fail_states[-1].split(' - ')[-1]:
                                    record = '%s - %s' % (
                                        self.fail_states[-1].split(' - ')[0], str(float(curve.xData[-1])))
                                    self.fail_states.pop()
                                    self.fail_states.append(record)
                                else:
                                    record = str(float(curve.xData[-1]))
                                    self.fail_states.append(record)
                                self.label_13.setText(_fromUtf8(','.join(self.fail_states)))
                            except IndexError:
                                record = str(float(curve.xData[-1]))
                                self.fail_states.append(record)
                                self.label_13.setText(_fromUtf8(','.join(self.fail_states)))
                            data_line = str(curve.xData[-1]) + ',' + str(mode) + ',' + str(curve.yData[-1]) \
                                        + ',' + str(rang) + ',' + self.readable_mode + '\r\n'
                            self.emit(QtCore.SIGNAL('MaskData(QString)'), str(data_line))
                        else:
                            self.label_12.setText(_fromUtf8('<span style="color: green">PASS</span>'))
            except BaseException:
                pass

    def saveMaskTesting(self, data_line):
        """Saves fail results of mask testing

        Params
            data_line - x,mode (unit),y,rang,mode (disconnected or connected)"""
        try:
            data = open('mask_testing.csv', 'rb')
            data = data.read()
        except IOError:
            data = None
        with open('mask_testing.csv', "wb+") as mask_file:
            if data:
                mask_file.write(data)
            mask_file.write(data_line)
            mask_file.close()

    def resetPlot(self, with_time):
        """Resets plot

        Params
            with_time - if True it deletes timestamps, else not"""
        self.label_13.setText(_fromUtf8('-----'))
        self.label_12.setText(_fromUtf8('---'))
        self.fail_states = []
        if with_time:
            self.mass_time = []
        self.matplotlibWidget.p.clear()
        self.matplotlibWidget.area = pg.FillBetweenItem(None, None, brush=COLORS['wisteria'])
        self.matplotlibWidget.p.addItem(self.matplotlibWidget.area)
        self.matplotlibWidget.initROI(self.points_t, self.points_b)

    # start thread
    def StartThread(self):
        self.thread = threading.Thread(target=self.fileReadTread)
        self.alive.set()
        self.thread.start()

    # stop thread
    def StopThread(self):
        if self.thread is not None:
            self.alive.clear()  # clear alive event for thread
            self.thread = None

    # file read thread
    def fileReadTread(self):
        while self.alive.isSet():
            if self.FLAG:
                # read file
                if self.mode == 0:
                    self.readable_mode = 'File: %s' % self.path_file
                    text = self.f.readline()  # read before \r\n
                    if text:
                        try:
                            text = text.replace('\x00', '')
                            tokens = text.split(',')
                            number = tokens[0]  # number sample
                            typ = tokens[1]  # mode
                            value = tokens[2]  # value
                            rang = tokens[3]  # range
                            try:
                                timestamp = tokens[4]
                                self.mass_time.append(timestamp)
                            except:
                                pass
                            self.emit(QtCore.SIGNAL('OutputData(QString,QString,QString,QString)'), str(number),
                                      str(typ), str(value), str(rang))  # signal for update
                            self.FLAG = False  # reset flag
                        except:
                            pass
                    else:
                        self.resetPlot(True)
                        self.send_timer.stop()
                        self.time_timer.stop()
                        self.stop()

                # read serial port
                else:
                    self.readable_mode = 'Connected mode'
                    text = self.serial.readline()  # port
                    if text:
                        text = text.replace('\x00', '')
                        tokens = text.split(',')
                        if len(tokens) == 4:
                            number = tokens[0]  # number sample
                            typ = tokens[1]  # mode
                            value = tokens[2]  # value
                            rang = tokens[3]  # range
                            self.emit(QtCore.SIGNAL('OutputData(QString,QString,QString,QString)'), str(number),
                                      str(typ), str(value), str(rang))  # signal for update
                    else:
                        pass
                    # time.sleep(0.05)  # timeout 50ms

    # close event
    def closeEvent(self, event):
        self.FLAG = False
        if self.thread is not None:
            self.alive.clear()  # clear alive event for thread
            self.thread = None
        try:
            self.f.close()  # data file
            self.log_file.close()  # log file
            self.serial.close()  #
        except:
            pass

    def exportLimits(self):
        """Exports limits to file"""
        points_t = self.matplotlibWidget.roi_t.lastState['points']
        points_b = self.matplotlibWidget.roi_b.lastState['points']
        units = str(self.label_15.text()).lower()
        with open('limits_%s.csv' % units, 'w') as limits:
            for p in points_t:
                line = 'high,%s,%s,%s\n' % (p[0], p[1], units)
                limits.write(line)
            for p in points_b:
                line = 'low,%s,%s,%s\n' % (p[0], p[1], units)
                limits.write(line)
        limits.close()

    def importLimits(self):
        """Imports limits from file, checks mask"""
        units = str(self.label_15.text()).lower().strip()
        points_t = []
        points_b = []
        success = False
        self.dialogTXT.setDirectory(os.getcwd())
        if self.dialogTXT.exec_():
            pp = self.dialogTXT.selectedFiles()
            self.path_file = pp[0]  #
            ff = unicode(pp[0]).encode('CP1251')
            tokens1 = ff.split("/")  #
            p1 = len(tokens1[len(tokens1) - 1]) + 1  #
            l = len(ff) - p1  #
            tt = ff[:l]  #
            tokens = pp[0].split("/")
            p = tokens[len(tokens) - 1]
            with open(p, 'r') as limits:
                for line in limits.readlines():
                    if line != '\n':
                        params = line.split(',')
                        l, point_x, point_y, unit = params[0], float(params[1]), float(params[2]), params[3].strip()
                        print "Provided log file unit: {}, Application current unit: {}".format(unit, units)
                        if unit != units:
                            self.msgBoxError.setText(_fromUtf8("You are import wrong units file!!!"))
                            self.msgBoxError.setVisible(True)
                        else:
                            success = True
                            if l == 'high':
                                points_t.append([point_x, point_y])
                            elif l == 'low':
                                points_b.append([point_x, point_y])
                            else:
                                success = False
                                self.msgBoxError.setText(_fromUtf8("Your file is corrupted!!!"))
                                self.msgBoxError.setVisible(True)
        if success:
            self.points_t = points_t
            self.points_b = points_b
            for p in self.points_t:
                if self.bottomCurveEq(p[0]):
                    if self.bottomCurveEq(p[0]) > p[1]:
                        success = False
                        self.msgBoxError.setText(_fromUtf8("Your mask is corrupted [Overlap]!!!"))
                        self.msgBoxError.setVisible(True)
            for p in self.points_b:
                if self.topCurveEq(p[0]):
                    if self.topCurveEq(p[0]) < p[1]:
                        success = False
                        self.msgBoxError.setText(_fromUtf8("Your mask is corrupted [Overlap]!!!"))
                        self.msgBoxError.setVisible(True)
        if success:
            self.matplotlibWidget.initROI(points_t, points_b)
            self.matplotlibWidget.createTopCurve(None)
            self.matplotlibWidget.createBottomCurve(None)
            self.matplotlibWidget.updateArea()
        else:
            self.points_t = []
            self.points_b = []


# launch
app = QtGui.QApplication(sys.argv)
form = MWindow()
form.show()
app.exec_()
