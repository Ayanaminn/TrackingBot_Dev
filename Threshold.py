import cv2
import Detection as Detection
import concurrent.futures
from collections import namedtuple

class Threshold(object):
    '''
    This class enable threshold video and return the threshold parameters
    '''

    def __init__(self,video_source):

        self.video_source = video_source
        self.camera_num = [0,1,2] # used to set condition when select video source
        # enable all debug window
        # self.debug_mode = True
        ## define constant for color threshold
        ## blocksize_ini: the initial value of block size used for adaptive thresholding
        ## blocksize_max: the max value of block size track bar
        ## offset_ini: the initial value of offset used for adaptive thresholding
        self.blocksize_ini = 13
        self.blocksize_max = 255
        self.offset_ini = 9
        self.offset_max = 255
        ## define constant for contour threshold
        ## cnt_min_th: minimum contour area for threshold
        ## cnt_max_th: maximum contour area for threshold
        self.cnt_lower_ini = 100
        self.cnt_lower_max = 5000
        self.cnt_upper_ini = 1000
        self.cnt_upper_max = 5000


    def selectVideoSource(self):
        # for live camera
        if self.video_source in self.camera_num:
            self.cap = cv2.VideoCapture(self.video_source,cv2.CAP_DSHOW)
            self.fps = 1000
        # for local video file
        else:
            self.cap = cv2.VideoCapture(self.video_source)
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        return self.fps

    def loadThresholdWindow(self):
        '''
        load live video or local file but only for thresholding
        '''
        fps = self.selectVideoSource()

        cv2.namedWindow('Threshold', cv2.WINDOW_GUI_EXPANDED)
        cv2.namedWindow('Detection', cv2.WINDOW_GUI_EXPANDED)
        ## create trackbar for blocksize adjust
        cv2.createTrackbar('block size', 'Threshold', self.blocksize_ini, self.blocksize_max, Detection.nothing)
        cv2.createTrackbar('offset', 'Threshold', self.offset_ini, self.offset_max, Detection.nothing)
        cv2.createTrackbar('min range', 'Threshold', self.cnt_lower_ini, self.cnt_lower_max, Detection.nothing)
        cv2.createTrackbar('max range', 'Threshold', self.cnt_upper_ini, self.cnt_upper_max, Detection.nothing)
        print('After find a proper threshold range, press \'Q\' to exit and start tracking')

        while True:
            ret, self.vid = self.cap.read()
            self.invert_vid = cv2.bitwise_not(self.vid)
            ## set parameter for thresholding
            ## read track bar position for each parameter
            self.set_blocksize = cv2.getTrackbarPos('block size', 'Threshold')
            # block_size must be odd value
            if self.set_blocksize % 2 == 0:
                self.set_blocksize += 1
            if self.set_blocksize < 3:
                self.set_blocksize = 3

            self.set_offset = cv2.getTrackbarPos('offset', 'Threshold')
            self.set_cnt_min = cv2.getTrackbarPos('min range','Threshold')
            self.set_cnt_max = cv2.getTrackbarPos('max range', 'Threshold')

            ## visualize threshold debugging
            self.th_vid = Detection.thresh_video(self.invert_vid, self.set_blocksize, self.set_offset)

            self.contour_vid, self.cnt, _,_ = Detection.detect_contours(self.vid,
                                                                      self.th_vid,
                                                                      self.set_cnt_min,
                                                                      self.set_cnt_max)



            cv2.imshow('Threshold', self.th_vid)
            cv2.imshow('Detection', self.contour_vid)


            # wait 1ms if no input continue
            key = cv2.waitKey(int(1000/fps))


            # pause
            if key == ord('p'):
                cv2.waitKey(-1)  # wait until any key is pressed

            # exit
            if key == ord('q'):
                cv2.destroyAllWindows()
                break

        self.cap.release()
        cv2.destroyAllWindows()
        return self.set_blocksize,self.set_offset,self.set_cnt_min,self.set_cnt_max

    def run(self):
        """
        call input calibration scale function and draw scale function in separate thread
        """

        with concurrent.futures.ThreadPoolExecutor() as executor:
            load_threshold_window = executor.submit(self.loadThresholdWindow)
            set_blocksize,set_offset,set_cnt_min,set_cnt_max = load_threshold_window.result()
        return set_blocksize,set_offset,set_cnt_min,set_cnt_max



