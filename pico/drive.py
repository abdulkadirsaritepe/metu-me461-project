
from machine import Pin, PWM
import time, os, ujson

class Vehicle:
    def __init__(self):
        param_path = 'pico_params.ujson' 
        info = ujson.loads(open(param_path).read()) 
        self.frequency = info['motorInfo']['motorfreq'] 
        motor1pins = (info['motorInfo'])['motor1pins']
        motor2pins = (info['motorInfo'])['motor2pins'] 
        self.leftWheelCalibration = (info['motorInfo'])['leftWheelCalibration']
        self.rightWheelCalibration = (info['motorInfo'])['rightWheelCalibration'] 
        # Define the GPIO pins for the motor driver
        self.motor_1_forward = PWM(Pin(motor1pins[0], Pin.OUT)) 
        self.motor_1_backward = PWM(Pin(motor1pins[1], Pin.OUT))
        self.motor_2_forward = PWM(Pin(motor2pins[0], Pin.OUT))
        self.motor_2_backward = PWM(Pin(motor2pins[1], Pin.OUT))
        # Set the frequency of the PWM
        self.motor_1_forward.freq(self.frequency)
        self.motor_1_backward.freq(self.frequency)
        self.motor_2_forward.freq(self.frequency)
        self.motor_2_backward.freq(self.frequency)
        # Set the duty cycle of the PWM
        self.motor_1_forward.duty_u16(0)
        self.motor_1_backward.duty_u16(0)
        self.motor_2_forward.duty_u16(0)
        self.motor_2_backward.duty_u16(0)

    def drive_robot(self, desiredAngleDir="ccw", desiredDir="forward", speed=0): # max speed is 65000
        # Set the speed of the motors
        signAngularSpeed = 1 if desiredAngleDir == "ccw" else -1 if desiredAngleDir == "cw" else 0
        signLinearSpeed = 1 if desiredDir == "forward" else -1 if desiredDir == "backward" else 0
        speed = int(speed)
        leftSpeed = (signAngularSpeed+signLinearSpeed)*speed*self.leftWheelCalibration
        rightSpeed = (-signAngularSpeed+signLinearSpeed)*speed*self.rightWheelCalibration
        # Drive the robot based on the angle and speed
        if leftSpeed == 0 and rightSpeed == 0:
            self.motor_1_forward.duty_u16(0)
            self.motor_2_forward.duty_u16(0)
            self.motor_1_backward.duty_u16(0)
            self.motor_2_backward.duty_u16(0)
        
        if leftSpeed > 0:
            self.motor_1_forward.duty_u16(speed)
            self.motor_1_backward.duty_u16(0)
        elif leftSpeed < 0:
            self.motor_1_forward.duty_u16(0)
            self.motor_1_backward.duty_u16(speed)
        if rightSpeed > 0:
            self.motor_2_forward.duty_u16(speed)
            self.motor_2_backward.duty_u16(0)
        elif rightSpeed < 0:
            self.motor_2_forward.duty_u16(0)
            self.motor_2_backward.duty_u16(speed)