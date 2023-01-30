
from machine import Pin, PWM
import ujson, os

class StatusUpdate:
    def __init__(self):
        self.param_path = 'pico_params.ujson'
        self.info = ujson.loads(open(self.param_path).read())
        self.ledInfo = self.info['ledInfo']
        self.leds = {}
        for led, ledpin in self.ledInfo.items():
            self.leds.update({led: Pin(ledpin, Pin.OUT)})
            self.leds[led].value(0)

    def updateLeds(self, led, status):
        self.leds[led].value(status)

    def updateAllLeds(self, status):
        for led in self.leds:
            self.leds[led].value(status)