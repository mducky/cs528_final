import serial
from kasa import SmartDevice, SmartStrip, SmartBulb, SmartPlug, SmartLightStrip
import asyncio
import time
import os


OUT_TIME = 10
MODE = "dev"  # TODO change to not dev

async def turnoff(devices):
    if MODE == "dev":
        return
    for device in devices:
        if device.is_strip:
            for plug in device.children():
                if "light" in plug.alias:
                    await plug.turn_off()
        elif device.is_plug or device.is_bulb or device.is_light_strip:
            await device.turn_off()
        else:
            #raise Exception("Device unknown")
            print("unknown device")
            break
        await device.update()

async def turnon(devices):
    if MODE == "dev":
        return
    for device in devices:
        if device.is_strip:
            for plug in device.children():
                if "light" in plug.alias:
                    await plug.turn_on()
        elif device.is_plug or device.is_bulb or device.is_light_strip:
            await device.turn_on()
        else:
             print("unknown device")
             break
             # raise Exception("Device unknown")
        await device.update()

def load_devices_from_file():
    devices = []
    with open("devices.txt", "r") as device_file:
        device_addrs = device_file.read()
        device_addr_list = device_addrs.split("\n")
        for device_addr in device_addr_list:
            if len(device_addr) > 0:
                if (device_addr[0] not in "#"):
                    devices.append(SmartDevice(device_addr))
    return devices

def scan_for_devices():
    print("scan for devices is not implemented")

def load_devices():
    devices = []
    if "devices.txt" in os.listdir():
        devices = load_devices_from_file()
    if devices == []:
        scan_for_devices()
    for device in devices:
        if device.is_strip:
            devices.remove(device)
            for plug in device.children():
                devices.append(plug)
    return devices

def load_arduino():
    files = os.listdir("/dev")
    for folders in files:
        if("ttyAC" in folders[:-2]):
            arduino_port = folders
    arduino = serial.Serial(f"/dev/{arduino_port}")
    return arduino

def readArduino(arduino):
    raw = arduino.readline()
    decode = raw.decode('utf-8')
    strip = decode.rstrip()
    return strip

async def loop(arduino, devices):
    off_state = True
    empty_timestamp = time.time()
    while True:
        try:
            ser_bytes = arduino.readline().decode('utf-8')
            ser_bytes = ser_bytes.rstrip()
            if(ser_bytes == "Training"):
                print(ser_bytes)
            if(ser_bytes == "occupied"):  # if the room is occupied,
                empty_timestamp = time.time()
                if(off_state == True):  # check if it is turned off, if so turn on.
                    print("turning on")
                    off_state = False
                    await turnon(devices)
            current_time = time.time()
            # if it has been OUT_TIME seconds and is in the onstate, turn off and set the state.
            if (off_state == False and (current_time - OUT_TIME > empty_timestamp)):
                print("turning off")
                off_state = True
                await turnoff(devices)
                empty_timestamp = time.time()
            # time.sleep(0.5)  # sleep 1 second
            arduino.flush()
        except KeyboardInterrupt:
            print("\nkeyboard interrupt. Stopping")
            break
        except Exception as e:
            print(e)
            break

def __init__():
    dev = load_devices()
    ard = load_arduino()
    return {"arduino": ard, "devices": dev}

if __name__ == "__main__":
    init = __init__()
    arduino = init["arduino"]
    devices = init["devices"]
    asyncio.run(loop(arduino,devices))
