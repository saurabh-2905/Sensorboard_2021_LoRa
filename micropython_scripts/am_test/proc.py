# process and plot data -- 05.04.2022

import matplotlib.pyplot as plt

file_name = input("Path to file plus filename: ")
if file_name == "":
    file_name = input("Please enter filename: ")

# --------- read log.txt in ---------------------------------------------------
print("Reading file ...")
with open(file_name, "r") as f:
    log_data = f.read()

log_data = log_data.split("\n")

data = []
timestamps = []

log_data = log_data[1:len(log_data)-1]

# --------- extract data and timestamps ---------------------------------------
print("Extract data and timestamps ...")
invalid_crcs = 0
for i in range(len(log_data)):
    split_data = log_data[i].split(";")
    if split_data[0][0] == "[":
        data.append(split_data[0])
        timestamps.append(split_data[1])
    else:
        invalid_crcs += 1

# --------- convert data to floats --------------------------------------------
print("Prepare data for visualization ...")
for i in range(len(data)):
    curr_data = data[i].split(",")
    curr_data[0] = curr_data[0][1:]
    curr_data[len(curr_data)-1] = curr_data[len(curr_data)-1][:-1]
    for j in range(len(curr_data)):
        curr_data[j] = round(float(curr_data[j]), 2)
    data[i] = curr_data

temp_am1 = []
temp_am2 = []
temp_am3 = []
temp_am4 = []
temps = [temp_am1, temp_am2, temp_am3, temp_am4]

hum_am1 = []
hum_am2 = []
hum_am3 = []
hum_am4 = []
hums = [hum_am1, hum_am2, hum_am3, hum_am4]

# --------- extract temperatures and humidities -------------------------------
for i in range(len(data)):
    m = 0
    n = 0
    for j in range(0, len(data[i]), 2):
        if not j == 0:
            m = int(j/2)
        temps[m].append(data[i][j])
    for k in range(1, len(data[i]), 2):
        if not k == 1:
            n = int((k-1)/2)
        hums[n].append(data[i][j])

# --------- plot data ---------------------------------------------------------
print("Plotting data ...")
# create subplots
fig, axs = plt.subplots(2)
title = "Temperature and Humidity measurements from {start}, to {end}\nNumber of invalid CRCs: {crcs}"
fig.suptitle(title.format(start=timestamps[0],
                          end=timestamps[len(timestamps)-1],
                          crcs=invalid_crcs))

new_timestamps = []
for i in range(len(timestamps)):
    new_timestamps.append(str(i+1))

for i in range(4):
    axs[0].plot(new_timestamps, temps[i], "+-", label="AM{}".format(str(i+1)))
    axs[0].set_title("Temperature measurements")
    axs[0].get_xaxis().set_visible(False)
    axs[0].legend(loc="upper right")
    axs[1].plot(new_timestamps, hums[i], "+-", label="AM{}".format(str(i+1)))
    axs[1].set_title("Humidity measurements")
    axs[1].get_xaxis().set_visible(False)
    axs[1].legend(loc="upper right")

plt.show()
