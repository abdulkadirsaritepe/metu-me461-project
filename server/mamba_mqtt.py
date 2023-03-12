import paho.mqtt.client as mqtt 
import time, sys, threading, ujson, os, random
from datetime import datetime

# info MQTT Broker for establishing connection and publishing data to the cloud and subscribing to the cloud
# info PicoMQTT class is used to establish connection to the MQTT Broker and publish and subscribe to the topics
# info The class is used for the communication between the Pico and the server
# info publishToTopic method is used to publish messages to the server topic
# info subscribeToTopic method is used to subscribe to the pico topic

class PicoMQTT: 
    def __init__(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__)) # Get the current directory
        self.param_path = f'{self.dir_path}/parameters.ujson' # Path to the parameters file
        self.mqtt_server = None # HiveMQ Cloud Broker
        self.client_id = None # MQTT Client ID
        self.username = None # MQTT Username
        self.password = None # MQTT Password
        self.port = None # MQTT Port
        self.servertopic = None # MQTT Server Topic
        self.picotopic = None # MQTT Pico Topic
        self.isConnected = False # MQTT Connection Status 
        self.client = None 
        self.get_params() # Get the parameters
        self.mqtt_connect() # Connect to the MQTT Broker

    def get_params(self): # Get the parameters
        info = ujson.loads(open(self.param_path).read()) # Read the parameters file
        self.mqtt_server = info['mqttInfo']['host'] # Get the MQTT Server
        self.port = info['mqttInfo']['port'] # Get the port
        self.username = info['mqttInfo']['username'] # Get the username
        self.password = info['mqttInfo']['password'] # Get the password
        self.client_id = f"{info['mqttInfo']['client_id']}{random.randint(0, 1000)}" # Get the client ID
        self.servertopic = info['mqttInfo']['servertopic'] # Get the topic
        self.picotopic = info['mqttInfo']['picotopic'] # Get the Pico topic

    def mqtt_connect(self):
        client = mqtt.Client(f"{self.client_id}") #create new instance
        client.username_pw_set(self.username, self.password) #set username and password
        client.on_log = self.on_log
        client.on_connect = self.on_connect #attach function to callback
        client.on_message= self.on_message        #attach function to callback
        client.connect(self.mqtt_server)  # connect to broker
        client.loop_start()  # start the loop
        self.client = client # Set the MQTT Client
        if self.client != None:
            self.isConnected = True

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0: # If the connection is successful, print the MQTT Server that the client is connected to
            print("Connected to %s MQTT Broker" % (self.mqtt_server))
            try:
                self.client.subscribe(self.picotopic)  # Subscribe to the topics
            except:
                print("Failed to subscribe to the topics")
        else:
            print("Connection failed with result code %s" % (rc)) # If the connection is not successful, print the error code

    def on_log(self, client, userdata, level, buf):
        pass # print("log: ", buf)
    
    def on_message(self, client, userdata, msg):
        messageContent = msg.payload.decode("utf-8") # Set the messageContent variable to the message payload
        print(messageContent)
    
    def on_publish(self, client, userdata, mid):
        pass # print(f"Message Published to: {client}") # Print the topic that the message was published to

    def publishToTopic(self, msg):
        # special protocol for publishing to the motor topic
        if self.client == None: # If the MQTT Client is not initialized or the topic is not motor, return
            return
        
        msg = bytes(msg, 'utf-8') # Convert the message to bytes
        (result, mid) = self.client.publish("server", msg, qos=1) # Publish the message to the topic
        # if result == 0: # If the message is published successfully, print the topic that the message was published to
        #     pass
        #     # print("Message Published to: %s" % (self.servertopic)) # Print the topic that the message was published to
        # else: # If the message is not published successfully, print the error code
        #     print("Error: Message Not Published to: %s/%s" % (result, self.servertopic))

    def mqtt_disconnect(self):
        print("Disconnecting from the MQTT Broker")
        self.mqttConnected = 0 # Set the MQTT Connection Status to 0
        self.client.loop_stop() # Stop the MQTT Client
        self.client.disconnect() # Disconnect from the MQTT Broker
