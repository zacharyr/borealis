#!/usr/bin/python

# write an experiment that creates a new control program.
import os
import sys
import copy

BOREALISPATH = os.environ['BOREALISPATH']
sys.path.append(BOREALISPATH)

from experiment_prototype.experiment_prototype import ExperimentPrototype
import experiments.superdarn_common_fields as scf

class Multipolitescan(ExperimentPrototype):

    def __init__(self):
        cpid = 350320

        if scf.IS_FORWARD_RADAR:
            beams_to_use = scf.STD_16_FORWARD_BEAM_ORDER
        else:
            beams_to_use = scf.STD_16_REVERSE_BEAM_ORDER

        if scf.opts.site_id in ["sas", "pgr"]:
            freqs = (10500, 13000)
        if scf.opts.site_id in ["rkn"]:
            freqs = (10100, 10600, 10900, 11500, 12300, 13200) 
        if scf.opts.site_id in ["inv"]:
            freqs = (10300, 12200)
        if scf.opts.site_id in ["cly"]:
            freqs = (10500, 12500)

        if scf.opts.site_id in ["cly", "rkn", "inv"]:
            num_ranges = scf.POLARDARN_NUM_RANGES
        if scf.opts.site_id in ["sas", "pgr"]:
            num_ranges = scf.STD_NUM_RANGES

        slice_1 = {  # slice_id = 0, the first slice
            "pulse_sequence": scf.SEQUENCE_7P,
            "tau_spacing": scf.TAU_SPACING_7P,
            "pulse_len": scf.PULSE_LEN_45KM,
            "num_ranges": num_ranges,
            "first_range": scf.STD_FIRST_RANGE,
            "intt": 3500,  # duration of an integration, in ms
            "beam_angle": scf.STD_16_BEAM_ANGLE,
            "beam_order": beams_to_use,
            "rxfreq" : freqs[0], #kHz
            "acf": True,
            "xcf": True,  # cross-correlation processing
            "acfint": True,  # interferometer acfs
        }

        slice_2 = copy.deepcopy(slice_1)
        slice_3 = copy.deepcopy(slice_1)
        slice_4 = copy.deepcopy(slice_1)
        slice_5 = copy.deepcopy(slice_1)
        slice_6 = copy.deepcopy(slice_1)

        slice_2['rxfreq'] = freqs[1]
        slice_3['rxfreq'] = freqs[2]
        slice_4['rxfreq'] = freqs[3]
        slice_5['rxfreq'] = freqs[4]
        slice_6['rxfreq'] = freqs[5]

        rxctrfreq = 11650

        super(Multipolitescan, self).__init__(cpid, rxctrfreq=rxctrfreq,
                comment_string='Multiple frequency politescan inttime interfaced')

        self.add_slice(slice_1)
        self.add_slice(slice_2, interfacing_dict={0: 'INTTIME'})
        self.add_slice(slice_3, interfacing_dict={0: 'INTTIME'})
        self.add_slice(slice_4, interfacing_dict={0: 'INTTIME'})
        self.add_slice(slice_5, interfacing_dict={0: 'INTTIME'})
        self.add_slice(slice_6, interfacing_dict={0: 'INTTIME'})

