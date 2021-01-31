'''
This module is to allow drawing objects (lines, rectangulars, circles)
on video use mouse operation in realtime and display the drawing
'''
import cv2
from math import  pi

isDrawing = False
resetDrawing = False

# before mouse event activate the drawing mode
# give a placeholder value for start and end coordinate of the line
ini_start = (0, 0)
ini_end = (0, 0)
# create a list to store coordinates of line
# before mouse event activate the drawing mode
# no coordinates will be stored in the list
# so at the initial, the list must not be empty by given placeholder value
line_coordinates = [(0, 0), (0, 0)]

class DrawObjectWidget(object):
    def __init__(self, frame):
        # take the frame of video that to be draw as argument
        self.frame = frame

        # draw line on copy of the frame
        self.frame_clone = self.frame.copy()

    # define mouse callback function
    def extract_coordinates(self, event, x, y, flags, parameters):

        global isDrawing, resetDrawing, startPoint, pathPoint, endPoint

        # When left mouse button click
        # activate drawing mode, allow coordinates (x,y) to be stored as start point
        if event == cv2.EVENT_LBUTTONDOWN:
            # clear the coordinate list that store placeholder/previous value
            # this will result drawing a new object each time right click
            # for drawing multiple objects, maybe group two coordinates in a list
            # then nest it in a parent list?
            # e.g. for line i:
            # xi, yi = parent_list[i][0],parent_list[i][1]
            line_coordinates.clear()
            # activate drawing mode, allow coordinates to be stored
            isDrawing = True
            resetDrawing = False
            startPoint = (x, y)
            # store coordinate in the list
            line_coordinates.append(startPoint)
            # print(line_coordinates)

        elif event == cv2.EVENT_MOUSEMOVE:
            # Draw line
            if isDrawing:
                pathPoint = (x, y)
            pathPoint = (x, y)

        elif event == cv2.EVENT_LBUTTONUP and isDrawing == True:
            # deactivate drawing mode, store coordinates as endpoint of line
            isDrawing = False
            resetDrawing = False
            endPoint = (x, y)
            line_coordinates.append(endPoint)
            # can return coordinates list here as output ?


        # Clear drawing boxes on right mouse button click
        elif event == cv2.EVENT_RBUTTONDOWN:
            # self.frame_clone = self.frame.copy()
            resetDrawing = True

    def drawingPath(self, x, y):
        # the name of window have to match the main function!!!
        cv2.setMouseCallback('Test', self.extract_coordinates)
        # while drawing mode is activate
        # return the start point and keep return all point on the path
        # that mouse drag through
        # in order to draw line from start point and draw the path continuously
        # when drag the mouse
        if isDrawing and not resetDrawing:
            x = startPoint
            y = pathPoint
        # while drawing mode is deactivate
        # return start and end point stored in the list
        # in order to draw a final line in between
        elif not isDrawing and not resetDrawing:
            x = line_coordinates[0]
            y = line_coordinates[1]
        elif resetDrawing:
            x = ini_start
            y = ini_end
        else:
            x = ini_start
            y = ini_end
        return x, y

    def displayDrawing(self, x, y, drawingMode=None):

        if drawingMode  == 'Line':
            cv2.line(self.show_image(), x, y, (0, 0, 255), 2)
            # lineLen = ((x[0]-y[0])**2 + (x[1]-y[1])**2)**0.5
            # print('Length of the line is : {}'.format(lineLen))


        elif drawingMode == 'Rectangle':
            cv2.rectangle(self.show_image(), x, y, (0, 0, 255), 2)
            # areaRec = (abs(x[0]-y[0]) * abs(x[1]-y[1]))
            # print('Area of the selected rectangular zone is : {}'.format(areaRec))


        elif drawingMode == 'Circle':
            r = int(((x[0]-y[0])**2 + (x[1]-y[1])**2)**0.5)
            areaCir = pi * (r**2)
            cv2.circle(self.show_image(), x, r, (0, 0, 255), 2)
            # print('Area of the selected circular zone is : {}\n'
            #       'Radius of the selected circular zone is: {}'.format(areaCir,r))

    def show_image(self):
        return self.frame_clone


# if __name__ == '__main__':
    # Video_load = 'zebrafish_video.mp4'
    # video = cv2.VideoCapture(Video_load)
    # cv2.namedWindow('Test', cv2.WINDOW_NORMAL)


    # while True:
    #     ret, vid = video.read()
    #
    #     # run draw line method for each frame
    #     draw_line = DrawLineWidget(vid)
    #     # grab coordinate returned from drawing function for each frame
    #     # drawing function takes initial (0,0) as default arguments
    #     draw_start, draw_end = draw_line.drawing(ini_start, ini_end)
    #     # print('Starting: {}, Ending: {}'.format(draw_start, draw_end))
    #     # draw based on returned coordinates on each frame
    #     if drawingMode == 'Line':
    #         cv2.line(draw_line.show_image(), draw_start, draw_end, (0, 0, 255), 2)
    #     elif drawingMode == 'Rectangle':
    #         cv2.rectangle(draw_line.show_image(), draw_start, draw_end, (0, 0, 255), 2)
    #     elif drawingMode == 'Circle':
    #         r = int(((draw_start[0]-draw_end[0])**2 + (draw_start[1]-draw_end[1])**2)**0.5)
    #         cv2.circle(draw_line.show_image(), draw_start, r, (0, 0, 255), 2)
    #     cv2.imshow('Test', draw_line.show_image())
    #
    #     key = cv2.waitKey(30)
    #
        # if key == ord('q'):
        #     cv2.destroyAllWindows()
        #     break
        # elif key == ord('m') and drawingMode == 'Line':
        #     resetDrawing = True
        #     drawingMode = 'Rectangle'
        #     print('Drawing mode : Rectangle')
        #     continue
        # elif key == ord('m') and drawingMode == 'Rectangle':
        #     resetDrawing = True
        #     drawingMode = 'Circle'
        #     print('Drawing mode : Circle')
        #     continue
        # elif key == ord('m') and drawingMode == 'Circle':
        #     resetDrawing = True
        #     drawingMode = 'Line'
        #     print('Drawing mode : Line')
        #     continue
        # elif key == ord('c'):
        #     resetDrawing = True
        #     continue


