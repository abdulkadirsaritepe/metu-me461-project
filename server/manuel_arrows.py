
import pygame, os, sys, time, ujson
from robot_position import RobotPosition
from arena import Arena

class ManuelArrows:
    def __init__(self, mqtt, gamemqtt):
        self.dir_path = os.path.dirname(os.path.realpath(__file__)) # Get the current directory
        self.param_path = f'{self.dir_path}/parameters.ujson' # Path to the parameters file
        self.game_info_path = f'{self.dir_path}/game_info.ujson' # Path to the game info file
        self.file_path = os.path.join(self.dir_path, "positions.ujson") # Path to the positions file
        self.img_path = os.path.join(self.dir_path, "arena_view.png") # Path to the arena image
        self.mqtt = mqtt
        self.gamemqtt = gamemqtt

        self.turnDelay = 283 # Delay in microseconds for turning
        self.moveDelay = 550 # Delay in microseconds for moving

        self.currentcell = [] # Current cell of the robot
        self.currentangle = 0 # Current angle of the robot
        self.nextcell = [] # Next cell of the robot
        self.robotPosition = []
        self.speedLimits = None
        self.started = False
        self.status = None
        self.robotId = None
        self.positions = None
        self.averageCs = None
        self.averageRs = None
        self.gameTime = 0
        # Initialize the pygame module
        pygame.init()
        self.screen = pygame.display.set_mode((500, 450))
        self.screen.fill((255, 255, 255))
        pygame.display.set_caption("Manuel Arrows")
        pygame.display.update()

        self.angulardirection = 0 # Angular direction of the robot
        self.lineardirection = 0 # Linear direction of the robot
        self.speedName = None 
        self.speed = 0 # Speed of the robot
        while not self.gamemqtt.arenaImageTaken:
            self.get_params()
            time.sleep(0.1)
        print("Arena image taken")
        # while self.gamemqtt.tick >= 0:
        #     while self.gamemqtt.tick == 0:
        #         self.gameTime = int(self.gamemqtt.tick )
        #     time.sleep(0.1)
        print("game started")
        self.arena = Arena(self.img_path)
        self.colors = self.arena.colors
        self.get_params()
        try:
            mqtt.publishToTopic("00-10")
            mqtt.publishToTopic(f"01:speed:{self.speedName}:string")
            self.robotControl = RobotPosition(mqtt, gamemqtt, self.colors)
            self.loop_control()
        except KeyboardInterrupt:
            mqtt.publishToTopic("00-00")
            print("Exiting...")
            pygame.quit()
            exit()

    def get_params(self):
        try:
            game_info = ujson.loads(open(self.game_info_path).read()) # Read the parameters file
            self.currentRole = game_info['role'] # Get the current role
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
            self.status = self.gamemqtt.status # ! game_info['status'] # Get the status
            self.TIMEOUT = self.gamemqtt.TIMEOUT
            try:
                with open(self.file_path, "r") as file:
                    positions = ujson.load(file)
                self.positions = positions['gridCenters']
                self.gridSize = positions['gridSize']
                self.averageRs = positions['averageRs']
                self.averageCs = positions['averageCs']
            except:
                pass
            # try:
            #     self.robotPosition = (game_info['stats'])[str(self.robotId)] # Get the stats
            # except:
            #     print("could not take position")
        except:
            print("ERROR")

    def findFourNeighbors(self, current_cell):
        if current_cell == []:
            return
        neighbours = []
        if current_cell[0] - 1 >= 0:
            neighbours.append([current_cell[0] - 1, current_cell[1]])
        if current_cell[0] + 1 < self.gridSize[0]:
            neighbours.append([current_cell[0] + 1, current_cell[1]])
        if current_cell[1] - 1 >= 0:
            neighbours.append([current_cell[0], current_cell[1] - 1])
        if current_cell[1] + 1 < self.gridSize[1]:
            neighbours.append([current_cell[0], current_cell[1] + 1])
        return neighbours

    def check_next_cell(self, cell):
        if cell[0] < 0 or cell[0] >= self.gridSize[0] or cell[1] < 0 or cell[1] >= self.gridSize[1]:
            return False
        elif self.colors[cell[0]][cell[1]] == "R":
            return False
        return True

    def decisionMaking(self):
        currentcell = self.robotControl.updateCurrentCell()
        next_step = currentcell
        neighbours = self.findFourNeighbors(currentcell)
        for neighbour in neighbours:
            if not self.check_next_cell(neighbour):
                neighbours.remove(neighbour)
        for i in pygame.event.get():
            if i.type == pygame.QUIT:
                self.mqtt.publishToTopic("00-00")
                pygame.quit()
                exit()
            if i.type == pygame.KEYDOWN:
                if i.key == pygame.K_LEFT:
                    next_step = [currentcell[0], currentcell[1] -1]
                if i.key == pygame.K_RIGHT:
                    next_step = [currentcell[0], currentcell[1] + 1]
                if i.key == pygame.K_UP:
                    next_step = [currentcell[0] - 1, currentcell[1]]
                if i.key == pygame.K_DOWN:
                    next_step = [currentcell[0] + 1, currentcell[1]]
        if next_step in neighbours:
            return next_step
        else:
            return currentcell

    def loop_control(self):
        while True:
            self.get_params()
            if self.status == "START":
                if self.started == False:
                    self.started = True
                    self.mqtt.publishToTopic("00-10")
                    print("Game started!")
                try:
                    currentcell = self.robotControl.updateCurrentCell()
                    next_step = self.decisionMaking()
                    rTime = self.gameTime - self.gamemqtt.tick # TODO
                    rTime = rTime if rTime > 0 else 0
                    if next_step != currentcell:
                        self.gamemqtt.robotSay(currentcell, next_step, rTime, self.speed)
                        self.robotControl.move(next_step, currentcell)
                except Exception as e:
                    print(f"ERROR505: {e}")
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

            time.sleep(0.1)
            pygame.display.update()
