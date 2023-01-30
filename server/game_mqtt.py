
import paho.mqtt.client as mqtt 
import time, ujson, os

# MQTT Broker for establishing connection and publishing data to the cloud and subscribing to the cloud
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
        self.get_params() # Get the parameters
        k = 0 # Counter for the connection attempts
        while self.client == None: 
            try:
                self.mqtt_connect() # Connect to the MQTT Broker
                print("Connection Established to the Mechatronics Laboratory MQTT Broker")
            except KeyboardInterrupt:
                print("Keyboard Interrupt")
                break
            except:
                # If the connection is not established, try again after 5 seconds
                print("Failed to connect to the Mechatronics Laboratory MQTT Broker. Reconnecting...")
                time.sleep(5)
                k+=1 
            if k == 5:
                # If the connection is not established after 5 attempts, exit the program
                print("Failed to connect to the Mechatronics Laboratory MQTT Broker. Please check your internet connection.")
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
            topicToSubscribe = []
            for topic in self.topics:
                topicToSubscribe.append((topic, 0))
                client.subscribe(topic) # Subscribe to the topics
            print(topicToSubscribe)
        except:
            print("Failed to subscribe to the topics")

    def on_log(self, client, userdata, level, buf):
        pass # print("log: ", buf)

    def on_message(self, client, userdata, msg, details=False):
        try:
            msgTopic = msg.topic
            msgContent = msg.payload
            if msgTopic == "arena":
                with open(f'{self.dir_path}/arena_view.png', 'wb') as f:
                    f.write(msgContent)
                self.arenaImageTaken = True
            elif msgTopic == "config": # TODO
                msgContent = eval(msgContent)
                msgContent = msgContent[self.currentRole]
                game_info = ujson.loads(open(self.game_info_path).read())
                for k, v in msgContent.items():
                    if str(k).strip()[1] == "P":
                        (game_info["points"]).update({str(k).strip()[0]:v}) # TODO
                    elif str(k).strip()[1] == "S":
                        (game_info["speedLimits"]).update({str(k).strip()[0]:v}) # TODO
                game_info = ujson.dumps(game_info)
                with open(self.game_info_path, 'w') as f:
                    f.write(game_info)
                timeout = float(msgContent["TIMEOUT"]) # TODO
                updated = self.updateGameInfo("timeout", timeout)
            elif msgTopic == "tick":
                msgContent = int(msgContent)
                updated = self.updateGameInfo("tick", msgContent)
            elif msgTopic == "start":
                msgContent = msgContent.decode("utf-8")
                if msgContent in ["GO", "STOP", "PAUSE"]:
                    updated = self.updateGameInfo("start", msgContent)
            elif msgTopic == "stats":
                msgContent = eval(msgContent)
                msgContent2 = {}
                for item in msgContent:
                    msgContent2.update({int(item['ID']): list(item['POS'])})
                updated = self.updateGameInfo("stats", msgContent2)
            else:
                print("Unknown topic: ", msgTopic)
            if updated:
                print("Updated game info")
            else:
                print("Failed to update game info")
        except Exception as e:
            print(e)

    def on_publish(self, client, userdata, mid):
        pass # print(f"Message Published to: {client}") # Print the topic that the message was published to

    def robotSay(self):
        # special protocol for publishing to the robotSay topic
        if self.client == None: # If the MQTT Client is not initialized or the topic is not motor, return
            return
        game_info = ujson.loads(open(self.game_info_path).read())
        msg = f"[{game_info['ID']}, '{game_info['role']}', '{game_info['speed']}', {game_info['totalpoints']}, {tuple(game_info['currentcell'])}, {tuple(game_info['destinationcell'])}, {game_info['remainingTime']}]"
        msg = bytes(msg, 'utf-8') # Convert the message to bytes
        (result, mid) = self.client.publish(self.servertopic, msg, qos=1) # Publish the message to the topic
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

    def mqtt_disconnect(self):
        print("Disconnecting from the MQTT Broker")
        self.client.disconnect() # Disconnect from the MQTT Broker
