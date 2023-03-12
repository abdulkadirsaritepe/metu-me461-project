
import paho.mqtt.client as mqtt 
import time, ujson, os

# info MQTT Broker for establishing connection and publishing data to the cloud and subscribing to the cloud
# info GameBoardMQTT class is used to establish connection to the MQTT Broker and publish and subscribe to the topics
# info robotSay method is used to send messages to the robot
# info arenaImageTaken is used to check if the arena image is taken or not

class GameBoardMQTT: 
    def __init__(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__)) # Get the current directory
        self.param_path = f'{self.dir_path}/parameters.ujson' # Path to the parameters file
        self.game_info_path = f'{self.dir_path}/game_info.ujson' # Path to the game info file
        self.mqtt_server = None # IP
        self.client_id = None # MQTT Client ID
        self.username = None # MQTT Username
        self.password = None # MQTT Password
        self.port = None # MQTT Port
        self.servertopic = None # MQTT Server Topic
        self.picotopic = None # MQTT Pico Topic
        self.isConnected = False # MQTT Connection Status 
        self.client = None 
        self.currentRole = None # Current Role of the robot
        self.robotId = None # Robot ID
        self.arenaImageTaken = False # Arena Image Taken Status
        self.tick = None
        self.stats = None
        self.totalpoints = 0
        self.TIMEOUT = 0
        self.status = "STOP"
        self.get_params() # Get the parameters
        k = 0 # Counter for the connection attempts
        while self.client == None: 
            try:
                self.mqtt_connect() # Connect to the MQTT Broker
                print("Connection Established to the Mechatronics Laboratory MQTT Broker")
                self.isConnected = True
            except KeyboardInterrupt:
                print("Keyboard Interrupt")
                break
            except:
                # If the connection is not established, try again after 5 seconds
                print("Failed to connect to the Mechatronics Laboratory MQTT Broker. Reconnecting...")
                time.sleep(3)
                k+=1 
                self.isConnected = False
            if k == 3:
                # If the connection is not established after 5 attempts, exit the program
                print("Failed to connect to the Mechatronics Laboratory MQTT Broker. Please check your internet connection.")
                self.isConnected = False
                return

    def get_params(self): # Get the parameters
        info = ujson.loads(open(self.param_path).read()) # Read the parameters file
        self.mqtt_server = info['servermqttInfo']['host'] # Get the MQTT Server
        self.username = info['servermqttInfo']['username'] # Get the username
        self.password = info['servermqttInfo']['password'] # Get the password
        self.client_id = info['servermqttInfo']['client_id'] # Get the client ID
        self.topics = info['servermqttInfo']['topics'] # Get the topic
        game_info = ujson.loads(open(self.game_info_path).read()) # Read the parameters file
        self.currentRole = game_info['role'] # Get the current role
        self.robotId = game_info['ID'] # Get the robot ID

    def mqtt_connect(self):
        client = mqtt.Client(f"{self.client_id}") #create new instance
        client.on_log = self.on_log
        client.on_message= self.on_message        #attach function to callback
        client.connect(self.mqtt_server)  # connect to broker
        client.loop_start()  # start the loop
        print("Connected to %s MQTT Broker" % (self.mqtt_server)) # Print result of connection attempt
        self.client = client # Set the MQTT Client

        try:
            client.subscribe("#") # Subscribe to all the topics
        except:
            print("Failed to subscribe to the topics")

    def on_log(self, client, userdata, level, buf):
        pass # print("log: ", buf)

    def on_message(self, client, userdata, msg, details=False):
        try:
            msgTopic = msg.topic
            msgContent = msg.payload
            if msgTopic == "arena":
                # ? Photo of the Arena captured from the overhead camera
                try:
                    with open(f'{self.dir_path}/arena_view.png', 'wb') as f:
                        f.write(msgContent)
                    self.arenaImageTaken = True
                except:
                    self.arenaImageTaken = False
                    print("Failed to save the arena image")
            elif msgTopic == "config": # TODO
                # ? {“PREDATOR”:[YV, BV, YS, BS, [ID1, ID2,...]],“PREY”:[YV, BV, YS, BS, [ID1,ID2,...]], “TIMEOUT”:15 }
                try:
                    msgContent = eval(msgContent)
                    preyInfo = msgContent["PREY"]
                    predatorInfo = msgContent["PREDATOR"]
                    if self.currentRole == "PREY":
                        info = preyInfo
                    elif self.currentRole == "PREDATOR":
                        info = predatorInfo
                    game_info = ujson.loads(open(self.game_info_path).read())
                    game_info[self.currentRole]["points"]["Y"] = info[0]
                    game_info[self.currentRole]["points"]["B"] = info[1]
                    game_info[self.currentRole]["speedLimits"]["Y"] = info[2]
                    game_info[self.currentRole]["speedLimits"]["B"] = info[3]
                    game_info["TIMEOUT"] = int(msgContent["TIMEOUT"])
                    self.TIMEOUT = int(msgContent['TIMEOUT'])

                    game_info = ujson.dumps(game_info)
                    with open(self.game_info_path, 'w') as f:
                        f.write(game_info)
                except:
                    print("Failed to get the config")
            elif msgTopic == "tick":
                # ? Number of seconds remaining for the game to start, or to end.
                try:
                    msgContent = int(msgContent)
                    self.tick = msgContent
                except:
                    print("Failed to get the tick")
            elif msgTopic == "start":
                # ? [“GO”, “PAUSE” or “STOP”] Either of the 3 words will be published.
                try:
                    msgContent = msgContent.decode("utf-8")
                    if msgContent in ["START", "STOP", "PAUSE"]:
                        self.status = msgContent
                        # self.updateGameInfo("status", msgContent)
                    else:
                        print("Unknown start command")
                except Exception as e:
                    print("Failed to get the start: ", e)
            elif msgTopic == "stats":
                # ? [{“ID”:Z_1, “POS”:[[X1_1,Y1_1],[X1_2,Y1_2],[X1_3,Y1_3],[X1_4,Y1_4]]} , … ,{“ID”:Z_i, “POS”:[[Xi_1,Yi_1],[Xi_2,Yi_2],[Xi_3,Yi_3],[Xi_4,Yi_4]]}, … , {...}, {...}]
                try:
                    msgContent = eval(msgContent)
                    msgContent2 = {}
                    for item in msgContent:
                        msgContent2.update({int(item['ID']): list(item['POS'])})
                    self.stats = msgContent2
                    # self.updateGameInfo("stats", msgContent2)
                except Exception as e:
                    print("Failed to get the stats ", e)
            else:
                pass
                # print("Unknown topic: ", msgTopic)

        except Exception as e:
            print(e)

    def on_publish(self, client, userdata, mid):
        pass # print(f"Message Published to: {client}") # Print the topic that the message was published to

    def robotSay(self, currentcell, targetcell, rTime, speed):
        # special protocol for publishing to the robotSay topic
        # ? [ID, current_role, speed, total_points, current_cell, remaining time to enable transformer cell]
        if self.client == None: # If the MQTT Client is not initialized or the topic is not motor, return
            return
        game_info = ujson.loads(open(self.game_info_path).read())
        msg = f"[11, '{game_info['role']}', '{speed}', {self.totalpoints}, {currentcell}, {targetcell}, {rTime}]"
        msg = bytes(msg, 'utf-8') # Convert the message to bytes
        (result, mid) = self.client.publish("robotsay", msg, qos=1) # Publish the message to the topic
        if result == 0: # If the message is published successfully, print the topic that the message was published to
            pass
            # print("Message Published to: %s" % (self.servertopic)) # Print the topic that the message was published to
        else: # If the message is not published successfully, print the error code
            print("Error: %s Message Not Published to: %s/%s" % (result, self.servertopic))

    def updateGameInfo(self, keyword=None, value=None):
        if keyword == None or value == None:
            return False
        else:
            game_info = ujson.loads(open(self.game_info_path).read())
            game_info[keyword] = value
            # game_info["lastUpdate"] = game_info["lastUpdate"] + 1
            game_info = ujson.dumps(game_info)
            with open(self.game_info_path, 'w') as f:
                f.write(game_info)
            return True

    def transformationDuty(self): # TODO - When transformation is possible, perform the function.
        pass

    def mqtt_disconnect(self):
        print("Disconnecting from the MQTT Broker")
        self.client.disconnect() # Disconnect from the MQTT Broker