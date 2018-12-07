import usocket as socket
import machine
import utime
import network
from ssconfig import client_id, server_id #poll a separate file for id number. For easier code changes

#ultrasonic pins
trig = machine.Pin(14, machine.Pin.OUT)
echo = machine.Pin(4, machine.Pin.IN)

def readdist(): #reading the distance from a HCSR04 Ultrasonic sensor
    trig.off()
    utime.sleep_us(2)
    trig.on()
    utime.sleep_us(10)
    trig.off()
    while echo.value() == 0:
        pass
    t1 = utime.ticks_us()
    while echo.value() == 1:
        pass
    t2 = utime.ticks_us()
    cm = (t2 - t1) / 58.0
    print(cm, 'cm')
    return cm

def ssclient():
    print('Starting Stall Sense as Client', client_id())
    #status led
    innerled = machine.Pin(16, machine.Pin.OUT) #occupied status
    edgeled = machine.Pin(2, machine.Pin.OUT) #connected
    innerled.value(1)
    edgeled.value(1)

    #config and vars
    ssid = 'Stallsense Server' + server_id()
    password = 'micropythoN'
    timeoutmutiplier = 1
    stop_button = machine.Pin(5, machine.Pin.IN, machine.Pin.PULL_UP) #Pin D5
    socket_started = 0
    message = client_id() + ':status' #to satsfy the finally statement in the comm loop

    #Connect to server wifi
    sta_if = network.WLAN(network.STA_IF) #create the wifi station object
    if not sta_if.isconnected(): #if not connecting by default force connect and timeout after 10 trys
        innerled.value(0)   #set both leds on
        edgeled.value(0)
        print('Connecting to Server...')
        sta_if.active(True) #activate the station module to connect to a wifi router/network
        utime.sleep(0.5)
        sta_if.connect(ssid,password)
        innerled.value(1) #turn inner led off signifiying connection attempts
        
        while not sta_if.isconnected(): #exit trying if connected or timeout
            edgeled.value(1) #turn edge led off as part of waiting for connection
            print('Searching... Attempt:', timeoutmutiplier, '/ 10')
            utime.sleep(0.5 * timeoutmutiplier)
            edgeled.value(0) #turn edge led on as part of waiting for connection
            timeoutmutiplier += 1
            utime.sleep(0.5)
            if timeoutmutiplier > 10:
                print('Connection Timeout. Breaking...')
                break

    if timeoutmutiplier <= 10: #pass main code if no connection
        print('Wifi Connected. Connecting Socket...')
        innerled.value(0) #turn edge led on steady to signify connected
        utime.sleep(1)
        edgeled.value(1) #turn edge led off to start socket creation

        HOST = '192.168.4.1'    # The remote host 
        PORT = 2018             # The same port as used by the server
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        while stop_button.value() != 0:
            try:
                s.connect((HOST, PORT))
                edgeled.value(0)
                print('Socket Connected. Starting...')
                socket_started = 1
                utime.sleep(0.5)

                #define vars
                prev_state = 'open'
                message = client_id() + ':open' #Format is 'Client#:status'   
                innerled.value(1)

                detect_threshold = 250 #in centimeters

                while stop_button.value() != 0:
                    distance = readdist()
                    if distance <= detect_threshold: 
                        if prev_state != 'occupied':
                            message = client_id() + ':occupied'
                            s.send(message)    
                            innerled.value(0)
                            print('occupied')
                            prev_state = 'occupied'
                    elif distance >= detect_threshold: 
                        if prev_state != 'open':
                            message = client_id() + ':open'
                            s.send(message)    
                            innerled.value(1)
                            print('open')
                            prev_state = 'open'
                    else:
                        print('Current State: ', prev_state)
                    utime.sleep(1)

            finally:
                print('Closing Socket...')
                if socket_started == 1:
                    message = client_id() + ':closing'
                    s.send(message)
                s.close()
                innerled.value(1)

    else:
        print('!>>> Failed to Connect. Restart to try again...')
        #error led code
        for i in range(5):
            innerled.value(1)
            edgeled.value(0)
            utime.sleep(0.5)
            innerled.value(0)
            edgeled.value(1)
            utime.sleep(0.5)

    innerled.value(1)   #set both leds off
    edgeled.value(1)

    print('Client Terminated...')
