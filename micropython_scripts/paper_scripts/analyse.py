import pickle

with open("log.pkl", "rb") as f:
    data = pickle.load(f)

board1_data = data[0]
board2_data = data[1]


def pdr_calc(board_data):
    len_data = len(board_data)
    num_recv = board_data[len_data-1][1]
    pck_list = []
    for i in range(len_data):
        pck_list.append(board_data[i][1])
    pck_lost = 0
    for i in range(len_data-1):
        j = i + board_data[0][1]
        if j not in pck_list:
            pck_lost += 1
    return 1-pck_lost/num_recv, num_recv, pck_lost


print(pdr_calc(board1_data))
print(pdr_calc(board2_data))
