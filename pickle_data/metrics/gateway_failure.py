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
    # print('PRR of the sensor node:', prr_sn)

    assert(len(data_all) == (len(data[1]) + len(data[3])))

    # ### filter hb signals
    # hb_pkts = []
    # data_pkts = []
    # board_index = [1,3]

    # for i in board_index:
    #     each_board = data[i]
    #     for d in each_board:
    #         #print(d[0][0])
    #         if d[0][0] == -1:
    #             hb_pkts += [d]
    #         else:
    #             data_pkts += [d]

    rssi_data_gf = []
    for d in data_all:
        rssi_data_gf += [d[3]]


    return(prr_sn, rssi_data_gf)


def eval_norm(pickle_file):
    '''
    pickle_file = path to the pickle file where data is stored (string)
    return:
        prr_sn = packet reception ratio of the node
        rssi_data = list of rssi values of all pkts
    '''

    #### Average RSSI of regular gateway
    # load data for gateway failure
    with open("log_red2_red_1.pkl", "rb") as f:
        data_sf = pickle.load(f)

    print(len(data_sf[0]), len(data_sf[1]), len(data_sf[2]), len(data_sf[3]))
    primary_board_ind = 1
    redundant_board_ind = 2

    data_format = ('board_id', 'pkt_no', 'Tx_time', 'reTx_time', 'RSSI')

    exp_data = [data_sf]
    data_all = []
    for de in exp_data:
        data = de[1] + de[2]
        data_all.extend(data)
    #data_all.extend(data_hf[1]+data_hf[2])

    #assert(len(data_all) == ( len(data_hf[1])+len(data_hf[2]) + len(data_sf[1])+len(data_sf[3]) + len(data_svf[1])+len(data_svf[3]) )) 
    assert(len(data_all) == ( len(data_sf[1])+len(data_sf[2]) )) 

    ### filter hb signals
    hb_pkts_sf = []
    data_pkts_sf = []
    board_index = [1,2]

    for i in board_index:
        each_board = data_sf[i]
        for d in each_board:
            print(d)
            #print(d[0][0])
            if d[1] == 0 and i == 2:  ### check hb indicator and board id
                hb_pkts_sf += [d]
            else:
                data_pkts_sf += [d]


    assert(len(hb_pkts_sf)+len(data_pkts_sf)==len(data_sf[1])+len(data_sf[2]))

    ### PRR of the sesnor node (PB+RB)
    packet_num_sf = []
    num_pkts_sent_sf = 0 
    num_pkts_rx_sf = 0
    for d in data_pkts_sf:
        if d[1] not in packet_num_sf:
            packet_num_sf += [d[1]]
    num_pkts_sent_sf = max(packet_num_sf)
    num_pkts_rx_sf = len(packet_num_sf)
    prr_sn_sf = (num_pkts_rx_sf/num_pkts_sent_sf) * 100
    print('PRR of the sensor node:', prr_sn_sf)

    #### rssi analysis
    rssi_data_rest = []
    for d in data_all:
        rssi_data_rest += [d[4]]

    return(prr_sn_sf, rssi_data_rest)