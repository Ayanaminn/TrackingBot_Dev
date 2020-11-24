from PyQt5 import QtCore,QtGui,QtWidgets
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QImage
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from PyQt5.QtCore import QTimer

import cv2, imutils
import time
import mainTest

class MainWindow(QtWidgets.QMainWindow,mainTest.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)


        self.videoThread = VideoThread()

        self.loadImage.clicked.connect(self.readImageFile)
        self.loadVideo.clicked.connect(self.readVideoFile)
        self.endVideo.clicked.connect(self.stopVideoThread)



    #
    # def connectionTest(self):
    #     print('connected')

    # example
    # def closeEvent(self, event):
    #     answer = QtWidgets.QMessageBox.question(
    #         self,
    #         'Are you sure you want to quit ?',
    #         'Task is in progress !',
    #         QtWidgets.QMessageBox.Yes,
    #         QtWidgets.QMessageBox.No)
    #     if answer == QtWidgets.QMessageBox.Yes:
    #         event.accept()
    #     else:
    #         event.ignore()

    def readImageFile(self):
        try:
            # set default directory for load files and set file type that only shown
            self.filename = QFileDialog.getOpenFileName(directory='C:/Users/BioMEMS/Videos',
                                                        filter='Images(*.jpg  *.png  *.jpeg)')
            if self.filename[0] =='':
                pass
            else:
                self.isImageFileLoaded = True
                image = cv2.imread(self.filename[0])
                self.convertImage(image)
        except:
            pass

    def convertImage(self, image):
        self.image = image
        img_rgb = cv2.cvtColor(self.image,cv2.COLOR_BGR2RGB)
        img_cvt = QImage(img_rgb,img_rgb.shape[1],img_rgb.shape[0],img_rgb.strides[0],
                         QImage.Format_RGB888)
        img_scal = img_cvt.scaled(441,271,Qt.KeepAspectRatio)
        self.displayImage(img_scal)

    def displayImage(self, image):
        self.image = image
        img_dis = QPixmap.fromImage(self.image)
        self.label.setPixmap(img_dis)



    def readVideoFile(self):

       global videoFile

       try:
           # set default directory for load files and set file type that only shown
            videoFile = QFileDialog.getOpenFileName(directory='C:/Users/BioMEMS/Videos',
                                                        filter='Videos(*.mp4 *.avi)')
            if videoFile[0] == '':
                print('passed')

            else:
                self.enableVideoThread()
                # print('activated')
       except:
           pass


    def enableVideoThread(self):
        '''
        wake up the thread
        connect the signal emited by the thread to a function
        :return:
        '''

        self.videoThread.start()
        self.videoThread.updateFrame.connect(self.displayVideo)
        # self.videoThread.endThread.connect(self.stopVideoThread)


    def displayVideo(self,frame):
        frame_display = QPixmap.fromImage(frame)
        self.label.setPixmap(frame_display)

    def connectTest(self):
        self.videoThread.activateTest()
        # print('connected')


    def stopVideoThread(self):
        # VideoThread.readVideo.video.release()
        print('end thread connected')
        self.videoThread.stop()
        return



class VideoThread(QThread):
    '''
    when this thread is called, it excute all modules within
    this thread and emit a custom signal as output
    this signal is used to communicate with main thread
    '''
    def __init__(self):
        super().__init__()


    # define a signal
    updateFrame = pyqtSignal(QImage)
    # updateFrame = pyqtSignal(str)

    def run(self):
        while True:
            self.readVideo()


    def readVideo(self):
        try:
            # if self.isVideoFileLoaded:
            video = cv2.VideoCapture(videoFile[0])
            fps = video.get(cv2.CAP_PROP_FPS)
            print('Video frame rate : {}'.format(fps))

            if not video.isOpened():
                print('Failed to open video file')
                # video.release()
                # self.endThread.emit('1')

            while video.isOpened():
                ret, frame = video.read()
                time.sleep(1/fps)

                if not ret:
                    if frame is None:
                        print('The video has end')
                        # msg = QMessageBox.Warning(self, u'Warning', u'The video has end',
                        #                           buttons=QMessageBox.Ok,
                        #                           defaultButton=QMessageBox.Ok)
                    else:
                        print('Failed to read video')
                    break

                self.convertVideo(frame)

            video.release()
        except:
            pass


    def convertVideo(self,frame):
        self.frame = frame
        frame_rgb = cv2.cvtColor(self.frame,cv2.COLOR_BGR2RGB)
        frame_cvt = QImage(frame_rgb, frame_rgb.shape[1], frame_rgb.shape[0], frame_rgb.strides[0], QImage.Format_RGB888)
        frame_scaled = frame_cvt.scaled(441,271,Qt.KeepAspectRatio)
        # send Image formatted frame as singal
        self.updateFrame.emit(frame_scaled)

    def activateTest(self):
        print('activated')




if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())