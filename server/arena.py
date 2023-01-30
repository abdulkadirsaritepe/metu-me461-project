
import cv2, os, ujson
import numpy as np
import matplotlib.pyplot as plt

class Arena:
    def __init__(self, imgPath):
        self.result = list([] for i in range(6))
        self.finalResult = list([] for i in range(6))
        self.center_lines = [[],[]]
        self.center_locations_general = []  # uncategorized
        self.center_locations = list([] for i in range(5))  # R G B Y W
        self.ordered_list = list([] for i in range(6))  # row0 row1 row2 row3 row4 row5
        self.row_list = []
        self.column_list = []
        self.group_0_x = []
        self.group_1_x = []
        self.group_2_x = []
        self.group_3_x = []
        self.group_4_x = []
        self.group_5_x = []
        self.averageCs = []
        self.averageRs = []
        self.showPlot = False
        self.imgPath = imgPath
        self.img = cv2.imread(self.imgPath)
        self.kernel = np.ones((7,7), np.uint8)
        self.hsv = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV)
        for i in range(0, 5):
            if i == 0:
                self.detect_red()
            elif i == 1:
                self.detect_green()
            elif i == 2:
                self.detect_blue()
            elif i == 3:
                self.detect_yellow()
            else:
                self.detect_white()
        self.what_abdulkadir_wants()
        self.updatePositions()
        cv2.destroyAllWindows()

    def equliz(self, img):
        img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
        img_yuv[:, :, 0] = cv2.equalizeHist(img_yuv[:, :, 0])
        img_yuv[:, 0, :] = cv2.equalizeHist(img_yuv[:, 0, :])
        img_yuv[0, :, :] = cv2.equalizeHist(img_yuv[0, :, :])
        img_output = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)
        return img_output

    def binarize(self, equlized_grayscale):
        _, my_threshold = cv2.threshold(equlized_grayscale, 75, 255, cv2.THRESH_BINARY)
        return my_threshold

    def detect_red(self):
        l = np.array([0,100,100])
        u = np.array([15,255,255])
        all_colored_images_detected = cv2.inRange(self.hsv, l, u)
        grid_erosion = cv2.erode(all_colored_images_detected, self.kernel, iterations = 1)
        grid_dilation = cv2.dilate(grid_erosion, self.kernel, iterations = 4)
        contours, _ = cv2.findContours(grid_dilation, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            M = cv2.moments(contour)
            if M['m00'] != 0.0:
                x = int(M['m10']/M['m00'])
                y = int(M['m01']/M['m00'])
            self.center_locations[0].append([x,y])
            self.center_locations_general.append([x,y])

    def detect_green(self):
        l = np.array([45, 100, 100])
        u = np.array([95, 255, 255])
        all_colored_images_detected = cv2.inRange(self.hsv, l, u)
        grid_erosion = cv2.erode(all_colored_images_detected, self.kernel, iterations=2)
        grid_dilation = cv2.dilate(grid_erosion, self.kernel, iterations=4)
        contours, _ = cv2.findContours(
            grid_dilation, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            M = cv2.moments(contour)
            if M['m00'] != 0.0:
                x = int(M['m10']/M['m00'])
                y = int(M['m01']/M['m00'])
            self.center_locations[1].append([x, y])
            self.center_locations_general.append([x, y])

    def detect_blue(self):
        l = np.array([95, 100, 100])
        u = np.array([170, 255, 255])
        all_colored_images_detected = cv2.inRange(self.hsv, l, u)
        grid_dilation = cv2.dilate(
            all_colored_images_detected, self.kernel, iterations=2)
        contours, _ = cv2.findContours(
            grid_dilation, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            M = cv2.moments(contour)
            if M['m00'] != 0.0:
                x = int(M['m10']/M['m00'])
                y = int(M['m01']/M['m00'])
            self.center_locations[2].append([x, y])
            self.center_locations_general.append([x, y])

    def detect_yellow(self):
        l = np.array([15, 100, 100])
        u = np.array([45, 255, 255])
        all_colored_images_detected = cv2.inRange(self.hsv, l, u)
        grid_erosion = cv2.erode(all_colored_images_detected, self.kernel, iterations=2)
        contours, _ = cv2.findContours(
            grid_erosion, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            M = cv2.moments(contour)
            if M['m00'] != 0.0:
                x = int(M['m10']/M['m00'])
                y = int(M['m01']/M['m00'])
            self.center_locations[3].append([x, y])
            self.center_locations_general.append([x, y])

    def detect_white(self):
        img2 = self.equliz(self.img)
        img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        img2 = self.binarize(img2)
        img2 = cv2.erode(img2, self.kernel, iterations = 8)
        img2 = cv2.dilate(img2, self.kernel, iterations = 5)
        contours, _ = cv2.findContours(
            img2, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        count = 1
        for contour in contours:
            M = cv2.moments(contour)
            if M['m00'] != 0.0:
                x = int(M['m10']/M['m00'])
                y = int(M['m01']/M['m00'])
            approx = cv2.approxPolyDP(contour, 0.01 * cv2.arcLength(contour, True), True)
            
            check = 0
            
            if len(approx) <= 10 and cv2.contourArea(contour) > 1000:
                if cv2.contourArea(contour) < 30000:
                    for center in self.center_locations[3]:
                        if ((x-center[0])**2+(y-center[1])**2)**0.5 < 50:
                            check = 1
                    if check == 0:
                        cv2.drawContours(self.img, [contour], 0, (255, 255, 255), 4)
                        cv2.putText(self.img, str(count), (x,y), cv2.FONT_HERSHEY_SIMPLEX, 1, (200,200,200), 1, cv2.LINE_AA)
                        self.center_locations[4].append([x, y])
                        self.center_locations_general.append([x, y])
                        count += 1
        if self.showPlot:
            plt.plot()
            plt.title("White Result")
            plt.imshow(cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB))
            plt.show()

    def what_abdulkadir_wants(self):
        for center in self.center_locations_general:
            self.row_list.append(center[0])
            self.column_list.append(center[1])
        self.row_list.sort()
        self.column_list.sort()
        group_difference_threshold = 150
        self.center_locations_general.sort()

        for center in self.center_locations_general:
            center.reverse()
        self.center_locations_general.sort()

        for center in self.center_locations_general:
            if center == self.center_locations_general[0]:
                    self.group_0_x.append(center)
            elif abs(center[0]-self.group_0_x[-1][0]) <= 50:
                self.group_0_x.append(center)
            elif abs(center[0]-self.group_0_x[-1][0]) <= group_difference_threshold:
                self.group_1_x.append(center)
            elif abs(center[0]-self.group_1_x[-1][0]) <= group_difference_threshold:
                self.group_2_x.append(center)
            elif abs(center[0]-self.group_2_x[-1][0]) <= group_difference_threshold:
                    self.group_3_x.append(center)
            elif abs(center[0]-self.group_3_x[-1][0]) <= group_difference_threshold:
                self.group_4_x.append(center)
            else:
                self.group_5_x.append(center)

        for center in self.center_locations_general:
            if center in self.group_0_x:
                self.result[0].append(center)
            elif center in self.group_1_x:
                self.result[1].append(center)
            elif center in self.group_2_x:
                self.result[2].append(center)
            elif center in self.group_3_x:
                self.result[3].append(center)
            elif center in self.group_4_x:
                self.result[4].append(center)
            else:
                self.result[5].append(center)

        sz = (len(self.result), len(self.result[0]))

        for i in range(0, sz[0]):
            for element in self.result[i]:
                element.reverse()

        for i in range(0, sz[0]):
            self.result[i].sort()

        # while len(self.result) > 6:
        #     self.result.pop()
        # for i in range(0, 6):
        #     while len(self.result[i]) > 8:
        #         self.result[i].pop()
        self.finalResult = self.result

        for i in range(len(self.result)):
                for j in range(len(self.result[i])):
                    doruk = self.result[i][j]
                    if doruk in self.center_locations[0]:
                        info = [(doruk[0], doruk[1]), "R"]
                        self.finalResult[i][j] = info
                    elif doruk in self.center_locations[1]:
                        info = [(doruk[0], doruk[1]), "G"]
                        self.finalResult[i][j] = info
                    elif doruk in self.center_locations[2]:
                        info = [(doruk[0], doruk[1]), "B"]
                        self.finalResult[i][j] = info
                    elif doruk in self.center_locations[3]:
                        info = [(doruk[0], doruk[1]), "Y"]
                        self.finalResult[i][j] = info
                    else:
                        info = [(doruk[0], doruk[1]), "W"]
                        self.finalResult[i][j] = info

        for i in range(len(self.finalResult)):
            averageR = 0
            for j in range(len(self.finalResult[i])):
                averageR += self.finalResult[i][j][0][1]
            self.averageRs.append(averageR / len(self.finalResult[i]))
        
        n = min(list(len(self.finalResult[a]) for a in range(len(self.finalResult))))
        for i in range(n):
            averageC = 0
            for j in range(len(self.finalResult)):
                averageC += self.finalResult[j][i][0][0]
            self.averageCs.append(round(averageC / len(self.finalResult),3))

    def updatePositions(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(dir_path, "positions.ujson")
        positions = ujson.loads(open(file_path).read())
        sz = (len(self.finalResult), len(self.finalResult[0]))
        positions['gridCenters'] = self.finalResult
        positions['gridSize'] = sz
        positions['averageRs'] = self.averageRs
        positions['averageCs'] = self.averageCs
        with open(file_path, 'w') as f:
            ujson.dump(positions, f)
