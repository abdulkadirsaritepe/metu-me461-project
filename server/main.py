
from mamba_mqtt import PicoMQTT
from game_mqtt import GameBoardMQTT
from manuel import Manuel
from manuel_arrows import ManuelArrows
from autonomous import Autonomous
from manuel_arrows_test import ManuelArrowsTest
import sys
from time import sleep

# info The main python script for the ME461 project
# info This script is used to run the robot in different modes
# info The modes are:
# info 1. Manuel w/Arrows
# info 2. Autonomous
# info 3. Update Parameter
# info 4. Exit
# info 9. Close Pico
# info The script will ask the user to enter the mode index
# info The script will then run the mode
# info picomqtt is the MQTT client for the robot
# info gamemqtt is the MQTT client for the game board
# info The script will run until the user enters 5 to exit
# info The script will then close the robot and exit

if __name__ == "__main__":
    try:
        picomqtt = PicoMQTT()
        gamemqtt = GameBoardMQTT()
    except Exception as e:
        print("Error: ", e)
        sys.exit()
    if gamemqtt.isConnected == False:
        print("Error: Game Manager MQTT connection failed")
    if picomqtt.isConnected == False:
        print("Error: Pico W MQTT connection failed")
        # sys.exit()
    
    while True:
        try:
            print("Modes: \n 1. Manuel w/Arrows \n 2. Autonomous \n 3. Update Parameter\n 4. Exit \n 8. Manuel \n 9. Close Pico")
            mode = input("Press Enter the mode index: ")
            if mode == "1":
                ManuelArrows(picomqtt, gamemqtt)
            elif mode == "2":
                Autonomous(picomqtt, gamemqtt)
            elif mode == "3":
                name = input("Enter the parameter name: ")
                value = input("Enter the new value: ")
                typeValue = input("Enter the type of the value: ")
                picomqtt.publishToTopic(f"01-{name}:{value}:{typeValue}")
            elif mode == "4":
                picomqtt.publishToTopic("00-00")
                picomqtt.publishToTopic("01-all:0")
                print("Exiting...")
                sleep(1)
                sys.exit()
            elif mode == "7":
                ManuelArrowsTest(picomqtt)
            elif mode == "8":
                Manuel(picomqtt)
            elif mode == "9":
                picomqtt.publishToTopic("99-99")
                print("Exiting...")
                sleep(1)
                sys.exit()
            else:
                print("Invalid mode")
        except KeyboardInterrupt:
            picomqtt.publishToTopic("00-00")
            print("Exiting...")
            sys.exit()