# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\Freenove\Desktop\树莓派四轮车项目\四轮车（python3+pyqt5）代码\server_ui.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_server_ui(object):
    def setupUi(self, server_ui):
        server_ui.setObjectName("server_ui")
        server_ui.resize(400, 300)
        font = QtGui.QFont()
        font.setFamily("3ds")
        server_ui.setFont(font)
        server_ui.setStyleSheet("""
QWidget { background:#23272e; color:#e8eaed; font-family:"DejaVu Sans","Segoe UI",sans-serif; font-size:11px; }
QPushButton {
  border:1px solid #3a3f47; border-radius:7px; padding:6px 10px; color:#e8eaed;
  background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #3b4049,stop:1 #2e333b);
}
QPushButton:hover { background:#00c2a3; color:#0b0f14; border-color:#00c2a3; }
QPushButton:pressed { background:#009d84; color:#ffffff; }
QPushButton:checked { background:#00c2a3; color:#0b0f14; border:1px solid #19e3c4; }
QPushButton:disabled { color:#7a818c; background:#2a2e35; }
QLabel { color:#e8eaed; border:1px solid #15181d; border-radius:7px; background:#15181d; }
QLineEdit {
  border:1px solid #3a3f47; border-radius:7px; padding:5px 9px; background:#15181d; color:#e8eaed;
  selection-background-color:#00c2a3; selection-color:#0b0f14;
}
QLineEdit:focus { border:1px solid #00c2a3; }
QCheckBox { color:#e8eaed; spacing:7px; background:transparent; border:none; }
QCheckBox::indicator { width:16px; height:16px; border-radius:4px; border:1px solid #3a3f47; background:#15181d; }
QCheckBox::indicator:hover { border:1px solid #00c2a3; }
QCheckBox::indicator:checked { background:#00c2a3; border:1px solid #00c2a3; }
QSlider::groove:horizontal { height:6px; border-radius:3px; background:#15181d; }
QSlider::sub-page:horizontal { height:6px; border-radius:3px; background:#00c2a3; }
QSlider::add-page:horizontal { height:6px; border-radius:3px; background:#15181d; }
QSlider::handle:horizontal { width:16px; margin:-6px 0; border-radius:8px; background:#e8eaed; }
QSlider::handle:horizontal:hover { background:#ffffff; }
QSlider::groove:vertical { width:6px; border-radius:3px; background:#15181d; }
QSlider::sub-page:vertical { width:6px; border-radius:3px; background:#15181d; }
QSlider::add-page:vertical { width:6px; border-radius:3px; background:#00c2a3; }
QSlider::handle:vertical { height:16px; margin:0 -6px; border-radius:8px; background:#e8eaed; }
QSlider::handle:vertical:hover { background:#ffffff; }
""")
        self.label = QtWidgets.QLabel(server_ui)
        self.label.setGeometry(QtCore.QRect(100, 150, 200, 42))
        font = QtGui.QFont()
        font.setFamily("3ds")
        font.setPointSize(26)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.Button_Server = QtWidgets.QPushButton(server_ui)
        self.Button_Server.setGeometry(QtCore.QRect(150, 220, 100, 40))
        font = QtGui.QFont()
        font.setFamily("3ds")
        font.setPointSize(12)
        self.Button_Server.setFont(font)
        self.Button_Server.setObjectName("Button_Server")
        self.label_2 = QtWidgets.QLabel(server_ui)
        self.label_2.setGeometry(QtCore.QRect(0, 0, 301, 41))
        font = QtGui.QFont()
        font.setFamily("3ds")
        font.setPointSize(28)
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setStyleSheet("")
        self.label_2.setObjectName("label_2")
        self.pushButton_Close = QtWidgets.QPushButton(server_ui)
        self.pushButton_Close.setGeometry(QtCore.QRect(350, 0, 50, 40))
        font = QtGui.QFont()
        font.setFamily("3ds")
        self.pushButton_Close.setFont(font)
        self.pushButton_Close.setObjectName("pushButton_Close")
        self.pushButton_Min = QtWidgets.QPushButton(server_ui)
        self.pushButton_Min.setGeometry(QtCore.QRect(300, 0, 50, 40))
        font = QtGui.QFont()
        font.setFamily("3ds")
        self.pushButton_Min.setFont(font)
        self.pushButton_Min.setObjectName("pushButton_Min")

        self.retranslateUi(server_ui)
        QtCore.QMetaObject.connectSlotsByName(server_ui)

    def retranslateUi(self, server_ui):
        _translate = QtCore.QCoreApplication.translate
        server_ui.setWindowTitle(_translate("server_ui", "Form"))
        self.label.setText(_translate("server_ui", "Server Off"))
        self.Button_Server.setText(_translate("server_ui", "Off"))
        self.label_2.setText(_translate("server_ui", "freenove"))
        self.pushButton_Close.setText(_translate("server_ui", "×"))
        self.pushButton_Min.setText(_translate("server_ui", "-"))

