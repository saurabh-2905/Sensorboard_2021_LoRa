
from metrics import hard_failure, faulty_sensor, faulty_value_sensor
import numpy as np


prr_hf_all = []
prrpb_hf_all = []
detection_hf_rate_all = []
for i in range(1,4):
    prr, prr_pb, dr = hard_failure.eval(f"log_red2_red_{i}.pkl")
    prr_hf_all += [prr]
    prrpb_hf_all += [prr_pb]
    detection_hf_rate_all += [dr]

print('PRR hf:', prr_hf_all)
print('efficiency hf:', detection_hf_rate_all)

prr_fs_all = []
detection_fs_rate_all = []
for i in range(1,4):
    prr, dr = faulty_sensor.eval(f"log_exp_sf{i}.pkl")
    prr_fs_all += [prr]
    detection_fs_rate_all += [dr]

print('PRR fs:', prr_fs_all)
print('efficiency fs:', detection_fs_rate_all)

prr_fvs_all = []
detection_fvs_rate_all = []
for i in range(1,4):
    prr, dr = faulty_value_sensor.eval(f"log_exp_svf{i}.pkl")
    prr_fvs_all += [prr]
    detection_fvs_rate_all += [dr]

print('PRR fsv:', prr_fs_all)
print('efficiency fsv:', detection_fs_rate_all)



hf_prr = np.mean(prr_hf_all)
hf_prr_pb = np.mean(prrpb_hf_all)
fs_prr = np.mean(prr_fs_all)
fvs_prr = np.mean(prr_fvs_all)

hf_dr = np.mean(detection_hf_rate_all)
fs_dr = np.mean(detection_fs_rate_all)
fvs_dr = np.mean(detection_fvs_rate_all)


print(hf_prr, hf_prr_pb, fs_prr, fvs_prr)
print(hf_dr, fs_dr, fvs_dr)