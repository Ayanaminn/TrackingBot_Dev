'''
interface with arduino board
communicate with serial port and send control output

'''

import serial
import time
import serial.tools.list_ports



def get_ports():
    # get a list of all the available serial ports
    # see https://pyserial.readthedocs.io/en/latest/tools.html
    arduino_ports = [
        port.device
        for port in serial.tools.list_ports.comports()  # list comprehension
        if 'Arduino' in port[1]  # may need tweaking to match new arduinos
    ]
    return arduino_ports


def connect_ports():
    arduino_ports = get_ports()
    print(arduino_ports)
    global activeDevice, portOpen

    if len(arduino_ports) == 1:
        print(f'Detected arduino device on port {arduino_ports[0]}')
        # port = 'COM'+ input('> please type port number: ')
        try:
            # portOpen = True
            activeDevice = serial.Serial(arduino_ports[0], 9600, timeout=1)
            activeDevice.isOpen()
            time.sleep(0.5)
            print(f'Connected to port {arduino_ports[0]}!')
            device_control(activeDevice)
        except Exception as e:
            print(e)
    elif len(arduino_ports) >= 1:
        for port in arduino_ports:
            print(f'Detected more than one arduino device\n'
                  f'{port}')
        retry = input('Multiple device not supported now.\n'
                      'Do you want to retry? Y/N : ')
        if retry == 'Y':
            get_ports()
            connect_ports()
        elif retry == 'N':
            print('Exit')
            return None
    elif not arduino_ports:
        retry = input('No arduino device found.\n'
                      'Do you want to retry? Y/N : ')
        if retry == 'Y':
            get_ports()
            connect_ports()
        elif retry == 'N':
            print('Exit')
            return None
    else:
        raise Exception('Error.Can not get list of ports.')


def device_control(device):
    # add status verify to avoid confilct/timeout/infinate loops of signals
    # e.g.only accept on when status is off
    # or do it in GUI part by enable/disable buttons
    while True:
        datafromUser = read_data()
        # to encode the string before sending it.
        # Arduino works with bytes, therefore must transform a string to bytes.

        if datafromUser == 'on':
            device.write(b'1')
            print("LED  turned ON")
        elif datafromUser == 'off':
            device.write(b'0')
            print("LED turned OFF")
        elif datafromUser == 'open':
            device.write(b'2')
            print("LED blink")
        elif datafromUser == 'close':
            print('Close connection...')
            time.sleep(0.5)
            disconnect(device)
            break


def read_data():
    data = input('> please give your command: ')
    return data


def disconnect(device):
    try:
        device.close()
    except Exception as e:
        print(e)
    if not device.isOpen():
        print('Connection with port closed')
        # print(device.name,device.isOpen())


connect_ports()
