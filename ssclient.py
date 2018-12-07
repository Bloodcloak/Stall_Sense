import machine
import utime

#status led
innerled = machine.Pin(16, machine.Pin.OUT) #occupied status
edgeled = machine.Pin(2, machine.Pin.OUT) #connected
innerled.value(1)
edgeled.value(1)

while True:
    #define vars
    occupied_button = machine.Pin(5, machine.Pin.IN, machine.Pin.PULL_UP) #Pin D1
    open_button = machine.Pin(4, machine.Pin.IN, machine.Pin.PULL_UP) # Pin D2
    prev_state = 'open'
    innerled.value(1)

    outputpin = machine.Pin(12, machine.Pin.OUT) #Pin D6

    while True:
        if occupied_button.value() == 0: #when pressed
            if prev_state != 'occupied':
                outputpin.value(1)    
                innerled.value(0)
                print('occupied')
                prev_state = 'occupied'

            if open_button.value() == 0: #when pressed
                if prev_state != 'open':
                    outputpin.value(0)    
                    innerled.value(1)
                    print('open')
                    prev_state = 'open'
                
            utime.sleep(0.5)