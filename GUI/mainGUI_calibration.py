from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QStyle, QApplication,QLabel,QWidget,QGraphicsLineItem
from PyQt5.QtGui import QImage, QPixmap,QPainter, QPen
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QObject, QMutex, QMutexLocker,QRect, QLine


import cv2, imutils
import time
from collections import namedtuple
from datetime import datetime, timedelta
import mainGUI


class Drawing(QLabel):

    def __init__(self, parent = None):
        QLabel.__init__(self,parent)

        self.x0 = 0
        self.y0 = 0
        self.x1 = 0
        self.y1 = 0
        self.line_coordinates = []
        self.draw_flag = False
        self.erase_flag = False

    # Mouse click event
    def mousePressEvent(self, event):
        self.draw_flag = True
        self.erase_flag = False
        self.line_coordinates.clear()
        self.x0 = event.x()
        self.y0 = event.y()
        self.x1 = self.x0
        self.y1 = self.y0
        print(self.x0,self.y0)
        start = (self.x0, self.y0)
        self.line_coordinates.append(start)

    # Mouse release event
    def mouseReleaseEvent(self, event):
        self.draw_flag = False
        self.erase_flag = False
        end = (self.x1, self.y1)
        self.line_coordinates.append(end)

    # Mouse movement events
    def mouseMoveEvent(self, event):
        if self.draw_flag:
            self.x1 = event.x()
            self.y1 = event.y()
            self.update()

     #Draw events
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        # painter = QGraphicsLineItem(self)
        if self.erase_flag:
            # painter.clear()
            self.x0 = 0
            self.y0 = 0
            self.x1 = 0
            self.y1 = 0
            # self.update()
        else:
            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            # rect =QRect(self.x0, self.y0, abs(self.x1-self.x0), abs(self.y1-self.y0))
            # painter.drawRect(rect)
            self.newline = QLine(self.x0,self.y0,self.x1,self.y1)
            painter.drawLine(self.newline)

    def earse(self):
        self.erase_flag = True
        self.update()


# class Calibrate():
#
#     def __init__(self):
#
#         self.draw = Drawing()
#
#     def logScale(self):
#         t = self.draw.logdata(self)
#         print(f'log scale for cal is {t}')