#!/usr/bin/python

import os
import sys

BOREALISPATH = os.environ['BOREALISPATH']
sys.path.append(BOREALISPATH)

# write an experiment that creates a new control program.
from experiment_prototype.experiment_prototype import ExperimentPrototype
import experiments.superdarn_common_fields as scf

from experiment_prototype.decimation_scheme.decimation_scheme import DecimationStage, DecimationScheme

class NormalscanBoresite(ExperimentPrototype):
    # with 7 PULSE sequence
    def __init__(self):
        cpid = 100000001

        super(NormalscanBoresite, self).__init__(cpid)

        self.add_slice({  # slice_id = 0, there is only one slice.
            "pulse_sequence": scf.SEQUENCE_7P,
            "tau_spacing": scf.TAU_SPACING_7P,
            "pulse_len": scf.PULSE_LEN_45KM,
            "num_ranges": scf.STD_NUM_RANGES,
            "first_range": scf.STD_FIRST_RANGE,
            "intt": 3500,  # duration of an integration, in ms
            "beam_angle": [0.0],
            "beam_order": [0],
            "txfreq" : scf.COMMON_MODE_FREQ_1, #kHz
            "acf": True,
            "xcf": True,  # cross-correlation processing
            "acfint": True,  # interferometer acfs
        })
