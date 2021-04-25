from PyQt5 import QtCore,QtGui,QtWidgets
from PyQt5.QtWidgets import QFileDialog,QMessageBox,QStyle,QApplication,QWidget
from PyQt5.QtGui import QImage,QPixmap
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread,QObject,QMutex,QMutexLocker
import numpy as np
from PyQt5.QtCore import QTimer

import cv2, imutils
import time
from collections import namedtuple
from datetime import datetime, timedelta
import threading
import concurrent.futures
import mainGUI
import mainGUI_VPlayer

class MainWindow(QtWidgets.QMainWindow, mainGUI.Ui_MainWindow):

    VIDEO_TYPE_OFFLINE = 0
    VIDEO_TYPE_REAL_TIME = 1

    STATUS_INIT = 0
    STATUS_PLAYING = 1
    STATUS_PAUSE = 2



    def __init__(self):
        super().__init__()
        self.setupUi(self)

        #
        # # self.video_type = video_type  # 0: offline  1: realTime
        # self.video_file = video_file
        self.status = self.STATUS_INIT  # 0: init 1:playing 2: pause
        self.videoPlayer = VideoPlayer()

        self.localMode.clicked.connect(self.enableLocalMode)
        #
        # self.playButton.clicked.connect(self.videoPlayer.videoPlayControl)
        # self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        #
        # self.stopButton.clicked.connect(self.videoPlayer.stopVideo)
        # self.stopButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))


        # videoPlayer = VideoPlayer()
        # timer
        # self.videoThread = VideoThread()
        # self.videoThread.timeSignal.signal[str].connect(self.videoPlayer.displayVideo)

    def enableLocalMode(self):
       #  app = QtWidgets.QApplication(sys.argv)

        # connect subclass with parent class
        window = VideoPlayer()
        window.show()

class VideoPlayer(QtWidgets.QMainWindow, mainGUI.Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.detection = Detection()

        self.loadVidButton.clicked.connect(self.selectVideoFile)

        self.playButton.clicked.connect(self.videoPlayControl)
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

        self.stopButton.clicked.connect(self.stopVideo)
        self.stopButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))

        self.videoThread = VideoThread()
        self.detectionThread = DetectionThread()
        self.videoThread.timeSignal.signal[str].connect(self.displayVideo)
        # self.videoThread.timeSignal.det_signal[str].connect(self.detectionThread.run)
        # video init
        self.playCapture = cv2.VideoCapture()

        self.resetVideo()

    def selectVideoFile(self):

       # global video_file
       try:
           # set default directory for load files and set file type that only shown
            self.video_file = QFileDialog.getOpenFileName(directory='C:/Users/Public/Desktop',
                                                     filter='Videos(*.mp4 *.avi)')
           # if no file selected
            if self.video_file[0] == '':
                print('passed')
                return

            else:
                self.playButton.setEnabled(True)
                self.stopButton.setEnabled(True)
                # display image on top of other widgets
                # can use either way
                #self.VBox.raise_()
                self.loadVidButton.hide()
                # self.enableVideoThread()
                # print('activated')

                # after select file, auto read and display its property
                print(self.video_file)
                self.readVideoFile(self.video_file[0])

       except:
           self.error_msg = QMessageBox()
           self.error_msg.setWindowTitle('Error')
           self.error_msg.setText('An error happened when trying to load video file.')
           self.error_msg.setInformativeText('Please ensure the video file is not corrupted.')
           self.error_msg.setIcon(QMessageBox.Warning)
           self.error_msg.setDetailedText('You caught a bug! \n'
                                          'Please submit this issue on GitHub to help us improve. ')
           self.error_msg.exec()

    def readVideoFile(self,file_path):

        try:
            video_cap = cv2.VideoCapture(file_path)
            video_prop = self.readVideoProp(video_cap)

            self.videoThread.set_fps(video_prop.fps)
            print(video_prop)
            # set a function here link to labels that display the parameters

            set_preview_frame = 1
            video_cap.set(cv2.CAP_PROP_POS_FRAMES, set_preview_frame)

            # while True:
            ret, preview_frame = video_cap.read()
            frame_rgb = cv2.cvtColor(preview_frame, cv2.COLOR_BGR2RGB)
            frame_cvt = QImage(frame_rgb, frame_rgb.shape[1], frame_rgb.shape[0], frame_rgb.strides[0],
                               QImage.Format_RGB888)
            frame_scaled = frame_cvt.scaled(1024, 576, Qt.KeepAspectRatio)
            frame_display = QPixmap.fromImage(frame_scaled)
            self.VBoxLabel.setPixmap(frame_display)
            video_cap.release()

        except:
            self.error_msg = QMessageBox()
            self.error_msg.setWindowTitle('Error')
            self.error_msg.setText('Failed to read video file.')
            self.error_msg.setInformativeText('cv2.VideoCapture() does not execute correctly.\n'
                                              'QImage is not converted correctly')
            self.error_msg.setIcon(QMessageBox.Warning)
            self.error_msg.setDetailedText('You caught a bug! \n'
                                           'Please submit this issue on GitHub to help us improve. ')
            self.error_msg.exec()

    def readVideoProp(self,file_path):
        """
        read parameters of loaded video file
        Parameters
        ----------
        video_file

        Returns
        -------
        get_video_prop: a named tuple of video parameter
        """
        # calculate total number of seconds of file
        total_sec = file_path.get(cv2.CAP_PROP_FRAME_COUNT) / file_path.get(cv2.CAP_PROP_FPS)
        # convert total seconds to hh:mm:ss format
        video_duraion = str(timedelta(seconds=total_sec))
        video_prop = namedtuple('video_prop', ['width', 'height', 'fps', 'length', 'elapse', 'duration'])
        get_video_prop = video_prop(file_path.get(cv2.CAP_PROP_FRAME_WIDTH),
                                    file_path.get(cv2.CAP_PROP_FRAME_HEIGHT),
                                    file_path.get(cv2.CAP_PROP_FPS),
                                    file_path.get(cv2.CAP_PROP_FRAME_COUNT),
                                    file_path.get(cv2.CAP_PROP_POS_MSEC),
                                    video_duraion)

        return get_video_prop

    def displayVideo(self):
        # print('emited signal connected')
        if self.playCapture.isOpened(): # when click the play button that connected with playVideo function
            ret, frame = self.playCapture.read()
            if ret:
                th_masked = self.detection.thresh_video(frame, block_size = 11, offset = 11)

                # contour_vid, cnt, pos_detection, pos_archive= self.detection.detect_contours(frame,
                #                                                                      th_masked,
                #                                                                      min_th = 100,
                #                                                                      max_th = 1500)



                # self.det_thread = threading.Thread(target=self.detection.detect_test,args=(5,))
                # self.det_thread.start()
                # thread_return, num = self.detection.detect_test()
                # print(thread_return,num)

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self.detection.detect_contours, frame,th_masked,min_th = 100,max_th = 1500)
                    contour_vid, cnt, pos_detection, pos_archive = future.result()
                    # print(f'thread return {return_bool} {return_value}')

                frame_rgb = cv2.cvtColor(contour_vid, cv2.COLOR_BGR2RGB)

                frame_cvt = QImage(frame_rgb, frame_rgb.shape[1], frame_rgb.shape[0], frame_rgb.strides[0],
                                    QImage.Format_RGB888)
                frame_scaled = frame_cvt.scaled(1024, 576, Qt.KeepAspectRatio)
                frame_display = QPixmap.fromImage(frame_scaled)
                self.VBoxLabel.setPixmap(frame_display)
            elif not ret:
                print("play finished")
                self.resetVideo()
                self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
                return
            else:
                self.error_msg = QMessageBox()
                self.error_msg.setWindowTitle('Error')
                self.error_msg.setText('Failed to read next video frame.')
                self.error_msg.setInformativeText('cv2.VideoCapture.read() does not return any frame.')
                self.error_msg.setIcon(QMessageBox.Warning)
                self.error_msg.setDetailedText('You caught a bug! \n'
                                               'Please submit this issue on GitHub to help us improve. ')
                self.error_msg.exec()

        else:
            self.error_msg = QMessageBox()
            self.error_msg.setWindowTitle('Error')
            self.error_msg.setText('Failed to read video file.')
            self.error_msg.setInformativeText('cv2.VideoCapture.isOpen() return false.\n'
                                              'Click "OK" to reset video.')
            self.error_msg.setIcon(QMessageBox.Warning)
            self.error_msg.setDetailedText('You caught a bug! \n'
                                           'Please submit this issue on GitHub to help us improve.')
            self.error_msg.exec()
            self.resetVideo()


    def videoPlayControl(self):

        if self.video_file[0] == '' or self.video_file[0] is None:
            print('No video is selected')
            return

        if self.status is MainWindow.STATUS_INIT:
            try:
                self.playVideo()
            except:
                self.error_msg = QMessageBox()
                self.error_msg.setWindowTitle('Error')
                self.error_msg.setText('An error happened when trying to play video file.')
                self.error_msg.setIcon(QMessageBox.Warning)
                self.error_msg.setDetailedText('You caught a bug! \n'
                                               'Please submit this issue on GitHub to help us improve. ')
                self.error_msg.exec()
            # self.playCapture.open(self.video_file[0])
            # self.videoThread.start()
            # self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

        elif self.status is MainWindow.STATUS_PLAYING:
            try:
                self.pauseVideo()
            except:
                self.error_msg = QMessageBox()
                self.error_msg.setWindowTitle('Error')
                self.error_msg.setText('An error happened when trying to pause video file.')
                self.error_msg.setIcon(QMessageBox.Warning)
                self.error_msg.setDetailedText('You caught a bug! \n'
                                               'Please submit this issue on GitHub to help us improve. ')
                self.error_msg.exec()
            # self.videoThread.stop()
            # if self.video_type is VideoBox.VIDEO_TYPE_REAL_TIME:
            #     self.playCapture.release()
            # self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        elif self.status is MainWindow.STATUS_PAUSE:
            try:
                self.resumeVideo()
            except:
                self.error_msg = QMessageBox()
                self.error_msg.setWindowTitle('Error')
                self.error_msg.setText('An error happened when trying to resume playing.')
                self.error_msg.setIcon(QMessageBox.Warning)
                self.error_msg.setDetailedText('You caught a bug! \n'
                                               'Please submit this issue on GitHub to help us improve. ')
                self.error_msg.exec()
            # if self.video_type is VideoBox.VIDEO_TYPE_REAL_TIME:
            #     self.playCapture.open(self.video_url)
            # self.videoThread.start()
            # self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        '''
        study below structure
        '''
        # self.status = (MainWindow.STATUS_PLAYING,
        #                MainWindow.STATUS_PAUSE,
        #                MainWindow.STATUS_PLAYING)[self.status]

    def playVideo(self):
        self.playCapture.open(self.video_file[0])
        self.videoThread.start()
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.status = MainWindow.STATUS_PLAYING

    def pauseVideo(self):
        # if local file, stop the thread

        self.videoThread.stop()
        # for camera
        # if self.video_type is MainWindow.VIDEO_TYPE_REAL_TIME:
        #     self.playCapture.release()

        self.status = MainWindow.STATUS_PAUSE
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def resumeVideo(self):
        # if self.video_file[0] == '' or self.video_file[0] is None:
        #     return
        # self.playCapture.release()
        # self.playCapture.open(self.video_file[0])
        self.videoThread.start()
        self.status = MainWindow.STATUS_PLAYING
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

    def stopVideo(self):
        is_stopped = self.videoThread.is_stopped()
        if is_stopped:
            self.playCapture.release()
            print('vid release')
            print(self.playCapture.isOpened())
            self.readVideoFile(self.video_file[0])
            self.status = MainWindow.STATUS_INIT
        elif not is_stopped:
            self.videoThread.stop()
            self.playCapture.release()
            self.readVideoFile(self.video_file[0])
            self.status = MainWindow.STATUS_INIT
            self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def resetVideo(self):
        self.videoThread.stop()
        self.playCapture.release()
        self.status = MainWindow.STATUS_INIT
        # MainWindow.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

class Communicate(QObject):
    signal = pyqtSignal(str)
    det_signal=pyqtSignal(str)

class VideoThread(QThread):

    def __init__(self, default_fps=25):
        QThread.__init__(self)
        self.stopped = False
        self.fps = default_fps
        self.timeSignal = Communicate()
        self.mutex = QMutex()

    def run(self):
        with QMutexLocker(self.mutex):
            self.stopped = False
        while True:
            if self.stopped:
                return
            self.timeSignal.signal.emit('1')
            self.timeSignal.det_signal.emit('1')
            time.sleep(1/self.fps)

    def stop(self):
        # print('thread stopped')
        with QMutexLocker(self.mutex):
            self.stopped = True

    def is_stopped(self):
        with QMutexLocker(self.mutex):
            return self.stopped

    def set_fps(self, video_fps):
        self.fps = video_fps
        print(f'set fps to {self.fps}')

class Detection():

    def __init__(self):
        super().__init__()
        self.is_thread = True
        self.num = 0
        self.i = 0
    ## video thresholding
    def thresh_video(self,vid, block_size, offset):
        """
        This function retrieves a video frame and preprocesses it for object tracking.
        The code 1) blurs image to reduce noise
                 2) converts it to greyscale
                 3) returns a thresholded version of the original image.
                 4) perform morphological operation to closing small holes inside objects
        Parameters
        ----------
        vid : source image containing all three colour channels
        block_size: int(optional), default = blocksize_ini
        offset: int(optional), default = offset_ini
        """
        vid = cv2.GaussianBlur(vid, (5, 5), 1)
        #vid = cv2.blur(vid, (5, 5))
        vid_gray = cv2.cvtColor(vid, cv2.COLOR_BGR2GRAY)
        vid_th = cv2.adaptiveThreshold(vid_gray,
                                       255,
                                       cv2.ADAPTIVE_THRESH_MEAN_C,
                                       cv2.THRESH_BINARY_INV,
                                       block_size,
                                       offset)

        ## Dilation followed by erosion to closing small holes inside the foreground objects
        kernel = np.ones((5, 5), np.uint8)
        vid_closing = cv2.morphologyEx(vid_th, cv2.MORPH_CLOSE, kernel)

        return vid_closing

    def detect_contours(self, vid, vid_th, min_th, max_th):

        """
        vid : original video source for drawing and visualize contours
        vid_detect : the masked video for detect contours
        min_th: minimum contour area threshold used to identify object of interest
        max_th: maximum contour area threshold used to identify object of interest

        :return
        contours: list
            a list of all detected contours that pass the area based threshold criterion
        pos_archive: a list of (2,1) array, dtype=float
            individual's location on previous frame
        pos_detection: a list of (2,1) array, dtype=float
            individual's location detected on current frame
            (  [[x0],[y0]]  ,  [[x1],[y1]]  , [[x2],[y2]] .....)
        """


        contours, _ = cv2.findContours(vid_th.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        vid_draw = vid.copy()

        print('contour lens is '+ str(len(contours)))
        ## initialize contour number

        ## roll current position to past
        ## clear current position to accept updated value
        pos_detection = []
        pos_archive = pos_detection.copy()
        del pos_detection[:]

        i = 0

        while i < len(contours):
        #     self.i += 1
        #     print(self.i)
        #     cnt_th = cv2.contourArea(contours[self.i])
        #     print(f'contour threh for {self.i} is {cnt_th}')
        #     if cnt_th < min_th or cnt_th > max_th:
        #         del contours[self.i]
        #         print('delete')
        #     else:
        #         cv2.drawContours(vid_draw, contours, self.i, (0, 0, 255), 2, cv2.LINE_8)
        #         print(f'draw contour for {self.i}')
        # else:
        #     pass


        # else:

        #     print('i not less than len(contours)')
            try:
                ## calculate contour area for current contour
                cnt_th = cv2.contourArea(contours[i])
                # print(f'cnt area for i is {cnt_th}')
                ## delete contour if not meet the threshold
                if cnt_th < min_th or cnt_th > max_th:
                    del contours[i]
                ## draw contour if meet the threshold
                else:
                    print('cv2 draw contours')
                    cv2.drawContours(vid_draw, contours, i, (0, 0, 255), 2, cv2.LINE_8)
                    ## calculate the centroid of current contour
                    M = cv2.moments(contours[i])
                    if M['m00'] != 0:
                        cx = M['m10'] / M['m00']
                        cy = M['m01'] / M['m00']
                    else:
                        cx = 0
                        cy = 0
                    ## update current position to new centroid
                    centroids = np.array([[cx], [cy]])
                    # pos_detection become a list of (2,1) array
                    pos_detection.append(centroids)
                    ## continue to next contour
                    i += 1
                    print(f'i = {i}')
            ## when a number is divided by a zero
            except ZeroDivisionError:
                pass
        return vid_draw, contours , pos_detection, pos_archive

    def detect_test(self, delta):
        print('detect test from detection class')
        while self.is_thread:
        # if self.num <100000000:
            self.num += delta
            print(self.num)
            if self.num >100000:
                break
        #         print('overflow')
        return self.is_thread,self.num

class DetectionThread(QThread):
    def __init__(self):
        QThread.__init__(self)
        self.detection = Detection()
    def run(self):
        print('test thread')
        self.detection.detect_test()



if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)

    # connect subclass with parent class
    window = VideoPlayer()
    window.show()

    sys.exit(app.exec_())