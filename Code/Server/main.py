import io
import os
import socket
import struct
import time
import sys,getopt
from thread import *
from threading import Thread
from server import Server
from server_ui import Ui_server_ui
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *


class mywindow(QMainWindow,Ui_server_ui):
    
    def __init__(self):
        self.user_ui=True
        self.start_tcp=False
        self.TCP_Server=Server()
        self.parseOpt()
        if self.user_ui:
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("SERVER")
            self.app.setApplicationDisplayName("SERVER")
            super(mywindow,self).__init__()
            self.setupUi(self)
            self.setWindowTitle("SERVER")
            self.m_DragPosition=self.pos()
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.setMouseTracking(True)
            try:
                self.label_ip.setText("IP: " + str(self.TCP_Server.get_interface_ip()))
            except Exception:
                self.label_ip.setText("IP: unavailable")
            self.Button_Server.setText("On")
            self.on_pushButton()
            self.Button_Server.clicked.connect(self.on_pushButton)
            self.pushButton_Close.clicked.connect(self.close)
            self.pushButton_Min.clicked.connect(self.windowMinimumed)
            # Poll the battery voltage (published by the Power thread) and show it
            # in the window: green normally, bold red when low.
            self.batt_timer = QTimer(self)
            self.batt_timer.timeout.connect(self._update_battery_label)
            self.batt_timer.start(1500)
        
        if self.start_tcp:
            self.TCP_Server.StartTcpServer()
            self.ReadData=Thread(target=self.TCP_Server.readdata)
            self.SendVideo=Thread(target=self.TCP_Server.sendvideo)
            self.power=Thread(target=self.TCP_Server.Power)
            self.SendVideo.start()
            self.ReadData.start()
            self.power.start()
            if self.user_ui:
                self.label.setText("Server On")
                self.Button_Server.setText("Off")
                
    def _update_battery_label(self):
        """Show the latest battery voltage in the window (red+bold when low)."""
        voltage = getattr(self.TCP_Server, "last_battery", 0)
        if voltage < 3:
            self.label_battery.setText("Battery: no power")
            self.label_battery.setStyleSheet("background:transparent;border:none;color:#9aa0a8;")
        elif voltage < 7.0:
            self.label_battery.setText("Battery: %.2f V  -  LOW" % voltage)
            self.label_battery.setStyleSheet("background:transparent;border:none;color:#e02d2d;font-weight:bold;")
        else:
            self.label_battery.setText("Battery: %.2f V" % voltage)
            self.label_battery.setStyleSheet("background:transparent;border:none;color:#21c46a;")

    def windowMinimumed(self):
        self.showMinimized()
    def mousePressEvent(self, event):
        if event.button()==Qt.LeftButton:
            self.m_drag=True
            self.m_DragPosition=event.globalPos()-self.pos()
            event.accept()
 
    def mouseMoveEvent(self, QMouseEvent):
        if QMouseEvent.buttons() and Qt.LeftButton:
            self.move(QMouseEvent.globalPos()-self.m_DragPosition)
            QMouseEvent.accept()
 
    def mouseReleaseEvent(self, QMouseEvent):
        self.m_drag=False
        
    def parseOpt(self):
        self.opts,self.args = getopt.getopt(sys.argv[1:],"tn")
        for o,a in self.opts:
            if o in ('-t'):
                print ("Open TCP")
                self.start_tcp=True
            elif o in ('-n'):
                self.user_ui=False
                        
    def close(self):
        try:
           stop_thread(self.SendVideo)
           stop_thread(self.ReadData)
           stop_thread(self.power)
        except:
            pass
        try:
            self.TCP_Server.server_socket.shutdown(2)
            self.TCP_Server.server_socket1.shutdown(2)
            self.TCP_Server.StopTcpServer()
        except:
            pass
        print ("Close TCP")
        if self.user_ui:
            QCoreApplication.instance().quit()
        os._exit(0)
    def _set_status(self, running):
        """Update the status label (green=On / red=Off, bold) and the button."""
        if running:
            self.label.setText("Server On")
            self.label.setStyleSheet("background:transparent;border:none;color:#21c46a;")
            self.Button_Server.setText("Off")
        else:
            self.label.setText("Server Off")
            self.label.setStyleSheet("background:transparent;border:none;color:#e02d2d;")
            self.Button_Server.setText("On")

    def on_pushButton(self):
        if self.label.text()=="Server Off":
            self._set_status(True)
            self.TCP_Server.tcp_Flag = True
            print ("Open TCP")
            try:
                self.TCP_Server.StartTcpServer()
                self.SendVideo=Thread(target=self.TCP_Server.sendvideo)
                self.ReadData=Thread(target=self.TCP_Server.readdata)
                self.power=Thread(target=self.TCP_Server.Power)
                self.SendVideo.start()
                self.ReadData.start()
                self.power.start()
            except Exception as e:
                # Never let a start-up hiccup crash the GUI; roll the button back.
                print("Could not start server:", e)
                self.TCP_Server.StopTcpServer()
                self._set_status(False)

        elif self.label.text()=='Server On':
            self._set_status(False)
            self.TCP_Server.tcp_Flag = False
            try:
                stop_thread(self.ReadData)
                stop_thread(self.power)
                stop_thread(self.SendVideo)
            except:
                pass
            self.TCP_Server.StopTcpServer()
            print ("Close TCP")
            
if __name__ == '__main__':
    myshow=mywindow()
    if myshow.user_ui==True:
        myshow.show();   
        sys.exit(myshow.app.exec_())
    else:
        try:
            pass
        except KeyboardInterrupt:
            myshow.close()
