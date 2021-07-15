###################################################################################
# This module manages all graphic related operations such as use paint tools
#
####################################################################################

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QLabel,QGraphicsScene,QGraphicsView
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt,QPoint, QLine, QRect



class Calibration(QLabel):

    def __init__(self, parent = None):
        QLabel.__init__(self,parent)
        self.setEnabled(False)
        self.lower()
        self.setGeometry(QRect(0, 0, 1024, 576))
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setFrameShape(QtWidgets.QFrame.Box)
        self.setCursor(Qt.CrossCursor)
        # force trasparent to override application style
        self.setStyleSheet("background-color: rgba(0,0,0,0%)")
        self.pen = QPen(Qt.red, 2, Qt.SolidLine)

        self.begin = QPoint()
        self.end = QPoint()
        self.lines = []
        self.draw_flag = False
        self.erase_flag = False

    # Mouse click event
    def mousePressEvent(self, event):
        self.lines.clear()
        self.erase_flag = False
        self.begin = self.end = event.pos()
        self.update()
        # call super for mousePressEvent for the original handler to kick in
        # and pass the QMouseEvent instance to the original handler
        # that is, passing all other button clicks
        super().mousePressEvent(event)

    # Mouse release event
    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()
        super().mouseMoveEvent(event)

    # Mouse movement events
    def mouseReleaseEvent(self, event):
        line = QLine(self.begin, self.end)
        self.lines.append(line)
        # reset
        self.begin = self.end = QPoint()
        self.update()
        super().mouseReleaseEvent(event)

     #Draw events
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(self.pen)
        if self.erase_flag:
            self.lines.clear()
            # self.update()
        else:
            for line in self.lines:
                painter.drawLine(line)
            # draw continuously when mouse is moving
            if not self.begin.isNull() and not self.end.isNull():
                painter.drawLine(self.begin,self.end)

    def erase(self):
        self.erase_flag = True
        self.update()

class DefineROI(QLabel):

    def __init__(self,parent = None):
        QLabel.__init__(self,parent)
        self.setEnabled(False)
        self.lower()
        self.setGeometry(QtCore.QRect(0, 0, 1024, 576))
        self.setObjectName("roiCanvas")
        self.setFrameShape(QtWidgets.QFrame.Box)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setCursor(Qt.CrossCursor)
        # force trasparent to override application style
        self.setStyleSheet("background-color: rgba(0,0,0,0%)")
        self.pen = QPen(Qt.red,2,Qt.SolidLine)
        self.begin = QPoint()
        self.end = QPoint()

        self.lines = []
        self.rectangles = []
        self.circles = []
        # list for all shapes for global indexing
        self.zones = []

        self.roi_list = list(range(1, 100))
        # the elements in this list needs to be in string format
        self.roi_id = [format(x, '01d') for x in self.roi_list]

        self.erase_flag = False
        self.line_flag = False
        self.rect_flag = False
        self.circ_flag = False


        # Mouse click event

    def mousePressEvent(self, event):
        self.erase_flag = False
        self.begin = self.end = event.pos()
        self.update()
        # call super for mousePressEvent for the original handler to kick in
        # and pass the QMouseEvent instance to the original handler
        # that is, passing all other button clicks
        super().mousePressEvent(event)


    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()
        super().mouseMoveEvent(event)


    def mouseReleaseEvent(self, event):
        # self.erase_flag = False
        if self.line_flag:
            line = QLine(self.begin,self.end)
            self.lines.append(line)

        elif self.rect_flag:
            rect = QRect(self.begin,self.end).normalized()
            self.rectangles.append(rect)
            # add in global list
            self.zones.append(rect)

        elif self.circ_flag:
            circ = QRect(self.begin,self.end).normalized()
            self.circles.append(circ)
            # add in global list
            self.zones.append(circ)

        # reset
        self.begin = self.end = QPoint()
        self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(self.pen)

        if self.erase_flag:
            self.lines.clear()
            self.rectangles.clear()
            self.circles.clear()
            self.zones.clear()


        elif self.line_flag:
            for line in self.lines:
                painter.drawLine(line)
            # draw continuously when mouse is moving
            if not self.begin.isNull() and not self.end.isNull():
                painter.drawLine(self.begin,self.end)

            for rect in self.rectangles:
                painter.drawRect(rect)
                painter.drawText(rect, Qt.AlignCenter,'Zone'+ str(self.zones.index(rect)+1))
            for circ in self.circles:
                painter.drawEllipse(circ)
                painter.drawText(circ, Qt.AlignCenter, 'Zone' + str(self.zones.index(circ) + 1))

        elif self.rect_flag:
            for rect in self.rectangles:
                painter.drawRect(rect)
                # print(self.rectangles.index(rect))
                # the corresponding index of each rect from the global list
                painter.drawText(rect, Qt.AlignCenter,'Zone'+ str(self.zones.index(rect)+1))

            # draw continuously when mouse is moving
            if not self.begin.isNull() and not self.end.isNull():
                painter.drawRect(QRect(self.begin,self.end).normalized())

            for line in self.lines:
                painter.drawLine(line)
            for circ in self.circles:
                painter.drawEllipse(circ)
                painter.drawText(circ, Qt.AlignCenter, 'Zone' + str(self.zones.index(circ) + 1))

        elif self.circ_flag:
            for circ in self.circles:
                painter.drawEllipse(circ)
                # the corresponding index of each circ from the global list
                painter.drawText(circ, Qt.AlignCenter, 'Zone' + str(self.zones.index(circ) + 1))
            # draw continuously when mouse is moving
            if not self.begin.isNull() and not self.end.isNull():
                painter.drawEllipse(QRect(self.begin,self.end).normalized())

            for line in self.lines:
                painter.drawLine(line)
            for rect in self.rectangles:
                painter.drawRect(rect)
                painter.drawText(rect, Qt.AlignCenter,'Zone'+ str(self.zones.index(rect)+1))

    def erase(self):
        self.erase_flag = True
        self.update()

    def drawLine(self):
        self.line_flag = True
        self.rect_flag = False
        self.circ_flag = False

    def drawRect(self):
        self.line_flag = False
        self.rect_flag = True
        self.circ_flag = False

    def drawCirc(self):
        self.line_flag = False
        self.rect_flag = False
        self.circ_flag = True
