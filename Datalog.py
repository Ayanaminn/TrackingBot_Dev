'''
This is data log module for the video tracking
'''
import numpy as np
import pandas as pd
import cv2
from datetime import  datetime

now = datetime.now()

# print(now.strftime('%Y%m%d%H%M'))
# output_filepath = now.strftime('%Y%m%d%H%M')+'_tracked.csv'

class TrackingDataLog(object):

    def __init__(self,video_fps):
        self.video = video_fps
        self.df = []

    def dataFrame(self, tracked_object, id_marks):
        for i in range(len(tracked_object)):

            # test create output dataframe
            self.df.append([tracked_object[i].pos_prediction[0],
                            tracked_object[i].pos_prediction[1], id_marks[i]])

        return self.df

    def dataConvert(self):
        pass


    def dataToCSV(self,dataframe):
        data = pd.DataFrame(np.array(dataframe), columns=['pos_x', 'pos_y', 'id'])
        data.to_csv('test_datalog2.csv', sep=',')

