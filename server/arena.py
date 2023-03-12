
import cv2, os, ujson
import numpy as np
import matplotlib.pyplot as plt

# info Arena class is used to detect the arena and the colors in the arena
# info The class is used to detect the colors in the arena and to detect the center of the colors
# info Class takes the image path as an argument
# info finalResult is the final result of the class which is in the form of a list that contains the image coordinates and the colors in the arena
# info colors is the list that contains the colors in the arena
# info averageCs is the list that contains the average column of the colors in the arena
# info averageRs is the list that contains the average row of the colors in the arena

class Arena:
    def __init__(self, imgPath, showPlot=False):
        ARUCO_DICT = {
            "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
            "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
            "DICT_4X4_250": cv2.aruco.DICT_4X4_250,
            "DICT_4X4_1000": cv2.aruco.DICT_4X4_1000,
            "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
            "DICT_5X5_100": cv2.aruco.DICT_5X5_100,
            "DICT_5X5_250": cv2.aruco.DICT_5X5_250,
            "DICT_5X5_1000": cv2.aruco.DICT_5X5_1000,
            "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
            "DICT_6X6_100": cv2.aruco.DICT_6X6_100,
            "DICT_6X6_250": cv2.aruco.DICT_6X6_250,
            "DICT_6X6_1000": cv2.aruco.DICT_6X6_1000,
            "DICT_7X7_50": cv2.aruco.DICT_7X7_50,
            "DICT_7X7_100": cv2.aruco.DICT_7X7_100,
            "DICT_7X7_250": cv2.aruco.DICT_7X7_250,
            "DICT_7X7_1000": cv2.aruco.DICT_7X7_1000,
            "DICT_ARUCO_ORIGINAL": cv2.aruco.DICT_ARUCO_ORIGINAL,
            "DICT_APRILTAG_16h5": cv2.aruco.DICT_APRILTAG_16h5,
            "DICT_APRILTAG_25h9": cv2.aruco.DICT_APRILTAG_25h9,
            "DICT_APRILTAG_36h10": cv2.aruco.DICT_APRILTAG_36h10,
            "DICT_APRILTAG_36h11": cv2.aruco.DICT_APRILTAG_36h11
        }

        arucoDict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT["DICT_4X4_1000"])
        arucoParams = cv2.aruco.DetectorParameters()
        self.aruco_det = cv2.aruco.ArucoDetector(arucoDict, arucoParams)

        self.result = list([] for i in range(6))
        self.finalResult = list([] for i in range(6))
        self.colors = list([] for i in range(6))
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
        self.arucoCenters = []
        self.showPlot = showPlot
        self.imgPath = imgPath
        self.img = cv2.imread(self.imgPath)
        self.kernel = np.ones((5,5), np.uint8)
        self.hsv = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV)

        self.grid_centers = [
                            [49, 438], [122, 437], [196, 436], [272, 435], [347, 434], [421, 432], [495, 430], [574, 429], 
                            [574, 354], [495, 354], [421, 355], [347, 356], [272, 357], [196, 357], [122, 358], [48, 358], 
                            [575, 278], [496, 278], [422, 279], [348, 278], [273, 278], [197, 278], [120, 278], [47, 277], 
                            [576, 200], [497, 200], [422, 200], [348, 200], [273, 199], [197, 199], [121, 200], [46, 199], 
                            [576, 123], [497, 123], [423, 123], [348, 123], [273, 123], [197, 123], [121, 123], [46, 122], 
                            [120, 47], [45, 47], [423, 46], [349, 46], [272, 46], [196, 47], [577, 46], [497, 46]
                            ]

        self.coor = self.get_pix_coords()

        self.half_edge = 25

        self.detect_red()
        self.detect_green()
        self.detect_blue()
        self.detect_yellow()
        self.detect_white()
        
        self.what_abdulkadir_wants()
        self.updatePositions()
        cv2.destroyAllWindows()

    def get_pix_coords(self):
        corners, ids, rejected  = self.aruco_det.detectMarkers(self.img)
        # verify *at least* one ArUco marker was detected
        if len(corners) > 0:
            coord_list = []
            # flatten the ArUco IDs list
            ids = ids.flatten()
            # loop over the detected ArUCo corners
            for (markerCorner, markerID) in zip(corners, ids):
                # extract the marker corners (which are always returned in
                # top-left, top-right, bottom-right, and bottom-left order)
                corners = markerCorner.reshape((4, 2))
                (topLeft, topRight, bottomRight, bottomLeft) = corners
                coord_list.append({'ID':markerID,'POS': np.squeeze(corners).tolist()})


                # convert each of the (x, y)-coordinate pairs to integers
                topRight = (int(topRight[0]), int(topRight[1]))
                bottomRight = (int(bottomRight[0]), int(bottomRight[1]))
                bottomLeft = (int(bottomLeft[0]), int(bottomLeft[1]))
                topLeft = (int(topLeft[0]), int(topLeft[1]))
                cX = int((topLeft[0] + bottomRight[0]) / 2.0)
                cY = int((topLeft[1] + bottomRight[1]) / 2.0)
                self.arucoCenters.append([cX, cY])
                
            return(coord_list)

    def detect_red(self):

        l = np.array([0, 100, 80])
        u = np.array([20, 255, 255])
        all_colored_images_detected = cv2.inRange(self.hsv, l, u)
        grid_erosion = cv2.erode(all_colored_images_detected, self.kernel, iterations=1)
        # cv2.imshow("",grid_erosion)
        contours, _ = cv2.findContours(grid_erosion, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for center in self.grid_centers:
            for contour in contours:
                M = cv2.moments(contour)
                if M['m00'] != 0.0:
                    if ( (center[0]-int(M['m10']/M['m00']))**2 + (center[1]-int(M['m01']/M['m00']))**2 )**0.5 < 45 and center not in self.center_locations_general:
                        cv2.rectangle(self.img, (center[0] + self.half_edge, center[1] + self.half_edge), (center[0] - self.half_edge, center[1] - self.half_edge), (0, 0,255), 5)
                        self.center_locations_general.append(center)
                        self.center_locations[0].append(center)

    def detect_green(self):
        l = np.array([25, 100, 80])
        u = np.array([95, 255, 255])
        all_colored_images_detected = cv2.inRange(self.hsv, l, u)
        grid_erosion = cv2.erode(all_colored_images_detected, self.kernel, iterations=1)
        contours, _ = cv2.findContours(grid_erosion, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for center in self.grid_centers:
            for contour in contours:
                M = cv2.moments(contour)
                if M['m00'] != 0.0:
                    if ( (center[0]-int(M['m10']/M['m00']))**2 + (center[1]-int(M['m01']/M['m00']))**2 )**0.5 < 45 and center not in self.center_locations_general:
                        cv2.rectangle(self.img, (center[0] + self.half_edge, center[1] + self.half_edge), (center[0] - self.half_edge, center[1] - self.half_edge), (0, 255, 0), 5)
                        self.center_locations_general.append(center)
                        self.center_locations[1].append(center)

    def detect_blue(self):
        l = np.array([95, 100, 70])
        u = np.array([170, 255, 255])
        all_colored_images_detected = cv2.inRange(self.hsv, l, u)
        grid_erosion = cv2.erode(all_colored_images_detected, self.kernel, iterations=1)
        contours, _ = cv2.findContours(grid_erosion, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for center in self.grid_centers:
            for contour in contours:
                M = cv2.moments(contour)
                if M['m00'] != 0.0:
                    if ( (center[0]-int(M['m10']/M['m00']))**2 + (center[1]-int(M['m01']/M['m00']))**2 )**0.5 < 45 and center not in self.center_locations_general:
                        cv2.rectangle(self.img, (center[0] + self.half_edge, center[1] + self.half_edge), (center[0] - self.half_edge, center[1] - self.half_edge), (255, 0, 0), 5)
                        self.center_locations_general.append(center)
                        self.center_locations[2].append(center)

    def detect_yellow(self):

        l = np.array([0, 100, 100])
        u = np.array([20, 255, 255])
        all_colored_images_detected = cv2.inRange(self.img, l, u)
        grid_erosion = cv2.erode(all_colored_images_detected, self.kernel, iterations=1)
        # cv2.imshow("",grid_erosion)
        contours, _ = cv2.findContours(grid_erosion, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        count = 1
        for center in self.grid_centers:
            for contour in contours:
                M = cv2.moments(contour)
                if M['m00'] != 0.0:
                    if ( (center[0]-int(M['m10']/M['m00']))**2 + (center[1]-int(M['m01']/M['m00']))**2 )**0.5 < 45 and center not in self.center_locations_general:
                        cv2.rectangle(self.img, (center[0] + self.half_edge, center[1] + self.half_edge), (center[0] - self.half_edge, center[1] - self.half_edge), (0, 255, 255), 5)
                        self.center_locations_general.append(center)
                        self.center_locations[3].append(center)
                        #print(count)
                        count += 1

    def detect_white(self):
        for center in self.grid_centers:
            if center not in self.center_locations_general:
                cv2.rectangle(self.img, (center[0] + self.half_edge, center[1] + self.half_edge), (center[0] - self.half_edge, center[1] - self.half_edge), (255, 255, 255), 1)
                self.center_locations_general.append(center)
                self.center_locations[4].append(center)
                
        if self.showPlot:
            plt.plot()
            plt.title("Differantiated White Regions")
            plt.imshow(cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB))
            plt.show()

    def what_abdulkadir_wants(self):
        for center in self.center_locations_general:
            self.row_list.append(center[0])
            self.column_list.append(center[1])
        self.row_list.sort()
        self.column_list.sort()
        group_difference_threshold = 100
        self.center_locations_general.sort()

        for center in self.center_locations_general:
            center.reverse()
        self.center_locations_general.sort()

        for center in self.center_locations_general:
            if center == self.center_locations_general[0]:
                self.group_0_x.append(center)
            elif abs(center[0]-self.group_0_x[-1][0]) <= 30:
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
        sz = (len(self.result), len(self.result[0]))
        self.finalResult = list(list([] for i in range(sz[1])) for j in range(sz[0])) 
        self.colors = list(list([] for i in range(sz[1])) for j in range(sz[0])) 

        for i in range(len(self.result)):
                for j in range(len(self.result[i])):
                    doruk = self.result[i][j]
                    if doruk in self.center_locations[0]:
                        info = [(doruk[0], doruk[1]), "R"]
                        self.finalResult[i][j] = info
                        self.colors[i][j] = "R"
                    elif doruk in self.center_locations[1]:
                        info = [(doruk[0], doruk[1]), "G"]
                        self.finalResult[i][j] = info
                        self.colors[i][j] = "G"
                    elif doruk in self.center_locations[2]:
                        info = [(doruk[0], doruk[1]), "B"]
                        self.finalResult[i][j] = info
                        self.colors[i][j] = "B"
                    elif doruk in self.center_locations[3]:
                        info = [(doruk[0], doruk[1]), "Y"]
                        self.finalResult[i][j] = info
                        self.colors[i][j] = "Y"
                    else:
                        info = [(doruk[0], doruk[1]), "W"]
                        self.finalResult[i][j] = info
                        self.colors[i][j] = "W"
        
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
