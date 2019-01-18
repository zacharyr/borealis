import os
import mmap
import sys
import numpy as np
import deepdish as dd
import posix_ipc as ipc
import datetime as dt

import dsp_input_options as dio
borealis_path = os.environ['BOREALISPATH']
if not borealis_path:
    raise ValueError("BOREALISPATH env variable not set")

if __debug__:
    sys.path.append(borealis_path + '/build/debug/utils/protobuf')
else:
    sys.path.append(borealis_path + '/build/release/utils/protobuf')

import rxsamplesmetadata_pb2
import sigprocpacket_pb2
import datawritemetadata_pb2

sys.path.append(borealis_path + '/utils/')
from zmq_borealis_helpers import socket_operations as so



def main():
    options = dio.DSPInputOptions()

    NRANGE = 0
    FRANGE = 0
    BEAM_DIRECTIONS = [[1+0j]*(options.main_antenna_count + options.intf_antenna_count)]
    BLANKS = []
    RX_ONLY = False
    PULSE_LEN = 300 #us
    TAU_SPACING = 1500
    PULSES = []
    ACF = False
    XCF = False
    ACFINT = False
    RSEP = 45
    LTAB = []
    INTERFACING = ""
    BEAMS = [{'num':0, 'azm': 0}]
    def fill_datawrite_meta(record, meta, sqn_num, output_rate):
        meta.experiment_id = record['experiment_id']
        meta.experiment_string = record['experiment_string'] + "_simulated"
        meta.integration_time = record['int_time']
        meta.nave = record['data_dimensions'][0]
        meta.last_seqn_num = sqn_num + meta.nave
        meta.scan_flag = record['start_scan_marker']
        meta.tx_center_freq = record['tx_center_freq']
        meta.rx_center_freq = record['rx_center_freq']

        for i,f in enumerate(record['rx_frequencies']):
            sequence = meta.sequences.add()
            rx_chan = sequence.add()
            rx_chan.slice_id = i
            rx_chan.rx_freq = f


    def fill_samples_metadata(record, samples_metadata, ringbuffer_size):
        samples_metadata.initialization_time = 0.0
        samples_metadata.rx_sample_rate = records['rx_sample_rate']
        samples_metadata.sequence_time = record['int_time']
        samples_metadata.ringbuffer_size = ringbuffer_size

    def fill_sigproc_packet(record, sig_packet, sequence_num, offset, output_rate):
        sig_packet.sequence_num = sequence_num
        sig_packet.kerneltime = record["int_time"]
        sig_packet.sequence_time = record["int_time"]
        sig_packet.rxrate = record["rx_sample_rate"]
        sig_packet.offset_to_first_rx_sample = offset
        sig_packet.output_rate = output_rate

        for i,f in enumerate(record['rx_frequencies']):
            rx_chan = .add()
            rx_chan.slice_id = i
            rx_chan.rx_freq = f

    filename = sys.argv[1]
    records = dd.io.load(filename).values()



    sockets = so.create_sockets([options.radctrl_to_dsp_identity, options.dsp_to_radctrl_identity,
                                     options.driver_to_dsp_identity,
                                     options.brian_to_dspbegin_identity,
                                    options.brian_to_dspend_identity])

    radctrl_to_dsp = sockets[0]
    dsp_to_radctrl = sockets[1]
    driver_to_dsp = sockets[2]
    brian_to_dspbegin = sockets[3]
    brian_to_dspend = sockets[4]

    total_samps = np.prod(records[0]['data_dimensions'][1:])

    ringbuffer_size = total_samps * np.dtype(np.complex64).itemsize

    shm = ipc.SharedMemory(options.ringbuffer_name, mode=ipc.O_CREX, size=ringbuffer_size)
    mapped_mem = mmap.mmap(shm.fd, shm.size)
    np_ringbuffer = np.frombuffer(mapped_mem, dtype=np.complex64)

    sig_packet = sigprocpacket_pb2.SigProcPacket()

    samples_metadata = rxsamplesmetadata_pb2.RxSamplesMetadata()
    fill_samples_metadata(records[0], samples_metadata, ringbuffer_size)

    datawrite_metadata = datawritemetadata_pb2.IntegrationTimeMetadata()

    sqn_num = 0
    for rec in records:
        data = np.reshape(rec['data'], tuple(rec['data_dimensions']))

        for i in data.shape[0]:
            np.copyto(np_ringbuffer, i)
            so.send_bytes(radctrl_to_dsp, options.dsp_to_radctrl_identity,
                            sig_packet.SerializeToString())


            samples_metadata.start_time = 0.0
            samples_metadata.sequence_num = sqn_num





