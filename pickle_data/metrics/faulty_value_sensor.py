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

    #### Checking the confidence interval (40s)
    data_all = data[1] + data[3]
    for d in data_all:
        if d[5]-d[4]>0:
            #print(d[1],d[4:6], d[5]-d[4])
            print('packets outside conf. interval', d)

    #### PRR of the sensor node as whole (PB+RB)
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
    # prr_sn = (num_pkts_rx/num_pkts_sent) * 100     ## incorrect, considers faulty packets sent by pb
    # print('PRR of the sensor node:', prr_sn)

    #### Efficiency of RB 
    ### total faulty packets
    # payload: RSSI=12, status=13 
    faulty_packets = []
    # taking raw data from PB
    for d in data[1]:
        #print('RSSI:', d[0][12])
        if d[0][0] == 1000.0:
            #print(d[2])
            faulty_packets += [d]
            
    # print('Total no. of faulty packets:', len(faulty_packets))
    # print('Total pkts from PB:', len(data[1]))
    # print('First and last faulty packet:', faulty_packets[0][2], faulty_packets[-1][2])

    ### PRR of the primary board (PB)
    num_pkts_sent_pb = 0 
    num_pkts_rx_pb = 0
    packet_num_pb = []

    num_pkts_sent_rb = 0 
    num_pkts_rx_rb = 0
    packet_num_rb = []

    for d in data[1]:  ##pb
        if d[2] < faulty_packets[0][2] or d[2] > faulty_packets[-1][2]:
            packet_num_pb += [d[2]]
            
    for d in data[3]:   #rb
        if d[2] >= faulty_packets[0][2] or d[2] <= faulty_packets[-1][2]: ### take only packets during faulty data
            if d[0][0] != -1:    # filter out hb
                packet_num_rb += [d[2]]
            
    num_pkts_rx_pb = len(packet_num_pb)
    prr_pb = (num_pkts_rx_pb/num_pkts_sent) * 100    ### packets rx from only PB out of total packets sent by node
    # print('PRR of the primary board:', prr_pb)

    num_pkts_rx_rb = len(packet_num_rb)
    prr_sn = (num_pkts_rx_pb+num_pkts_rx_rb)/num_pkts_sent * 100
    # print('PRR of the sensor node:', prr_sn)
                

    ### efficiency of RB
    # how many faulty pkts detected?    how many lost packets detected

    hb_pkts = []
    data_pkts = []

    for d in data[3]:
        #print(d[0][0])
        if d[0][0] == -1:
            hb_pkts += [d]
        else:
            data_pkts += [d]
            
    faulty_detected_pkts = []
    lost_detected_pkts = []
            
    for d in data_pkts:
        if d[2] < faulty_packets[0][2] or d[2] > faulty_packets[-1][2]:   ### filter out the packets that were transmitted when data was not faulty
            lost_detected_pkts += [d]
        else:
            faulty_detected_pkts += [d]

    detection_rate = len(faulty_detected_pkts)/(faulty_packets[-1][2]-faulty_packets[0][2]+1)*100
    # print('Detection rate for faulty Sensor:', detection_rate)

    assert(len(lost_detected_pkts)+len(faulty_detected_pkts) == len(data_pkts))
    assert(len(data_pkts)+len(hb_pkts) == len(data[3]))

    return(prr_sn, prr_pb, detection_rate)
