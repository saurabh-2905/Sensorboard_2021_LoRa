import pickle
import matplotlib.pyplot as plt

def eval(pickle_file):
    '''
    pickle_file = path to the pickle file where data is stored (string)
    return:
        prr_sn = packet reception ratio of the node
        detection_rate = percentage of faulty packets detected by redundant board
    '''

    # load data for sensor value fault
    with open(pickle_file, "rb") as f:
        data = pickle.load(f)

    print(len(data[0]), len(data[1]), len(data[2]), len(data[3]))
    primary_board_ind = 1
    redundant_board_ind = 2

    data_format = ('board_id', 'pkt_no', 'Tx_time', 'reTx_time', 'RSSI', 'payload')

    ### Number of Packets received by primary board and redundant board
    print('Primary Board:', len(data[primary_board_ind]))
    print('Redundant Board:', len(data[redundant_board_ind]))

    ### check if all packets belong to same board
    ### PB
    pb_id = 0
    rb_id = 0
    for d_i, d in enumerate(data[primary_board_ind]):
        if d_i == 0:
            pb_id = d[0]
            print('PB Id:',pb_id) 
        assert(data[primary_board_ind][0][0]==d[0])
    ### RB
    for d_i, d in enumerate(data[redundant_board_ind]):
        if d_i == 0:
            rb_id = d[0]
            print('RB Id:', rb_id)
        assert(data[redundant_board_ind][0][0]==d[0])


    #### Checking the confidence interval (40s)
    data_all = data[primary_board_ind] + data[redundant_board_ind]
    print(len(data_all))

    for d in data_all:
        if d[3]-d[2]>0:
            #print(d[1],d[4:6], d[5]-d[4])
            print('packets outside conf. interval', d)

    #### PRR of the sensor node as whole (PB+RB)
    ### count lost packets and calculate PRR (APPROach 1)
    hb_pkts = []
    data_pkts_rb = []
    board_index = [primary_board_ind, redundant_board_ind]
    pkts_lost_pb = 0
    pkts_lost_rb = 0
    pb_reset_count = 0
    rb_reset_count = 0
    for i in board_index:
        each_board = data[i]
        if i == primary_board_ind:
            previous_id = 0
            for d in each_board:
                # print(d[1])
                if d[1] - previous_id > 1:
                    # print(d[1], previous_id)
                    pkts_lost_pb += (d[1] - previous_id - 1)
                if d[1] - previous_id < 0:
                    pb_reset_count += 1
                previous_id = d[1]
        if i == redundant_board_ind:
            previous_id = 0
            data_pkts_rb = []
            for d in each_board:
                #print(d[0][0])
                if d[5][0] == -1:
                    hb_pkts += [d]
                else:
                    # print(d[1])
                    if d[1] - previous_id > 1:
                        if d[1] > 20 and d[1] < 47:
                            # print(d[1], previous_id)
                            pkts_lost_rb += (d[1] - previous_id - 1)
                    if d[1] - previous_id < 0:
                        pb_reset_count += 1
                    data_pkts_rb += [d]
                    previous_id = d[1]

    ### PRR with Redundancy (PB+RB)
    total_pkts = 47 + 22             ### last packet of redundant board and 2nd session of PB
    total_pkts_lost = pkts_lost_pb+pkts_lost_rb
    prr_sn = ((total_pkts-total_pkts_lost)/total_pkts) * 100
    print('PRR with Redundancy:', prr_sn)

    ### PRR without Redundancy (PB)
    prr_pb = ((20+22-pkts_lost_pb)/total_pkts) * 100
    print('PRR without Redundancy:', prr_pb)

    #### Efficiency of RB 
    # how many faulty pkts detected?    how many lost packets detected

    hb_pkts = []
    data_pkts = []

    for d in data[redundant_board_ind]:
        #print(d[0][0])
        if d[5][0] == -1:
            hb_pkts += [d]
        else:
            data_pkts += [d]
            
    faulty_detected_pkts = []
    lost_detected_pkts = []
            
    for d in data_pkts:
        if d[1] < 20 or d[1] > 47:   ### 20: last pkt by PB before failure, 47: last pkt by RB bfore resetting pkt count
            lost_detected_pkts += [d]
        else:
            faulty_detected_pkts += [d]

    detection_rate = len(faulty_detected_pkts)/(47-20)*100
    print('Detection rate for hard failure:', detection_rate)

    return(prr_sn, prr_pb, detection_rate)