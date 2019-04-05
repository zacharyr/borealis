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

import experiment_prototype.decimation_scheme.decimation_scheme as ds


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
    RX_RATE = 5.0e6
    OUTPUT_RATE = 10000.0/3

    dm_scheme = ds.DecimationScheme(RX_RATE, OUTPUT_RATE)

    pulse_offset = (PULSE_LEN/2) * 1e-6 + options.tr_window_time

    def fill_datawrite_meta(record, meta, sqn_num):
        meta.experiment_id = record['experiment_id']
        meta.experiment_string = record['experiment_string'] + "_simulated"
        meta.integration_time = record['int_time']
        meta.nave = record['data_dimensions'][0]
        meta.last_seqn_num = sqn_num + meta.nave -1
        meta.scan_flag = record['scan_start_marker']
        meta.tx_center_freq = record['tx_center_freq']
        meta.rx_center_freq = record['rx_center_freq']
        meta.output_sample_rate = dm_scheme.output_sample_rate

        for i,f in enumerate(record['rx_frequencies']):
            sequence = meta.sequences.add()
            sequence.blanks[:] = BLANKS

            rx_chan = sequence.rxchannel.add()
            rx_chan.slice_id = i
            rx_chan.rxfreq = f
            rx_chan.frang = FRANGE
            rx_chan.nrang = NRANGE
            rx_chan.rx_only = RX_ONLY
            rx_chan.pulse_len = PULSE_LEN
            rx_chan.tau_spacing = TAU_SPACING
            rx_chan.acf = ACF
            rx_chan.xcf = XCF
            rx_chan.acfint = ACFINT
            rx_chan.rsep = RSEP
            rx_chan.comment = "simulated data"
            rx_chan.interfacing = INTERFACING

            main_ants = list(range(record['main_antenna_count']))
            intf_ants = list(range(record['intf_antenna_count']))

            rx_chan.rx_main_antennas[:] = main_ants
            rx_chan.rx_intf_antennas[:] = intf_ants

            for beam in BEAMS:
                b = rx_chan.beams.add()
                b.beamnum = beam['num']
                b.beamazimuth = beam['azm']

            for pulse in PULSES:
                p = rx_chan.ptab.add()
                p.pulse_position = pulse


            for j,lags in enumerate(LTAB):
                l = rx_chan.ltab.lag.add()
                l.pulse_position[:] = lags
                l.lag_num = j


    def fill_samples_metadata(record, samples_metadata, sequence_num, start_time):
        samples_metadata.initialization_time = 0.0
        samples_metadata.sequence_num = sequence_num
        samples_metadata.rx_rate = record['rx_sample_rate']
        samples_metadata.sequence_time = record['int_time']
        samples_metadata.sequence_start_time = start_time
        samples_metadata.ringbuffer_size = record['num_samps'] - 2*10000
        samples_metadata.numberofreceivesamples = record['num_samps']


    def fill_sigproc_packet(record, sig_packet, sequence_num):
        sig_packet.sequence_num = sequence_num
        sig_packet.kerneltime = record["int_time"]
        sig_packet.sequence_time = record["int_time"]
        sig_packet.rxrate = record["rx_sample_rate"]
        sig_packet.offset_to_first_rx_sample = pulse_offset
        sig_packet.output_sample_rate = dm_scheme.output_sample_rate

        for i,f in enumerate(record['rx_frequencies']):
            rx_chan = sig_packet.rxchannel.add()
            rx_chan.slice_id = i
            rx_chan.rxfreq = f
            rx_chan.nrang = NRANGE
            rx_chan.frang = FRANGE
            for beam_dir in BEAM_DIRECTIONS:
                beam = rx_chan.beam_directions.add()
                for b in beam_dir:
                    phase = beam.phase.add()
                    phase.real_phase = b.real
                    phase.imag_phase = b.imag

        for stage in dm_scheme.stages:
            dm_stage = sig_packet.decimation_stages.add()
            dm_stage.stage_num = stage.stage_num
            dm_stage.input_rate = stage.input_rate
            dm_stage.dm_rate = stage.dm_rate
            dm_stage.filter_taps[:] = stage.filter_taps



    filename = sys.argv[1]
    records = list(dd.io.load(filename).values())

    sockets = so.create_sockets([options.radctrl_to_dsp_identity,
                                    options.driver_to_dsp_identity,
                                    options.brian_to_dspbegin_identity,
                                    options.brian_to_dspend_identity,
                                    options.radctrl_to_dw_identity], options.router_addr)

    radctrl_to_dsp = sockets[0]
    driver_to_dsp = sockets[1]
    brian_to_dspbegin = sockets[2]
    brian_to_dspend = sockets[3]
    radctrl_to_dw = sockets[4]

    total_samps = int(np.prod(records[0]['data_dimensions'][1:]))

    ringbuffer_bytes = int(total_samps * np.dtype(np.complex64).itemsize)

    shm = ipc.SharedMemory(options.ringbuffer_name, flags=ipc.O_CREAT, size=ringbuffer_bytes)

    sqn_num = 0
    for rec in records:
        data = np.reshape(rec['data'], tuple(rec['data_dimensions']))

        start_sqn_num = sqn_num
        for i in range(data.shape[0]):
            mapped_mem = mmap.mmap(shm.fd, shm.size)
            #print(data[i])
            mapped_mem.write(data[i].tobytes())
            mapped_mem.close()

            sig_packet = sigprocpacket_pb2.SigProcPacket()
            fill_sigproc_packet(rec, sig_packet, sqn_num)
            so.send_bytes(radctrl_to_dsp, options.dsp_to_radctrl_identity,
                            sig_packet.SerializeToString())


            samples_metadata = rxsamplesmetadata_pb2.RxSamplesMetadata()
            start_time = sqn_num * (rec['num_samps']/RX_RATE)
            fill_samples_metadata(rec, samples_metadata, sqn_num, start_time)

            so.recv_request(driver_to_dsp, options.dsp_to_driver_identity, lambda *args: None)
            so.send_bytes(driver_to_dsp, options.dsp_to_driver_identity,
                            samples_metadata.SerializeToString())

            so.send_request(brian_to_dspbegin, options.dspbegin_to_brian_identity,
                            "Requesting work begins")
            so.recv_reply(brian_to_dspbegin, options.dspbegin_to_brian_identity, lambda *args: None)

            so.send_request(brian_to_dspend, options.dspend_to_brian_identity,
                            "Requesting work ends")
            so.recv_bytes(brian_to_dspend, options.dspend_to_brian_identity, lambda *args: None)
            sqn_num += 1

        datawrite_metadata = datawritemetadata_pb2.IntegrationTimeMetadata()
        fill_datawrite_meta(rec, datawrite_metadata, start_sqn_num)
        so.send_bytes(radctrl_to_dw, options.dw_to_radctrl_identity,
                        datawrite_metadata.SerializeToString())

main()




