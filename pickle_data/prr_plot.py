
from metrics import hard_failure, faulty_sensor, faulty_value_sensor
import numpy as np
import matplotlib.pyplot as plt


# prr_hf_all = []
# prrpb_hf_all = []
# detection_hf_rate_all = []
# for i in range(1,4):
#     prr, prr_pb, dr = hard_failure.eval(f"log_red2_red_{i}.pkl")
#     prr_hf_all += [prr]
#     prrpb_hf_all += [prr_pb]
#     detection_hf_rate_all += [dr]



# prr_fs_all = []
# prrpb_fs_all = []
# detection_fs_rate_all = []
# for i in range(1,4):
#     prr, prr_pb, dr = faulty_sensor.eval(f"log_exp_sf{i}.pkl")
#     prr_fs_all += [prr]
#     detection_fs_rate_all += [dr]
#     prrpb_fs_all += [prr_pb]


# prr_fvs_all = []
# prrpb_fsv_all = []
# detection_fvs_rate_all = []
# for i in range(1,4):
#     prr, prr_pb, dr = faulty_value_sensor.eval(f"log_exp_svf{i}.pkl")
#     prr_fvs_all += [prr]
#     detection_fvs_rate_all += [dr]
#     prrpb_fsv_all += [prr_pb]

# print('PRR hf:', prr_hf_all)
# print('PRR hf pb:', prrpb_hf_all)
# print('efficiency hf:', detection_hf_rate_all)

# print('PRR fs:', prr_fs_all)
# print('PRR fs pb:', prrpb_fs_all)
# print('efficiency fs:', detection_fs_rate_all)

# print('PRR fsv:', prr_fvs_all)
# print('PRR fsv pb:', prrpb_fsv_all)
# print('efficiency fsv:', detection_fvs_rate_all)



# hf_prr = np.mean(prr_hf_all)
# hf_prr_pb = np.mean(prrpb_hf_all)
# fs_prr = np.mean(prr_fs_all)
# fs_prr_pb = np.mean(prrpb_fs_all)
# fvs_prr = np.mean(prr_fvs_all)
# fvs_prr_pb = np.mean(prrpb_fsv_all)

# hf_dr = np.mean(detection_hf_rate_all)
# fs_dr = np.mean(detection_fs_rate_all)
# fvs_dr = np.mean(detection_fvs_rate_all)


# print(hf_prr, fs_prr, fvs_prr)
# print(hf_prr_pb, fs_prr_pb, fvs_prr_pb)
# print(hf_dr, fs_dr, fvs_dr)

#### expected values based on single exp

prr_sn_exp = [99.00, 73.52, 74.21]
prr_pb_exp = [47.00, 41.17, 40.00]
dr_exp = [70.96, 40.90, 40.10]
prr_without_mac = [85.71, 47.05, 48.01]

[hf_prr, fs_prr, fvs_prr] = prr_sn_exp
[hf_prr_pb, fs_prr_pb, fvs_prr_pb] = prr_pb_exp
[hf_dr, fs_dr, fvs_dr] = dr_exp
##### PRR plot ########
# set width of bar
barWidth = 0.2
data_plot = [[hf_prr, fs_prr, fvs_prr],
        [hf_prr_pb, fs_prr_pb, fvs_prr_pb],
        prr_without_mac]
data_plot_mac = [[5, 20, 12],
                 [8,12, 5]]
fig = plt.subplots(figsize =(12, 8))

# Set position of bar on X axis
br1 = np.arange(len(data_plot[0]))     ## with rb
br2 = [x + barWidth for x in br1]       ## without rb

# Make the plot
plt.bar(br1, data_plot[0], color ='#063970', width = barWidth,
        edgecolor ='grey', label ='w/ redundancy')
# plt.bar(br1, data_plot_mac[0], color ='#15710D', width = barWidth,
#         edgecolor ='grey', label ='mac', bottom=data_plot[0])
plt.bar(br2, data_plot[1], color ='#8C0909', width = barWidth,
        edgecolor ='grey', label ='w/o redundancy')
# plt.bar(br2, data_plot_mac[1], color ='#15710D', width = barWidth,
#         edgecolor ='grey', bottom=data_plot[1])

# Adding Xticks
plt.xlabel('Failure Scenarios', fontsize = 25)
plt.ylabel('PRR', fontsize = 25)
plt.xticks([r + barWidth/2 for r in range(len(data_plot[0]))],
        ['HF', 'SF1', 'SF2'], fontsize=20)
plt.yticks(np.arange(0, 100, 10), fontsize=20)

# ax = fig.add_axes([0,0,1,1])
# ax.bar(X + 0.00, data[0], color = 'b', width = 0.25)
# ax.bar(X + 0.25, data[1], color = 'r', width = 0.25)
# # ax.bar(X + 0.50, data[2], color = 'g', width = 0.25)
# ax.set_ylabel('PRR')
# ax.set_title('Failure Secnarios')
# ax.set_xticks(ind, ('HF', 'SF', 'SVF'))
# ax.set_yticks(np.arange(0, 100, 10))

plt.legend(fontsize=20)
plt.show()

###### Influence of MAC ##########

fig = plt.subplots(figsize =(12, 8))

# Set position of bar on X axis
br1 = np.arange(len(data_plot[0]))     ## with rb
br2 = [x + barWidth for x in br1]       ## without rb

# Make the plot
plt.bar(br1, data_plot[0], color ='#063970', width = barWidth,
        edgecolor ='grey', label ='w/ MAC')
plt.bar(br2, data_plot[2], color ='#8C0909', width = barWidth,
        edgecolor ='grey', label ='w/o MAC')

# Adding Xticks
plt.xlabel('Failure Scenarios', fontsize = 25)
plt.ylabel('PRR', fontsize = 25)
plt.xticks([r + barWidth/2 for r in range(len(data_plot[0]))],
        ['HF', 'SF1', 'SF2'], fontsize=20)
plt.yticks(np.arange(0, 100, 10), fontsize=20)

plt.legend(fontsize=20)
plt.show()

######## Detection rate plot ######
# set width of bar
barWidth = 0.2
data_plot = [hf_dr, fs_dr, fvs_dr]
fig = plt.subplots(figsize =(12, 8))

# Set position of bar on X axis
br1 = np.arange(len(data_plot))

# Make the plot
plt.bar(br1, data_plot, color ='#063970' , width = barWidth,
        edgecolor ='grey',)

# Adding Xticks
plt.xlabel('Failure Scenarios', )
plt.ylabel('Detection Rate', fontsize = 25)
plt.xticks([r for r in range(len(data_plot))],
        ['HF', 'SF1', 'SF2'], fontsize=20)
plt.yticks(np.arange(0, 100, 10), fontsize=20)
plt.show()


