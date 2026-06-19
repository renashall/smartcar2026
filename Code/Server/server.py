#!/usr/bin/python 
# -*- coding: utf-8 -*-
import io
import socket
import struct
import time
from picamera2 import Picamera2   # libcamera-based camera library (Bullseye/Bookworm)
import fcntl
import  sys
import threading
from motor import *
from servo import *
from led import *
from buzzer import *
from adc import *
from thread import *
from light import *
from ultrasonic import *
from line_tracking import *
from threading import Timer
from threading import Thread
from command import COMMAND as cmd

class Server:   
    def __init__(self):
        self.PWM=Motor()
        self.servo=Servo()
        self.led=Led()
        self.ultrasonic=Ultrasonic()
        self.buzzer=Buzzer()
        self.adc=Adc()
        self.light=Light()
        self.infrared=Line_Tracking()
        self.tcp_Flag = True
        self.sonic=False
        self.Light=False
        self.Mode = 'one'
        self.endChar='\n'
        self.intervalChar='#'
        self.last_battery = 0     # latest battery voltage, published by Power()
    def get_interface_ip(self):
        # Find the Pi's primary LAN IP for display, without assuming an
        # interface name. (The old code was hard-coded to wlan0 and failed on
        # Ethernet or when Wi-Fi was down.) Opening a UDP socket to a dummy
        # address makes the OS pick the outgoing interface; no data is sent.
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def StartTcpServer(self):
        display_ip = str(self.get_interface_ip())
        # Bind to all interfaces ('') so the client can connect via the Pi's
        # Wi-Fi IP, its Ethernet IP, or 127.0.0.1 (handy when the client runs on
        # the Pi too). Binding to a single interface IP was the cause of a client
        # connecting while the server reported no connection.
        self.server_socket1 = socket.socket()
        self.server_socket1.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.server_socket1.bind(('', 5000))
        self.server_socket1.listen(1)
        self.server_socket = socket.socket()
        self.server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.server_socket.bind(('', 8000))
        self.server_socket.listen(1)
        print('Server address: '+display_ip)
        
        
    def StopTcpServer(self):
        # Close BOTH the accepted client connections AND the listening sockets.
        # If the listening sockets are left open, the next StartTcpServer() (on a
        # server On/Off toggle or a Reset) fails to re-bind the same ports with
        # "Address already in use" and the server crashes. Each close is guarded
        # so a missing/already-closed socket never raises.
        for sock_name in ("connection", "connection1", "server_socket", "server_socket1"):
            sock = getattr(self, sock_name, None)
            if sock is not None:
                # shutdown() first so a thread blocked in accept()/recv() on this
                # socket wakes up and releases the file descriptor; otherwise the
                # port stays bound and the next StartTcpServer() hits EADDRINUSE.
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    sock.close()
                except Exception:
                    pass
                setattr(self, sock_name, None)
         
    def Reset(self):
        self.StopTcpServer()
        self.StartTcpServer()
        self.SendVideo=Thread(target=self.sendvideo)
        self.ReadData=Thread(target=self.readdata)
        self.SendVideo.start()
        self.ReadData.start()
    def send(self,data):
        self.connection1.send(data.encode('utf-8'))    
    def sendvideo(self):
        try:
            self.connection,self.client_address = self.server_socket.accept()
            self.connection=self.connection.makefile('wb')
        except:
            pass
        try:
            self.server_socket.close()
        except Exception:
            pass
        camera = None
        try:
            camera = Picamera2()
            # 400x300 jpeg frames, same resolution the old picamera code used.
            camera.configure(camera.create_video_configuration(main={"size": (400, 300)}))
            camera.start()
            time.sleep(2)                       # give 2 secs for camera to initilize
            stream = io.BytesIO()
            # send jpeg format video stream
            print ("Start transmit ... ")
            while True:
                try:
                    stream.seek(0)
                    stream.truncate()
                    camera.capture_file(stream, format='jpeg')   # grab one frame as jpeg
                    self.connection.flush()
                    stream.seek(0)
                    b = stream.read()
                    length=len(b)
                    if length >5120000:
                        continue
                    lengthBin = struct.pack('L', length)
                    self.connection.write(lengthBin)
                    self.connection.write(b)
                except Exception as e:
                    print(e)
                    print ("End transmit ... " )
                    break
        except BaseException as e:
            # BaseException also catches the SystemExit that stop_thread injects
            # when the server is toggled Off, so the camera is always released in
            # the finally below and the next On can reopen it.
            print(e)
        finally:
            if camera is not None:
                try:
                    camera.stop()
                except Exception:
                    pass
                try:
                    camera.close()
                except Exception:
                    pass
                 
    def stopMode(self):
        try:
            stop_thread(self.infraredRun)
            self.PWM.setMotorModel(0,0,0,0)
        except:
            pass
        try:
            stop_thread(self.lightRun)
            self.PWM.setMotorModel(0,0,0,0)
        except:
            pass            
        try:
            stop_thread(self.ultrasonicRun)
            self.PWM.setMotorModel(0,0,0,0)
            self.servo.setServoPwm('0',90)
            self.servo.setServoPwm('1',90)
        except:
            pass
        
    def readdata(self):
        try:
            try:
                self.connection1,self.client_address1 = self.server_socket1.accept()
                print ("Client connection successful !")
            except:
                print ("Client connect failed")
            restCmd=""
            self.server_socket1.close()
            while True:
                try:
                    AllData=restCmd+self.connection1.recv(1024).decode('utf-8')
                except:
                    if self.tcp_Flag:
                        self.Reset()
                    break
                print(AllData)
                if len(AllData) < 5:
                    restCmd=AllData
                    if restCmd=='' and self.tcp_Flag:
                        self.Reset()
                        break
                restCmd=""
                if AllData=='':
                    break
                else:
                    cmdArray=AllData.split("\n")
                    if(cmdArray[-1] != ""):
                        restCmd=cmdArray[-1]
                        cmdArray=cmdArray[:-1]     
            
                for oneCmd in cmdArray:
                    data=oneCmd.split("#")
                    if data==None:
                        continue
                    elif cmd.CMD_MODE in data:
                        if data[1]=='one' or data[1]=="1":
                            self.stopMode()
                            self.Mode='one'
                        elif data[1]=='two' or data[1]=="3":
                            self.stopMode()
                            self.Mode='two'
                            self.lightRun=Thread(target=self.light.run)
                            self.lightRun.start()
                        elif data[1]=='three' or data[1]=="4":
                            self.stopMode()
                            self.Mode='three'
                            self.ultrasonicRun=threading.Thread(target=self.ultrasonic.run)
                            self.ultrasonicRun.start()
                        elif data[1]=='four' or data[1]=="2":
                            self.stopMode()
                            self.Mode='four'
                            self.infraredRun=threading.Thread(target=self.infrared.run)
                            self.infraredRun.start()
                            
                    elif (cmd.CMD_MOTOR in data) and self.Mode=='one':
                        try:
                            data1=int(data[1])
                            data2=int(data[2])
                            data3=int(data[3])
                            data4=int(data[4])
                            self.PWM.setMotorModel(data1,data2,data3,data4)
                        except:
                            pass
                    elif cmd.CMD_SERVO in data:
                        try:
                            data1=data[1]
                            data2=int(data[2])
                            if data1==None or data2==None:
                                continue
                            self.servo.setServoPwm(data1,data2)
                        except:
                            pass

                    elif cmd.CMD_LED in data:
                        try:
                            data1=int(data[1])
                            data2=int(data[2])
                            data3=int(data[3])
                            data4=int(data[4])
                            self.led.ledIndex(data1,data2,data3,data4)
                        except:
                            pass
                    elif cmd.CMD_LED_MOD in data:
                        self.LedMoD=data[1]
                        if self.LedMoD== '0':
                            try:
                                stop_thread(Led_Mode)
                            except:
                                pass
                            self.led.ledMode(self.LedMoD)
                            time.sleep(0.1)
                            self.led.ledMode(self.LedMoD)
                        else :
                            try:
                                stop_thread(Led_Mode)
                            except:
                                pass
                            time.sleep(0.1)
                            Led_Mode=Thread(target=self.led.ledMode,args=(data[1],))
                            Led_Mode.start()
                    elif cmd.CMD_SONIC in data:
                        if data[1]=='1':
                            self.sonic=True
                            self.ultrasonicTimer = threading.Timer(0.5,self.sendUltrasonic)
                            self.ultrasonicTimer.start()
                        else:
                            self.sonic=False
                    elif cmd.CMD_BUZZER in data:
                        try:
                            self.buzzer.run(data[1])
                        except:
                            pass
                    elif cmd.CMD_LIGHT in data:
                        if data[1]=='1':
                            self.Light=True
                            self.lightTimer = threading.Timer(0.3,self.sendLight)
                            self.lightTimer.start()
                        else:
                            self.Light=False
                    elif cmd.CMD_POWER in data:
                        ADC_Power=self.adc.recvADC(2)*3
                        try:
                            self.send(cmd.CMD_POWER+'#'+str(ADC_Power)+'\n')
                        except:
                            pass
        except Exception as e: 
            print(e)
        self.StopTcpServer()    
    def sendUltrasonic(self):
        if self.sonic==True:
            ADC_Ultrasonic=self.ultrasonic.get_distance()
            if ADC_Ultrasonic==self.ultrasonic.get_distance():
                try:
                    self.send(cmd.CMD_SONIC+"#"+str(ADC_Ultrasonic)+'\n')
                except:
                    self.sonic=False
            self.ultrasonicTimer = threading.Timer(0.13,self.sendUltrasonic)
            self.ultrasonicTimer.start()
    def sendLight(self):
        if self.Light==True:
            ADC_Light1=self.adc.recvADC(0)
            ADC_Light2=self.adc.recvADC(1) 
            try:
                self.send(cmd.CMD_LIGHT+'#'+str(ADC_Light1)+'#'+str(ADC_Light2)+'\n')
            except:
                self.Light=False
            self.lightTimer = threading.Timer(0.17,self.sendLight)
            self.lightTimer.start()
    def Power(self):
        while True:
            ADC_Power=self.adc.recvADC(2)*3
            # Publish the latest reading so the GUI can show it without touching
            # the I2C bus from another thread (a plain attribute read is safe).
            self.last_battery = ADC_Power
            time.sleep(3)
            if ADC_Power < 3:
                # A reading near 0 V means the battery is switched off or simply
                # not connected - that is not a "low battery", so stay silent
                # instead of beeping continuously.
                self.buzzer.run('0')
            elif ADC_Power < 6.8:
                print("WARNING: battery critically low (%.2f V) - charge now!" % ADC_Power)
                for i in range(4):
                    self.buzzer.run('1')
                    time.sleep(0.1)
                    self.buzzer.run('0')
                    time.sleep(0.1)
            elif ADC_Power< 7:
                print("WARNING: battery low (%.2f V)" % ADC_Power)
                for i in range(2):
                    self.buzzer.run('1')
                    time.sleep(0.1)
                    self.buzzer.run('0')
                    time.sleep(0.1)
            else:
                self.buzzer.run('0')
if __name__=='__main__':
    pass
