# coding=utf-8
# Script for analysing and plotting the data of Experiment 1 (Redundant Board Vs. Normal Board)

# import pickle
# import matplotlib.pyplot as plt

# # load data for sensor fault
# with open("log_exp_sf1.pkl", "rb") as f:
#     data = pickle.load(f)


# print('length of the data from each board:', len(data[0]), len(data[1]), len(data[2]), len(data[3]))

# data_format = ('payload', 'board_id', 'pkt_no', 'RSSI', 'Tx_time', 'reTx_time', 'rx_time' )

# ### Number of Packets received by primary board and redundant board
# print('Primary Board:', len(data[1]))
# print('Redundant Board:', len(data[3]))

# ### check if all packets belong to same board
# ### PB
# pb_id = 0
# rb_id = 0
# for d_i, d in enumerate(data[1]):
#     if d_i == 0:
#         pb_id = d[1]
#         print('PB Id:',pb_id) 
#     assert(data[1][0][1]==d[1])
# ### RB
# for d_i, d in enumerate(data[3]):
#     if d_i == 0:
#         rb_id = d[1]
#         print('RB Id:', rb_id)
#     assert(data[3][0][1]==d[1])


# #### Checking the confidence interval (40s)
# data_all = data[1] + data[3]
# for d in data_all:
#     if d[5]-d[4]>40:
#         #print(d[1],d[4:6], d[5]-d[4])
#         print('packets outside conf. interval', d)


# ### filter hb signals
# hb_pkts = []
# data_pkts = []
# board_index = [1,3]

# for i in board_index:
#     each_board = data[i]
#     for d in each_board:
#         #print(d[0][0])
#         if d[0][0] == -1:
#             hb_pkts += [d]
#         else:
#             data_pkts += [d]

# ### PRR of the sesnor node (PB+RB)
# packet_num = []
# num_pkts_sent = 0 
# num_pkts_rx = 0
# for d in data_pkts:
#     if d[2] not in packet_num:
#         packet_num += [d[2]]
# num_pkts_sent = max(packet_num)
# num_pkts_rx = len(packet_num)
# prr_sn = (num_pkts_rx/num_pkts_sent) * 100
# print('PRR of the sensor node:', prr_sn)


# ### total faulty packets
# # payload: RSSI=12, status=13 
# faulty_packets = []
# # taking raw data from PB
# for d in data[1]:
#     #print('RSSI:', d[0][12])
#     if d[0][13] == 1:
#         faulty_packets += [d]
        
# print('Total no. of faulty packets:', len(faulty_packets))
# print('Total pkts from PB:', len(data[1]))
# print('First and last faulty packet:', faulty_packets[0][2], faulty_packets[-1][2])

# ### efficiency of RB
# # how many faulty pkts detected?    how many lost packets detected

# hb_pkts = []
# data_pkts = []

# for d in data[3]:
#     #print(d[0][0])
#     if d[0][0] == -1:
#         hb_pkts += [d]
#     else:
#         data_pkts += [d]
        
# faulty_detected_pkts = []
# lost_detected_pkts = []
        
# for d in data_pkts:
#     if d[2] < faulty_packets[0][2] or d[2] > faulty_packets[-1][2]:
#         lost_detected_pkts += [d]
#     else:
#         faulty_detected_pkts += [d]

# detection_rate = len(faulty_detected_pkts)/len(faulty_packets)*100
# print('Detection rate for faulty Sensor:', detection_rate)

# assert(len(lost_detected_pkts)+len(faulty_detected_pkts) == len(data_pkts))
# assert(len(data_pkts)+len(hb_pkts) == len(data[3]))

from metrics import faulty_sensor

prr_all = []
detection_rate_all = []

for i in range(1,4):
    prr, dr = faulty_sensor.eval(f"log_exp_sf{i}.pkl")
    prr_all += [prr]
    detection_rate_all += [dr]

print('PRR:', prr_all)
print('efficiency:', detection_rate_all)