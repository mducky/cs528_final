import serial

arduino = serial.Serial('/dev/ttyACM0')
while True:
    ser_bytes = arduino.readline().decode('utf-8')
    print(ser_bytes)
    if(ser_bytes == "occupied"):
    	timer.reset()
    if(ser_bytes == "empty"):
    	if(timer.started == False):
    		timer.start()
    if timer > 60:
    	turnitalloff()
    
