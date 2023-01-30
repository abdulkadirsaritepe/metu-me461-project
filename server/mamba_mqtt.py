import paho.mqtt.client as mqtt 
import time, sys, threading, ujson, os, random
from datetime import datetime

# MQTT Broker for establishing connection and publishing data to the cloud and subscribing to the cloud
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
        self.mqttConnected = 0 # MQTT Connection Status
        self.get_params() # Get the parameters
        k = 0 # Counter for the connection attempts
        while not self.mqttConnected: 
            try:
                if not self.mqttConnected:
                    self.client = self.mqtt_connect() # Connect to the MQTT Broker
                    print("Connected to %s MQTT Broker" % (self.mqtt_server))
                    self.client.loop_start() # Start the MQTT Client
                else:
                    self.client = None
                    raise Exception
            except KeyboardInterrupt:
                print("Keyboard Interrupt")
                break
            except:
                # If the connection is not established, try again after 5 seconds
                print("Failed to connect to the Pico W MQTT Broker. Reconnecting...")
                time.sleep(5)
                k+=1 
            if k == 5:
                # If the connection is not established after 5 attempts, exit the program
                print("Failed to connect to the Pico W MQTT Broker. Please check your internet connection.")
                return
        # If the connection is established, initialize the MQTT Client
        try:
            self.client.subscribe(self.picotopic, qos=1) # Subscribe to the motor/status topic
            print("Subscribed to %s" % (self.picotopic))
        except:
            print("Failed to subscribe to %s" % (self.picotopic))

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
        client = mqtt.Client(self.client_id)
        client.username_pw_set(self.username, self.password)
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.connect(self.mqtt_server, self.port)
        return client

    def on_connect(self, client, userdata, flags, rc):
        self.mqttConnected = 1 # Set the MQTT Connection Status to 1
    
    def on_message(self, client, userdata, msg):
        # global messageReceived, messageContent # Make the messageReceived and messageContent variables global
        # messageReceived = True # Set the messageReceived variable to True
        messageContent = msg.payload.decode("utf-8") # Set the messageContent variable to the message payload
    
    def on_publish(self, client, userdata, mid):
        pass # print(f"Message Published to: {client}") # Print the topic that the message was published to

    def publishToTopic(self, msg):
        # special protocol for publishing to the motor topic
        if self.client == None: # If the MQTT Client is not initialized or the topic is not motor, return
            return
        
        msg = bytes(msg, 'utf-8') # Convert the message to bytes
        (result, mid) = self.client.publish(self.servertopic, msg, qos=1) # Publish the message to the topic
        if result == 0: # If the message is published successfully, print the topic that the message was published to
            pass
            # print("Message Published to: %s" % (self.servertopic)) # Print the topic that the message was published to
        else: # If the message is not published successfully, print the error code
            print("Error: Message Not Published to: %s/%s" % (result, self.servertopic))

    def mqtt_disconnect(self):
        print("Disconnecting from the MQTT Broker")
        self.mqttConnected = 0 # Set the MQTT Connection Status to 0
        self.client.loop_stop() # Stop the MQTT Client
        self.client.disconnect() # Disconnect from the MQTT Broker
