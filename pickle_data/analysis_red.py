# script for visualizing the redundancy experiment data

import pickle
import matplotlib.pyplot as plt

# load data
with open("log_red2.pkl", "rb") as f:
    data = pickle.load(f)


def calc_normal_pdr(data):
    board1_data = data
    pck_list_b1 = []
    for i in range(len(board1_data)):
        val = board1_data[i][1]
        if val < 100:
            pck_list_b1.append(val)
    return len(pck_list_b1)/100


# non faulty boards pdr + print
pdr_b1 = calc_normal_pdr(data[0])
print("(PDR Board1: " + str(pdr_b1) + ")")
pdr_b3 = calc_normal_pdr(data[3])
print("PDR Board2: " + str(pdr_b3))

# PB data
board2_data = data[1]

# RB data
redundant_data = data[2]

# create PB packet list for PDR calc
pck_list = []
for i in range(len(board2_data)):
    pck_list.append([board2_data[i][1], board2_data[i][3]])

# create RB packet list for PDR calc
pck_list_red = []
pck_list_hb = []
for i in range(len(redundant_data)):
    no = redundant_data[i][5][0]
    val = [redundant_data[i][1], redundant_data[i][3]]
    if not no == -1.0:
        pck_list_red.append(val)
    else:
        pck_list_hb.append(val)

pl_1 = []
pl_2 = []
pr = pck_list_red
r = False
for i in range(len(pck_list)):
    if not r:
        pl_1.append(pck_list[i])
    else:
        pkt, time = pck_list[i]
        pl_2.append([pkt, time+2400])
    if pck_list[i][0] == 20:
        r = True

for i in range(len(pr)):
    pr[i][0] += 20

for i in range(len(pl_2)):
    pl_2[i][0] += 67

r = False
for i in range(len(pr)):
    if r:
        pr[i][0] += 47
    if pr[i][0] == 67:
        r = True

print(pr)

# plot data (or don't)
plot = 0
if plot:
    # create PB plot data
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

    # create RB plot data
    red_xdata = []
    red_ydata = []
    for i in range(len(redundant_data)):
        red_xdata.append(redundant_data[i][3])
        if redundant_data[i][5][0] == -1.0:
            red_ydata.append("R")
        else:
            red_ydata.append("N")
    fig = plt.figure()
    plt.rcParams.update({'font.size': 12})
    plt.plot(red_xdata, red_ydata, '+', color="green",
             label="redundant node")
    plt.plot(board2_xdata, board2_ydata, 'x', color="red",
             label="primary node")
    plt.yticks(["N", "R"], rotation=0)
    plt.gca().invert_yaxis()
    plt.xlim([0, 3000])
    plt.ylabel("Status of the sensor nodes")
    plt.xlabel("Time in seconds")
    plt.grid(True)
    plt.legend(bbox_to_anchor=(1, 1), loc="upper left")
    plt.show()
