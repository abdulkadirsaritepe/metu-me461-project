
from mamba_mqtt import PicoMQTT
from game_mqtt import GameBoardMQTT
from manuel_arrows import ManuelArrows
from manuel_directives import ManuelDirectives
from autonomous import Autonomous
import sys
from time import sleep

if __name__ == "__main__":
    try:
        picomqtt = PicoMQTT()
        gamemqtt = GameBoardMQTT()
    except Exception as e:
        print("Error: ", e)
        sys.exit()

    while True:
        try:
            print("Modes: \n 1. Manuel w/Arrows \n 2. Manuel w/Directives \n 3. Autonomous \n 4. Update Parameter\n 5. Exit \n 9. Close Pico")
            mode = input("Press Enter the mode index: ")
            if mode == "1":
                ManuelArrows(picomqtt)
            elif mode == "2":
                ManuelDirectives(picomqtt, gamemqtt)
            elif mode == "3":
                Autonomous(picomqtt, gamemqtt)
            elif mode == "4":
                name = input("Enter the parameter name: ")
                value = input("Enter the new value: ")
                typeValue = input("Enter the type of the value: ")
                picomqtt.publishToTopic(f"01-{name}:{value}:{typeValue}")
            elif mode == "5":
                picomqtt.publishToTopic("00-00")
                picomqtt.publishToTopic("01-all:0")
                print("Exiting...")
                sleep(1)
                sys.exit()
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