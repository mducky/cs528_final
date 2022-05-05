import asyncio
import os
import socket
import time

import serial
from kasa import (Discover, SmartBulb, SmartDevice, SmartLightStrip, SmartPlug,
                  SmartStrip)

OUT_TIME = 10
MODE = "testing"  # TODO change to not dev
printmodes = ["testing", "dev"]
DEVICE_FILE = "devices.txt"


async def _turnoff(devices):
    """turn off passed SmartDevices"""
    if MODE == "dev":
        return
    for device in devices:
        if device.is_strip:
            for plug in device.children():
                if "light" in plug.alias:
                    await plug.turn_off()
        elif (
            device.is_plug
            or device.is_bulb
            or device.is_light_strip
            or device.is_strip_socket
        ):
            await device.turn_off()
            await device.update()
            await asyncio.sleep(0.25)
        else:
            raise Exception("Device unknown")
            break
    await asyncio.sleep(1)


async def _turnon(devices):
    """Turn on passed SmartDevices"""
    if MODE == "dev":
        return
    for device in devices:
        if device.is_strip:
            for plug in device.children():
                if "light" in plug.alias:
                    await plug.turn_on()
        elif (
            device.is_plug
            or device.is_bulb
            or device.is_light_strip
            or device.is_strip_socket
        ):
            await device.turn_on()
            await device.update()
            await asyncio.sleep(0.25)
        else:
            raise Exception(f"{device.device_type} Device unknown")
            break
    await asyncio.sleep(1)


async def _load_devices_from_file():
    """Loads devices from devices.txt in the same folder. format is IP address per line"""

    def get_ip():  # from stack overflow
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            s.connect(("10.255.255.255", 1))
            ip_address = s.getsockname()[0]
        except Exception:
            ip_address = "127.0.0.1"
        finally:
            s.close()
        return ip_address

    def compare_addr(addr, ip):  # lazy solution but likely to workout
        if addr[:6] in ip[:6]:
            return True
        return False

    address = get_ip()
    devices = []
    with open("devices.txt", "r") as device_file:
        device_addrs = device_file.read().split("\n")
        for device_addr in device_addrs:
            if len(device_addr) > 0:
                if device_addr[0] not in "#" and compare_addr(device_addr, address):
                    device = await Discover.discover_single(device_addr)
                    await device.update()
                    devices.append(device)
    return devices


async def _scan_for_devices():
    """Will scan for compatible SmartDevices on the network"""
    devices = []
    found_devices = await Discover.discover()
    for device in found_devices.values():
        await device.update()
        devices.append(device)
    return devices


async def _load_devices(loadfrom="files"):
    """Primary device loader, will first try from file then from scanning"""
    devices = []
    if DEVICE_FILE in os.listdir() and loadfrom in ["files", "all"]:
        if MODE in printmodes:
            print(f"searching {DEVICE_FILE} for devices")
        devices = await _load_devices_from_file()
    if devices == [] or loadfrom in ["all", "scan"]:
        if MODE in printmodes:
            print(f"no devices found in {DEVICE_FILE} scanning for devices")
        devices = await _scan_for_devices()
    if MODE in printmodes:
        if len(devices) > 0:
            print(f"Loaded devices: {[dev.alias for dev in devices]}")
        else:
            print(f"Loaded no devices check {DEVICE_FILE} and your network")
    for device in devices:
        if device.is_strip:
            for plug in device.children:
                devices.append(plug)
            devices.remove(device)
    return devices


def _load_arduino():
    """Finds likely arduino port and assigns it"""
    _wait_for_arduino()
    files = os.listdir("/dev")
    for folders in files:
        if "ttyAC" in folders[:-2]:
            arduino_port = folders
    arduino = serial.Serial(f"/dev/{arduino_port}")
    if MODE in printmodes or MODE == "debug":
        print(f"Arduino found at {arduino_port}")

    return arduino


async def loop(arduino, devices):
    """Loops through reading data and controlling devices"""
    off_state = True
    empty_timestamp = time.time()
    arduino.flush()
    while True:
        try:
            tasks = []
            ser_bytes = arduino.readline().decode("utf-8")
            ser_bytes = ser_bytes.rstrip()
            if (ser_bytes not in ["occupied", "empty"]) and (MODE in printmodes):
                print(ser_bytes)
            if ser_bytes == "occupied":
                empty_timestamp = time.time()
                if off_state is True:  # check if it is turned off, if so turn on.
                    if MODE in printmodes:
                        print("turning on")
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

            for task in tasks:
                await task
                tasks.remove(task)
            arduino.flush()

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


def _wait_for_arduino():
    """Helper function that waits for a port the be similar to arduino before proceeding"""
    while "ttyAC" not in [fd[:-2] for fd in os.listdir("/dev")]:
        print("no arduino waiting 10 seconds and trying again")
        time.sleep(10)


if __name__ == "__main__":
    init = asyncio.run(_init())
    time.sleep(2)
    ard = init["arduino"]
    devs = init["devices"]
    asyncio.run(loop(ard, devs))
