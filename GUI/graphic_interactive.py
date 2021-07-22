###################################################################################
# This module manages all graphic related operations such as use paint tools
#
####################################################################################

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QLabel, QInputDialog, QGraphicsScene, QGraphicsView, QGraphicsLineItem, \
    QGraphicsRectItem, QGraphicsEllipseItem,QGraphicsItem
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt, QPoint, QPointF,QLine, QLineF, QRect,QRectF, pyqtSignal, QObject
import math


# class Calibration_deprecated(QLabel):
#
#     def __init__(self, parent = None):
#         QLabel.__init__(self,parent)
#         self.setEnabled(False)
#         self.lower()
#         self.setGeometry(QRect(0, 0, 1024, 576))
#         self.setAlignment(QtCore.Qt.AlignCenter)
#         self.setFrameShape(QtWidgets.QFrame.Box)
#         self.setCursor(Qt.CrossCursor)
#         # force trasparent to override application style
#         self.setStyleSheet("background-color: rgba(0,0,0,0%)")
#         self.pen = QPen(Qt.red, 2, Qt.SolidLine)
#
#         self.begin = QPoint()
#         self.end = QPoint()
#         self.lines = []
#         self.draw_flag = False
#         self.erase_flag = False
#
#     # Mouse click event
#     def mousePressEvent(self, event):
#         self.lines.clear()
#         self.erase_flag = False
#         self.begin = self.end = event.pos()
#         self.update()
#         # call super for mousePressEvent for the original handler to kick in
#         # and pass the QMouseEvent instance to the original handler
#         # that is, passing all other button clicks
#         super().mousePressEvent(event)
#
#     # Mouse release event
#     def mouseMoveEvent(self, event):
#         self.end = event.pos()
#         self.update()
#         super().mouseMoveEvent(event)
#
#     # Mouse movement events
#     def mouseReleaseEvent(self, event):
#         line = QLine(self.begin, self.end)
#         self.lines.append(line)
#         # reset
#         self.begin = self.end = QPoint()
#         self.update()
#         super().mouseReleaseEvent(event)
#
#      #Draw events
#     def paintEvent(self, event):
#         super().paintEvent(event)
#         painter = QPainter(self)
#         painter.setPen(self.pen)
#         if self.erase_flag:
#             self.lines.clear()
#             # self.update()
#         else:
#             for line in self.lines:
#                 painter.drawLine(line)
#             # draw continuously when mouse is moving
#             if not self.begin.isNull() and not self.end.isNull():
#                 painter.drawLine(self.begin,self.end)
#
#     def erase(self):
#         self.erase_flag = True
#         self.update()

class DefineROI_deprecated(QLabel):

    def __init__(self, parent=None):
        QLabel.__init__(self, parent)
        self.setEnabled(False)
        self.lower()
        self.setGeometry(QtCore.QRect(0, 0, 1024, 576))
        self.setObjectName("roiCanvas")
        self.setFrameShape(QtWidgets.QFrame.Box)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setCursor(Qt.CrossCursor)
        # force trasparent to override application style
        self.setStyleSheet("background-color: rgba(0,0,0,0%)")
        self.pen = QPen(Qt.red, 2, Qt.SolidLine)
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
            line = QLine(self.begin, self.end)
            self.lines.append(line)

        elif self.rect_flag:
            rect = QRect(self.begin, self.end).normalized()
            self.rectangles.append(rect)
            # add in global list
            self.zones.append(rect)

        elif self.circ_flag:
            circ = QRect(self.begin, self.end).normalized()
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
                painter.drawLine(self.begin, self.end)

            for rect in self.rectangles:
                painter.drawRect(rect)
                painter.drawText(rect, Qt.AlignCenter, 'Zone' + str(self.zones.index(rect) + 1))
            for circ in self.circles:
                painter.drawEllipse(circ)
                painter.drawText(circ, Qt.AlignCenter, 'Zone' + str(self.zones.index(circ) + 1))

        elif self.rect_flag:
            for rect in self.rectangles:
                painter.drawRect(rect)
                # print(self.rectangles.index(rect))
                # the corresponding index of each rect from the global list
                painter.drawText(rect, Qt.AlignCenter, 'Zone' + str(self.zones.index(rect) + 1))

            # draw continuously when mouse is moving
            if not self.begin.isNull() and not self.end.isNull():
                painter.drawRect(QRect(self.begin, self.end).normalized())

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
                painter.drawEllipse(QRect(self.begin, self.end).normalized())

            for line in self.lines:
                painter.drawLine(line)
            for rect in self.rectangles:
                painter.drawRect(rect)
                painter.drawText(rect, Qt.AlignCenter, 'Zone' + str(self.zones.index(rect) + 1))

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


class Calibration(QGraphicsView):

    def __init__(self, parent=None):
        QGraphicsView.__init__(self, parent)
        self.setEnabled(False)
        self.lower()
        self.setGeometry(QtCore.QRect(0, 0, 1024, 576))
        self.scene = CalibrationScene()
        self.setScene(self.scene)
        self.setAlignment(Qt.AlignTop)
        self.setAlignment(Qt.AlignLeft)
        self.setCursor(Qt.CrossCursor)
        # force trasparent to override application style
        self.setStyleSheet("background-color: rgba(0,0,0,0%)")
        rcontent = self.contentsRect()
        self.setSceneRect(0, 0, rcontent.width(), rcontent.height())


class CalibrationScene(QGraphicsScene):

    def __init__(self, parent=None):
        QGraphicsScene.__init__(self, parent)
        # self.setSceneRect(0, 0, 450, 250)

        self.inputDialog = ScaleInput()
        self.erase_flag = False

        self.begin = QPointF()
        self.end = QPointF()
        self.pen = QPen(Qt.yellow, 2)

        self.new_line = None
        self.arrow = None

        self.lines = []

    # Mouse click event
    def mousePressEvent(self, event):
        self.lines.clear()
        self.erase_flag = False
        self.begin = self.end = event.scenePos()

        # if there are no items at this position.
        if self.itemAt(event.scenePos(), QtGui.QTransform()) is None:
            self.new_line = QGraphicsLineItem()
            # self._current_line_item.setFlag(QGraphicsItem.ItemIsMovable, True)
            self.new_line.setPen(self.pen)
            self.addItem(self.new_line)

            line = QLineF(self.begin.x(), self.begin.y(), self.end.x(), self.end.y())
            self.new_line.setLine(line)
            # init arrow item
            self.arrow_head = ArrowPath(origin=self.begin, destination=self.end, pen=self.pen)
            self.arrow_tail = ArrowPath(origin=self.begin, destination=self.end, pen=self.pen)
            self.addItem(self.arrow_head)
            self.addItem(self.arrow_tail)

        self.update()
        # call super for mousePressEvent for the original handler to kick in
        # and pass the QMouseEvent instance to the original handler
        # that is, passing all other button clicks
        super().mousePressEvent(event)
        print(self.begin)

    # Mouse release event
    def mouseMoveEvent(self, event):
        self.end = event.scenePos()
        print(self.end)
        # set 1 pixel border margin
        if self.end.x() < 1:
            self.end.setX(1)
        elif self.end.x() > 1023:
            self.end.setX(1023)
        if self.end.y() < 1:
            self.end.setY(1)
        elif self.end.y() > 575:
            self.end.setY(575)

        # draw (update start and end coordinate) continously
        if self.new_line is not None:
            line = QLineF(self.begin.x(), self.begin.y(), self.end.x(), self.end.y())
            self.new_line.setLine(line)

            self.arrow_head.setDestination(self.end)
            # opposite direction
            self.arrow_tail.setOrigin(self.end)
        self.update()
        super().mouseMoveEvent(event)

    # Mouse movement events
    def mouseReleaseEvent(self, event):
        print(f'end pos{self.begin, self.end}')
        self.arrow_head.setDestination(self.end)
        self.arrow_tail.setOrigin(self.end)

        self.lines.append(self.new_line)
        # Returns the item’s line, or a null line if no line has been set.
        # print(self.lines)
        # print(self.lines[0].line().x2())

        # reset
        self.begin = self.end = QPoint()
        self.new_line = None
        self.update()
        super().mouseReleaseEvent(event)

        self.inputDialog.getValue()
        # self.inputDialog.show()

    def erase(self):
        self.erase_flag = True

        self.lines.clear()

        self.clear()
        self.update()


class ArrowPath(QtWidgets.QGraphicsPathItem):
    '''
    coordinates at the origin of QGraphicsView
    '''

    def __init__(self, origin, destination, pen):
        super(ArrowPath, self).__init__()

        self.origin_pos = origin
        self.destination_pos = destination

        self._arrow_height = 5
        self._arrow_width = 4

        self.pen = pen

    def setOrigin(self, origin_pos):
        self.origin_pos = origin_pos

    def setDestination(self, destination_pos):
        self.destination_pos = destination_pos

    def directionPath(self):
        path = QtGui.QPainterPath(self.origin_pos)
        path.lineTo(self.destination_pos)
        return path

    # calculates the point og triangle where the arrow should be drawn
    def arrowCalc(self, origin_point=None, des_point=None):

        try:
            originPoint, desPoint = origin_point, des_point

            if origin_point is None:
                originPoint = self.origin_pos

            if desPoint is None:
                desPoint = self.destination_pos

            dx, dy = originPoint.x() - desPoint.x(), originPoint.y() - desPoint.y()

            leng = math.sqrt(dx ** 2 + dy ** 2)
            normX, normY = dx / leng, dy / leng  # normalize

            # perpendicular vector
            perpX = -normY
            perpY = normX

            leftX = desPoint.x() + self._arrow_height * normX + self._arrow_width * perpX
            leftY = desPoint.y() + self._arrow_height * normY + self._arrow_width * perpY

            rightX = desPoint.x() + self._arrow_height * normX - self._arrow_height * perpX
            rightY = desPoint.y() + self._arrow_height * normY - self._arrow_width * perpY

            leftPoint = QtCore.QPointF(leftX, leftY)
            rightPoint = QtCore.QPointF(rightX, rightY)

            return QtGui.QPolygonF([leftPoint, desPoint, rightPoint])

        except (ZeroDivisionError, Exception):
            return None

    def paint(self, painter: QtGui.QPainter, option, widget=None):

        painter.setRenderHint(painter.Antialiasing)
        painter.setPen(self.pen)
        path = self.directionPath()
        self.setPath(path)

        # change path.PointAtPercent() value to move arrow on the line
        triangle_source = self.arrowCalc(path.pointAtPercent(0.1), self.origin_pos)

        if triangle_source is not None:
            painter.drawPolyline(triangle_source)


class ScaleInput(QInputDialog):
    def __init__(self, parent=None):
        QInputDialog.__init__(self, parent)

        self.scale = Communicate()
        self.get_scale = pyqtSignal(str)
        self.scale_value = 1
        # layout = QFormLayout()
        # self.le = QLineEdit()
        # self.btn = QPushButton("OK")
        # layout.addRow(self.btn, self.le)
        # self.setLayout(layout)

    def getValue(self):
        # self.setCancelButtonText('not ok')
        num, ok = self.getInt(self, 'Input Scale',
                              'Enter actual scale (mm):', 1, 1, 1001, flags=Qt.WindowSystemMenuHint)

        if num and ok:  # accept and pass the value
            self.scale_value = num
            self.scale.get_scale.emit('1')

        else:  # cancel and reset
            self.scale_value = 1
            self.scale.reset_scale.emit('1')


class Communicate(QObject):
    get_scale = pyqtSignal(str)
    reset_scale = pyqtSignal(str)


class DefineROI(QGraphicsView):

    def __init__(self, parent=None):
        QGraphicsView.__init__(self, parent)
        self.setEnabled(False)
        self.lower()
        self.setGeometry(QtCore.QRect(0, 0, 1024, 576))
        self.scene = ROIScene()
        self.setScene(self.scene)
        self.setAlignment(Qt.AlignTop)
        self.setAlignment(Qt.AlignLeft)
        self.setCursor(Qt.CrossCursor)
        # force trasparent to override application style
        self.setStyleSheet("background-color: rgba(0,0,0,0%)")
        rcontent = self.contentsRect()
        self.setSceneRect(0, 0, rcontent.width(), rcontent.height())





class ROIScene(QGraphicsScene):

    def __init__(self, parent=None):
        QGraphicsScene.__init__(self, parent)

        self.erase_flag = False
        self.line_flag = False
        self.rect_flag = False
        self.circ_flag = False

        self.begin = QPointF()
        self.end = QPointF()
        self.pen = QPen(Qt.red,2)

        self.new_line = None
        self.arrow = None
        self.new_rect = None
        self.new_circ = None

        # list for all shapes for global indexing
        # QGraphicsEllipseItem and QGraphicRectItem both return rect() or rectF()

        self.ROIs = []
        self.ROI_index = 1

    # Mouse click event
    def mousePressEvent(self, event):

        print(self.new_rect)
        self.erase_flag = False

       # this is main window coordinate
        # self.begin = self.graphicsView.mapToScene(event.pos())
        # self.end = self.mapToScene(event.scenePos())

        # if there are no items at this position.
        if self.itemAt(event.scenePos(), QtGui.QTransform()) is None:

            # only allow one shape
            self.clear()
            self.ROIs.clear()

            # this is scene coordinate
            self.begin = self.end = event.scenePos()

            if self.line_flag:

                    self.new_line = QGraphicsLineItem()
                    # self._current_line_item.setFlag(QGraphicsItem.ItemIsMovable, True)
                    self.new_line.setPen(self.pen)
                    self.addItem(self.new_line)

                    line = QLineF(self.begin.x(), self.begin.y(), self.end.x(), self.end.y())
                    self.new_line.setLine(line)

            elif self.rect_flag:

                    self.new_rect = RectItem()
                    self.new_rect.setPen(self.pen)
                    self.addItem(self.new_rect)
                    rect = QRectF(self.begin, self.end).normalized()
                    self.new_rect.setRect(rect)
                    # self.new_rect = pg.RectROI()

            elif self.circ_flag:
                    self.new_circ = EllipseItem()
                    self.new_circ.setPen(self.pen)
                    self.addItem(self.new_circ)
                    circ = QRectF(self.begin, self.end).normalized()
                    self.new_circ.setRect(circ)

        self.update()
        # call super for mousePressEvent for the original handler to kick in
        # and pass the QMouseEvent instance to the original handler
        # that is, passing all other button clicks
        super().mousePressEvent(event)


    def mouseMoveEvent(self, event):

        self.end = event.scenePos()

        # set 1 pixel border margin
        if self.end.x() < 1:
            self.end.setX(1)
        elif self.end.x() > 1023:
            self.end.setX(1023)
        if self.end.y() < 1:
            self.end.setY(1)
        elif self.end.y() > 575:
            self.end.setY(575)

        # draw (update start and end coordinate) continously
        if self.line_flag:
            if self.new_line is not None:
                line = QLineF(self.begin.x(), self.begin.y(), self.end.x(), self.end.y())
                self.new_line.setLine(line)

        elif self.rect_flag:
            if self.new_rect is not None:
                rect = QRectF(self.begin, self.end).normalized()
                self.new_rect.setRect(rect)

        elif self.circ_flag:
            if self.new_circ is not None:
                rect = QRectF(self.begin, self.end).normalized()
                self.new_circ.setRect(rect)

        self.update()
        super().mouseMoveEvent(event)


    def mouseReleaseEvent(self, event):

        # print(f'end pos{self.begin, self.end}')

        if self.line_flag:

            # self.lines.append(self.new_line)
            # Returns the item’s line, or a null line if no line has been set.
            # print(self.lines)
            # print(self.lines[0].line().x2())
            if self.new_line is not None:
                # new item, else if is none means
                # transform operations applied on item

                self.new_line.index = self.ROI_index
                roi = ROI(self.new_line,self.ROI_index)
                self.ROIs.append(roi)
                self.ROI_index += 1

        elif self.rect_flag:

            # print(f'before move {self.rectangles[0].rect().getCoords()}')
            if self.new_rect is not None:
                # new item, else if is none means
                # transform operations applied on item

                self.new_rect.index = self.ROI_index
                roi = ROI(self.new_rect,self.ROI_index)
                self.ROIs.append(roi)
                self.ROI_index += 1
                # when use GraphicItem paint to overwrite
                # self.new_rect.index = self.zones.index(self.new_rect)

        elif self.circ_flag:

            if self.new_circ is not None:
                # new item, else if is none means
                # transform operations applied on item

                self.new_circ.index = self.ROI_index
                roi = ROI(self.new_circ,self.ROI_index)
                self.ROIs.append(roi)
                self.ROI_index += 1

        # reset
        self.begin = self.end = QPointF()
        self.new_line = None
        self.new_rect = None
        self.new_circ = None

        self.update()
        super().mouseReleaseEvent(event)
        print(self.ROIs)


    def erase(self):
        self.erase_flag = True
        self.line_flag = False
        self.rect_flag = False
        self.circ_flag = False

        self.ROIs.clear()
        self.ROI_index = 1
        self.clear()
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


class RectItem(QGraphicsRectItem):

    # QRect (left , top , width, height)
    # Use getCoords() if want pos coords of topleft and bottomright
    # Use contains()

    def __init__(self):
        QGraphicsRectItem.__init__(self)
        # self.painter = QPainter()
        self.setAcceptHoverEvents(True)
        self.setFlag(self.ItemIsMovable, True)
        self.index = 0

    def hoverEnterEvent(self, event):
        # self.setCursor(Qt.OpenHandCursor)
        self.setCursor(Qt.SizeAllCursor)

    def hoverLeaveEvent(self, event):
        pass

    def mousePressEvent(self, event):
        # pass
        print(f'rect item index {self.index}')
        # self.setCursor(Qt.ClosedHandCursor)

    def mouseReleaseEvent(self, event):
        self.update()
        super().mouseReleaseEvent(event)
        # self.setCursor(Qt.ClosedHandCursor)

    # overwrite addItem()
    # def paint(self, painter=QPainter,option=None,widget=None):
    #     painter.setPen(QPen(Qt.blue))
    #     painter.drawRect(self.rect())
    #     painter.drawText(self.rect(), Qt.AlignCenter, 'Zone'+ str(self.index+1))


class EllipseItem(QGraphicsEllipseItem):

    def __init__(self):
        QGraphicsEllipseItem.__init__(self)
        # self.painter = QPainter()
        self.setAcceptHoverEvents(True)
        self.setFlag(self.ItemIsMovable, True)
        self.index = 0

    def hoverEnterEvent(self, event):
        # self.setCursor(Qt.OpenHandCursor)
        self.setCursor(Qt.SizeAllCursor)

    def hoverLeaveEvent(self, event):
        pass

    def mousePressEvent(self, event):
        pass
        # self.setCursor(Qt.ClosedHandCursor)

    def mouseReleaseEvent(self, event):
        self.update()
        super().mouseReleaseEvent(event)
        # self.setCursor(Qt.ClosedHandCursor)


class ROI(object):

    def __init__(self, ROI, index):
        self.ROI = ROI
        self.roi_index = index
        # use a type paramenter to index line/rec/circ....
        # self.type