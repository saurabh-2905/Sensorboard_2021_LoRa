import pickle
import matplotlib.pyplot as plt


def eval(pickle_file):
    '''
    pickle_file = path to the pickle file where data is stored (string)
    return:
        prr_sn = packet reception ratio of the node
        rssi_data = list of rssi values of all pkts
    '''
    # load data for gateway failure
    with open(pickle_file, "rb") as f:
        data = pickle.load(f)

    print(len(data[0]), len(data[1]), len(data[2]), len(data[3]))
    primary_board_ind = 1
    redundant_board_ind = 3

    data_format = ('payload', 'board_id', 'pkt_no', 'RSSI', 'Tx_time', 'reTx_time', 'rx_time' )

    ### Number of Packets received by primary board and redundant board
    print('Primary Board:', len(data[1]))
    print('Redundant Board:', len(data[3]))

    ### check if all packets belong to same board
    ### PB
    pb_id = 0
    rb_id = 0
    for d_i, d in enumerate(data[1]):
        if d_i == 0:
            pb_id = d[1]
            print('PB Id:',pb_id) 
        assert(data[1][0][1]==d[1])
    ### RB
    for d_i, d in enumerate(data[3]):
        if d_i == 0:
            rb_id = d[1]
            print('RB Id:', rb_id)
        assert(data[3][0][1]==d[1])

    data_all = data[1] + data[3]
    for d in data_all:
        if d[5]-d[4]>0:
            #print(d[1],d[4:6], d[5]-d[4])
            print('packets outside conf. interval', d)
            

    ### filter hb signals
    hb_pkts = []
    data_pkts = []
    board_index = [1,3]

    for i in board_index:
        each_board = data[i]
        for d in each_board:
            #print(d[0][0])
            if d[0][0] == -1:
                hb_pkts += [d]
            else:
                data_pkts += [d]
                

    ### PRR of the sesnor node (PB+RB)
    packet_num = []
    num_pkts_sent = 0 
    num_pkts_rx = 0
    for d in data_pkts:
        if d[2] not in packet_num:
            packet_num += [d[2]]
    num_pkts_sent = max(packet_num)
    num_pkts_rx = len(packet_num)
    prr_sn = (num_pkts_rx/num_pkts_sent) * 100
    print('PRR of the sensor node:', prr_sn)

    len(data_all) == (len(data[1]) + len(data[3]))

    ### filter hb signals
    hb_pkts = []
    data_pkts = []
    board_index = [1,3]

    for i in board_index:
        each_board = data[i]
        for d in each_board:
            #print(d[0][0])
            if d[0][0] == -1:
                hb_pkts += [d]
            else:
                data_pkts += [d]

    rssi_data = []
    for d in data_pkts:
        rssi_data += [d[3]]


    return(prr_sn, rssi_data)