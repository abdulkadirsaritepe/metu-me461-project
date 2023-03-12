
from umqtt.simple import MQTTClient
import network
from machine import Pin, PWM, ADC
import utime, _thread ,math, sys, os, ujson
from utime import sleep
from drive import Vehicle
from status_update import StatusUpdate

class PicoMQTT:
    def __init__(self):
        self.paused = 0
        self.stopped = 0 
        self.speed = None
        self.param_path = 'pico_params.ujson' # Path to the parameters file
        self.ssid_path = 'ssid_params.ujson' # Path to the SSID parameters file
        self.ssids = {} # SSIDs
        self.mqtt_server = None # MQTT Server
        self.port = None # Port
        self.client_id = None # Client ID
        self.username = None # Username
        self.password = None # Password
        self.topic = None # Topic
        self.picotopic = None # Pico Topic
        self.client = None # MQTT Client
        self.statusLeds = StatusUpdate()
        self.statusLeds.updateLeds('bootLed', 1)
        self.get_params() # Get the parameters
        self.vehicle = Vehicle() # Create a vehicle object
        for ssid, password in self.ssids.items():
            status = self.connect_wifi(ssid, password) # Connect to the WiFi
            if status:
                self.statusLeds.updateLeds('wifiLed', 1) # Turn on the WiFi LED
                break
            else:
                self.statusLeds.updateLeds('wifiLed', 0)
        if status:
            self.connect_mqtt() # Connect to the MQTT Server
            try: # Try to create a thread
                self.client.subscribe(self.topic, qos=0) # Subscribe to the topic with QoS 1
            except:
                pass
            while self.client:
                try:
                    self.client.wait_msg() # Wait for a message
                except KeyboardInterrupt:
                    print("Exiting...") # Exit
                    self.statusLeds.updateAllLeds(0) # Turn off the LEDs
                    self.client.disconnect() # Disconnect from the MQTT Server
                    sys.exit() # Exit
                except:
                    print("Could not wait for message") # Could not wait for message: 
                utime.sleep_ms(5) # Sleep for 5 ms
        else:
            print('No wifi connection') # No WiFi connection
    
    def get_params(self): # Get the parameters
        info = ujson.loads(open(self.param_path).read()) # Read the parameters file
        ssids = ujson.loads(open(self.ssid_path).read()) # Read the SSIDs file
        self.ssids = ssids # Get the SSIDs
        self.mqtt_server = info['mqttInfo']['host'] # Get the MQTT Server
        self.port = info['mqttInfo']['port'] # Get the port
        self.username = info['mqttInfo']['username'] # Get the username
        self.password = info['mqttInfo']['password'] # Get the password
        self.client_id = info['mqttInfo']['client_id'] # Get the client ID
        self.topic = info['mqttInfo']['servertopic'] # Get the topic
        self.picotopic = info['mqttInfo']['picotopic'] # Get the Pico topic
        self.speed = info['motorInfo']['speed'] # Get the speed
        self.statusLeds.updateLeds(f"speed{self.speed}Led", 1)

    def connect_wifi(self, ssid, password): # Connect to the WiFi
        maxTry = 10
        numberofTry = 0
        sta_if = network.WLAN(network.STA_IF)
        sta_if.active(True)
        sta_if.connect(ssid, password)
        while not sta_if.isconnected() and numberofTry < maxTry:
            numberofTry += 1
            sleep(0.5)
        
        if sta_if.isconnected():
            print('network config:', sta_if.ifconfig())
            return sta_if.ifconfig()
        else:
            print(f'Connection failed! {ssid}')
            return False
    
    def connect_mqtt(self): # Connect to the MQTT Server
        k = 0 # Counter
        while self.client == None and k < 10: # Try to connect to the MQTT Server
            print("Trying to connect to %s MQTT Broker..." % (self.mqtt_server)) # Trying to connect to the MQTT Server
            self.client = MQTTClient(self.client_id, self.mqtt_server, self.port, self.username, self.password)
            utime.sleep(1) # Sleep for 1 second
            k += 1 # Increment the counter
        if self.client == None:
            print("Could not connect, exiting...")
            sys.exit()
        self.client.set_callback(self.on_message) # Set the callback function
        self.client.connect() # Connect to the MQTT Server
        self.publishMessage(self.picotopic, "Connected to %s MQTT Broker" % (self.mqtt_server)) # Publish a message
        print("Connected to %s MQTT Broker" % (self.mqtt_server)) # Connected to the MQTT Server
        self.statusLeds.updateLeds("mqttLed", "1")  # Turn on the WiFi LED

    def on_message(self, client, msg):
        if self.client == None:
            return
        msg = msg.decode("utf-8") # decode the message
        msgCode = (str(msg).split("-"))[0] # get the first part of the message
        msgValue = (str(msg).split("-"))[1] # get the second part of the message
        if msgCode == "00": # if the message code is 00, update the status
            if msgValue == "00":
                self.statusLeds.updateLeds("startLed", 0) # turn off the start led
                self.vehicle.drive_robot(0, 0, 0) # stop the robot
                self.stopped = 1 # update the status
                self.paused = 0 # update the status
            elif msgValue == "01":
                self.statusLeds.updateLeds("startLed", 0) # turn on the status led
                self.drive_robot(0, 0, 0) # stop the robot
                self.paused = 0 # update the status
                self.stopped = 1 # update the status
            elif msgValue == "10":
                self.statusLeds.updateLeds("startLed", 1) # turn on the status led
                self.paused = 0 # update the status
                self.stopped = 0 # update the status
        elif msgCode == "01": # if the message code is 01, update the parameters
            parameterName = (str(msgValue).split(":"))[0] # get the first part of the message
            parameterValue = (str(msgValue).split(":"))[1] # get the second part of the message
            parameterType = (str(msgValue).split(":"))[2] # get the second part of the message
            if parameterName == "speed":
                self.statusLeds.updateLeds(f"speed{self.speed}Led", 0)
            self.updateParameters(parameterName, parameterValue, parameterType)
            self.get_params()
            if parameterName == "speed":
                self.statusLeds.updateLeds(f"speed{self.speed}Led", 1)
        elif msgCode == "10": # if the message code is 10, update the status of leds
            led = (str(msgValue).split(":"))[0] # get the first part of the message
            value = (str(msgValue).split(":"))[1] # get the second part of the message
            if led == "all":
                self.statusLeds.updateAllLeds(value)
            self.statusLeds.updateLeds(led, value)
        elif msgCode == "11" and not self.paused and not self.stopped: # if the message code is 11, drive motors
            angularDirection = (str(msgValue).split(":"))[0] # get the first part of the message
            linearDirection = (str(msgValue).split(":"))[1] # get the second part of the message
            angularDirection = "cw" if angularDirection == "1" else "ccw" if angularDirection == "0" else "none"
            linearDirection = "forward" if linearDirection == "1" else "backward" if linearDirection == "0" else "none"
            speed = (str(msgValue).split(":"))[2] # get the third part of the message
            self.vehicle.drive_robot(angularDirection, linearDirection, speed)
            if angularDirection == "none" and linearDirection == "none":
                self.statusLeds.updateLeds("workingLed", 0)
            else:
                self.statusLeds.updateLeds("workingLed", 1)
        elif msgCode == "22" and not self.paused and not self.stopped: # if the message code is 22, drive motors
            leftDirection = (str(msgValue).split(":"))[0] # get the first part of the message
            leftSpeed = (str(msgValue).split(":"))[1] # get the first part of the message
            rightDirection = (str(msgValue).split(":"))[2] # get the first part of the message
            rightSpeed = (str(msgValue).split(":"))[3] # get the second part of the message
            delayTime = (str(msgValue).split(":"))[4] # get the third part of the message
            leftDirection = -1 if leftDirection == "0" else 1
            rightDirection = -1 if rightDirection == "0" else 1
            self.vehicle.drive_step(leftDirection*int(leftSpeed), rightDirection*int(rightSpeed), int(delayTime))
            
        elif msgCode == "99": # if the message code is 10, update the status of leds
            self.statusLeds.updateAllLeds(0)
            self.quit()
        else:
            self.publishMessage(self.picotopic, "Invalid message code received!")
            print("Invalid message code")
    
    def publishMessage(self, topic, message):
        if self.client == None:
            return
        self.client.publish(topic, message, qos=1)

    def updateParameters(self, name, value, typeValue="string"):
        info = ujson.loads(open(self.param_path).read())
        for key1, value1 in info.items():
            for key2, value2 in value1.items():
                if key2 == name:
                    if typeValue == "int":
                        value = int(value)
                    elif typeValue == "float":
                        value = float(value)
                    elif typeValue == "bool":
                        value = bool(value)
                    elif typeValue == "string":
                        value = str(value)
                    else:
                        value = eval(value)
                    (info[key1])[key2] = value
        if name == "speed":
            self.speed = value
        info = ujson.dumps(info)
        with open(self.param_path, "w") as f:
            f.write(info)
    
    def quit(self):
        self.client.disconnect()
        self.client = None
        sys.exit()
