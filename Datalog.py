'''
This is data log module for the video tracking
'''
import numpy as np
import pandas as pd
import cv2
from datetime import  datetime,timedelta

# now = datetime.now()

# print(now.strftime('%Y%m%d%H%M'))
# output_filepath = now.strftime('%Y%m%d%H%M')+'_tracked.csv'

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
        is_stampSec = local_elapse % 1000
        is_stampMin = local_elapse % 60000
        # is_stampSec = frame_count % frame_rate
        # is_stampMin = frame_count % (frame_rate * 60)

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

        if interval == '1sec':
            if is_stampSec == 0:
                self.result_index +=1
                video_elapse = f"{str(timedelta(milliseconds=local_elapse)).split('.')[0]}.000"
                self.is_stamp = True
            else:
                video_elapse = f"{str(timedelta(milliseconds=local_elapse)).split('.')[0]}.{str(timedelta(milliseconds=local_elapse)).split('.')[1][:-3]}"
                self.is_stamp = False
            return self.is_stamp , video_elapse

        if interval == '1min':
            if is_stampSec == 0:
                video_elapse = f"{str(timedelta(milliseconds=local_elapse)).split('.')[0]}.000"
                self.is_stamp = False
            elif is_stampMin == 0:
                video_elapse = f"{str(timedelta(milliseconds=local_elapse)).split('.')[0]}.{str(timedelta(milliseconds=local_elapse)).split('.')[1][:-3]}"
                self.is_stamp = True
                print('1min')
            else:
                video_elapse = f"{str(timedelta(milliseconds=local_elapse)).split('.')[0]}.{str(timedelta(milliseconds=local_elapse)).split('.')[1][:-3]}"
                self.is_stamp = False
            return self.is_stamp , video_elapse

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
        data = pd.DataFrame(np.array(dataframe),
                            columns=[self.result_index_label, 'Video elapse (s)', 'Video frame', 'pos_x', 'pos_y', 'Object'])

        # use 300 frame to test
        data.to_csv('test_datalog_with time stamp 1min.csv', sep=',',index=False)

