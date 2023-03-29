import pickle
import matplotlib.pyplot as plt
from metrics import gateway_failure

prr, rssi_gf = gateway_failure.eval("log_exp_gf1.pkl")

#### Average RSSI of regular gateway
# load data for gateway failure
with open("log_red2_red_1.pkl", "rb") as f:
    data_sf = pickle.load(f)
    
exp_data = [data_sf]
data_all = []
for de in exp_data:
    data = de[1] + de[2]
    data_all.extend(data)

assert(len(data_all) == ( len(data_sf[1])+len(data_sf[2]) )) 

rssi_data_rest = []
for d in data_all:
    rssi_data_rest += [d[4]]


fig = plt.figure(figsize =(10, 7))
# Creating plot
plt.boxplot([rssi_data_rest, rssi_gf])
# plt.xlabel('Time (seconds)', fontsize = 15)
plt.ylabel('RSSI', fontsize = 15)
plt.xticks([r for r in range(1,3)],
        ['Normal GW', 'Backup GW'])
# show plot
plt.show()