
from machine import Pin, PWM
import ujson, os

class StatusUpdate:
    def __init__(self):
        self.param_path = 'pico_params.ujson'
        self.info = ujson.loads(open(self.param_path).read())
        self.ledInfo = self.info['ledInfo']
        self.leds = {}
        self.power = 10000
        for led, ledpin in self.ledInfo.items():
            self.leds.update({led: PWM(Pin(ledpin, Pin.OUT))})
            self.leds[led].duty_u16(0)

    def updateLeds(self, led, status):
        status = self.power if str(status) == "1" else 0
        self.leds[led].duty_u16(status)

    def updateAllLeds(self, status):
        status = self.power if str(status) == "1" else 0
        for led in self.leds:
            self.leds[led].duty_u16(status)
