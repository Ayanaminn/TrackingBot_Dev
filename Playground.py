# import cv2
# import numpy as np
# import time
# from Kalman import KalmanFilter
# from scipy.optimize import linear_sum_assignment
# from scipy.spatial.distance import cdist
# from sklearn.cluster import KMeans
# from sklearn.cluster import MiniBatchKMeans
#
# Video_load = 'bf_test.mp4'
# # Video_load = 'randomball.mp4'
# Mask_file_load = 'mask1.png'
# mask_on = True
#
# obj_num = 10
# obj_id = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H' , 'I', 'J', 'K', 'L', 'M']
# colours = [(0, 0, 255), (0, 255, 255), (255, 0, 255), (255, 255, 255), (255, 255, 0),
#            (255, 0, 0),
#            (0, 255, 0),
#            (0, 0, 0),
#            (54, 0, 7),
#            (0, 72, 0),
#            (8, 77, 134),
#            (130, 56, 99),
#            (255, 0, 0)]
# mark_on=1
# ## define constant for color threshold
# ## blocksize_ini: the initial value of block size used for adaptive thresholding
# ## blocksize_max: the max value of block size track bar
# ## offset_ini: the initial value of offset used for adaptive thresholding
# blocksize_ini = 13
# offset_ini = 9
#
# cnt_min_th = 50
# cnt_max_th = 1500
#
#
# scaling = 1.0
#
# ## video thresholding
# def thresh_video(vid, block_size, offset):
#     """
#     This function retrieves a video frame and preprocesses it for object tracking.
#     The code 1) blurs image to reduce noise
#              2) converts it to greyscale
#              3) returns a thresholded version of the original image.
#              4) perform morphological operation to closing small holes inside objects
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
#     return vid_closing
#     # return vid_th
#
#
# def create_mask(mask_file):
#     """
#     this function is to create a mask image for analyzed frame
#     """
#     mask_gray = cv2.cvtColor(mask_file, cv2.COLOR_BGR2GRAY)
#     mask_th = cv2.threshold(mask_gray, 10, 255, cv2.THRESH_BINARY_INV)
#     return mask_th
#
#
# def apply_mask(raw_mask, raw_vid):
#     """
#     this function perform biwise operation
#     apply mask on video
#     """
#     mask_inv = cv2.bitwise_not(raw_mask)
#     bitwise_mask = cv2.bitwise_and(raw_vid, raw_vid, mask=mask_inv)
#     return bitwise_mask
#
#
# def nothing(x):
#     """
#     call back function for trackbar
#     """
#     pass
#
#
# def detect_contours(vid, masked_th, min_th, max_th, pos_last, pos_now):
#     """
#     vid : original video source
#     vid_detect : the masked video
#     min_th: minimum contour area threshold used to identify object of interest
#     max_th: maximum contour area threshold used to identify object of interest
#
#     :return
#     contours: list
#         a list of all detected contours that pass the area based threhold criterion
#     pos_last: array_like, dtype=float
#         individual's location on previous frame
#     pos_now: array_like, dtype=float
#         individual's location on current frame
#         [  [x0,y0]  ,  [x1,y1]  , [x2,y2] .....]
#     """
#
#     contours, _ = cv2.findContours(masked_th.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
#     vid_draw = vid.copy()
#     ## initialize contour number
#     i = 0
#     ## roll current position to past
#     ## clear current position to accept updated value
#
#     pos_last = pos_now.copy()
#     del pos_now[:]
#     while i < len(contours):
#         try:
#             ## calculate contour area for current contour
#             cnt_th = cv2.contourArea(contours[i])
#             ## delete contour if not meet the threshold
#             if cnt_th < min_th or cnt_th > max_th:
#                 del contours[i]
#             ## draw contour if meet the threshold
#             else:
#                 cv2.drawContours(vid_draw, contours, i, (0, 0, 255), 1)
#                 ## calculate the centroid of current contour
#                 M = cv2.moments(contours[i])
#                 if M['m00'] != 0:
#                     cx = M['m10'] / M['m00']
#                     cy = M['m01'] / M['m00']
#                 else:
#                     cx = 0
#                     cy = 0
#                 ## update current position to new centroid
#                 pos_now.append([cx, cy])
#                 # print([cx,cy])
#                 #print(pos_now)
#                 #print(pos_last)
#                 ## continue to next contour
#                 i += 1
#         ## when a number is divided by a zero
#         except ZeroDivisionError:
#             pass
#     return vid_draw, contours, pos_last, pos_now
#
#
# def identify(pos_last, pos_now):
#     '''
#     Apply hungarian algorithm to differentiate tracked centroids
#     from new detected centroids.Cost function is the euclidean distances
#     between centroids measured in previous and current step
#     :param pos_last:
#     :param pos_now:
#     :return:An array of row indices and one of corresponding column indices
#     giving the optimal assignment.
#     rearranged id based on matching previous and current centroids
#     by minimize the cost function
#     id_index:array
#     id_assign:array
#     '''
#     pos_last = np.array(pos_last)
#     pos_now = np.array(pos_now)
#     print(pos_last)
#     if pos_now.shape != pos_last.shape:
#         if pos_now.shape[0] < pos_last.shape[0]:
#             while pos_now.shape[0] != pos_last.shape[0]:
#                 pos_last = np.delete(pos_last, pos_last.shape[0] - 1, 0)
#         else:
#             result = np.zeros(pos_now.shape)
#             result[:pos_last.shape[0], :pos_last.shape[1]] = pos_last
#             pos_last = result
#
#     #pos_last = list(pos_last)
#     #pos_now = list(pos_now)
#     print(pos_now)
#     #cdist:cdist(XA, XB, metric='euclidean', *args, **kwargs)
#     # XA: mA*n  array
#     # XB: mB*n  array
#     # return cost: mA*mB array
#     cost = cdist(pos_last, pos_now)
#     print(cost)
#     # print(cost.shape)
#     '''
#     ## according the distance(cost) value to set up
#     ## a threshold so when cost very high, delete the assignment
#     '''
#     # print((pos_last[1], pos_now[4]))
#     # print(cost[1,4].sum())
#
#     id_index, id_assign = linear_sum_assignment(cost)
#
#     # print(id_index)
#     # print(id_assign)
#
#     return id_index, id_assign
#
#
# def assignment(vid, id, colours, obj_num, id_assign, pos_now, flag):
#     '''
#
#     :param vid:
#     :param id:
#     :param colours:
#     :param pos_now:
#     :param obj_id:
#     :param obj_id_now:
#     :return:
#     '''
#     equal = np.array_equal(id_assign, list(range(len(id_assign))))
#     if equal == False:
#         current_ids = id_assign.copy()
#         reorder = [i[0] for i in sorted(enumerate(current_ids), key=lambda x: x[1])]
#         pos_now = [x for (y, x) in sorted(zip(reorder, pos_now))]
#     # print(re_order)
#     # print(pos_now)
#     if flag == True:
#         for i in range(obj_num):
#             cv2.circle(vid, tuple([int(x) for x in pos_now[i]]), 5, colours[i % obj_num], -1, cv2.LINE_AA)
#             cv2.putText(vid, id[i % obj_num], tuple([int(x) for x in pos_now[i]]), 1, 2, (0, 0, 0), 2)
#
#     return vid,pos_now
#
#
# def kf_update(pos_now,trackidcount):
#     track=[]
#     trackid=trackidcount
#
#
# #
# # def apply_k_means(contours, obj_n, pos_now_update):
# #     del pos_now_update[:]
# #
# #     cnt_array = np.vstack(contours)
# #     cnt_array = cnt_array.reshape(cnt_array.shape[0], cnt_array.shape[2])
# #
# #     kmeans = KMeans(n_clusters=obj_n, random_state=42, n_init=5, max_iter=50).fit(cnt_array)
# #     l = len(kmeans.cluster_centers_)
# #     runs = kmeans.n_iter_
# #     for i in range(l):
# #         x = int(tuple(kmeans.cluster_centers_[i])[0])
# #         y = int(tuple(kmeans.cluster_centers_[i])[1])
# #         pos_now_update.append([x, y])
# #     return contours, pos_now_update
#
# # def apply_mini_k_means(contours, obj_n, pos_now_update):
# #     del pos_now_update[:]
# #
# #     cnt_array = np.vstack(contours)
# #     cnt_array = cnt_array.reshape(cnt_array.shape[0], cnt_array.shape[2])
# #
# #     kmeans = MiniBatchKMeans(n_clusters=obj_n, random_state=42, batch_size=5).fit(cnt_array)
# #     l = len(kmeans.cluster_centers_)
# #     runs = kmeans.n_iter_
# #     for i in range(l):
# #         x = int(tuple(kmeans.cluster_centers_[i])[0])
# #         y = int(tuple(kmeans.cluster_centers_[i])[1])
# #         pos_now_update.append([x, y])
# #     return contours, pos_now_update,runs
#
#
# video = cv2.VideoCapture(Video_load)
#
# cv2.namedWindow('Test', cv2.WINDOW_NORMAL)
#
# pos_last = list(np.zeros((obj_num, 2)))
# pos_now = list(np.zeros((obj_num, 2)))
#
# # KF = KalmanFilter(0.1, 1, 1, 1, 0.1, 0.1)
#
# while True:
#     ret, input_vid = video.read()
#     mask_img = cv2.imread(Mask_file_load, 1)
#     input_vid = cv2.resize(input_vid,
#                            None,
#                            fx=scaling,
#                            fy=scaling,
#                            interpolation=cv2.INTER_LINEAR)
#     # set_blocksize = blocksize_ini
#     # set_offset = offset_ini
#
#     tic = time.time()
#     if mask_on == True:
#         # create a mask and apply on video
#         ret, mask = create_mask(mask_img)
#         masked_vid = apply_mask(mask, input_vid)
#         th_masked = thresh_video(masked_vid, blocksize_ini, offset_ini)
#
#         contour_vid, cnt, pos_last, pos_now = detect_contours(input_vid, th_masked,
#                                                               cnt_min_th, cnt_max_th,
#                                                               pos_last, pos_now)
#
#
#         id_index, id_assign = identify(pos_last, pos_now)
#         # print(obj_id)
#         # print(obj_id_now)
#         # print(range(len(obj_id_m)))
#         # print(list(range(len(obj_id_now))))
#         contour_vid,pos_now = assignment(contour_vid, obj_id, colours,
#                                          obj_num, id_assign, pos_now,mark_on)
#
#
#
#     else:
#
#
#
#         th_masked = thresh_video(input_vid, blocksize_ini, offset_ini)
#
#         contour_vid, cnt, pos_last, pos_now = detect_contours(input_vid, th_masked,
#                                                               cnt_min_th, cnt_max_th,
#                                                               pos_last, pos_now)
#
#         id_index, id_assign = identify(pos_last, pos_now)
#         # print(obj_id)
#         # print(obj_id_now)
#         # print(range(len(obj_id_m)))
#         # print(list(range(len(obj_id_now))))
#         contour_vid, pos_now = assignment(contour_vid, obj_id, colours,
#                                           obj_num, id_assign, pos_now,mark_on)
# ##
#     # cv2.circle(contour_vid, (int(pos_now[0][0]), int(pos_now[0][1])), 10, (0, 191, 255), 1)
#     # Predict
#     # (x, y) = KF.predict()
#     # print(x, y)
#     # Draw a rectangle as the predicted object position
#     # cv2.rectangle(contour_vid, (x - 15, y - 15), (x + 15, y + 15), (255, 0, 0), 2)
#
#     # Update
#     # (x1, y1) = KF.update(pos_now[0])
#
#     # # Draw a rectangle as the estimated object position
#     # cv2.rectangle(contour_vid, (x1 - 15, y1 - 15), (x1 + 15, y1 + 15), (0, 0, 255), 1)
#
#     #  print(x1,y1)
#
#     # for i in range(obj_num):
#     #     cv2.circle(contour_vid, tuple([int(x) for x in pos_now[i]]), 5, colours[i % obj_num], -1, cv2.LINE_AA)
#     # if len(pos_now) != obj_num:
#     #     cnt, pos_now_update, runs = apply_mini_k_means(cnt, obj_num, pos_now)
#     #    cv2.putText(contour_vid, "Estimated Position", (x1 + 15, y1 + 10), 0, 0.5, (0, 0, 255), 2)
#     #    cv2.putText(contour_vid, "Predicted Position", (x + 15, y), 0, 0.5, (255, 0, 0), 2)
#     #    cv2.putText(contour_vid, "Measured Position", (int(pos_now[0][0]) + 15, int(pos_now[0][1] - 15)), 0, 0.5, (0, 191, 255), 2)
# ##
#     toc = time.time()
#
#     # cv2.imshow('Test', final_vid)
#     cv2.imshow('Test', contour_vid)
#
#     print("Time Elapsed Per Loop {:.3f}".format((tic - toc) / 50))
#     # cnt_array = np.vstack(cnt)
#     # print(cnt_array.shape)
#
#     if cv2.waitKey(0) & 0xFF == ord('q'):
#         video.release()
#         cv2.destroyAllWindows()
#         break
#
# video.release()
# cv2.destroyAllWindows()



#
# # import cv2
# # import numpy as np
#
#https://jinzhangyu.github.io/2018/08/21/2018-08-21-OpenCV-Python%E6%95%99%E7%A8%8B-5-%E9%BC%A0%E6%A0%87%E5%BD%93%E7%94%BB%E7%AC%94/
# import cv2
# import numpy as np
# import math
# mode = 'c'
# drawing = False
# start = (0,0)
# end = (0,0)
# img = np.zeros((512, 512, 3), np.uint8)
#
# def mouse_event(event, x, y, flags, param):
#     global mode, drawing, start, img, end
#
#     # 鼠标按下，开始画图：记录下起点
#     if event == cv2.EVENT_LBUTTONDOWN:
#         drawing = True
#         start = (x,y)
#     # 实时移动的位置作为矩形终点
#     elif event == cv2.EVENT_MOUSEMOVE:
#         if drawing :
#             if mode == 'c':
#                 radius = int(((start[0] - x) ** 2 + (start[1] - y) ** 2) ** 0.5)
#                 cv2.circle(img, start, radius, (0, 0, 255), 3)
#             else:
#                 cv2.rectangle(img, start, (x, y), (0, 255, 0), 3)
#         #end = (x,y)
#     # 鼠标释放后，停止绘图，并画出最终结果
#     elif event == cv2.EVENT_LBUTTONUP and drawing == True:
#         drawing = False
#
#
#
#     start = end = (0, 0)
#
# cv2.namedWindow('image')
# cv2.setMouseCallback('image', mouse_event)
#
# while (True):
#         # 下面这句话很关键，拷贝出原图，这样才可以实时画图形
#     temp = np.copy(img)
#
#     if drawing == True and mode == 'rectangle':
#         cv2.rectangle(temp, start, end, (0, 255, 0), 3)
#     elif drawing == True and mode == 'circle':
#         radius = int(((start[0] - end[0]) ** 2 + (start[1] - end[1]) ** 2) ** 0.5)
#         cv2.circle(temp, start, radius, (0, 0, 255), 3)
#
#         cv2.imshow('image', temp)
#
#
#     if cv2.waitKey(1) == ord('q'):
#         cv2.destroyAllWindows()
#         break
#     elif cv2.waitKey(1) == ord('m') and mode == 'rectangle':
#         mode = 'circle'
#         continue
#     elif cv2.waitKey(1) == ord('m') and mode == 'circle':
#         mode = 'rectangle'
#         continue
#     elif cv2.waitKey(1) == ord('c'):
#         img = np.zeros((512, 512, 3), np.uint8)
#         continue
#
# # drawing = False  # 是否开始画图
# # mode = True  # True：画矩形，False：画圆
# # ix,iy = (-1, -1)
# #
# # def mouse_event(event, x, y,flag,para):
# #
# #     global ix, iy, drawing, mode
# #     # drawing = False
# #     # mode = True
# #     # ix, iy = (-1, -1)
# #
# #     if event == cv2.EVENT_LBUTTONDOWN:
# #         drawing = True
# #         ix,iy = (x, y)
# #     elif event == cv2.EVENT_MBUTTONDOWN:
# #         if drawing:
# #             if mode == True:
# #                 r = int(math.sqrt(((x - ix) ** 2) + ((y - iy) ** 2)))
# #                 cv2.circle(img, (ix, iy), r, (0, 0, 255), 1)
# #                 # print(r)
# #                 # print(ix,iy)
# #                 # print(x,y)
# #                 # print(x-ix)
# #                 # print(int(math.sqrt(((x-ix)**2)+((y-iy)**2))))
# #             else:
# #                 cv2.rectangle(img, (ix, iy), (x, y), (0, 255, 0), 1)
# #     # 左键释放：结束画图
# #     elif event == cv2.EVENT_LBUTTONUP:
# #         drawing = False
# #         if mode == True:
# #             r = int(math.sqrt(((x - ix) ** 2) + ((y - iy) ** 2)))
# #             cv2.circle(img, (ix, iy), r, (0, 0, 255), 1)
# #         else:
# #             cv2.rectangle(img, (ix,iy), (x, y), (0, 255, 0), 1)
# #
# #
# # img = np.zeros((512, 512, 3), np.uint8)
# #
# # cv2.namedWindow('image')
# # cv2.setMouseCallback('image', mouse_event)
# #
# # while(True):
# #     cv2.imshow('image', img)
# #     # 按下m切换模式
# #     if cv2.waitKey(1) == ord('m'):
# #         mode = not mode
# #     elif cv2.waitKey(1) == 27:
# #         break

import cv2
import numpy as np
Video_load = 'randomball.mp4'
video = cv2.VideoCapture(Video_load)
# img = np.zeros((512,512,3), np.uint8)


ret, vid = video.read()
vid_draw = vid.copy()
drawing = False
start = (0,0)
end = (0,0)
img = vid_draw

def mouse_event(event, x, y, flags, param):
    global drawing, start, img, end

    # 鼠标按下，开始画图：记录下起点
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        start = (x,y)
        #start_copy=start
    # 实时移动的位置作为矩形终点
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing :
            path=(x,y)
            cv2.line(img,start,path,color=(255,0,0),thickness=2)
        end = (x,y)
    # 鼠标释放后，停止绘图，并画出最终结果
    elif event == cv2.EVENT_LBUTTONUP and drawing == True:
        drawing = False
        start = end = (0, 0)



def draw(x,y):

    cv2.setMouseCallback('Test',mouse_event)
    if drawing == True:
        x=start
        y=end

    return x,y
    #cv2.line(vid_draw, start_copy, end_copy, (0, 255, 0), 3)

start_copy=(0,0)
end_copy=(0,0)
cv2.namedWindow('Test', cv2.WINDOW_NORMAL)
while True:
    ret, vid = video.read()
    vid_draw = vid.copy()
    xx, yy = draw(start_copy,end_copy)
    # cv2.setMouseCallback('Test', mouse_event)
    # if drawing == True:
    #     start_copy=start
    #     end_copy=end

    cv2.line(vid_draw, xx,yy,(0, 255, 0), 3)
    cv2.imshow('Test', vid_draw)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()