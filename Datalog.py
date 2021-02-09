'''
This is data log module for the video tracking
'''
import numpy as np
import pandas as pd
import cv2
from datetime import  datetime,timedelta
from scipy.spatial import distance
from Interactive import DrawObjectWidget

# now = datetime.now()

# print(now.strftime('%Y%m%d%H%M'))
# output_filepath = now.strftime('%Y%m%d%H%M')+'_tracked.csv'

class CalibrateScale(object):

    def __init__(self,video):

        myFrameNumber = 1
        self.cap = cv2.VideoCapture(video,cv2.CAP_DSHOW)

        # set frame position
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, myFrameNumber)
        ret, self.frame = self.cap.read()
        self.scale_frame = self.frame.copy()
        cv2.namedWindow('Calibration', cv2.WINDOW_NORMAL)
        self.ini_start = (0,0)
        self.ini_end = (0, 0)
        self.line_coordinates = [(0, 0), (0, 0)]
        self.isDrawing = False
        self.resetDrawing = False

    # def loadCaliFrame(self,video):
    #
    #     myFrameNumber = 1
    #     cap = cv2.VideoCapture(video)
    #
    #     # set frame position
    #     cap.set(cv2.CAP_PROP_POS_FRAMES, myFrameNumber)
    #     ret, frame = cap.read()
    #     cali_frame = frame.copy()
    #     cv2.namedWindow('cali',cv2.WINDOW_NORMAL)
    #     cv2.setMouseCallback('cali', self.drawCaliLine)
    #     # cv2.line(cali_frame, self.line_coordinates[0], self.line_coordinates[1], (0, 0, 255), 2)
    #     # cali_line = DrawObjectWidget(frame)
    #     # cali_start, cali_end = cali_line.drawingPath(self.ini_start, self.ini_start)
    #     # print(cali_start)
    #     # cali_line.displayDrawing(cali_start, cali_start, self.drawingMode)
    #
    #     cv2.imshow('cali',cali_frame)
    #
    #     cv2.waitKey(-1)
    #     cv2.destroyAllWindows()
    #     # cv2.imshow("frame", frame)
    #     # return frame
    #     # cali_frame = frame.copy()
    #
    #     # cv2.waitKey(-1)
    #     # is_continue = input('Sure? Y/N')
    #     #
    #     # if is_continue == 'Y':
    #     #     cap.release()
    #     #     cv2.destroyAllWindows()
    #     #     return True
    #     # elif is_continue == 'N':
    #     #     return False
    #     #     # cv2.destroyAllWindows()
    #
    def drawScale(self, event, x, y, flags, param):

        global startPoint, pathPoint, endPoint

        if event == cv2.EVENT_LBUTTONDOWN:
            self.line_coordinates.clear()
            self.isDrawing = True
            self.resetDrawing = False
            startPoint = (x, y)
            self.line_coordinates.append(startPoint)
            print(self.line_coordinates)

        elif event == cv2.EVENT_MOUSEMOVE:
            # Draw line
            if self.isDrawing:
                pathPoint = (x, y)

            pathPoint = (x, y)

        elif event == cv2.EVENT_LBUTTONUP and self.isDrawing == True:
            # deactivate drawing mode, store coordinates as endpoint of line
            self.isDrawing = False
            #self.resetDrawing = False
            endPoint = (x, y)
            self.line_coordinates.append(endPoint)


        # Clear drawing boxes on right mouse button click
        elif event == cv2.EVENT_RBUTTONDOWN:

            self.resetDrawing = True
            self.scale_frame = self.frame.copy()


    def drawingPath(self, x, y,xx,yy):
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
            yy= self.line_coordinates[1]
        elif self.resetDrawing:
            x = self.ini_start
            y = self.ini_end
        else:
            x = self.ini_start
            y = self.ini_end
        return x, y, xx,yy

    def show_image(self):
        return self.scale_frame

    def displayScale(self, x, y, xx, yy):

        # cv2.rectangle(self.show_image(), x, y, (0, 255, 255), 1)

        cv2.arrowedLine(self.show_image(), xx, yy, (0, 255, 255), 1,
                        tipLength = 0.1)
        cv2.arrowedLine(self.show_image(), yy, xx, (0, 255, 255), 1,
                        tipLength=0.1)

        return self.line_coordinates

    def inputScale(self):
        metric = int(input('input metric value (mm): '))
        is_int = isinstance(metric, int)
        if is_int:
            if (metric < 1 or metric >= 1000):
                print('Out of range')
                self.inputScale()
            else:
                is_confirm = input('Use input number? Y/N')
                if is_confirm == 'Y':
                    return metric
                elif is_confirm == 'N':
                    self.inputScale()
                else:
                    print('Error')
        else:
            print('please input a number')
            self.inputScale()

    def convertScale(self, scale, metric):

        pixel_length = distance.euclidean(scale[0],scale[1])
        pixel_per_metric = round(pixel_length,3)/metric

        return pixel_per_metric



class TrackingDataLog(object):

    def __init__(self):
        self.df = []
        self.result_index = -1
        self.result_index_label = 'Result'
        #self.get_date = datetime.now().strftime('%Y-%m-%d')
        #self.get_time = datetime.now().strftime('%H:%M:%S:%f')[:-3]

    @staticmethod
    def updateClock():
        get_date = datetime.now().strftime('%Y-%m-%d')
        get_clock = datetime.now().strftime('%H:%M:%S:%f')[:-3]
        return get_date,get_clock


        # store, calculate and convert time stamp parameters
    def localTimeStamp(self, frame_rate, local_elapse, frame_count, interval=None):


        self.is_stamp = False
        self.is_min = 1
        is_stampSec = local_elapse % 1000
        is_stampMin = local_elapse % 60000

        if interval == None:
            if is_stampSec == 0:
                self.result_index +=1
                video_elapse = f"{str(timedelta(milliseconds=local_elapse)).split('.')[0]}.000"
                self.is_stamp = True
            else:
                self.result_index += 1
                video_elapse = f"{str(timedelta(milliseconds=local_elapse)).split('.')[0]}.{str(timedelta(milliseconds=local_elapse)).split('.')[1][:-3]}"
                self.is_stamp = True
            return self.is_stamp , video_elapse

        ## can store time bin data by define timebin parameter and calling this function
        ## but since already stored all raw data , maybe auto sort the raw data to time bin dataframe
        ## is more efficiency?

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

    def localDataFrame(self,video_elapse,frame_count,tracked_object, id_marks):

        for i in range(len(tracked_object)):
            # test create output dataframe
            self.df.append([self.result_index, video_elapse, frame_count, tracked_object[i].pos_prediction[0],
                            tracked_object[i].pos_prediction[1], id_marks[i]])

        return self.df


    # def liveDataFrame(self, clock,elapse,tracked_object, id_marks):
    #
    #     for i in range(len(tracked_object)):
    #         # test create output dataframe
    #         self.df.append([clock,elapse,self.time_index,tracked_object[i].pos_prediction[0],
    #                         tracked_object[i].pos_prediction[1], id_marks[i]])
    #
    #     return self.df

    def dataConvert(self):
        pass


    def dataToCSV(self,dataframe):

        raw_data = pd.DataFrame(np.array(dataframe),
                            columns=[self.result_index_label, 'Video elapse (s)', 'Video frame', 'pos_x', 'pos_y', 'Object'])

        # use 300 frame to test
        raw_data.to_csv('test_datalog_with time stamp 1min.csv', sep=',',index=False)

