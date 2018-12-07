import machine
import socket
import utime
import neopixel
import ure
import select
import network
from ssconfig import server_id

def start():
    print('Starting Stall Sense as Server', server_id())
    #open pins and vars
    stop_button = machine.Pin(5, machine.Pin.IN, machine.Pin.PULL_UP) #Pin D1
    stop_server = 1
    innerled = machine.Pin(16, machine.Pin.OUT) #inner led
    edgeled = machine.Pin(2, machine.Pin.OUT) #edge led
    innerled.value(0)
    edgeled.value(0)
    stallstat = [2,2,2]

    #access point config
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(True)
    ap_if.config(essid='Stallsense Server' + server_id(), password='micropythoN')

    #neopixel defs
    panelpin = 12 #Pin D6
    npan = neopixel.NeoPixel(machine.Pin(panelpin, machine.Pin.OUT),64)

    def selectcolor(status):
        if status == 0:
            red = 0
            green = 20
        elif status == 1:
            red = 20
            green = 0
        elif status == 2:
            red = 0
            green = 0
        else:
            red = 25
            green = 25
        return red,green
        
    def updatestat(): 
        (red1, green1) = selectcolor(stallstat[0])
        (red2, green2) = selectcolor(stallstat[1])
        (red3, green3) = selectcolor(stallstat[2])

        for i in range(64):
            if i < 16:
                npan[i] = (red1, green1, 0)
            elif 24 <= i < 40:
                npan[i] = (red2, green2, 0)
            elif 48 <= i < 64:
                npan[i] = (red3, green3, 0)
        npan.write()
    
    #panel test
    for i in range(64):
        npan[i] = (20,20,0)
    npan.write()
    utime.sleep(1)
    for i in range(64):
        npan[i] = (0,0,0)
    npan.write()
    utime.sleep(0.5) 

    #ure setup delimiter to use regex.split
    regex = ure.compile('[:]')  

    #socket config
    s = socket.socket() 
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setblocking(0) #set to be nonblocking
    connectedclients = 0
    poss_readable = [s] #keep track the open sockets 's' being the server itself

    HOST = '192.168.4.1' #could be blank, idk really
    PORT = 2018 #reserve a port

    #bind and start server
    edgeled.value(1)
    print('!>>> Server Starting...')
    s.bind((HOST,PORT))
    s.listen(3) #set how many waiting connections to have in buffer
    edgeled.value(0)

    while stop_server != 0:
        try:
            print('!>>> Started >> Waiting for clients...')
            innerled.value(1)
            while stop_button.value() != 0 and stop_server != 0:
                #check the socket for new connections or messages
                (readable, writeable, in_error) = select.select(poss_readable, [], poss_readable, 60)
                
                for i in readable: #check and process the whole list of sockets for information
                    if i is s:
                        (clientsocket, addr) = s.accept() #establish connection with a new client
                        clientsocket.setblocking(0) 
                        poss_readable.append(clientsocket) #add to list of open sockets
                        print('!>>> Established Connection from ', addr)
                        connectedclients += 1
                    else:
                        msg = i.recv(1024) #recieve message from the current socket being checked
                        if msg:
                            #decode the incoming bytes to string and process
                            decoded = msg.decode('UTF-8')   
                            processed = regex.split(decoded)
                            
                            if processed[1] == 'open':
                                stallstat[int(processed[0]) - 1] = 0
                                print('Stall:', processed[0], '> Open')
                            elif processed[1] == 'occupied':
                                stallstat[int(processed[0]) - 1] = 1
                                print('Stall:', processed[0], '> Occupied')
                            elif processed[1] == 'closing':
                                stallstat[int(processed[0]) - 1] = 2
                                connectedclients -= 1
                                print('Stall:', processed[0], '> <<< Closing >>>')
                                if connectedclients == 0:
                                    stop_server = 0
                                    print('>>> No Stall Clients Left <<<')
                            else:
                                print('>>>> Error > Invalid Message Recieved')
                        else:
                            #close the socket to release resources for a reconnect
                            connectedclients -= 1
                            poss_readable.remove(i)
                            i.close() 
                            print('Socket Msg Error Occured. Closing Socket...')
                            if connectedclients == 0:
                                stop_server = 0
                                print('>>> No Stall Clients Left <<<')
                for i in in_error:
                    #close the socket to release resources for a reconnect
                    connectedclients -= 1
                    poss_readable.remove(i)
                    i.close()
                    if connectedclients == 0:
                        stop_server = 0
                        print('>>> No Stall Clients Left <<<')
                updatestat()
                utime.sleep(1)
            stop_server = 0
            break

        finally:
            print('Closing Server...')
            s.close()
            innerled.value(1)

    print('Checking...')
    #set leds off
    for i in range(64):
        npan[i] = (0,0,0)
    npan.write() 
    innerled.value(1)   
    edgeled.value(1)   
    s.close()
    print('Server Terminated...')


