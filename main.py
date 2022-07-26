# Cod scris pentru etapa nationala a concursului infoeducatie 2022, 25-30 iulie#
# HSCDBot - HighSpeedCableDriverRobot, Lazaroiu Mihai, Iatagan Andrei,#
# Colegiul national Grigore Moisil Bucuresti #
# Cod "aproape" final la data 23 iulie(poate 24 ...)#

#CONTROLARE:

# q - quit
# key_left - linear stanga
# key_right - linear dreapta
# key_up - umar jos
# key_down - umar sus
# w - cot sus
# s - cot jos
# e - incheietura sus
# d - incheietura jos
# f - deschidere gheara
# g - inchidere gheara
# h - home in tipul operarii
# t - verificarea conditiilor din carcasa de electronice
# z - dezactivare motor umar
# x - dezactivare motor liniar slide
# 1 - set viteza liniar
# 2 - set viteza umar
# 3 - set viteza cot
# 4 - set viteza incheietura

#importare librarii
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_StepperMotor
from adafruit_servokit import ServoKit
import adafruit_dht
import RPi.GPIO as GPIO
from gpiozero import Buzzer, LED
import curses
import time
import board
import atexit
import threading

        #VARIABILE GLOBALE SI INITIALIZARI#


#initializare control tastatura
screen = curses.initscr()
curses.noecho()
curses.cbreak()
screen.keypad(True)

#desemnare HAT-uri
kit1 = Adafruit_MotorHAT(addr=0x60)
kit2 = Adafruit_MotorHAT(addr=0x61)
kit3 = ServoKit(channels=16)

#initializare senzor
sensor = adafruit_dht.DHT11(board.D19)

#initializare buzzer
buzzer = Buzzer(16)

#initializare LED
led = LED(13)

#initializare limitatoare
GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_UP)

myStepper1 = kit1.getStepper(200, 2) #initializare stepper liniar
myStepper2 = kit2.getStepper(200, 1) #initializare stepper umar

#homing stepper motor stepping rate
h_stepper1_steppingrate = 2
h_stepper2_steppingrate = 2

#normal stepper motor stepping rate
stepper1_steppingrate = 2
stepper2_steppingrate = 2

#limita stepper1 (counts)
linear_maxrange = 1000

#limita stepper2 (counts)
first_joint_maxrange = 275

#valoare unghi home servo (deg)
servo1_hAng = 180 
servo2_hAng = 90 
servo3_hAng = 90

#variabila care retine unghiul curent al servo
servo1_cAng = servo1_hAng
servo2_cAng = servo2_hAng
servo3_cAng = servo3_hAng

myStepper1.setSpeed(25) #setare viteza implicita stepper #1
myStepper2.setSpeed(25) #setare viteza implicita stepper #2

#setare viteze servomotoare implicite
servo1_sStep = 10
servo2_sStep = 10
servo3_sStep = 10

#setare limite servomotoare
servo1_maxrange = 170
servo2_maxrange = 170
servo3_maxrange = 170 
servo1_minrange = 10
servo2_minrange = 10
servo3_minrange = 10

#timestep servomotoare
time_step = 0.1


        #FUNCTII#

#oprire motoare la terminarea programului
def turnOffMotors():
    kit1.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    kit1.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
    kit1.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
    kit1.getMotor(4).run(Adafruit_MotorHAT.RELEASE)
    kit2.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    kit2.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
    kit2.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
    kit2.getMotor(4).run(Adafruit_MotorHAT.RELEASE)
    
#la inchiderea programului se apeleaza turnOffMotors
atexit.register(turnOffMotors)

def updateServoAngle():
    kit3.servo[0].angle = servo1_cAng
    kit3.servo[1].angle = servo2_cAng
    kit3.servo[2].angle = servo3_cAng
    
def homeStepper1():
    while GPIO.input(21) == True:
       myStepper1.step(h_stepper1_steppingrate, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.DOUBLE)
    while GPIO.input(21) == False:
        myStepper1.step(h_stepper1_steppingrate, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
    linear_steps = 0
    
def homeStepper2():
    while GPIO.input(20) == True:
        myStepper2.step(h_stepper2_steppingrate, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
    while GPIO.input(20) == False:
        myStepper2.step(h_stepper2_steppingrate, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.DOUBLE)
    first_joint_steps = 0
    
def totalHome():
    homeStepper1()
    homeStepper2()
    led.on()
     
def disableStepper1():
    kit1.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    kit1.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
    kit1.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
    kit1.getMotor(4).run(Adafruit_MotorHAT.RELEASE)
    
def disableStepper2():
    kit2.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    kit2.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
    kit2.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
    kit2.getMotor(4).run(Adafruit_MotorHAT.RELEASE)

warning_temp = 50
kill_temp = 80
temperatura_curenta = 0
umiditate_curenta = 0
def functie_multithread_temp_sensor():
    global temperatura_curenta
    global umiditate_curenta
    while True:
        time.sleep(5)
        try:
            #citire senzor
            temperatura_curenta = sensor.temperature
            umiditate_curenta = sensor.humidity
        except RuntimeError as error:
            pass     


        #HOME INITIAL#
    
#HOME STEPPER #1
while GPIO.input(20) == True:
        myStepper2.step(h_stepper2_steppingrate, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
while GPIO.input(20) == False:
        myStepper2.step(h_stepper2_steppingrate, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.DOUBLE)
first_joint_steps = 0
led.on()

#HOME STEPPER #2
while GPIO.input(21) == True:
       myStepper1.step(h_stepper1_steppingrate, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.DOUBLE)
while GPIO.input(21) == False:
        myStepper1.step(h_stepper1_steppingrate, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
linear_steps = 0
led.on()

#pornim thread ul folosit strict pentru senzorul de temperatura.

thread_1 = threading.Thread(target = functie_multithread_temp_sensor, daemon = True)
thread_1.start()

        #MAINLOOP

try:
    while True:
    
        curses.noecho()
        curses.cbreak()
        screen.keypad(True)
            
        updateServoAngle()
    
    #inregistreaza input de la tastatura
        char = screen.getch()

        if temperatura_curenta > kill_temp:
            break
            thread_1.join()
        elif temperatura_curenta > warning_temp:
            buzzer.beep()
        elif temperatura_curenta < warning_temp:
            buzzer.off()
    #inchidere program
        if char == ord('q'):
            totalHome()
            break
            thread_1.join()
        
    #realizeaza home total
        elif char == ord('h'):
            totalHome()
            servo1_cAng = servo1_hAng
            servo2_cAng = servo2_hAng
            servo3_cAng = servo3_hAng

        #CONTROL STEPPERE#
            
        elif char == curses.KEY_LEFT:
            if linear_steps < linear_maxrange:
                myStepper1.step(stepper1_steppingrate, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
                linear_steps = linear_steps + stepper1_steppingrate
                
        elif char == curses.KEY_RIGHT:
            if linear_steps > 0:
                myStepper1.step(stepper1_steppingrate, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.DOUBLE)
                linear_steps = linear_steps - stepper1_steppingrate
                
        elif char == curses.KEY_UP:
            if first_joint_steps < first_joint_maxrange:
                myStepper2.step(stepper2_steppingrate, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.DOUBLE)
                first_joint_steps = first_joint_steps + stepper2_steppingrate
                
        elif char == curses.KEY_DOWN:
            if first_joint_steps > 0:
                myStepper2.step(stepper2_steppingrate, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
                first_joint_steps = first_joint_steps - stepper2_steppingrate
        
        #CONTROL SERVOMOTOARE#
                
        elif char == ord('w'):
            if servo1_cAng < servo1_maxrange:
                servo1_cAng = servo1_cAng + servo1_sStep
                time.sleep(time_step)
                buzzer.off()
            if servo1_cAng == servo1_maxrange:
                print("Elbow uppermost limit reached!")
                buzzer.beep()
        
        elif char == ord('s'):
            if servo1_cAng > servo1_minrange:
                servo1_cAng = servo1_cAng - servo1_sStep
                time.sleep(time_step)
                buzzer.off()
            if servo1_cAng == servo1_minrange:
                print("Elbow bottommost most limit reached!")
                buzzer.beep()
                
        elif char == ord('e'):
            if servo2_cAng < servo2_maxrange:
                servo2_cAng = servo2_cAng + servo2_sStep
                time.sleep(time_step)
                buzzer.off()
            if servo2_cAng == servo2_maxrange:
                print("Wrist uppermost limit reached!")
                buzzer.beep()
                
        elif char == ord('d'):
            if servo2_cAng > servo2_minrange:
                servo2_cAng = servo2_cAng - servo2_sStep
                time.sleep(time_step)
                buzzer.off()
            if servo2_cAng == servo2_minrange:
                print("Wrist bottommost limit reached!")
                buzzer.beep()
                
        elif char == ord('f'):
            if servo3_cAng < servo3_maxrange:
                servo3_cAng = servo3_cAng + servo3_sStep
                time.sleep(time_step)
            if servo3_cAng == servo3_maxrange:
                print("Claw fully opened!")
                
        elif char == ord('g'):
            if servo3_cAng > servo3_minrange:
                servo3_cAng = servo3_cAng - servo3_sStep
                time.sleep(time_step)
            if servo3_cAng == servo3_minrange:
                print("Claw fully closed!")
                
        #DEZACTIVARE STEPPERE
        
        elif char == ord('x'):
            disableStepper1()
            led.off()
            
        elif char == ord('z'):
            disableStepper2()
            led.off()
            
        #AJUSTAREA LIVE A VITEZEI
            
        elif char == ord('1'):
            curses.nocbreak(); screen.keypad(False); curses.echo()
            curses.endwin()
            stepper1_speed = int(input("Enter desired speed for linear stepper: "))
            myStepper1.setSpeed(stepper1_speed)
            print("\n")
            print("Speed setting updated!")
            print("Linear speed has been set to ", stepper1_speed)
            
        elif char == ord('2'):
            curses.nocbreak(); screen.keypad(False); curses.echo()
            curses.endwin()
            stepper2_speed = int(input("Enter desired speed for shoulder stepper: "))
            myStepper2.setSpeed(stepper2_speed)
            print("\n")
            print("Speed setting updated!")
            print("Shoulder speed has been set to ", stepper2_speed)
            
        elif char == ord('3'):
            curses.nocbreak(); screen.keypad(False); curses.echo()
            curses.endwin()
            servo1_sStep = int(input("Enter desired speed for elbow servo: "))
            print("\n")
            print("Speed setting updated!")
            print("Elbow speed has been set to ", servo1_sStep)
            
        elif char == ord('4'):
            curses.nocbreak(); screen.keypad(False); curses.echo()
            curses.endwin()
            servo2_sStep = int(input("Enter desired speed for wrist servo: "))
            print("\n")
            print("Speed setting updated!")
            print("Wrist speed has been set to ", servo2_sStep)
            
        #AFISARE TEMPERATURA + UMIDITATE LA ELECTRONICE
            
        elif char == ord('t'):
            print("Temperature: {}*C  Humidity: {}% ".format(temperatura_curenta, umiditate_curenta))

            
finally:
    curses.nocbreak(); screen.keypad(False); curses.echo()
    curses.endwin()
    
