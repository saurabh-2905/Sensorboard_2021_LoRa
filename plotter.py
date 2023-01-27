import matplotlib.pyplot as plt
import pickle
import numpy as np
from collections import defaultdict

with open('sensor_values_2102.pkl', 'rb') as f:
    newlist = pickle.load(f)

# print(newlist)
sensor_wise = defaultdict(list)
plot_titles = ['co2', 'co', 'o2', 'pressure', 'temperature_1', 'humidity_1', 'temperature_2', 'humidity_2', 'temperature_3', 'humidity_3', 'temperature_4', 'humidity_4']

#### [co2, co, o2, press, tmp1, hum1, tmp2, hum2, tmp3, hum3, tmp4, hum4, sensor_status, limit broken, 0, board_id, timestamp ]
for each_list in newlist:
    # print('each_list:', each_list)
    for idx, element in enumerate(each_list):
        sensor_wise[idx] += [element]

# print(list(sensor_wise.keys()))
print(sensor_wise[12])
keys_dict = list(sensor_wise.keys())
for i in keys_dict[4:12]:
    if plot_titles[i][:-2] == 'temperature':
        plt.subplot(1,2,1)
        plt.plot([x/60 for x in sensor_wise[keys_dict[-1]]], sensor_wise[i])
        plt.ylim((0,50))
        plt.title('Temperature')
        plt.ylabel('Degree celcius')
        plt.xlabel('Time (minutes)')
        plt.legend(plot_titles[4:12:2])
        plt.grid('on')
    elif plot_titles[i][:-2] == 'humidity':
        plt.subplot(1,2,2)
        plt.plot([x/60 for x in sensor_wise[keys_dict[-1]]], sensor_wise[i])
        plt.ylim((0,60))
        plt.title('Humidity')
        plt.ylabel('Percentage')
        plt.xlabel('Time (minutes)')
        plt.legend(plot_titles[5:12:2])
        plt.grid('on')
    
    # plt.show()
plt.show()

