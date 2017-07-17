#!/usr/bin/python

""" Scans are made up of AveragingPeriods, these are typically a 3sec time of
the same pulse sequence pointing in one direction.  AveragingPeriods are made
up of Sequences, typically the same sequence run ave. 21 times after a clear
frequency search.  Sequences are made up of pulse_time lists, which give
timing, CPObject, and pulsenumber. CPObject provides channels, pulseshift (if
any), freq, pulse length, beamdir, and wavetype.
"""

import sys
from averaging_periods import AveragingPeriod
from experiments.list_tests import slice_combos_sorter
from scan_class_base import ScanClassBase
from experiments.experiment_exception import ExperimentException


class Scan(ScanClassBase):
    """ 
    Made up of AveragingPeriods at defined beam directions, and some other metadata for the scan itself.
    """

    def __init__(self, scan_keys, scan_slice_dict, scan_interface, options):

        ScanClassBase.__init__(self, scan_keys, scan_slice_dict, scan_interface, options)

        # scan metadata - must be the same between all slices combined in scan.  Metadata includes:
        self.scanboundf = self.slice_dict[self.keys[0]]['scanboundflag']
        for slice_id in self.keys:
            if self.slice_dict[slice_id]['scanboundflag'] != self.scanboundf:
                errmsg = """Scan Boundary Flag not the Same Between Slices {} and {} combined in Scan"""\
                    .format(self.keys[0], slice_id)
                raise ExperimentException(errmsg)
        if self.scanboundf == 1:
            self.scanbound = self.slice_dict[self.keys[0]]['scanbound']
            for slice_id in self.keys:
                if self.slice_dict[slice_id]['scanbound'] != self.scanbound:
                    errmsg = """Scan Boundary not the Same Between Slices {} and {}
                         combined in Scan""".format(self.keys[0], slice_id)
                    raise ExperimentException(errmsg)

        # NOTE: for now we assume that when INTTIME combined, the AveragingPeriods of the various slices in the scan are
        #   just interleaved 1 then the other.

        # Create a dictionary of beam directions for slice_id #
        self.beamdir = {}
        self.scan_beams = {}
        for slice_id in self.keys:
            self.beamdir[slice_id] = self.slice_dict[slice_id]['beam_angle']
            self.scan_beams[slice_id] = self.slice_dict[slice_id]['beam_order']

        # However we need to make sure the number of inttimes (as determined by length of slice['scan'] is the same
        # for slices combined in the averaging period.
        for inttime_list in self.slice_id_inttime_lists:
            for slice_id in inttime_list:
                if len(self.scan_beams[slice_id]) != len(self.scan_beams[inttime_list[0]]):
                    errmsg = """Slice {} and {} are mixed within the AveragingPeriod but do not have the same number of
                        AveragingPeriods in their scan""".format(self.keys[0], slice_id)
                    raise ExperimentException(errmsg)

        self.aveperiods = []
        self.slice_id_inttime_lists = self.get_inttimes()
        self.nested_slice_list = self.slice_id_inttime_lists

        for params in self.prep_for_nested_scan_class():
            self.aveperiods.append(AveragingPeriod(*params))

        # AveragingPeriod will be in slice_id # order

    def get_inttimes(self):
        intt_combos = []

        for k in self.interface.keys():
            if (self.interface[k] == "PULSE" or self.interface[k] == "INTEGRATION"):
                intt_combos.append([k])
        # Save only the keys that are combinations within inttime.

        combos = slice_combos_sorter(intt_combos, self.keys)  # TODO make this a method of the base class?

        return combos