#!/usr/bin/python

# Copyright 2017 SuperDARN Canada
#
# dsp_input_sim_options.py
# 2019-03-27
# options class for dsp input simulator

import json
import os


def ascii_encode_dict(data):
    ascii_encode = lambda x: x.encode('ascii')
    return dict(map(ascii_encode, pair) for pair in data.items())


class DSPInputOptions(object):
    """
    Parses the options from the config file that are relevant to the dsp input sim

    """
    def __init__(self):
        super(DSPInputOptions, self).__init__()

        if not os.environ["BOREALISPATH"]:
            raise ValueError("BOREALISPATH env variable not set")
        config_path = os.environ["BOREALISPATH"] + "/config.ini"
        try:
            with open(config_path, 'r') as config_data:
                raw_config = json.load(config_data)
        except IOError:
            errmsg = 'Cannot open config file at {0}'.format(config_path)
            raise IOError(errmsg)

        self._ringbuffer_size_bytes = float(raw_config["ringbuffer_size_bytes"])
        self._ringbuffer_name = raw_config["ringbuffer_name"]
        self._radctrl_to_dsp_identity = raw_config["radar_control_to_dsp_identity"]
        self._dsp_to_radctrl_identity = raw_config["dsp_to_radctrl_identity"]
        self._driver_to_dsp_identity = raw_config["driver_to_dsp_identity"]
        self._brian_to_dspbegin_identity = raw_config["brian_to_dspbegin_identity"]
        self._brian_to_dspend_identity = raw_config["brian_to_dspend_identity"]
        self._main_antenna_count = int(raw_config["main_antenna_count"])
        self._intf_antenna_count = int(raw_config["interferometer_antenna_count"])

    @property
    def ringbuffer_size_bytes(self):
        """
        @brief      Gets the ringbuffer size in bytes

        @param      self  The object

        @return     The ringbuffer size in bytes.
        """
        return self._ringbuffer_size_bytes

    @property
    def ringbuffer_name(self):
        """
        @brief      Gets the ringbuffer name

        @param      self  The object

        @return     The ringbuffer name.
        """
        return self._ringbuffer_name

    @property
    def radctrl_to_dsp_identity(self):
        """
        @brief      Gets the identity used for the radar control to dsp socket.

        @param      self  The object

        @return     The radar control to dsp identity.
        """
        return self._radctrl_to_dsp_identity

    @property
    def dsp_to_radctrl_identity(self):
        """ Gets the identity used for the dsp to radar control socket

        Returns:
            TYPE: The dsp to radar control identity.
        """
        return self._dsp_to_radctrl_identity

    @property
    def driver_to_dsp_identity(self):
        """
        @brief      Gets the identity used for the driver to dsp socket.

        @param      self  The object

        @return     The driver to dsp socket.
        """
        return self._driver_to_dsp_identity

    @property
    def brian_to_dspbegin_identity(self):
        """
        @brief      Gets the identity used for brian to dsp beginning socket.

        @param      self  The object

        @return    The brian to dsp begin identity.
        """
        return self._brian_to_dspbegin_identity

    @property
    def brian_to_dspend_identity(self):
        """
        @brief      Gets the identity used for brian to dsp end socket.

        @param      self  The object

        @return     The brian to dsp end identity.
        """
        return self._brian_to_dspend_identity

    @property
    def main_antenna_count(self):
        """
        Gets the number of main array antennas.

        :return:    number of main antennas.
        :rtype:     int
        """

        return self._main_antenna_count

    @property
    def intf_antenna_count(self):
        """
        Gets the number of interferometer array antennas.

        :return:    number of interferometer antennas.
        :rtype:     int
        """

        return self._intf_antenna_count
