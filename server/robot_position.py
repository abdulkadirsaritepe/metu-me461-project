
import os, ujson, time
from math import atan2, degrees

# info RobotPosition class is used to get the robot positions and the grid centers
# info It also calculates the current cell of the robot
# info The angle of the robot is calculated using the atan2 function
# info The euclidean distance is calculated using the Pythagorean theorem
# info The current cell is calculated using the euclidean distance
# info After the currentcell and the angle are calculated, the robot position is updated
# info The robot is moved according to the currentcell and the targetcell
# info move method is used to move the robot by using the grid coordinates ex. (1, 1)

class RobotPosition:
    def __init__(self, picomqtt, gamemqtt, colors):
        self.dir_path = os.path.dirname(os.path.realpath(__file__)) # Get the current directory
        self.game_info_path = f'{self.dir_path}/game_info.ujson' # Path to the game info file
        self.file_path = os.path.join(self.dir_path, "positions.ujson") # Path to the positions file
        self.param_path = f'{self.dir_path}/parameters.ujson' # Path to the parameters file
        self.colors = colors
        self.game_info = {}
        self.role = None
        self.positions = []
        self.gridSize = []
        self.robotPositions = {}
        self.robotCenters = {}
        self.robotPos = []
        self.robotPosImg = []
        self.averageRs = []
        self.averageCs = []
        self.currentcell = []
        self.currentAngle = 0
        self.euclideanDistance = 0
        self.speed = 0
        self.previousAngle = None
        self.picomqtt = picomqtt
        self.gamemqtt = gamemqtt
        while not self.gamemqtt.arenaImageTaken:
            time.sleep(0.1)
        while self.gamemqtt.tick > 0:
            time.sleep(0.1)
        self.updatePositions()

    def get_params(self): # Get the parameters
        try:
            game_info = ujson.loads(open(self.game_info_path).read()) # Read the parameters file
            self.robotId = int(game_info['ID']) # Get the robot ID
            # ! self.robotPositions = game_info['stats'] # Get the robot positions
            # ! self.robotPos = self.robotPositions[str(self.robotId)] # Get the robot position
            self.robotPositions = self.gamemqtt.stats
            self.robotPos = self.robotPositions[int(self.robotId)]
            self.role = game_info['role'] # Get the robot role
            self.speedLimits = game_info[self.role]['speedLimits'] # Get the speed limit
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
            print("error")

    def updateCurrentCell(self):
        self.get_params()
        if self.robotPos == []:
            return
        x = sum([int(self.robotPos[i][0]) for i in range(4)])/4
        y = sum([int(self.robotPos[i][1]) for i in range(4)])/4
        rx, ry = 0, 0
        pointR, pointC = 0,0

        for i in range(len(self.averageRs)):
            if self.averageRs[i]-60 < y < self.averageRs[i]+60:
                ry = self.averageRs[i]
                pointR = i # IMPORTANT
                break
        for j in range(len(self.averageCs)):
            if self.averageCs[j]-60 < x < self.averageCs[j]+60:
                rx = self.averageCs[j]
                pointC = j # IMPORTANT
                break
        r = ((rx-x)**2+(ry-y)**2)**0.5
        self.robotPosImg = [x, y]
        self.euclideanDistance = r
        if r < 30 or self.currentcell == []:
            self.currentcell = [pointR, pointC]
        # try:
        #     with open(self.game_info_path, "r") as file:
        #         game_info = ujson.load(file)
        #     game_info['currentcell'] = self.currentcell
        #     with open(self.game_info_path, "w") as file:
        #         ujson.dump(game_info, file)
        # except:
        #     pass
        return self.currentcell

    def updateCurrentRobotCells(self):
        self.get_params()
        self.updatePositions()
        for robot, pos in self.robotPositions.items():
            x = sum([int(pos[i][0]) for i in range(4)])/4
            y = sum([int(pos[i][1]) for i in range(4)])/4
            r, c = 0, 0
            for i in range(len(self.averageRs)):
                if self.averageRs[i]-60 < y < self.averageRs[i]+60:
                    r = i
                    break
            for j in range(len(self.averageCs)):
                if self.averageCs[j]-60 < x < self.averageCs[j]+60:
                    c = j
                    break
            self.robotCenters.update({robot:[r, c]})
    
    def findCurrentAngle(self): 
        self.updateCurrentCell()
        # Find the current angle of the robot between the two front wheels (in degrees) 0,1 aruco markers.
        angle1 = atan2((self.robotPos[3][1] - self.robotPos[0][1]), (self.robotPos[3][0] - self.robotPos[0][0]))
        angle2 = atan2((self.robotPos[2][1] - self.robotPos[1][1]), (self.robotPos[2][0] - self.robotPos[1][0]))
        angle = (angle1 + angle2) / 2
        self.currentAngle = degrees(angle)
        self.currentAngle = self.currentAngle if self.currentAngle > 0 else self.currentAngle + 360
        return self.currentAngle

    def calculateSpeed(self, cell):
        if self.colors[cell[0]][cell[1]] == "R":
            return 0
        info = ujson.loads(open(self.param_path).read()) # Read the parameters file
        cellColor = self.colors[cell[0]][cell[1]] # TODO Get the color of the cell
        speedLimit = self.speedLimits[cellColor] # Get the speed limit
        speed = (info["speedInfo"])[speedLimit]*(info['speedInfo'])['speedMultiplier'] # Speed of the robot
        self.speedName = speedLimit # Name of the speed
        return speed

    def turnSomeAngle(self, direction, turnDelay):
        speed = 20000
        turnDelay = 100 if turnDelay < 100 else int(turnDelay)
        direction1 = "0" if str(direction) == "1" else "1" if str(direction) == "0" else str(direction)
        msg = f"22-{direction1}:{int(speed)}:{direction}:{speed}:{turnDelay}"
        self.picomqtt.publishToTopic(msg)

    def goSomeDistance(self, direction, moveDelay):
        self.speed = self.calculateSpeed(self.currentcell)
        moveDelay = 100 if moveDelay < 100 else int(moveDelay)
        msg = f"22-{direction}:{int(self.speed)}:{direction}:{self.speed}:{moveDelay}"
        self.picomqtt.publishToTopic(msg)

    def move(self, targetcell, currentcell):
        self.get_params()
        self.speed = self.calculateSpeed(currentcell)
        print(f'{currentcell} -> {targetcell}')
        r = targetcell[0] - currentcell[0]
        c = targetcell[1] - currentcell[1]
        if r != 0 and c != 0:
            return
        elif r == 0:
            targetangle = 270 if c > 0 else 90
        elif c == 0:
            targetangle = 0 if r > 0 else 180
        else:
            return
        delta = targetangle - self.currentAngle
        turnDelay = 50 # int(abs(delta)*280/90)
        k = 0
        self.previousAngle = self.findCurrentAngle()
        while abs(delta) > 5: # and k < 10:
            angulardirectionMsg = '0' if delta < 0 else '1' if delta > 0 else 'none'
            self.turnSomeAngle(angulardirectionMsg, turnDelay)
            while int(self.findCurrentAngle()) == int(self.previousAngle):
                time.sleep(0.01)
            print(delta)
            delta = targetangle - self.findCurrentAngle()
            # turnDelay = int(abs(delta)*200/90)
            k += 1
            self.previousAngle = self.currentAngle

        moveDelay = 120
        k = 0
        while self.updateCurrentCell != targetcell or self.euclideanDistance > 30:
            lineardirectionMsg = '1' # if targetangle > 0 else '0'
            self.updateCurrentCell()
            self.goSomeDistance(lineardirectionMsg, moveDelay)
            moveDelay = moveDelay / 2
            k += 1
            if k == 5:
                break
