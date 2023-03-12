
import pygame, os, sys, time, ujson
from robot_position import RobotPosition
from arena import Arena

class ManuelArrowsTest:
    def __init__(self, mqtt):
        self.dir_path = os.path.dirname(os.path.realpath(__file__)) # Get the current directory
        self.param_path = f'{self.dir_path}/parameters.ujson' # Path to the parameters file
        self.game_info_path = f'{self.dir_path}/game_info.ujson' # Path to the game info file
        self.mqtt = mqtt

        self.turnDelay = 283 # Delay in microseconds for turning
        self.moveDelay = 550 # Delay in microseconds for moving

        self.currentcell = [] # Current cell of the robot
        self.currentangle = 0 # Current angle of the robot
        self.nextcell = [] # Next cell of the robot
        self.status = None
        self.robotId = None
        # Initialize the pygame module
        pygame.init()
        self.screen = pygame.display.set_mode((500, 450))
        self.screen.fill((255, 255, 255))
        pygame.display.set_caption("Manuel Arrows")

        self.angulardirection = 0 # Angular direction of the robot
        self.lineardirection = 0 # Linear direction of the robot
        self.speedName = None 
        self.speed = 25000 # Speed of the robot
        self.leftSpeed = 25000
        self.rightSpeed = 25000
        print(f"Speed: {self.speed}")
        self.get_params()
        try:
            mqtt.publishToTopic("00-10")
            mqtt.publishToTopic("10-predator1:1")
            mqtt.publishToTopic("10-predator2:1")
            mqtt.publishToTopic(f"01:speed:{self.speedName}:string")
            self.robotControl = RobotPosition(picomqtt=mqtt)
            self.loop_control()
        except KeyboardInterrupt:
            mqtt.publishToTopic("00-00")
            print("Exiting...")
            pygame.quit()
            exit()

    def get_params(self):
        try:
            game_info = ujson.loads(open(self.game_info_path).read()) # Read the parameters file
            param_info = ujson.loads(open(self.param_path).read()) # Read the parameters file
            self.currentRole = game_info['role'] # Get the current role
            if self.currentRole == "PREY":
                self.picomqtt.publishToTopic("10-prey1:1")
                self.picomqtt.publishToTopic("10-prey2:1")
                self.picomqtt.publishToTopic("10-predator1:0")
                self.picomqtt.publishToTopic("10-predator2:0")
            elif self.currentRole == "PREDATOR":
                self.picomqtt.publishToTopic("10-predator1:1")
                self.picomqtt.publishToTopic("10-predator2:1")
                self.picomqtt.publishToTopic("10-prey1:0")
                self.picomqtt.publishToTopic("10-prey2:0")
            else:
                self.picomqtt.publishToTopic("10-prey1:0")
                self.picomqtt.publishToTopic("10-prey2:0")
                self.picomqtt.publishToTopic("10-predator1:0")
                self.picomqtt.publishToTopic("10-predator2:0")
            self.robotId = game_info['ID'] # Get the robot ID
            self.status = game_info['status'] # Get the status
            turnDelay = param_info["turnDelay"]
            moveDelay = param_info["moveDelay"]
            if turnDelay != self.turnDelay:
                self.turnDelay = turnDelay
                print(f"Turn Delay: {self.turnDelay}")
            if moveDelay != self.moveDelay:
                self.moveDelay = moveDelay
                print(f"Turn Delay: {self.turnDelay}")
            try:
                self.robotPosition = (game_info['stats'])[str(self.robotId)] # Get the stats
                if self.printed == False:
                    print("the stats of the robot are: ", self.stats)
                    self.printed = True
            except:
                if self.printed == False:
                    print("The robot is not on the arena!")
                    self.printed = True
        except:
            pass

    def loop_control(self):
        while True:
            move = False
            direction = 0
            self.get_params()
            for i in pygame.event.get():
                if i.type == pygame.QUIT:
                    self.mqtt.publishToTopic("00-00")
                    pygame.quit()
                    exit()
                if i.type == pygame.KEYDOWN:
                    if i.key == pygame.K_LEFT:
                        self.currentangle = (self.currentangle+90) % 360
                        print(self.currentangle)
                        self.mqtt.publishToTopic(f"22-0:{self.leftSpeed}:1:{self.rightSpeed}:{self.turnDelay}")
                        # self.turn(-1)
                    if i.key == pygame.K_RIGHT:
                        self.currentangle = (self.currentangle-90) % 360
                        self.mqtt.publishToTopic(f"22-1:{self.leftSpeed}:0:{self.rightSpeed}:{self.turnDelay}")
                        print(self.currentangle)
                        # self.turn(1)
                    if i.key == pygame.K_UP:
                        move = True
                        direction = 1
                    if i.key == pygame.K_DOWN:
                        move = True
                        direction = -1
            if move == True:
                direction = 0 if direction == -1 else 1
                self.mqtt.publishToTopic(f"22-{direction}:{self.leftSpeed}:{direction}:{self.rightSpeed}:{self.moveDelay}")

            time.sleep(0.1)
            pygame.display.update()
