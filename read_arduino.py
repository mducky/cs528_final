import serial
from kasa import SmartDevice, SmartStrip, SmartBulb, SmartPlug, SmartLightStrip
import asyncio
import time

arduino = object
off_state = {}
empty_timestamp = time.time()
devices = []  # KASA smart devices
out_time = 10  # seconds

def turnoff(device):
    if device.is_strip():
        for plug in device.children():
            if "light" in plug.alias:
                plug.turn_off()
    elif device.is_plug() or device.is_bulb() or device.is_light_strip():
        device.turn_off()
    else:
        raise Exception("Device unknown")
    device.update()

def turnon(device):
    if device.is_strip():
        for plug in device.children():
            if "light" in plug.alias:
                plug.turn_on()
    elif device.is_plug() or device.is_bulb() or device.is_light_strip():
        device.turn_on()
    else:
        raise Exception("Device unknown")
    device.update()

def load_devices_from_file()
    
    with open("devices.txt", "r") as device_file:
        device_addrs = device_file.read()
        device_addr_list = device_addrs.split("\n")
        for device_addr in device_addr_list:
            if (!device_addr[0] == "#"):
                devices.append(SmartDevice(device_addr))

def scan_for_devices():
    pass

def load_devices():
    if "devices.txt" in os.listdir():
        load_devices_from_file()
    if devices == []:
        scan_for_devices()
    for device in devices:
        if device.is_strip():
            devices.remove(device)
            for plug in device.children():
                devices.append(plug)

def load_arduino():
    arduino = serial.Serial(f'/dev/ttyACA0')


def loop():
    for device in devices:
        ser_bytes = arduino.readline().decode('utf-8')
        print(ser_bytes)
        if(ser_bytes == "occupied"):  # if the room is occupied,
            if(off_state == 1):  # check if it is turned off, if so turn on.
                turnon(device)
                off_state[device] = 0
        if(ser_bytes == "empty"):  # if the room is empty record time
            empty_timestamp = time.time()
        current_time = time.time()
        # if it has been 30 minutes and is in the offstate, turn off and set the state.
        if (off_state == 1 and (current_time - out_time > empty_timestamp)):
            turnoff(device)
            off_state[device] = 1
    time.sleep(1)  # sleep 1 second


def __init__():
    load_devices()
    load_arduino()

if __name__ == "__main__":
    __init__()
    while True:
        loop()

