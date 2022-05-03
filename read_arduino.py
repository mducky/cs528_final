import serial
import time
import avs


# alexa = avs.new()
off_state = {}
empty_timestamp = time.time()
arduino = {}
rooms = {}
out_time = 10

def turnoff(room):
    if room in rooms:
        outlet = rooms[room]
    else:
        raise Exception("Room not found")
    outlet_control(outlet)

def turnon(room):
    if room in rooms:
        outlet = rooms[room]
    else:
        raise Exception("Room not found")
    outlet_control(outlet)


def outlet_control(outlet):
    print(outlet)
    # TODO implement alexa control of outlet
"""def outlet_control(outlet):
    if type(outlet) == str:
        alexa.lambda({
            alexa.toggle(outlet)
            })
    elif type(outlet) == list:
        for plug in outlet:
            alexa.lambda({
                alexa.toggle(plug)
                })
    else:
        raise Exception("invalid outlet input")
"""

def load_rooms():
    room_data = {}
    with open("rooms.txt", "r") as room_file:
        room_file_data = room_file.read()
        room_list = room_file_data.split("\n")
        for room in room_list:
            if room[0] == "#":
                break
            room_split = room.split(" ")
            room_data[room_split[0]] = [x for x in room_split[1:]]
    return room_data

def load_arduino(rooms):
    for room in enumerate(rooms):
        arduino[room[1]] = serial.Serial(f'/dev/ttyACM{room[0]}')


if __name__ == "__main__":
    rooms = load_rooms()
    while True:
        for room in rooms:
            ser_bytes = arduino[room].readline().decode('utf-8')
            print(ser_bytes)
            if(ser_bytes == "occupied"):  # if the room is occupied,
                if(off_state == 1):  # check if it is turned off, if so turn on.
                    turnon(room)
                    off_state[room] = 0
            if(ser_bytes == "empty"):  # if the room is empty record time
                empty_timestamp = time.time()
            current_time = time.time()
            # if it has been 30 minutes and is in the offstate, turn off and set the state.
            if (off_state == 1 and (current_time - out_time > empty_timestamp)):
                turnoff(room)
                off_state[room] = 1
        time.sleep(1)  # sleep 1 second


