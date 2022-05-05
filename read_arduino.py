import asyncio
import os
import time

import serial
from kasa import (Discover, SmartBulb, SmartDevice, SmartLightStrip, SmartPlug,
                  SmartStrip)

OUT_TIME = 10
MODE = "testing"  # TODO change to not dev


async def _turnoff(devices):
    """turn off passed SmartDevices"""
    if MODE == "dev":
        return
    for device in devices:
        #await device.update()
        if device.is_strip:
            for plug in device.children():
                if "light" in plug.alias:
                    await plug.turn_off()
        elif device.is_plug or device.is_bulb or device.is_light_strip or device.is_strip_socket:
            await device.turn_off()
        else:
            raise Exception("Device unknown")
            break
        #await device.update()


async def _turnon(devices):
    """Turn on passed SmartDevices"""
    if MODE == "dev":
        return
    for device in devices:
        #await device.update()
        if device.is_strip:
            for plug in device.children():
                if "light" in plug.alias:
                    await plug.turn_on()
        elif device.is_plug or device.is_bulb or device.is_light_strip or device.is_strip_socket:
            await device.turn_on()
        else:
            raise Exception(f'{device.device_type} Device unknown')
            break
        #await device.update()


async def _load_devices_from_file():
    """Loads devices from devices.txt in the same folder. format is IP address per line"""
    devices = []
    with open("devices.txt", "r") as device_file:
        device_addrs = device_file.read()
        device_addr_list = device_addrs.split("\n")
        for device_addr in device_addr_list:
            if len(device_addr) > 0:
                if device_addr[0] not in "#":
                    device = await Discover.discover_single(device_addr)
                    await device.update()
                    devices.append(device)
    print(f'Loaded devices: {[dev.alias for dev in devices]}')
    return devices


async def _scan_for_devices():
    """Will scan for compatible SmartDevices on the network"""
    devices = []
    found_devices = await Discover.discover()
    for device in found_devices.values():
        await device.update()
        devices.append(device)
    return devices


async def _load_devices():
    """Primary device loader, will first try from file then from scanning"""
    devices = []
    if "devices.txt" in os.listdir():
        devices = await _load_devices_from_file()
    if devices == []:
        devices = await _scan_for_devices()
    for device in devices:
        if device.is_strip:
            for plug in device.children:
                devices.append(plug)
            devices.remove(device)
    return devices


def _load_arduino():
    """Finds likely arduino port and assigns it"""
    files = os.listdir("/dev")
    for folders in files:
        if "ttyAC" in folders[:-2]:
            arduino_port = folders
    arduino = serial.Serial(f"/dev/{arduino_port}")
    return arduino

async def create_power_task(func):
    return asyncio.create_task(func)



async def loop(arduino, devices):
    """Loops through reading data and controlling devices"""
    off_state = True
    empty_timestamp = time.time()
    mainloop = asyncio.get_event_loop()
    loopcount = 0
    while True:
        try:
            tasks = []
            ser_bytes = arduino.readline().decode("utf-8")
            ser_bytes = ser_bytes.rstrip()
            if ser_bytes == "Training" or loopcount == 0:
                print(ser_bytes)
            if ser_bytes == "occupied":  # if the room is occupied,
                empty_timestamp = time.time()
                if off_state is True:  # check if it is turned off, if so turn on.
                    print(f"turning on")
                    off_state = False
                    ontask = asyncio.create_task(_turnon(devices))
                    tasks.append(ontask)
            current_time = time.time()
            # if it has been OUT_TIME seconds and is in the onstate, turn off and set the state.
            if off_state is False and (current_time - OUT_TIME > empty_timestamp):
                print("turning off")
                off_state = True
                offtask = asyncio.create_task(_turnoff(devices))
                tasks.append(offtask)
                empty_timestamp = time.time()
            # time.sleep(0.5)  # sleep 1 second
            for task in tasks:
                await task
                for dev in devices:
                    await dev.update()
            arduino.flush()
            loopcount = (loopcount + 1) % 15

        except KeyboardInterrupt:
            print("\nkeyboard interrupt. Stopping")
            break
        except Exception as e:
            print(e)
            raise e
            break


async def _init():
    """loads devices and the arduino for easy use later"""
    devices = await _load_devices()
    arduino = _load_arduino()
    return {"arduino": arduino, "devices": devices}


if __name__ == "__main__":
    init = asyncio.run(_init())
    ard = init["arduino"]
    devs = init["devices"]
    asyncio.run(loop(ard, devs))
