import serial 
import threading
import pickle

def cb():
    global timer_done
    timer_done = True

timer_done = False
with serial.Serial("COM6", 115200, timeout=10.0) as ser:
    threading.Timer(120, cb).start()
    all_values = []
    while(True):
        line = ser.readline().decode("utf-8")
        if line[:2] == '##'and line[-4:-2]=='//':
            # print(line[2:-4], len(line[2:]))
            current_val = line[3:-5]   #### remove brackets and identifiers for start and end of line
            actual_val = current_val.split(',')
            for num, x in enumerate(actual_val):
                if num < 12:
                    actual_val[num] = float(x)
                else: 
                    actual_val[num] = int(x)
            print(actual_val)
            all_values += [actual_val]

            if timer_done:
                with open('sensor_values.pkl', 'wb') as f:
                    pickle.dump(all_values, f)
                    threading.Timer(120, cb).start()
                timer_done = False

        