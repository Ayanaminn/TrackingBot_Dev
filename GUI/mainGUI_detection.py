import numpy as np
import cv2
from sklearn.cluster import KMeans
import mainGUI
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QStyle

class ThresholdVideo(QtWidgets.QMainWindow, mainGUI.Ui_MainWindow):

    STATUS_INIT = 0
    STATUS_PLAYING = 1
    STATUS_PAUSE = 2

    def __init__(self, video_file = ''):
        super().__init__()
        self.setupUi(self)

        self.video_file = video_file
        self.playCapture = cv2.VideoCapture()

        # self.videoThread = VideoThread()
        # self.videoThread.timeSignal.signal[str].connect(self.displayVideo)

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

    def play(self):
        print('play button activated')
        print(self.video_file)
        self.playCapture.open(self.video_file[0])
        print(self.playCapture.isOpened())
        self.applyMaskcheckBox.setEnabled(False)
        # self.videoThread.start()
        # self.threPlayButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        # self.status = ThresholdVideo.STATUS_PLAYING
        # print(f'status is {self.status}')

    # ## video thresholding
    # def thresh_video(vid, block_size, offset):
    #     """
    #     This function retrieves a video frame and preprocesses it for object tracking.
    #     The code 1) blurs image to reduce noise
    #              2) converts it to greyscale
    #              3) returns a thresholded version of the original image.
    #              4) perform morphological operation to closing small holes inside objects
    #     Parameters
    #     ----------
    #     vid : source image containing all three colour channels
    #     block_size: int(optional), default = blocksize_ini
    #     offset: int(optional), default = offset_ini
    #     """
    #     vid = cv2.GaussianBlur(vid, (5, 5), 1)
    #     #vid = cv2.blur(vid, (5, 5))
    #     vid_gray = cv2.cvtColor(vid, cv2.COLOR_BGR2GRAY)
    #     vid_th = cv2.adaptiveThreshold(vid_gray,
    #                                    255,
    #                                    cv2.ADAPTIVE_THRESH_MEAN_C,
    #                                    cv2.THRESH_BINARY_INV,
    #                                    block_size,
    #                                    offset)
    #
    #     ## Dilation followed by erosion to closing small holes inside the foreground objects
    #     kernel = np.ones((5, 5), np.uint8)
    #     vid_closing = cv2.morphologyEx(vid_th, cv2.MORPH_CLOSE, kernel)
    #
    #     return vid_closing