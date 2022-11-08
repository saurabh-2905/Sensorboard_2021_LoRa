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
        pck_list_b1.append(val)
    return len(pck_list_b1)/pck_list_b1[len(pck_list_b1)-1]


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

p_hb = pck_list_hb

# calculate pdr for faulty board alone
pdr_list = []
for i in range(len(pl_1)):
    pdr_list.append(pl_1[i][0])
for i in range(len(pl_2)):
    pdr_list.append(pl_2[i][0])

pdr_faulty = len(pdr_list)/pdr_list[len(pdr_list)-1]

# calculate pdr for faulty board with redundant board
pdr_list2 = []
for i in range(len(pr)):
    pdr_list2.append(pr[i][0])
pdr_list2 += pdr_list
pdr_list2.sort()
pdr_red = len(pdr_list2)/pdr_list2[len(pdr_list2)-1]

print("PDR faulty: " + str(pdr_faulty))
print("PDR redundancy: " + str(pdr_red))

# create plot data
# create x and y data for faulty board
faulty_xdata = pl_1 + pl_2
faulty_ydata = []
for i in range(len(faulty_xdata)):
    faulty_xdata[i] = faulty_xdata[i][1]
    faulty_ydata.append("Tx")

# create x and y data for hb signals
hb_xdata = pck_list_hb
hb_ydata = []
for i in range(len(hb_xdata)):
    hb_xdata[i] = hb_xdata[i][1]
    hb_ydata.append("NoTx")

# create x and ydata for redundancy board data msgs,
# as well as x and y data for faulty board, when it is
# not working
red_xdata = pr
red_ydata = []
faulty2_xdata = []
faulty2_ydata = []
for i in range(len(red_xdata)):
    red_xdata[i] = red_xdata[i][1]
    red_ydata.append("Tx")
    faulty2_xdata.append(red_xdata[i])
    faulty2_ydata.append("NoTX")

# plot data (or don't)
plot = 1
if plot:
    plt.rcParams.update({'font.size': 12})

    fig, (ax1, ax2) = plt.subplots(2, 1)
    ax1.grid(which='both')
    ax1.set_xlim(0, 3000)
    ax1.set_xlabel("time in seconds")
    ax1.set_ylabel("primary board")
    ax1.plot(faulty_xdata, faulty_ydata, '+', color="green",
             label="transmission")
    ax1.plot(faulty2_xdata, faulty2_ydata, '+', color="red",
             label="no transmission")
    ax1.legend(loc="center right")
    ax1.invert_yaxis()

    ax2.grid(which='both', zorder=0)
    ax2.set_xlim(0, 3000)
    ax2.set_xlabel("time in seconds")
    ax2.set_ylabel("redundant board")
    ax2.plot(hb_xdata, hb_ydata, 'x', color="red",
             label="heartbeat transmission")
    ax2.plot(red_xdata, red_ydata, 'x', color="green",
             label="transmission")
    ax2.legend(loc="center right")

    plt.yticks(["NoTx", "Tx"], rotation=0)
    plt.show()
