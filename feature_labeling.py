import os
import numpy as np
import pandas as pd

directory = '.\\real-traffic'

"""ip_dict = {
    '10.0.0.6': 'Win 7',
    '192.168.0.100': 'Win10',
    '192.168.1.11': 'Win10',
    '132.73.223.74': 'Win10',
    '192.168.1.34': 'Win11',
    '192.168.1.105': 'Win11',
    '192.168.1.81': 'Mac2017',
    '192.168.31.59': 'Mac2018',
    '192.168.1.56': 'Mac2019',
    '192.168.0.10': 'Mac2020',
    '10.100.102.8': 'Rhel8',
    '192.168.43.80': 'Pop',
    '10.100.102.7': 'Ubuntu2018',
    '10.0.0.7': 'Arch',
    '10.0.0.5': 'Ubuntu 20.4'
}"""

# ip_dict = {
#     '10.0.0.6': 'Windows',
#     '192.168.0.100': 'Windows',
#     '192.168.1.11': 'Windows',
#     '132.73.223.74': 'Windows',
#     '192.168.1.34': 'Windows',
#     '192.168.1.105': 'Windows',
#
#     '192.168.1.81': 'Mac',
#     '192.168.31.59': 'Mac',
#     '192.168.1.56': 'Mac',
#     '192.168.0.10': 'Mac',
#
#     '10.100.102.8': 'Linux',
#     '192.168.43.80': 'Linux',
#     '10.100.102.7': 'Linux',
#     '10.0.0.7': 'Linux',
#     '10.0.0.5': 'Linux'
# }

ip_dict = {
    #cicids 2017
    '192.168.10.51': 'Ubuntu',
    '192.168.10.19': 'Ubuntu',
    '192.168.10.17': 'Ubuntu',
    '192.168.10.16': 'Ubuntu',
    '192.168.10.12': 'Ubuntu',
    '192.168.10.9': 'Windows',
    '192.168.10.5': 'Windows',
    '192.168.10.8': 'Windows',
    '192.168.10.14': 'Windows',
    '192.168.10.15': 'Windows',
    '192.168.10.25': 'macOS',
    #real traffic
    '10.0.0.6': 'Win 7',
    '192.168.0.100': 'Win10',
    '192.168.1.11': 'Win10',
    '132.73.223.74': 'Win10',
    '192.168.1.34': 'Win11',
    '192.168.1.105': 'Win11',
    '192.168.1.81': 'Mac2017',
    '192.168.31.59': 'Mac2018',
    '192.168.1.56': 'Mac2019',
    '192.168.0.10': 'Mac2020',
    '10.100.102.8': 'Rhel8',
    '192.168.43.80': 'Pop',
    '10.100.102.7': 'Ubuntu2018',
    '10.0.0.7': 'Arch',
    '10.0.0.5': 'Ubuntu 20.4'
    }


def data_preprocess(init_df):

    init_df.drop(columns=['ip.tos', 'tcp.options.mss_val'], inplace=True)
    # init_df['tcp.options.mss_val'].fillna(method='ffill', inplace=True)
    init_df.dropna(inplace=True)

    """init_df['tcp.srcport'] = np.where(init_df['tcp.srcport'] > 1024, 1, 0)
    init_df['tcp.dstport'] = np.where(init_df['tcp.dstport'] > 1024, 1, 0)"""

    init_df['ip.dsfield'] = init_df['ip.dsfield'].apply(str).apply(int, base=16)
    init_df['tcp.flags'] = init_df['tcp.flags'].apply(str).apply(int, base=16)
    init_df['ip.flags'] = init_df['ip.flags'].apply(str).apply(int, base=16)

    init_df.sort_values(['tcp.stream', 'frame.time_relative'], inplace=True, ignore_index=True)

    init_df = count_delta_time_average_and_std_per_10_packets(init_df)
    init_df = average_and_std_ttl_per_10_packets(init_df)
    init_df = average_and_std_packet_len_per_10_packets(init_df)
    init_df.dropna(inplace=True)

    return init_df


def count_delta_time_average_and_std_per_10_packets(init_df):

    init_df['stream_key'] = 0
    stream_num = init_df['tcp.stream'][0]
    counter, stream_index = 1, 1

    for row in range(init_df.shape[0]):

        if init_df['tcp.stream'][row] != stream_num:
            stream_num = init_df['tcp.stream'][row]
            counter, stream_index = 1, stream_index + 1

        elif counter > 10:
            counter, stream_index = 1, stream_index + 1

        init_df.at[row, 'stream_key'] = stream_index
        counter += 1

    average_values_dict = {}
    std_values_dict = {}

    for i_stream in sorted(init_df['stream_key'].unique()):
        mean = init_df.loc[init_df['stream_key'] == i_stream]['tcp.time_delta'].mean()
        std = init_df.loc[init_df['stream_key'] == i_stream]['tcp.time_delta'].std()
        average_values_dict[i_stream] = mean
        std_values_dict[i_stream] = std
    init_df['average_time_delta'] = init_df['stream_key'].apply(set_row_feature, args=(average_values_dict,))
    init_df['std_time_delta'] = init_df['stream_key'].apply(set_row_feature, args=(std_values_dict,))

    return init_df


def average_and_std_ttl_per_10_packets(init_df):

    average_values_dict = {}
    std_values_dict = {}

    for i_stream in sorted(init_df['stream_key'].unique()):
        mean = init_df.loc[init_df['stream_key'] == i_stream]['ip.ttl'].mean()
        std = init_df.loc[init_df['stream_key'] == i_stream]['ip.ttl'].std()
        average_values_dict[i_stream] = mean
        std_values_dict[i_stream] = std
    init_df['average_ttl'] = init_df['stream_key'].apply(set_row_feature, args=(average_values_dict,))
    init_df['std_ttl'] = init_df['stream_key'].apply(set_row_feature, args=(std_values_dict,))

    return init_df


def average_and_std_packet_len_per_10_packets(init_df):

    average_values_dict = {}
    std_values_dict = {}

    for i_stream in sorted(init_df['stream_key'].unique()):
        mean = init_df.loc[init_df['stream_key'] == i_stream]['tcp.len'].mean()
        std = init_df.loc[init_df['stream_key'] == i_stream]['tcp.len'].std()
        average_values_dict[i_stream] = mean
        std_values_dict[i_stream] = std
    init_df['average_len'] = init_df['stream_key'].apply(set_row_feature, args=(average_values_dict,))
    init_df['std_len'] = init_df['stream_key'].apply(set_row_feature, args=(std_values_dict,))

    return init_df


def set_row_feature(row_value, values_dict):
    """
        This is a helper function for the dataframe's apply method
    """
    return values_dict[row_value]


def add_label(df, ip_label_dict):

    # create list of known IP addresses
    known_ip_list = [key for key in ip_label_dict.keys()]

    # filter df based on known IP addresses
    all_ip_list = list(set(df['ip.src'].tolist()))
    unnecessary_ip_list = [item for item in all_ip_list if item not in known_ip_list]
    filtered_df = df.copy()
    for ip in unnecessary_ip_list:
        filtered_df = filtered_df[filtered_df['ip.src'] != ip]

    # add label to the filtered df
    for ip in known_ip_list:
        filtered_df.loc[filtered_df['ip.src'] == ip, "os"] = ip_label_dict[ip]

    # print(filtered_df)

    return filtered_df


if __name__ == '__main__':

    for i, filename in enumerate(os.listdir(directory)):
        f = os.path.join(directory, filename)
        if os.path.isfile(f):
            print(directory + '\\' + filename)
            df = pd.read_csv(directory + '\\' + filename)
            processed_df = data_preprocess(df)
            labeled_df = add_label(processed_df, ip_dict)

            # limit number of records
            test_df = labeled_df[700:840] if df.shape[0] > 840 else labeled_df[700:]
            labeled_df = labeled_df[:700] if df.shape[0] > 700 else labeled_df
            print(labeled_df.shape[0])

            filename_to_miss = ""

            if filename == filename_to_miss:
                labeled_df.to_csv(directory + '\\labeled_to_miss.csv', mode='a+', index=False)
                continue

            elif not i:
                labeled_df.to_csv(directory + '\\labeled.csv', mode='a+', index=False)
                test_df.to_csv(directory + '\\test.csv', mode='a+', index=False)
            else:
                labeled_df.to_csv(directory + '\\labeled.csv', mode='a+', header=False, index=False)
                test_df.to_csv(directory + '\\test.csv', mode='a+', header=False, index=False)

    # print(labeled_df)