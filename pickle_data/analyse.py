import pickle

with open("log.pkl", "rb") as f:
    data = pickle.load(f)

board1_data = data[0]
board2_data = data[1]
board4_data = data[3]


def pdr_calc(board_data):
    len_data = len(board_data)
    num_recv = board_data[len_data-1][0]
    pck_list = []
    for i in range(len_data):
        pck_list.append(board_data[i][0])
    pck_lost = 0
    for i in range(len_data-1):
        j = i + board_data[0][0]
        if j not in pck_list:
            pck_lost += 1
    return 1-pck_lost/num_recv, num_recv, pck_lost


def calc_rssi_mean(rssi_data):
    len_data = len(rssi_data)
    rssi_sum = 0
    for i in range(len_data):
        rssi_sum += rssi_data[i][1]
    return rssi_sum/len_data
    
print(str(pdr_calc(board1_data)) + ' ' + str(calc_rssi_mean(board1_data)))
print(str(pdr_calc(board2_data)) + ' ' + str(calc_rssi_mean(board2_data)))
print(str(pdr_calc(board4_data)) + ' ' + str(calc_rssi_mean(board4_data)))
