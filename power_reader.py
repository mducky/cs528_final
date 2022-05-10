#! /usr/bin/python

import kasa
from kasa import Discover
import time
import datetime
import asyncio
import csv
import os

DATA_FILE = "/home/pi/cs528_final/time_data.csv"

def write_time(pstrip):
    try: 
        rows = [
            "DateTime",
            "device_name",
            "energy_today",
            "energy_this_month",
            "real_time_energy",
            "on_since"
            ]
        exists = False
        if(DATA_FILE in os.listdir()):
            exists = True
        with open(DATA_FILE, "a", newline="") as csvfile:
            spamwriter = csv.DictWriter(csvfile, rows)
            if(not exists):
                spamwriter.writeheader()
            spamwriter.writerows(pstrip)
        print(str(datetime.datetime.now()))
        print("rows written")
    except Exception(e):
        print(e)

def generate_rows(device):
    data_list = []
    if(device.is_strip):
        for plug in device.children:
            data = {"DateTime": plug.time}
            data.update({"device_name": plug.alias})
            data.update({"energy_today": plug.emeter_today})
            data.update({"energy_this_month": plug.emeter_this_month})
            data.update({"real_time_energy": plug.emeter_realtime})
            data.update({"on_since": plug.on_since})
            data_list.append(data)
    else:
        data = {}
        data.update({f"Plug0_today": device.emeter_today})
        data.update({f"Plug0_this_month": device.emeter_this_month})
        data.update({f"Plug0_real_time": device.emeter_realtime})
        data_list.append(data)
    return data_list


async def _scan_for_devices():
    """Will scan for compatible SmartDevices on the network"""
    devices = []
    found_devices = await Discover.discover()
    for device in found_devices.values():
        await device.update()
        if(device.is_strip):
            for plug in device.children:
                await plug.update()
        devices.append(device)
    return devices

async def main():
    devices = await _scan_for_devices()
    try:
        for device in devices:
            print(f"working with device: {device.alias}")
            data = generate_rows(device)
            write_time(data)
    except KeyboardInterrupt:
        print("Keyboard interrupt, printing current data")

    except Exception(e):
        print(e)

if __name__ == "__main__":
    asyncio.run(main())
