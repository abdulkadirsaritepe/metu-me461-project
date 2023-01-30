
import pygame, os, sys, time, ujson

class ManuelArrows:
    def __init__(self, mqtt):
        self.dir_path = os.path.dirname(os.path.realpath(__file__)) # Get the current directory
        self.param_path = f'{self.dir_path}/parameters.ujson' # Path to the parameters file
        self.info = ujson.loads(open(self.param_path).read()) # Read the parameters file
        self.mqtt = mqtt
        # Initialize the pygame module
        pygame.init()
        self.screen = pygame.display.set_mode((500, 450))
        self.screen.fill((255, 255, 255))
        pygame.display.set_caption("Manuel Arrows")

        self.angulardirection = 0 # Angular direction of the robot
        self.lineardirection = 0 # Linear direction of the robot
        self.speedName = (self.info['speedInfo'])['speed'] # Name of the speed
        self.speed = ((self.info['speedInfo'])[((self.info['speedInfo'])['speed'])])*(self.info['speedInfo'])['speedMultiplier'] # Speed of the robot
        print(f"Speed: {self.speed}")
        self.previousMsg = "" # Previous message sent to the robot
        try:
            mqtt.publishToTopic("00-10")
            mqtt.publishToTopic("10-predator1:1")
            mqtt.publishToTopic("10-predator2:1")
            mqtt.publishToTopic(f"01:speed:{self.speedName}:string")
            self.loop_control()
        except KeyboardInterrupt:
            mqtt.publishToTopic("00-00")
            print("Exiting...")
            pygame.quit()
            exit()

    def loop_control(self):
        while True:
            for i in pygame.event.get():
                if i.type == pygame.QUIT:
                    self.mqtt.publishToTopic("00-00")
                    pygame.quit()
                    exit()
                if i.type == pygame.KEYDOWN:
                    if i.key == pygame.K_LEFT:
                        self.angulardirection += -1
                    if i.key == pygame.K_RIGHT:
                        self.angulardirection += 1
                    if i.key == pygame.K_UP:
                        self.lineardirection += 1
                    if i.key == pygame.K_DOWN:
                        self.lineardirection += -1
                elif i.type == pygame.KEYUP:
                    if i.key == pygame.K_LEFT:
                        self.angulardirection += 1
                    if i.key == pygame.K_RIGHT:
                        self.angulardirection += -1
                    if i.key == pygame.K_UP:
                        self.lineardirection += -1
                    if i.key == pygame.K_DOWN:
                        self.lineardirection += 1
            angulardirectionMsg = 0 if self.angulardirection == -1 else 1 if self.angulardirection == 1 else "none"
            lineardirectionMsg = 0 if self.lineardirection == -1 else 1 if self.lineardirection == 1 else "none"

            msg = f'11-{angulardirectionMsg}:{lineardirectionMsg}:{self.speed}'
            
            if self.previousMsg != msg:
                self.mqtt.publishToTopic(msg)
                self.previousMsg = msg
            
            time.sleep(0.1)
            pygame.display.update()
