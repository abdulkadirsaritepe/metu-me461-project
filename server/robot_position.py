
import os, ujson
from math import atan2, degrees

class RobotPosition:
    def __init__(self, picomqtt):
        self.dir_path = os.path.dirname(os.path.realpath(__file__)) # Get the current directory
        self.game_info_path = f'{self.dir_path}/game_info.ujson' # Path to the game info file
        self.file_path = os.path.join(self.dir_path, "positions.ujson") # Path to the positions file
        self.game_info = {}
        self.positions = []
        self.gridSize = []
        self.robotPositions = []
        self.robotCenters = []
        self.robotPos = []
        self.robotPosImg = []
        self.averageRs = []
        self.averageCs = []
        self.currentcell = []
        self.currentAngle = 0
        self.euclideanDistance = 0
        self.picomqtt = picomqtt

    def get_params(self): # Get the parameters
        try:
            game_info = ujson.loads(open(self.game_info_path).read()) # Read the parameters file
            self.robotId = int(game_info['ID']) # Get the robot ID
            self.robotPositions = game_info['stats'] # Get the robot positions
            self.robotPos = self.robotPositions[str(self.robotId)] # Get the robot position
        except:
            pass
        
    def updatePositions(self):
        try:
            self.get_params()           
            with open(self.file_path, "r") as file:
                positions = ujson.load(file)
            self.positions = positions['gridCenters']
            self.gridSize = positions['gridSize']
            self.averageRs = positions['averageRs']
            self.averageCs = positions['averageCs']
        except:
            pass

    def updateCurrentCell(self):
        self.updatePositions()
        if self.robotPos == []:
            return
        x = sum([int(self.robotPos[i][0]) for i in range(4)])/4
        y = sum([int(self.robotPos[i][1]) for i in range(4)])/4
        rx, ry = 0, 0
        for i in range(len(self.averageRs)):
            if self.averageRs[i]-60 < x < self.averageRs[i]+60:
                rx = self.averageRs[i]
                break
        for j in range(len(self.averageCs)):
            if self.averageCs[j]-60 < y < self.averageCs[j]+60:
                ry = self.averageCs[j]
                break
        r = ((rx-x)**2+(ry-y)**2)**0.5
        self.robotPosImg = [x, y]
        self.euclideanDistance = r
        if r < 30 or self.currentcell == []:
            self.currentcell = [i, j]
        return self.currentcell

    def updateCurrentRobotCells(self):
        self.updatePositions()
        for robot, pos in self.robotPositions.items():
            x = sum([int(pos[i][0]) for i in range(4)])/4
            y = sum([int(pos[i][1]) for i in range(4)])/4
            r, c = 0, 0
            for i in range(len(self.averageRs)):
                if self.averageRs[i]-60 < x < self.averageRs[i]+60:
                    r = i
                    break
            for j in range(len(self.averageCs)):
                if self.averageCs[j]-60 < y < self.averageCs[j]+60:
                    c = j
                    break
            self.robotCenters.append({robot:[r, c]})
    
    def findCurrentAngle(self): 
        self.updateCurrentCell()
        self.findCurrentAngle()
        # Find the current angle of the robot between the two front wheels (in degrees) 0,1 aruco markers.
        angle1 = atan2((self.robotPos[3][1] - self.robotPos[0][1]), (self.robotPos[3][0] - self.robotPos[0][0]))
        angle2 = atan2((self.robotPos[2][1] - self.robotPos[1][1]), (self.robotPos[2][0] - self.robotPos[1][0]))
        angle = (angle1 + angle2) / 2
        self.currentAngle = degrees(angle)

    def move(self, targetcell, speed):
        x = targetcell[1] - self.currentcell[1]
        y = targetcell[0] - self.currentcell[0]
        if x == 0:
            targetangle = 90 if y > 0 else -90
        elif y == 0:
            targetangle = 0 if x > 0 else -180
        else:
            return
        delta = targetangle - self.currentAngle
        angulardirectionMsg = '0' if delta > 0 else '1' if delta < 0 else 'none'
        msg = f'11-{angulardirectionMsg}:none:{speed}'
        self.picomqtt.publishToTopic(msg)
        while abs(delta) > 2:
            self.findCurrentAngle()
            delta = targetangle - self.currentAngle
        self.picomqtt.publishToTopic('11-none:none:0')

        lineardirectionMsg = '1' if targetangle > 0 else '0'
        msg = f'11-none:{lineardirectionMsg}:{speed}'
        self.picomqtt.publishToTopic(msg)
        while self.euclideanDistance > 30:
            self.updateCurrentCell()
        self.picomqtt.publishToTopic('11-none:none:0')
