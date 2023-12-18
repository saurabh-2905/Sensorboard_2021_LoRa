# coding=utf-8
# Script for analysing and plotting the data of Experiment 2 (Sensor Fault and Sensor Value Fault)


import pickle
import matplotlib.pyplot as plt
import numpy as np


###files
#for no noise: log_exp_svf_re1.pkl
# for actual: log_exp_svf1.pkl
# load data for sensor value fault
with open("log_exp_gf1.pkl", "rb") as f:
    data = pickle.load(f)

### check if all packets belong to same board
### PB
pb_id = 0
rb_id = 0
for d_i, d in enumerate(data[1]):
    if d_i == 0:
        pb_id = d[1]
        print('PB Id:',pb_id) 
    assert(data[1][0][1]==d[1])
### RB
for d_i, d in enumerate(data[3]):
    if d_i == 0:
        rb_id = d[1]
        print('RB Id:', rb_id)
    assert(data[3][0][1]==d[1])

### filter hb signals
hb_pkts = []
data_pkts = []
board_index = [1,3]

for i in board_index:
    each_board = data[i]
    for d in each_board:
        #print(d[0][0])
        if d[0][0] == -1:
            hb_pkts += [d]
        else:
            data_pkts += [d]
            

#### Plotting timing diag ####
primary_plotdata = []
redundant_plotdata = []

for d in data_pkts:
    plotdata = [d[2], d[4], 0]   ### use the pkt id and tx time for plotting
    if d[1] == pb_id:
        if d[0][0] == 1000.0:
            plotdata[2] = 1
        primary_plotdata += [plotdata]
    elif d[1] == rb_id:
        redundant_plotdata += [plotdata]

y_correct_pb = []
y_faulty_pb = []
x_correct_pb = []
x_faulty_pb = []

x_rb = []
y_rb = []

for d in primary_plotdata:
    if d[-1] == 0:
        y_correct_pb += [10]      
        x_correct_pb += [d[1]]
    else:
        y_faulty_pb += [10]
        x_faulty_pb += [d[1]]
        
for d in redundant_plotdata:
    x_rb += [d[1]]
    y_rb += [8]


fig = plt.subplots(figsize =(20, 8))

# define x ticks
xticks = np.arange(0, 1800, 20)

plt.scatter(x_correct_pb, y_correct_pb, label='data')
plt.scatter(x_rb, y_rb, label='backup data')
plt.ylim((7,11))
plt.grid(True)
#plt.xticks(xticks, fontsize=20, rotation=90)
plt.xticks(xticks, fontsize=20)
plt.xlabel('Time (seconds)', fontsize = 25)
plt.ylabel('Packet reception of resp. boards', fontsize = 25)
plt.yticks([10,8],['Primary Board', 'Redundant Board'], rotation=90, fontsize=20)
plt.legend(fontsize=20)
ax = plt.gca().get_xticklabels()
plt.setp(ax, visible=False)
plt.setp(ax[::2], visible=True)

plt.show()
