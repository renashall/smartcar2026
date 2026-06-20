import time
from pca9685 import PCA9685

MIN_ANGLE = 0
MAX_ANGLE = 180
MIN_SERVO_PULSE = 500
MAX_SERVO_PULSE = 2500


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


class Servo:
    def __init__(self):
        self.PwmServo = PCA9685(0x40, debug=True)
        self.PwmServo.setPWMFreq(50)
        self.PwmServo.setServoPulse(8,1500)
        self.PwmServo.setServoPulse(9,1500)
    def setServoPwm(self,channel,angle,error=10):
        angle=clamp(int(angle),MIN_ANGLE,MAX_ANGLE)
        if channel=='0':
            pulse=2500-int((angle+error)/0.09)
            self.PwmServo.setServoPulse(8,clamp(pulse,MIN_SERVO_PULSE,MAX_SERVO_PULSE))
        elif channel=='1':
            pulse=500+int((angle+error)/0.09)
            self.PwmServo.setServoPulse(9,clamp(pulse,MIN_SERVO_PULSE,MAX_SERVO_PULSE))
        elif channel=='2':
            pulse=500+int((angle+error)/0.09)
            self.PwmServo.setServoPulse(10,clamp(pulse,MIN_SERVO_PULSE,MAX_SERVO_PULSE))
        elif channel=='3':
            pulse=500+int((angle+error)/0.09)
            self.PwmServo.setServoPulse(11,clamp(pulse,MIN_SERVO_PULSE,MAX_SERVO_PULSE))
        elif channel=='4':
            pulse=500+int((angle+error)/0.09)
            self.PwmServo.setServoPulse(12,clamp(pulse,MIN_SERVO_PULSE,MAX_SERVO_PULSE))
        elif channel=='5':
            pulse=500+int((angle+error)/0.09)
            self.PwmServo.setServoPulse(13,clamp(pulse,MIN_SERVO_PULSE,MAX_SERVO_PULSE))
        elif channel=='6':
            pulse=500+int((angle+error)/0.09)
            self.PwmServo.setServoPulse(14,clamp(pulse,MIN_SERVO_PULSE,MAX_SERVO_PULSE))
        elif channel=='7':
            pulse=500+int((angle+error)/0.09)
            self.PwmServo.setServoPulse(15,clamp(pulse,MIN_SERVO_PULSE,MAX_SERVO_PULSE))

# Main program logic follows:
if __name__ == '__main__':
    print("Now servos will rotate to 90°.") 
    print("If they have already been at 90°, nothing will be observed.")
    print("Please keep the program running when installing the servos.")
    print("After that, you can press ctrl-C to end the program.")
    pwm=Servo()
    while True:
        try :
            pwm.setServoPwm('0',90)
            pwm.setServoPwm('1',90)
        except KeyboardInterrupt:
            print ("\nEnd of program")
            break

    

    
       



    
