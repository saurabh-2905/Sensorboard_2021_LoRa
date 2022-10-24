import pickle

with open("log.pkl", "rb") as f:
    data = pickle.load(f)

board1_data = data[0]
board2_data = data[1]
board4_data = data[3]


def pdr_calc(board_data):
    len_data = len(board_data)
    pck_list = []
    num_recv = 0
    for i in range(len_data):
        pck_no = board_data[i][1]
        if pck_no < 100:
            pck_list.append(pck_no)
            if pck_no > num_recv:
                num_recv = pck_no
    pck_lost = 0
    for i in range(100):
        if i not in pck_list:
            pck_lost += 1
    return 1-pck_lost/num_recv, num_recv, pck_lost


def calc_rssi_mean(rssi_data):
    len_data = len(rssi_data)
    rssi_sum = 0
    for i in range(len_data):
        rssi_sum += rssi_data[i][4]
    return rssi_sum/len_data


def timestamp_calc(data):
    len_data = len(data)
    no_retr = 0
    retr = 0
    for i in range(len_data):
        time_diff = data[i][3] - data[i][2]
        if time_diff > 20:
            no_retr += 1
        else:
            retr += 1
    return no_retr, retr


print('#1: PDR, TX, lost: ' + str(pdr_calc(board1_data)) + '| RSSI: ' +
      str(calc_rssi_mean(board1_data)) + '| NoReTX, ReTX: ' +
      str(timestamp_calc(board1_data)))
print('#2: PDR, TX, lost: ' + str(pdr_calc(board2_data)) + '| RSSI: ' +
      str(calc_rssi_mean(board2_data)) + '| NoReTX, ReTX: ' +
      str(timestamp_calc(board2_data)))
print('#4: PDR, TX, lost: ' + str(pdr_calc(board4_data)) + '| RSSI: ' +
      str(calc_rssi_mean(board4_data)) + '| NoReTX, ReTX: ' +
      str(timestamp_calc(board4_data)))
