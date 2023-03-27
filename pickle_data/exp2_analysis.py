# coding=utf-8
# Script for analysing and plotting the data of Experiment 2 (Sensor Fault and Sensor Value Fault)


from metrics import faulty_sensor, faulty_value_sensor

prr_fs_all = []
detection_fs_rate_all = []

for i in range(1,4):
    prr, dr = faulty_sensor.eval(f"log_exp_sf{i}.pkl")
    prr_fs_all += [prr]
    detection_fs_rate_all += [dr]

print('PRR:', prr_fs_all)
print('efficiency:', detection_fs_rate_all)

prr_fvs_all = []
detection_fvs_rate_all = []

for i in range(1,4):
    prr, dr = faulty_value_sensor.eval(f"log_exp_svf{i}.pkl")
    prr_fvs_all += [prr]
    detection_fvs_rate_all += [dr]

print('PRR:', prr_fs_all)
print('efficiency:', detection_fs_rate_all)
