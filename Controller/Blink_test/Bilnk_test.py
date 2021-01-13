'''
interface with arduino board
communicate with serial port and send control output

'''

import serial
import time

port = 'COM'+ input('> please type port number: ')
try:
    arduino = serial.Serial(port,9600)
    time.sleep(1)
    print('Connected!')
except Exception as e:
    print(e)


while True:

    datafromUser = input('> please give your command: ')
    # to encode the string before sending it.
    # Arduino works with bytes, therefore must transform a string to bytes.
    try:
        if datafromUser == 'on':
            arduino.write(b'1')
            print("LED  turned ON")
        elif datafromUser == 'off':
            arduino.write(b'0')
            print("LED turned OFF")
        elif datafromUser == 'pulse':
            arduino.write(b'2')
            print("LED blink")
        else:
            print('No such command')
    except Exception as e:
        print(e)
