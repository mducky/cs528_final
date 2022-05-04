import asyncio
import os
import time

import serial
from kasa import (Discover, SmartBulb, SmartDevice, SmartLightStrip, SmartPlug,
                  SmartStrip)

OUT_TIME = 10
MODE = "dev"  # TODO change to not dev


async def _turnoff(devices):
    """turn off passed SmartDevices"""
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
            raise Exception("Device unknown")
            break
        await device.update()


async def _turnon(devices):
    """Turn on passed SmartDevices"""
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
            raise Exception("Device unknown")
            break
        await device.update()


def _load_devices_from_file():
    """Loads devices from devices.txt in the same folder. format is IP address per line"""
    devices = []
    with open("devices.txt", "r") as device_file:
        device_addrs = device_file.read()
        device_addr_list = device_addrs.split("\n")
        for device_addr in device_addr_list:
            if len(device_addr) > 0:
                if device_addr[0] not in "#":
                    devices.append(SmartDevice(device_addr))
    return devices


def _scan_for_devices():
    """Will scan for compatible SmartDevices on the network"""
    print("scan for devices is not implemented")
    devices = asyncio.run(Discover.discover())
    return list(devices.values())


def _load_devices():
    """Primary device loader, will first try from file then from scanning"""
    devices = []
    if "devices.txt" in os.listdir():
        devices = _load_devices_from_file()
    if devices == []:
        _scan_for_devices()
    for device in devices:
        if device.is_strip:
            devices.remove(device)
            for plug in device.children():
                devices.append(plug)
    return devices


def _load_arduino():
    """Finds likely arduino port and assigns it"""
    files = os.listdir("/dev")
    for folders in files:
        if "ttyAC" in folders[:-2]:
            arduino_port = folders
    arduino = serial.Serial(f"/dev/{arduino_port}")
    return arduino


async def loop(arduino, devices):
    """Loops through reading data and controlling devices"""
    off_state = True
    empty_timestamp = time.time()
    while True:
        try:
            ser_bytes = arduino.readline().decode("utf-8")
            ser_bytes = ser_bytes.rstrip()
            if ser_bytes == "Training":
                print(ser_bytes)
            if ser_bytes == "occupied":  # if the room is occupied,
                empty_timestamp = time.time()
                if off_state is True:  # check if it is turned off, if so turn on.
                    print("turning on")
                    off_state = False
                    await _turnon(devices)
            current_time = time.time()
            # if it has been OUT_TIME seconds and is in the onstate, turn off and set the state.
            if off_state is False and (current_time - OUT_TIME > empty_timestamp):
                print("turning off")
                off_state = True
                await _turnoff(devices)
                empty_timestamp = time.time()
            # time.sleep(0.5)  # sleep 1 second
            arduino.flush()
        except KeyboardInterrupt:
            print("\nkeyboard interrupt. Stopping")
            break
        except Exception as e:
            print(e)
            raise e
            break


def _init():
    """loads devices and the arduino for easy use later"""
    devices = _load_devices()
    arduino = _load_arduino()
    return {"arduino": arduino, "devices": devices}


if __name__ == "__main__":
    init = _init()
    ard = init["arduino"]
    devs = init["devices"]
    asyncio.run(loop(ard, devs))
