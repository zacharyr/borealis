#!/usr/bin/python3

# Copyright 2019 SuperDARN Canada
#
# realtime.py

# Sends data to realtime applications

import zmq
import threading
import os
import sys
import queue
import json
import zlib
import pydarnio
from pydarnio import BorealisRead
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from backscatter import fitacf

borealis_path = os.environ['BOREALISPATH']
if not borealis_path:
    raise ValueError("BOREALISPATH env variable not set")

sys.path.append(borealis_path + '/utils/')
import realtime_options.realtime_options as rto
from zmq_borealis_helpers import socket_operations as so
import shared_macros.shared_macros as sm

rt_print = sm.MODULE_PRINT("Realtime", "green")

def _main():
    opts = rto.RealtimeOptions()

    borealis_sockets = so.create_sockets([opts.rt_to_dw_identity], opts.router_address)
    data_write_to_realtime = borealis_sockets[0]

    context = zmq.Context().instance()
    realtime_socket = context.socket(zmq.PUB)
    realtime_socket.bind(opts.rt_address)

    q = queue.Queue()

    def get_temp_file_from_datawrite():
        last_file_time = None

        ############ Set up the plot #####################
        num_seq = 2001
        num_range = 70
        power_array = np.zeros([num_seq, num_range])
        
        vmin = 10  # minimum log power for plotting (dB)
        vmax = 40  # maximum log power for plotting (dB)
        
        #kw = {'width_ratios': [95,5]}
        fig, (ax1, cax1) = plt.subplots(1, 2, figsize=(32,16)) #, gridspec_kw=kw)
        fig.suptitle('Realtime Power')

        img = ax1.imshow(power_array, aspect='auto', origin='lower',
                        cmap=plt.get_cmap('gnuplot2'), vmax=vmax, vmin=vmin)
        ax1.set_title('Range-time based on last 2000 samples')
        ax1.set_ylabel('Sample number (Range)')
        ax1.set_xticks([0, 500, 1000, 1500, 2000])
        ax1.set_xticklabels([-2000, -1500, -1000, -500, 0])
        ax1.set_xlabel('Sequence number relative to present')
        fig.colorbar(img, cax=cax1, label='Log Power of Voltage (a.u.)')
        
        plt.plot()
        ##################################################

        while True:
            filename = so.recv_data(data_write_to_realtime, opts.dw_to_rt_identity, rt_print)
            
            print(filename)
            # Plot the realtime data
            if "antennas_iq" in filename:
                fields = filename.split(".")
                file_time = fields[0] + fields[1] + fields[2] + fields[3]

                slice_num = int(fields[5])
                desired_slice = 0       #TODO: Hardcoded, change later
                if file_time == last_file_time or slice_num != desired_slice:
                    os.remove(filename)
                    continue

                last_file_time = file_time

                slice_num = int(fields[5])
                
                try:
                    rt_print("Appending data from {}".format(file_time))
                    reader = BorealisRead(filename, 'antennas_iq',
                                          borealis_file_structure='site')
                    arrays = reader.arrays

                    (num_records, num_antennas, max_num_sequences, num_samps) = \
                            arrays['data'].shape
                    antenna_indices = list(range(0, num_antennas))
                    antenna_names = list(arrays['antenna_arrays_order'])
                    sequences_data = arrays['num_sequences']
                    timestamps_data = arrays['sqn_timestamps']
                    
                    antenna_num = 7     #TODO: Hardcoded in for now, change this to a parameter later

                    antenna_data = arrays['data'][:,antenna_num,:,:]
                    power_list = []
                    timestamps = []
                    
                    for record_num in range(num_records):
                        num_sequences = int(sequences_data[record_num])
                        voltage_samples = antenna_data[record_num,:num_sequences,:]
                        
                        for sequence in range(num_sequences):
                            timestamp = float(timestamps_data[record_num, sequence])
                            power = np.sqrt(voltage_samples.real**2 + voltage_samples.imag**2)[sequence,
                                        start_sample:end_sample]
                            power = np.where(power > 0, power, sys.float_info.epsilon)
                            power_db = 10 * np.log10(power)
                            power_list.append(power_db)
                            timestamps.append(float(timestamp))

                    new_power_array = np.fliplr(np.transpose(np.array(power_list)))
                    shift_num = new_power_array.shape[0]
                    power_array = np.concatenate(power_array[:num_seq-shift_num,:], new_power_array)

                    fig.canvas.draw()         
                    print(filename)
                    os.remove(filename)
                except Exception as err:
                    rt_print("Error appending data from {}".format(file_time))
                    os.remove(filename)
                    continue

            else:
                os.remove(filename)

            """
            elif "rawacf" in filename:
                #Read and convert data
                fields = filename.split(".")
                file_time = fields[0] + fields[1] + fields[2] + fields[3]


                # Make sure we only process the first slice for simulatenous multislice data for now
                if file_time == last_file_time:
                    os.remove(filename)
                    continue

                last_file_time = file_time

                slice_num = int(fields[5])
                try:
                    rt_print("Using pyDARNio to convert {}".format(filename))
                    converted = pydarnio.BorealisConvert(filename, "rawacf", "/dev/null", slice_num,
                                                    "site")
                    os.remove(filename)
                except pydarnio.exceptions.borealis_exceptions.BorealisConvert2RawacfError as e:
                    rt_print("Error converting {}".format(filename))
                    os.remove(filename)
                    continue

                data = converted.sdarn_dict

                fit_data = fitacf._fit(data[0])
                tmp = fit_data.copy()

                # Can't jsonify numpy so we convert to native types for rt purposes.
                for k,v in fit_data.items():
                    if hasattr(v, 'dtype'):
                        if isinstance(v, np.ndarray):
                            tmp[k] = v.tolist()
                        else:
                            tmp[k] = v.item()

                q.put(tmp)

            else:
                os.remove(filename)
            """


    def handle_remote_connection():
        """
        Compresses and serializes the data to send to the server.
        """
        while True:
            data_dict = q.get()
            serialized = json.dumps(data_dict)
            compressed = zlib.compress(serialized.encode('utf-8'))
            realtime_socket.send(compressed)

    threads = [threading.Thread(target=get_temp_file_from_datawrite),
                threading.Thread(target=handle_remote_connection)]

    for thread in threads:
        thread.daemon = True
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == '__main__':
    _main()

