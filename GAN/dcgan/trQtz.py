import numpy as np
np.set_printoptions(threshold=np.inf)

def transQuantization(data, qtz_info):
    e, m, b = qtz_info
    th_p_up = 2 ** (e) - 1 - b
    th_p_lo = - b
    #print ('up:',th_p_up,'lo:',th_p_lo)
    th_v_up = 2 ** (th_p_up + 1) - 2 ** (-m)
    th_v_lo = 2 ** (th_p_lo)
    data_out = data.copy()

    data_idx = data.copy()
    data_idx[np.where(data>0)] = 1
    data_idx[np.where(data<0)] = -1
    data_idx[np.where(data==0)] = 0

    tmp_data = data * data_idx
    tmp_data[np.where(data==0)] = 1
    tmp_data_int = np.floor(tmp_data)
    tmp_data_fra = tmp_data - tmp_data_int


    p = np.floor(np.log2(tmp_data))
    #print ('m,p type', type(m), type(p))
    #print (m)
    m_tmp = m - p

    tmp_data[np.floor(np.log2(tmp_data)) < th_p_lo] = th_v_lo
    tmp_data[np.floor(np.log2(tmp_data)) > th_p_up] = th_v_up

    tmp_data[(tmp_data < 1) & (np.floor(np.log2(tmp_data)) >= th_p_lo) & (np.floor(np.log2(tmp_data)) <= th_p_up)] = (2 ** (-m_tmp[(tmp_data < 1) & (np.floor(np.log2(tmp_data)) >= th_p_lo) & (np.floor(np.log2(tmp_data)) <= th_p_up)])) * (np.floor(tmp_data[(tmp_data < 1) & (np.floor(np.log2(tmp_data)) >= th_p_lo) & (np.floor(np.log2(tmp_data)) <= th_p_up)] / (2 ** (-m_tmp[(tmp_data < 1) & (np.floor(np.log2(tmp_data)) >= th_p_lo) & (np.floor(np.log2(tmp_data)) <= th_p_up)]))) + 0.5)
    tmp_data_fra[(tmp_data > 1) & (m_tmp <= 0) & (np.floor(np.log2(tmp_data)) >= th_p_lo) & (np.floor(np.log2(tmp_data)) <= th_p_up)] = 0.0
    tmp_data_fra[(tmp_data > 1) & (m_tmp > 0) & (np.floor(np.log2(tmp_data)) >= th_p_lo) & (np.floor(np.log2(tmp_data)) <= th_p_up)] = (2 ** (-m_tmp[(tmp_data > 1) & (m_tmp > 0) & (np.floor(np.log2(tmp_data)) >= th_p_lo) & (np.floor(np.log2(tmp_data)) <= th_p_up)])) * (np.floor(tmp_data_fra[(tmp_data > 1) & (m_tmp > 0) & (np.floor(np.log2(tmp_data)) >= th_p_lo) & (np.floor(np.log2(tmp_data)) <= th_p_up)] /  (2 ** (-m_tmp[(tmp_data > 1) & (m_tmp > 0) & (np.floor(np.log2(tmp_data)) >= th_p_lo) & (np.floor(np.log2(tmp_data)) <= th_p_up)]))) + 0.5 )
    tmp_data[(tmp_data > 1) & (np.floor(np.log2(tmp_data)) >= th_p_lo) & (np.floor(np.log2(tmp_data)) <= th_p_up)] = tmp_data_int[(tmp_data > 1) & (np.floor(np.log2(tmp_data)) >= th_p_lo) & (np.floor(np.log2(tmp_data)) <= th_p_up)] + tmp_data_fra[(tmp_data > 1) & (np.floor(np.log2(tmp_data)) >= th_p_lo) & (np.floor(np.log2(tmp_data)) <= th_p_up)]
    data_out = tmp_data * data_idx
    #print ((2 ** (-m_tmp[(tmp_data > 1) & (m_tmp > 0) & (np.floor(np.log2(tmp_data)) >= th_p_lo) & (np.floor(np.log2(tmp_data)) <= th_p_up)] /  (2 ** (-m_tmp[(tmp_data > 1) & (m_tmp > 0) & (np.floor(np.log2(tmp_data)) >= th_p_lo) & (np.floor(np.log2(tmp_data)) <= th_p_up)])))))
    #print (-m_tmp[(tmp_data > 1) & (m_tmp > 0) & (np.floor(np.log2(tmp_data)) >= th_p_lo) & (np.floor(np.log2(tmp_data)) <= th_p_up)])
    #print  /  (2 ** (-m_tmp[(tmp_data > 1) & (m_tmp > 0) & (np.floor(np.log2(tmp_data)) >= th_p_lo) & (np.floor(np.log2(tmp_data)) <= th_p_up_up)])))))
    #print (tmp_data_fra)
    diff = data - data_out
    # print (data[1])
    # print (data_out[1])
    # print ('quantize diff max: ', np.max(diff))
    # print ('quantize diff mean: ', np.mean(diff))
    return data_out

if __name__ == '__main__':
    data = np.array([1, 0.1, 0.001])
    data_out = transQuantization(data)

    print ('input', data)
    print ('output', data_out)
