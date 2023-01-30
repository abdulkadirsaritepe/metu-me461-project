
import sys
from pico_mqtt import PicoMQTT
from status_update import StatusUpdate
from machine import Pin

led = Pin('LED', Pin.OUT)
led.value(1)
statusLeds = StatusUpdate()

try:
    statusLeds.updateAllLeds(0)
    PicoMQTT()
    statusLeds.updateAllLeds(0)
except KeyboardInterrupt:
    led.value(0)
    statusLeds.updateAllLeds(0)
    print("Exiting...")
    sys.exit()