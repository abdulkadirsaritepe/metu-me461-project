
import pygame, os, sys, time, ujson
from robot_position import RobotPosition
from arena import Arena

class Autonomous:
    def __init__(self, picomqtt, gamemqtt):
        self.dir_path = os.path.dirname(os.path.realpath(__file__)) # Get the current directory
        self.param_path = f'{self.dir_path}/parameters.ujson' # Path to the parameters file
        self.game_info_path = f'{self.dir_path}/game_info.ujson' # Path to the game info file
        self.file_path = os.path.join(self.dir_path, "positions.ujson") # Path to the positions file
        self.img_path = os.path.join(self.dir_path, "arena_view.png") # Path to the arena image
        self.mqtt = picomqtt
        self.gamemqtt = gamemqtt

        self.turnDelay = 283 # Delay in microseconds for turning
        self.moveDelay = 550 # Delay in microseconds for moving

        self.started = False
        self.robotId = None
        self.status = None
        self.speedLimits = None
        self.points = None
        self.gridSize = None
        self.paths = None
        self.next_step = []
        self.currentPath = None
        self.currentStep = None
        self.currentTarget = None
        self.gridCenters = None
        self.robotCenters = None
        self.positions = None
        self.averageCs = None
        self.averageRs = None
        self.gridCenters = None
        self.robotPosition = None
        self.gameTime = 0
        while not gamemqtt.arenaImageTaken:
            time.sleep(0.5)
        # while self.gamemqtt.tick >= 0:
        #     while self.gamemqtt.tick == 0:
        #         self.gameTime = int(self.gamemqtt.tick)
        #     time.sleep(0.1)
        print("Arena Image Taken")
        self.arena = Arena(self.img_path)
        self.colors = self.arena.colors
        self.robotPositionClass = RobotPosition(self.mqtt, self.gamemqtt, self.colors)
        self.get_params()
        self.updateInfo()
        while True:
            self.processDecision()
            time.sleep(0.5)

    def get_params(self):
        try:
            game_info = ujson.loads(open(self.game_info_path).read()) # Read the parameters file
            self.currentRole = game_info['role'] # Get the current role
            self.robotId = game_info['ID'] # Get the robot ID
            self.points = game_info[self.currentRole]['points'] # Get the points
            self.speedLimits = game_info[self.currentRole]['speedLimits'] # Get the speed limit
            param_info = ujson.loads(open(self.param_path).read()) # Read the parameters file
            self.speedValues = param_info['speedInfo'] # Get the speed values
            self.defaultSpeed = self.speedValues['speed'] # Get the default speed
            self.TIMEOUT = self.gamemqtt.TIMEOUT
            if self.currentRole == "PREY":
                self.mqtt.publishToTopic("10-prey1:1")
                self.mqtt.publishToTopic("10-prey2:1")
                self.mqtt.publishToTopic("10-predator1:0")
                self.mqtt.publishToTopic("10-predator2:0")
            elif self.currentRole == "PREDATOR":
                self.mqtt.publishToTopic("10-predator1:1")
                self.mqtt.publishToTopic("10-predator2:1")
                self.mqtt.publishToTopic("10-prey1:0")
                self.mqtt.publishToTopic("10-prey2:0")
            else:
                self.mqtt.publishToTopic("10-prey1:0")
                self.mqtt.publishToTopic("10-prey2:0")
                self.mqtt.publishToTopic("10-predator1:0")
                self.mqtt.publishToTopic("10-predator2:0")
            self.robotId = game_info['ID'] # Get the robot ID
            self.speedLimits = (game_info[self.currentRole])['speedLimits'] # Get the speed limits
            self.status = self.gamemqtt.status
            try:
                with open(self.file_path, "r") as file:
                    positions = ujson.load(file)
                self.positions = positions['gridCenters']
                self.gridSize = positions['gridSize']
                self.averageRs = positions['averageRs']
                self.averageCs = positions['averageCs']
            except:
                pass
        except Exception as e:
            print(f"ERROR: {e}")

    def updateInfo(self):
        self.robotPositionClass.updateCurrentRobotCells()  # Get the robot centers
        self.robotCenters = self.robotPositionClass.robotCenters # Get the robot centers
        for robot, pos in self.robotCenters.items():
            if str(robot) != str(self.robotId):
                self.colors[pos[0]][pos[1]] = "R" # Set the robot color

    def transformation(self):
        self.robotPositionClass.updateCurrentRobotCells()  # Get the robot centers
        self.robotCenters = self.robotPositionClass.robotCenters  # Get the robot centers
        for robot, pos in self.robotCenters.items():
            color = self.colors[pos[0]][pos[1]]
            if color == "G":
                self.currentRole = "PREY" if self.currentRole == "PREDATOR" else "PREDATOR"
                self.gameTime = self.gameTime - self.TIMEOUT

    def findEightNeighbors(self, current_cell):
        neighbours = [[current_cell[0],   current_cell[1]-1],
                      [current_cell[0]-1, current_cell[1]-1],
                      [current_cell[0]-1, current_cell[1]],
                      [current_cell[0]-1, current_cell[1]+1],
                      [current_cell[0],   current_cell[1]+1],
                      [current_cell[0]+1, current_cell[1]+1],
                      [current_cell[0]+1, current_cell[1]],
                      [current_cell[0]+1, current_cell[1]-1]]
        return neighbours

    def findFourNeighbors(self, current_cell):
        neighbours = [[current_cell[0],   current_cell[1]-1],
                      [current_cell[0]-1, current_cell[1]],
                      [current_cell[0],   current_cell[1]+1],
                      [current_cell[0]+1, current_cell[1]]]
        return neighbours

    def decisionMaking(self):
        if self.currentStep == None or self.currentStep == []:
            return
        go_to = []
        whiteCells = []
        blueCells = []
        greenCells = []
        yellowCells = []
        redCells = []
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
                else:
                    redCells.append([i, j])

        neighbours_update = []
        eight_neighbour = self.findEightNeighbors(self.currentStep)
        four_neighbour = self.findFourNeighbors(self.currentStep)

        if self.currentRole == "PREY":
            #########
            # THE COLOR POINTS MUST BE SPECIAL FOR PREY NOW
            #########
            for n in eight_neighbour:
                if n[0] >= 0 and n[0] <= 5:
                    if n[1] >= 0 and n[1] <= 6:
                        if n not in redCells:
                            if n not in self.robotCenters.values():
                                # available cells are included
                                neighbours_update.append(n)
                            else:
                                neighbours_update.append(
                                    [-2, -2])  # robot_cell
                        else:
                            neighbours_update.append([-1, -1])  # red cell
                    else:
                        neighbours_update.append([-1, -1])  # out of range
                else:
                    # out of range neighbour
                    neighbours_update.append([-1, -1])

            count = 0
            for neighbour in neighbours_update:  # avoid the risk of crashing a robot
                if count == 7 and neighbour == [-2, -2]:
                    neighbours_update[6] = [-1, -1]
                    neighbours_update[7] = [-1, -1]
                    neighbours_update[0] = [-1, -1]

                elif neighbour == [-2, -2]:
                    neighbours_update[count-1] = [-1, -1]
                    neighbours_update[count] = [-1, -1]
                    neighbours_update[count+1] = [-1, -1]
                count += 1
            # print("neighbours update")
            # print(neighbours_update)
            main_1, main_2, main_3, main_4 = [], [], [], []

            # decide on the most applicable options
            if self.points['B'] > 0 or self.points['Y'] > 0:
                if self.points['B'] > self.points['Y'] and self.points['B'] > 0:
                    main_1 = blueCells
                    if self.points['Y'] > 0:
                        main_2 = yellowCells
                        main_3 = whiteCells
                        main_4 = greenCells
                    else:
                        main_2 = whiteCells
                        main_3 = greenCells
                        main_4 = yellowCells
                else:
                    main_1 = yellowCells
                    if self.points['B'] > 0:
                        main_2 = blueCells
                        main_3 = whiteCells
                        main_4 = greenCells
                    else:
                        main_2 = whiteCells
                        main_3 = greenCells
                        main_4 = blueCells
            else:
                main_1 = whiteCells
                if self.points['B'] >= self.points['Y']:
                    main_2 = greenCells
                    main_3 = blueCells
                    main_4 = yellowCells
                else:
                    main_2 = greenCells
                    main_3 = yellowCells
                    main_4 = blueCells

            priority_1, priority_2, priority_3, priority_4 = [], [], [], []

            for n in neighbours_update:  # select our priorities from our neighbours
                if n in main_1:
                    priority_1.append(n)
                elif n in main_2:
                    priority_2.append(n)
                elif n in main_3:
                    priority_3.append(n)
                elif n in main_4:
                    priority_4.append(n)
                else:
                    pass

            if len(priority_1) != 0:
                for element in priority_1:
                    if element in four_neighbour:
                        go_to.append(element)
                        break

            if len(priority_2) != 0:
                for element in priority_2:
                    if element in four_neighbour:
                        go_to.append(element)
                        break

            if len(priority_3) != 0:
                for element in priority_3:
                    if element in four_neighbour:
                        go_to.append(element)
                        break

            if len(priority_4) != 0:
                for element in priority_4:
                    if element in four_neighbour:
                        go_to.append(element)
                        break

            if len(go_to) == 0:
                go_to.append(self.current_cell)

        ####### WE CAN RECONSIDER FOR SAME POINT CAPABILITY###
            self.next_step = go_to[-1]
            print(go_to[-1])
            return self.next_step
        #####################################################

        elif self.currentRole == "PREDATOR":
            #########
            # THE COLOR POINTS MUST BE SPECIAL FOR PREDATOR NOW
            #########
            for n in eight_neighbour:
                if n[0] >= 0 and n[0] <= 5:
                    if n[1] >= 0 and n[1] <= 6:
                        if n not in redCells:
                            # available cells are included
                            neighbours_update.append(n)
                        else:
                            neighbours_update.append([-1, -1])  # red cell
                    else:
                        neighbours_update.append([-1, -1])  # out of range
                else:
                    # out of range neighbour
                    neighbours_update.append([-1, -1])

            main_1, main_2, main_3, main_4 = [], [], [], []
            # decide on the most applicable options
            if self.points['B'] > 0 or self.points['Y'] > 0:
                if self.points['B'] > self.points['Y'] and self.points['B'] > 0:
                    main_1 = blueCells
                    if self.points[1] > 0:
                        main_2 = yellowCells
                        main_3 = whiteCells
                        main_4 = greenCells
                    else:
                        main_2 = whiteCells
                        main_3 = greenCells
                        main_4 = yellowCells
                else:
                    main_1 = yellowCells
                    if self.points['B'] > 0:
                        main_2 = blueCells
                        main_3 = whiteCells
                        main_4 = greenCells
                    else:
                        main_2 = whiteCells
                        main_3 = greenCells
                        main_4 = blueCells
            else:
                main_1 = whiteCells
                if self.points['B'] >= self.points['Y']:
                    main_2 = greenCells
                    main_3 = blueCells
                    main_4 = yellowCells
                else:
                    main_2 = greenCells
                    main_3 = yellowCells
                    main_4 = blueCells

            priority_A, priority_1, priority_2, priority_3, priority_4 = [], [], [], [], []

            for n in neighbours_update:  # select our priorities from our neighbours
                if n in self.robotCenters:
                    priority_A.append(n)
                if n in main_1:
                    priority_1.append(n)
                elif n in main_2:
                    priority_2.append(n)
                elif n in main_3:
                    priority_3.append(n)
                elif n in main_4:
                    priority_4.append(n)
                else:
                    pass

            if len(priority_A) != 0:
                for element in priority_A:
                    if element in four_neighbour:
                        go_to.append(element)
                        break

            elif len(priority_1) != 0:
                for element in priority_1:
                    if element in four_neighbour:
                        go_to.append(element)
                        break

            elif len(priority_2) != 0:
                for element in priority_2:
                    if element in four_neighbour:
                        go_to.append(element)
                        break

            elif len(priority_3) != 0:
                for element in priority_3:
                    if element in four_neighbour:
                        go_to.append(element)
                        break

            elif len(priority_4) != 0:
                for element in priority_4:
                    if element in four_neighbour:
                        go_to.append(element)
                        break

            else:
                go_to.append(self.current_cell)

            print(go_to[-1])
            self.next_step = go_to[-1]
            return self.next_step
        
    def processDecision(self):
        self.get_params()
        self.updateInfo()
        self.transformation()
        rTime = (self.gameTime - self.gamemqtt.tick) # TODO
        rTime = rTime if rTime > 0 else 0
        self.currentStep = self.robotPositionClass.updateCurrentCell()
        if self.status == "START":
            if self.started == False:
                self.started = True
                self.mqtt.publishToTopic("00-10")
                print("Game started!")
            choose = self.decisionMaking()
            if self.next_step != None and self.next_step != [] and self.next_step != self.currentStep:
                color = self.colors[self.next_step[0]][self.next_step[1]]
                speedLimit = self.speedLimits[color]
                speed = self.speedValues[speedLimit]*self.speedValues["speedMultiplier"]
                self.robotPositionClass.move(choose, self.currentStep) # IMPORTANT
                self.mqtt.publishToTopic(f"01:speed:{speedLimit}:string")
                self.currentStep = self.robotPositionClass.updateCurrentCell()
                self.gamemqtt.robotSay(self.currentStep, self.next_step, rTime, speed)

        elif self.status == "STOP":
            if self.started == True:
                self.started = False
                self.mqtt.publishToTopic("00-00")
                print("Game stopped!")

        elif self.status == "PAUSE":
            if self.started == True:
                self.started = False
                self.mqtt.publishToTopic("00-00")
                print("Game paused!")