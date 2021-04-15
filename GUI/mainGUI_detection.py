import numpy as np
import cv2
from sklearn.cluster import KMeans
import mainGUI
from PyQt5 import QtWidgets,QtCore
from PyQt5.QtWidgets import QFileDialog,QMessageBox
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QObject, QMutex, QMutexLocker
import  time

class ThresholdVideo(QtWidgets.QMainWindow):

    STATUS_INIT = 0
    STATUS_PLAYING = 1
    STATUS_PAUSE = 2

    playClicked = QtCore.pyqtSignal(str)
    pauseClicked = QtCore.pyqtSignal(str)
    resumeClicked = QtCore.pyqtSignal(str)
    stopClicked = QtCore.pyqtSignal(str)
    updateThreshDisplay = QtCore.pyqtSignal(QImage)

    def __init__(self, video_file = '',mask_file = ''):
        super().__init__()


        self.video_file = ('C:/Users/BioMEMS/Desktop/Yutao/Real-time object tracking project/OpenCV/zebrafish_video.mp4', 'Videos(*.mp4 *.avi)')
        self.mask_file = mask_file
        self.playCapture = cv2.VideoCapture()
        self.status = self.STATUS_INIT
        self.apply_mask = False

        self.detection = Detection()

        self.videoThread = VideoThread()
        self.videoThread.timeSignal.signal[str].connect(self.displayThreshold)

    def updateVideoFile(self,current_file):
        '''
        get video path passed from main every time when file selected
        :param current_file:
        :return:
        '''
        self.video_file = current_file

    def updateVideoProp(self,current_prop):
        self.video_prop = current_prop
        # self.videoThread.set_fps(self.video_prop.fps)

    def playControl(self):

        if self.video_file[0] == '' or self.video_file[0] is None:
            print('No video is selected')
            return

        if self.status is ThresholdVideo.STATUS_INIT:
            try:
                self.play()

            except:
                self.error_msg = QMessageBox()
                self.error_msg.setWindowTitle('Error')
                self.error_msg.setText('An error happened when trying to play video file.')
                self.error_msg.setIcon(QMessageBox.Warning)
                self.error_msg.setDetailedText('You caught a bug! \n'
                                               'Please submit this issue on GitHub to help us improve. ')
                self.error_msg.exec()
        elif self.status is ThresholdVideo.STATUS_PLAYING:
            try:
                self.pause()
            except:
                self.error_msg = QMessageBox()
                self.error_msg.setWindowTitle('Error')
                self.error_msg.setText('An error happened when trying to pause video file.')
                self.error_msg.setIcon(QMessageBox.Warning)
                self.error_msg.setDetailedText('You caught a bug! \n'
                                               'Please submit this issue on GitHub to help us improve. ')
                self.error_msg.exec()
        elif self.status is ThresholdVideo.STATUS_PAUSE:
            try:
                self.resume()
            except:
                self.error_msg = QMessageBox()
                self.error_msg.setWindowTitle('Error')
                self.error_msg.setText('An error happened when trying to resume playing.')
                self.error_msg.setIcon(QMessageBox.Warning)
                self.error_msg.setDetailedText('You caught a bug! \n'
                                               'Please submit this issue on GitHub to help us improve. ')
                self.error_msg.exec()

    @QtCore.pyqtSlot()
    def play(self):
        # print('play button activated')
        # print(self.video_file)
        self.playCapture.open(self.video_file[0])
        print(self.playCapture.isOpened())
        self.videoThread.start()

        self.status = ThresholdVideo.STATUS_PLAYING
        # print(f'status is {self.status}')

        # set icon
        self.playClicked.emit('1')

    @QtCore.pyqtSlot()
    def pause(self):
        self.videoThread.stop()
        self.status = ThresholdVideo.STATUS_PAUSE
        self.pauseClicked.emit('1')

    @QtCore.pyqtSlot()
    def resume(self):
        self.videoThread.start()
        self.status = ThresholdVideo.STATUS_PLAYING
        self.resumeClicked.emit('1')

    @QtCore.pyqtSlot()
    def stop(self):
        is_stopped = self.videoThread.is_stopped()
        # reset when video is paused
        if is_stopped:
            self.playCapture.release()
            # self.readVideoFile(self.video_file[0])
            self.status = ThresholdVideo.STATUS_INIT
        # reset when video still playing
        elif not is_stopped:
            self.videoThread.stop()
            self.playCapture.release()
            # self.readVideoFile(self.video_file[0])
            self.status = ThresholdVideo.STATUS_INIT
            self.stopClicked.emit('1')

    def loadMask(self):
        try:
            # set default directory for load files and set file type that only shown
            self.mask_file = QFileDialog.getOpenFileName(directory='C:/Users/Public/Desktop',
                                                         filter='Images(*.jpg  *.png  *.jpeg)')
            if self.mask_file[0] == '':
                return
            else:
                pass
                # self.isImageFileLoaded = True
                # image = cv2.imread(self.mask_file[0])
                # self.convertImage(image)
        except:
            self.error_msg = QMessageBox()
            self.error_msg.setWindowTitle('Error')
            self.error_msg.setText('An error happened when trying to load mask file.')
            self.error_msg.setInformativeText('Please ensure the image file is not corrupted.')
            self.error_msg.setIcon(QMessageBox.Warning)
            self.error_msg.setDetailedText('You caught a bug! \n'
                                           'Please submit this issue on GitHub to help us improve. ')
            self.error_msg.exec()

    @QtCore.pyqtSlot()
    def displayThreshold(self):

        if self.playCapture.isOpened():
            ret, frame = self.playCapture.read()
            print('return frame')
            if ret:
                if self.apply_mask is True:
                    pass
                else:
                    th_masked = self.detection.thresh_video(frame, block_size = 9, offset = 11)

                    contour_vid, cnt, pos_detection, pos_archive = self.detection.detect_contours(frame,
                                                                                         th_masked,
                                                                                         min_th = 100,
                                                                                         max_th = 1500, )
                    vid_rgb = cv2.cvtColor(contour_vid, cv2.COLOR_BGR2RGB)
                    vid_cvt = QImage(vid_rgb, vid_rgb.shape[1], vid_rgb.shape[0], vid_rgb.strides[0],
                                       QImage.Format_RGB888)
                    vid_scaled = vid_cvt.scaled(1024, 576, Qt.KeepAspectRatio)
                    self.updateThreshDisplay.emit(vid_scaled)
                    # vid_display = QPixmap.fromImage(vid_scaled)
                    # self.updateThreshDisplay.emit(vid_display)


class Detection():
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

    def detect_contours(self,vid, masked_th, min_th, max_th):
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
        contours, _ = cv2.findContours(masked_th.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        vid_draw = vid.copy()
        ## initialize contour number
        i = 0
        ## roll current position to past
        ## clear current position to accept updated value
        pos_detection = []
        pos_archive = pos_detection.copy()
        del pos_detection[:]

        while i < len(contours):
            try:
                ## calculate contour area for current contour
                cnt_th = cv2.contourArea(contours[i])
                ## delete contour if not meet the threshold
                if cnt_th < min_th or cnt_th > max_th:
                    del contours[i]
                ## draw contour if meet the threshold
                else:
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
            ## when a number is divided by a zero
            except ZeroDivisionError:
                pass
        return vid_draw, contours, pos_detection, pos_archive


def nothing(x):
    """
    call back function for track bar
    """
    pass

class Communicate(QObject):
    signal = pyqtSignal(str)

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
            print('thread singal emitted')
            time.sleep(1 / self.fps)

    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True

    def is_stopped(self):
        with QMutexLocker(self.mutex):
            return self.stopped

    def set_fps(self, video_fps):
        self.fps = video_fps
        print(f'set fps to {self.fps}')