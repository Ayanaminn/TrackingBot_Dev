'''
This is data log module for the video tracking
'''
import numpy as np
import pandas as pd
import cv2
import threading
import concurrent.futures
import time
from datetime import datetime, timedelta
from scipy.spatial import distance
from Interactive import DrawObjectWidget


# now = datetime.now()

# print(now.strftime('%Y%m%d%H%M'))
# output_filepath = now.strftime('%Y%m%d%H%M')+'_tracked.csv'

class CalibrateScale(object):
    """
    This class enable draw a scale on first frame of video source and
    use the scale to calculate pixel per metric for unit conversion
    """

    def __init__(self, video_source):

        self.video_source = video_source
        self.myFrameNumber = 1  # used to set frame position
        self.camera_num = [0, 1, 2] # used to set condition when select video source
        self.ini_start = (0, 0)
        self.ini_end = (0, 0)
        self.line_coordinates = [(0, 0), (0, 0)]
        self.isDrawing = False
        self.resetDrawing = False

    def selectVideoSource(self):

        if self.video_source in self.camera_num:
            # for live camera
            self.cap = cv2.VideoCapture(self.video_source, cv2.CAP_DSHOW)
        else:
            # for local video file
            self.cap = cv2.VideoCapture(self.video_source)

    def loadScaleFrame(self):
        """
        load first frame of video source in calibration window
        Return:
            pixel coordinate of scale line
        """

        self.selectVideoSource()
        x, y, xx, yy = (0, 0), (0, 0), (0, 0), (0, 0)
        cv2.namedWindow('Calibration', cv2.WINDOW_NORMAL)

        while True:
            ret, self.frame = self.cap.read()
            self.scale_frame = self.frame.copy()

            # set frame position
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.myFrameNumber)

            path_x, path_y, cali_x, cali_y = self.drawingPath(x, y, xx, yy)

            self.displayScale(path_x, path_y, cali_x, cali_y)

            cv2.imshow('Calibration', self.show_image())

            key = cv2.waitKey(1)

            if key == ord('q'):

                break

        self.cap.release()
        cv2.destroyAllWindows()
        return self.line_coordinates

    def drawScale(self, event, x, y, flags, param):

        global startPoint, pathPoint, endPoint

        if event == cv2.EVENT_LBUTTONDOWN:
            # set start point of line and clear previous drawing
            self.line_coordinates.clear()
            self.isDrawing = True
            self.resetDrawing = False
            startPoint = (x, y)
            self.line_coordinates.append(startPoint)
            # print(self.line_coordinates)

        elif event == cv2.EVENT_MOUSEMOVE:
            # Draw line
            if self.isDrawing:
                pathPoint = (x, y)

            pathPoint = (x, y)

        elif event == cv2.EVENT_LBUTTONUP and self.isDrawing == True:
            # deactivate drawing mode, store coordinates as endpoint of line
            self.isDrawing = False
            self.resetDrawing = False
            endPoint = (x, y)
            self.line_coordinates.append(endPoint)
            # print(self.line_coordinates)

        # Clear drawing when right mouse button click
        elif event == cv2.EVENT_RBUTTONDOWN:
            self.resetDrawing = True
            self.scale_frame = self.frame.copy()

    def drawingPath(self, x, y, xx, yy):
        """
        need review, not working in calibration mode
        """
        # the name of window have to match the main function!!!

        cv2.setMouseCallback('Calibration', self.drawScale)
        # while drawing mode is activate
        # return the start point and keep return all point on the path
        # that mouse drag through
        # in order to draw line from start point and draw the path continuously
        # when drag the mouse
        if self.isDrawing and not self.resetDrawing:
            x = startPoint
            y = pathPoint

        # while drawing mode is deactivate
        # return start and end point stored in the list
        # in order to draw a final line in between
        elif not self.isDrawing and not self.resetDrawing:
            self.scale_frame = self.frame.copy()

            x = self.line_coordinates[0]
            y = self.line_coordinates[1]
            xx = self.line_coordinates[0]
            yy = self.line_coordinates[1]
        elif self.resetDrawing:
            x = self.ini_start
            y = self.ini_end
        else:
            x = self.ini_start
            y = self.ini_end
        return x, y, xx, yy

    def show_image(self):
        return self.scale_frame

    def displayScale(self, x, y, xx, yy):


        # to show double-sided arrow
        cv2.arrowedLine(self.show_image(), xx, yy, (0, 255, 255), 1,
                        tipLength=0.1)
        cv2.arrowedLine(self.show_image(), yy, xx, (0, 255, 255), 1,
                        tipLength=0.1)

        return self.line_coordinates

    def inputScale(self):

        is_metric = None

        while True:

            metric = int(input('input metric value (mm): '))

            if (metric > 1 and metric <= 1000):

                is_confirm = input('Use this value? Y/N')

                if is_confirm == 'Y':
                    is_metric = True
                    break

                elif is_confirm == 'N':
                    continue
            else:
                print('Out of range')

        return metric, is_metric

    def convertScale(self, scale, metric):
        """
        calculate pixel per metric
        """

        pixel_length = distance.euclidean(scale[0], scale[1])
        pixel_per_metric = round(pixel_length, 2) / metric

        return pixel_per_metric

    def run(self):
        """
        call input calibration scale function and draw scale function in separate thread
        """

        with concurrent.futures.ThreadPoolExecutor() as executor:
            load_scale_frame = executor.submit(self.loadScaleFrame)
            input_scale = executor.submit(self.inputScale)
            scale_coordinates = load_scale_frame.result()
            metric, is_metric = input_scale.result()

        return scale_coordinates, metric, is_metric


class TrackingDataLog(object):
    '''
    This class is used to store and export tracking data
    '''

    def __init__(self):

        self.df = []
        # index the stored data
        # first frame start from 0
        self.result_index = -1
        self.result_index_label = 'Result'
        # self.get_date = datetime.now().strftime('%Y-%m-%d')
        # self.get_time = datetime.now().strftime('%H:%M:%S:%f')[:-3]


    def updateClock(self):

        get_clock = datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')[:-3]

        return get_clock

        # store, calculate and convert time stamp parameters

    def localTimeStamp(self, frame_rate, local_elapse, frame_count, interval=None):
        """Create time stamp when tracking local video files
           and store data based on time stamp mark
        Args:
            local_elapse: time elapsed between each frame by read current position of video files in milisec

        Return:
            self.is_stamp: store data if time mark condition is true
            video_elapse: absolute time elapsed between each frame
                          display while video playing
        """
        self.is_stamp = False
        self.is_min = 1  # count how many mintues passed
        is_stampSec = local_elapse % 1000  # bool condition when reach one sec mark
                                           # this condition is need to avoid display format error when at each second
        is_stampMin = local_elapse % 60000

        # store data every frame
        if interval == None:
            if is_stampSec == 0:
                self.result_index += 1
                # avoid format error when at each second
                video_elapse = f"{str(timedelta(milliseconds=local_elapse)).split('.')[0]}.000"
                self.is_stamp = True
            else:
                self.result_index += 1
                video_elapse = f"{str(timedelta(milliseconds=local_elapse)).split('.')[0]}.{str(timedelta(milliseconds=local_elapse)).split('.')[1][:-3]}"
                self.is_stamp = True
            return self.is_stamp, video_elapse

        ## can store time bin data by define timebin parameter and calling this function
        ## but since already stored all raw data , maybe auto sort the raw data to time bin dataframe
        ## is more efficiency?

        ## better to use frame rate for time mark?
        ## the reseason to use elapsed time is due to the concern of e.g.:24.96fps


        # if interval == '1sec':
        #     if is_stampSec == 0:
        #         self.result_index +=1
        #         video_elapse = f"{str(timedelta(milliseconds=local_elapse)).split('.')[0]}.000"
        #         self.is_stamp = True
        #     else:
        #         video_elapse = f"{str(timedelta(milliseconds=local_elapse)).split('.')[0]}.{str(timedelta(milliseconds=local_elapse)).split('.')[1][:-3]}"
        #         self.is_stamp = False
        #     return self.is_stamp , video_elapse
        #
        # if interval == '1min':
        #     if is_stampSec == 0 and not is_stampMin == 0:
        #         video_elapse = f"{str(timedelta(milliseconds=local_elapse)).split('.')[0]}.000"
        #         self.is_stamp = False
        #     elif is_stampMin == 0:
        #         self.result_index += 1
        #         self.is_min += 1
        #         video_elapse = f"{str(timedelta(milliseconds=local_elapse)).split('.')[0]}.000"
        #         self.is_stamp = True
        #     else:
        #         video_elapse = f"{str(timedelta(milliseconds=local_elapse)).split('.')[0]}.{str(timedelta(milliseconds=local_elapse)).split('.')[1][:-3]}"
        #         self.is_stamp = False
        #     return self.is_stamp , video_elapse

    def localDataFrame(self, video_elapse, frame_count, tracked_object, id_marks):
        """Create dataframe that contain data needs to store when use local video file for tracking
        Args:
            video_elapse:returned value of localTimeStamp function,absolute time elapsed between each frame
            frame_count:frame count of video
            tracked_object:registered object
            id_marks: alphabet object id
        Return:
            dataframe contain time and location ( in pixel) of each tracked object

        """

        for i in range(len(tracked_object)):
            self.df.append([self.result_index, video_elapse, frame_count, tracked_object[i].pos_prediction[0][0],
                            tracked_object[i].pos_prediction[1][0], id_marks[i]])

        dataframe = pd.DataFrame(np.array(self.df),
                                 columns=[self.result_index_label, 'Video elapse (s)', 'Video frame', 'pos_x', 'pos_y',
                                          'Object'])

        return dataframe

    def liveTimeStamp(self, frame_rate, live_elapse, frame_count, interval=None):
        """Create time stamp when tracking live video source
           and store data based on time stamp mark
        Args:
            live_elapse: time elapsed between each frame by read current position of video files in milisec

        Return:
            self.is_stamp: store data if time mark condition is true
            video_elapse: absolute time elapsed between each frame
                          display while video playing
        """
        self.is_stamp = False
        self.is_min = 1  # count how many mintues passed

        # is_stampSec = live_elapse % 1000  # bool condition when reach one sec mark
                                           # 1sec mark in living tracking need modify
        # is_stampMin = live_elapse % 60000

        # store data every frame
        if interval == None:
            self.result_index += 1
            video_elapse = f"{str(time.strftime('%H:%M:%S', time.gmtime(live_elapse)))}"
            self.is_stamp = True

            return self.is_stamp, video_elapse

    def liveDataFrame(self,clock, video_elapse,tracked_object, id_marks):

        for i in range(len(tracked_object)):
            # test create output dataframe
            self.df.append([self.result_index,clock,video_elapse,tracked_object[i].pos_prediction[0][0],
                            tracked_object[i].pos_prediction[1][0], id_marks[i]])

        dataframe = pd.DataFrame(np.array(self.df),
                                 columns=[self.result_index_label, 'Recording Time', 'Time elapsed(s)','pos_x', 'pos_y',
                                          'Object'])

        return dataframe

    def exportData(self, dataframe, save_path):
        is_export = input('Export data in .csv file? Y/N')
        if is_export == 'Y':
            try:
                self.dataToCSV(dataframe, save_path)
                print(dataframe)
            except Exception as e:
                print(e)
        elif is_export == 'N':
            exit()

    def dataToCSV(self, dataframe, save_path):
        """
        save dataframe as .csv file
        Args:
            dataframe: returned dataframe from local/liveDateFrame function
            save_path: save path and file name of .csv file
        """

        raw_data = dataframe

        raw_data.to_csv(save_path, sep=',', index=False)

    def dataConvert(self, save_path, obj_num, metric):
        """
        calculate basic behavior parameter and convert unit from pixel to scaled metric
        Args:
            save_path: load saved raw data
            obj_num: number of tracking objects
            metric: pixel_per_metric obtained from calibration module
        """

        df = pd.read_csv(save_path)

        # calculate coordinate pixel changes of each object between each frame
        # at 0 frame no previous value for subtraction, so shift n rows, n equals
        # number of tracking objects
        dx = df['pos_x'] - df['pos_x'].shift(obj_num)
        dy = df['pos_y'] - df['pos_y'].shift(obj_num)

        # calculate distance moved between each frame and convert
        # unit using scaled metric obtained from calibration module
        df['Distance (mm)'] = (np.sqrt(dx ** 2 + dy ** 2)) / metric

        df.to_csv(save_path, index=False)

# open another thread?
class TrackingVideoLog(object):
    '''
    This class is used to store and export live tracking video
    '''
    def __init__(self, video):
        self.video = video # frame to be write
        self.codec = 'mp4v'

    def exportVideo(self,save_path, fps,frame_size):
        # for living only
        fourcc = cv2.VideoWriter_fourcc(*self.codec)
        frame_size = (int(frame_size[1]), int(frame_size[0]))
        cv2.VideoWriter(filename=save_path, fourcc=fourcc,fps=fps,
                        frameSize=frame_size,isColor=True).write(self.video)
