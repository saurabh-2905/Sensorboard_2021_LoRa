# script for visualizing the redundancy experiment data

import pickle
import matplotlib.pyplot as plt


def pdr_calc(board_data):
    len_data = len(board_data)
    pck_list = []
    num_recv = 0
    for i in range(len_data):
        pck_no = board_data[i][1]
        if pck_no < 100:
            pck_list.append(pck_no)
            if pck_no > num_recv:
                num_recv = pck_no
    pck_lost = 0
    for i in range(100):
        if i not in pck_list:
            pck_lost += 1
    return 1-pck_lost/num_recv, num_recv, pck_lost


def calc_rssi_mean(rssi_data):
    len_data = len(rssi_data)
    rssi_sum = 0
    for i in range(len_data):
        rssi_sum += rssi_data[i][4]
    return rssi_sum/len_data


def timestamp_calc(data):
    len_data = len(data)
    no_retr = 0
    retr = 0
    for i in range(len_data):
        if data[i][1] < 100:
            time_diff = data[i][3] - data[i][2]
            if time_diff > 20:
                no_retr += 1
            else:
                retr += 1
    return no_retr, retr


with open("log_red.pkl", "rb") as f:
    data = pickle.load(f)

board2_data = data[1]
redundant_data = data[2]

board2_xdata = []
board2_ydata = []
restart = 0
init_time = board2_data[0][3]
for i in range(len(board2_data)):
    val = board2_data[i][3]
    if val < 50:
        restart += 1
    if restart == 2:
        val += 2400

    board2_xdata.append(val)
    board2_ydata.append("N")

red_xdata = []
red_ydata = []
for i in range(len(redundant_data)):
    red_xdata.append(redundant_data[i][3])
    if redundant_data[i][5][0] == -1.0:
        red_ydata.append("R")
    else:
        red_ydata.append("N")

pck_list = []
for i in range(len(board2_data)):
    pck_list.append(board2_data[i][1])

pck_list_red = []
pck_list_hb = []
for i in range(len(redundant_data)):
    val = redundant_data[i][1]
    if not val == 0:
        pck_list_red.append(val)
    else:
        pck_list_hb.append(val)

print(pck_list)
b2_restart = False
for i in range(len(pck_list)):
    if b2_restart:
        pck_list[i] += 21
    if pck_list[i] == 21:
        b2_restart = True
print(pck_list)

# fig = plt.figure()
# plt.rcParams.update({'font.size': 12})
# plt.plot(red_xdata, red_ydata, '+', color="green", label="redundant node")
# plt.plot(board2_xdata, board2_ydata, 'x', color="red", label="primary node")
# plt.yticks(["N", "R"], rotation=0)
# plt.gca().invert_yaxis()
# plt.xlim([0, 3000])
# plt.ylabel("Status of the sensor nodes")
# plt.xlabel("Time in seconds")
# plt.grid(True)
# plt.legend(bbox_to_anchor=(1, 1), loc="upper left")
# plt.show()
