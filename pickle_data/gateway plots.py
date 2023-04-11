import matplotlib.pyplot as plt
from metrics import gateway_failure
import numpy as np

prr, rssi_gf = gateway_failure.eval("log_exp_gf1.pkl")

prr_sf, rssi_data_rest = gateway_failure.eval_norm("log_red2_red_1.pkl")

# #### Average RSSI of regular gateway
# # load data for gateway failure
# with open("log_red2_red_1.pkl", "rb") as f:
#     data_sf = pickle.load(f)
    
# exp_data = [data_sf]
# data_all = []
# for de in exp_data:
#     data = de[1] + de[2]
#     data_all.extend(data)

# assert(len(data_all) == ( len(data_sf[1])+len(data_sf[2]) )) 

# rssi_data_rest = []
# for d in data_all:
#     rssi_data_rest += [d[4]]


fig = plt.figure(figsize =(10, 7))
# Creating plot
plt.boxplot([rssi_data_rest, rssi_gf])
# plt.xlabel('Time (seconds)', fontsize = 15)
plt.ylabel('RSSI (dbm)', fontsize = 25)
plt.xticks([r for r in range(1,3)],
        ['Normal GW', 'Backup GW'], fontsize = 20)
plt.yticks(fontsize = 20)
# show plot
plt.show()

##### prr plot 

# set width of bar
barWidth = 0.2
data_plot = [prr_sf, prr]
fig = plt.subplots(figsize =(12, 8))

# Set position of bar on X axis
br1 = np.arange(len(data_plot))
# br2 = [x for x in br1]

# Make the plot
plt.bar(br1, data_plot, color ='b', width = barWidth,
        edgecolor ='grey')
# plt.bar(br2, data_plot[1], color ='r', width = barWidth,
#         edgecolor ='grey', label ='w/o redundancy')

# Adding Xticks
plt.ylabel('PRR', fontsize = 25)
plt.xticks([r for r in range(len(data_plot))],
        ['Normal GW', 'Backup GW'])
plt.yticks(np.arange(0, 100, 10))

plt.show()