
import os, sys, time, ujson, random
from path_finder import PathFinder
from arena import Arena
from robot_position import RobotPosition

class Autonomous:
    def __init__(self, picomqtt, gamemqtt):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.file_path = os.path.join(dir_path, "arena_view.png")
        self.game_info_path = os.path.join(dir_path, "game_info.json")
        self.positions_path = os.path.join(dir_path, "positions.json")
        self.picomqtt = picomqtt
        self.gamemqtt = gamemqtt
        self.status = None
        self.colors = None
        self.points = None
        self.gridSize = None
        self.paths = None
        self.currentPath = None
        self.currentStep = None
        self.currentTarget = None
        self.gridCenters = None
        while not gamemqtt.arenaImageTaken:
            time.sleep(0.5)
        self.arena = Arena(self.file_path)
        self.robotPositionClass = RobotPosition(self.picomqtt)
        self.get_params()
        self.updateInfo()
        self.pathFinder = PathFinder(self.gridSize, self.colors)

    def get_params(self): # Get the parameters
        info = ujson.loads(open(self.game_info_path).read()) # Read the parameters file
        self.role = info['role'] # Get the current role
        self.status = info['status'] # Get the current status
        self.robotId = info['ID'] # Get the robot ID
        self.points = info['role']['points'] # Get the points
        self.speedLimits = info['role']['speedLimits'] # Get the speed limit
        positions_info = ujson.loads(open(self.positions_path).read()) # Read the positions file
        self.gridCenters = positions_info['gridCenters'] # Get the positions
        self.gridSize = positions_info['gridSize'] # Get the grid size
        self.colors = list([] for i in range(6))
        for row in self.gridCenters:
            for item in row:
                self.colors.append(item[1])

    def updateInfo(self):
        self.robotPositionClass.updateCurrentRobotCells()  # Get the robot centers
        self.robotCenters = self.robotPositionClass.robotCenters # Get the robot centers
        for robot, pos in self.robotCenters.items():
            if robot != self.robotId:
                self.colors[pos[0]][pos[1]] = "R" # Set the robot color

    def findAutonomousPath(self, startcell, targetcell):
        self.paths = self.pathFinder.findPath(startcell, targetcell)
        if len(self.paths) > 0:
            self.currentPath = self.paths[0]
            self.currentStep = 0
            self.currentTarget = targetcell
            return True
        else:
            return False

    def decisionMaking(self):
        whiteCells = []
        blueCells = []
        greenCells = []
        yellowCells = []
        for i in range(len(self.colors)):
            for j in range(len(self.colors[i])):
                if self.colors[i][j] == "W":
                    whiteCells.append([i, j])
                elif self.colors[i][j] == "B":
                    blueCells.append([i, j])
                elif self.colors[i][j] == "G":
                    greenCells.append([i, j])
                elif self.colors[i][j] == "Y":
                    yellowCells.append([i, j])
        
        if len(yellowCells) == 0 or self.points['B'] >= self.points['Y']:
            choose = random.choice(blueCells)
        elif len(blueCells) == 0 or self.points['B'] < self.points['Y']:
            choose = random.choice(yellowCells)
        else:
            choose = random.choice(whiteCells)

        if len(self.pathFinder.findNeighbors(choose)) < 2:
            self.decisionMaking()

        return choose
        
    def processDecision(self):
        self.updateInfo()
        choose = self.decisionMaking()
        paths = self.pathFinder.findPath(self.robotPositionClass.updateCurrentCell(), choose)
        if len(paths) == 0:
            self.processDecision()
        else:
            path = paths[0]
            speed = self.speedLimits['A'] # TODO
            self.robotPositionClass.move(path[1], speed)

