# script for plotting data

import pickle
import matplotlib.pyplot as plt
from datetime import datetime

with open("log_exp_red_re3.pkl", "rb") as f:
    data = pickle.load(f)

pb = data[1]
rb = data[3]

# get relevant data from primary board
pb_pn = []
pb_tx = []
pb_retx = []
pb_rx = []
pb_st = []
pb_co2 = []
pb_tx_plt = []
for i in range(len(pb)):
    pb_pn.append(pb[i][2])
    pb_tx.append(pb[i][4])
    pb_retx.append(pb[i][5])
    temp = str(pb[i][6][0]) + "-" + str(pb[i][6][1]) + "-" + str(pb[i][6][2]) + "T" + str(pb[i][6][3]) + ":" + str(pb[i][6][4]) + ":" + str(pb[i][6][5])
    ts = datetime.strptime(temp, "%Y-%m-%dT%H:%M:%S")
    pb_rx.append(ts)
    st = pb[i][0][13]
    if st == 0:
        pb_st.append("Sensor\nworking")
    elif st == 1:
        pb_st.append("Sensor not\nworking")
    pb_co2.append(pb[i][0][0])
    pb_tx_plt.append("P")

# get relevant data from redundant board
rb_pn = []
rb_tx = []
rb_retx = []
rb_rx = []
rb_rx_co2 = []
rb_st = []
rb_co2 = []
rb_tx_plt = []
for i in range(len(rb)):
    rb_pn.append(rb[i][2])
    rb_tx.append(rb[i][4])
    rb_retx.append(rb[i][5])
    temp = str(rb[i][6][0]) + "-" + str(rb[i][6][1]) + "-" + str(rb[i][6][2]) + "T" + str(rb[i][6][3]) + ":" + str(rb[i][6][4]) + ":" + str(rb[i][6][5])
    ts = datetime.strptime(temp, "%Y-%m-%dT%H:%M:%S")
    rb_rx.append(ts)
    rb_st.append(rb[i][0][13])
    if not rb[i][0][0] == -1.0:
        rb_co2.append(rb[i][0][0])
        rb_rx_co2.append(ts)
        rb_tx_plt.append("P")
    else:
        rb_tx_plt.append("H")

num_pkt_pb = pb_pn[len(pb_pn)-1]+1

# remove double packet numbers
pb_pn_reduced = []
for i in range(len(pb_pn)):
    if not pb_pn[i] in pb_pn_reduced:
        pb_pn_reduced.append(pb_pn[i])
num_pkt_rx = len(pb_pn_reduced)
pdr_pb = num_pkt_rx/num_pkt_pb

# plt settings
plt.rcParams.update({'font.size': 14})
plt.rcParams["font.family"] = "Times New Roman"

# plot of sensor status, plus messages
fig1, (ax1, ax2, ax3) = plt.subplots(3, 1)
ax1.set_title("Primary Board")
ax1.set_xlabel("Time")
ax1.plot(pb_rx, pb_tx_plt, "+", color="green", label="Primary Board")
ax1.set_yticklabels(["Packet\nreceived"])
ax2.set_title("Redundant Board")
ax2.plot(rb_rx, rb_tx_plt, "+", color="red", label="Redundant Board")
ax2.set_yticklabels(["Heartbeat\nreceived", "Packet\nreceived"])
ax3.set_title("Sensorstatus (CO2 Sensor)")
ax3.plot(pb_rx, pb_st, "+", label="Sensorstatus")
ax3.set_xlabel("Time")

# plot of co2 data
fig2, ax4 = plt.subplots(1, 1)
ax4.set_title("CO2 Sensordata")
ax4.plot(pb_rx, pb_co2, "+", label="Primary Board Data")
ax4.plot(rb_rx_co2, rb_co2, "+", label="Redundant Board Data")
ax4.set_xlabel("Time")
ax4.set_ylabel("CO2 in ppm")
ax4.legend(bbox_to_anchor=(0.5, -0.4), ncol=2, loc="lower center",  fontsize=11)
fig2.tight_layout()

plt.show()
