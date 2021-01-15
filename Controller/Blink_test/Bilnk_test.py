'''
interface with arduino board
communicate with serial port and send control output

'''

import serial
import time
import serial.tools.list_ports

# ports = list(serial.tools.list_ports.comports())
# for p in ports:
#     if 'Arduino' in p[1]:
#         print(p[0])
#         print(p[1])
#     else:
#         pass
 def get_ports():

    # get all the available serial ports
    # see https://pyserial.readthedocs.io/en/latest/tools.html
    arduino_ports = [
        port.device
        for port in serial.tools.list_ports.comports() # list comprehension
        if 'Arduino' in port[1]  # may need tweaking to match new arduinos
    ]

    if len(arduino_ports) == 1:
        print(arduino_ports[0])

        # port = 'COM'+ input('> please type port number: ')
        # try:
        #     arduino = serial.Serial(arduino_ports[0],9600)
        #     time.sleep(1)
        #     print(f'Connected to port {arduino_ports}!')
        # except Exception as e:
        #     print(e)
    elif len(arduino_ports) == 1:
        print('Please the right port')
    elif not arduino_ports:
        raise Exception('No Arduino device found')

#
# while True:
#
#     datafromUser = input('> please give your command: ')
#     # to encode the string before sending it.
#     # Arduino works with bytes, therefore must transform a string to bytes.
#     try:
#         if datafromUser == 'on':
#             arduino.write(b'1')
#             print("LED  turned ON")
#         elif datafromUser == 'off':
#             arduino.write(b'0')
#             print("LED turned OFF")
#         elif datafromUser == 'pulse':
#             arduino.write(b'2')
#             print("LED blink")
#         else:
#             print('No such command')
#     except Exception as e:
#         print(e)
