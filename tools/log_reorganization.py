#!/bin/python3

"""
Copyright SuperDARN Canada 2021
Remington Rohel

Script for reorganizing Borealis log file directories.
"""

import subprocess as sp
import argparse as ap
import os
import sys


def usage_msg():
    """
    Return the usage message for this process.

    This is used if a -h flag or invalid arguments are provided.

    :returns: the usage message
    """

    usage_message = """ log_reorganization.py [-h] [--log_dir LOG_DIR]

    This script will reorganize the Borealis log file directory structure
    and naming convention. The default log_dir is /data/borealis_logs 
    unless a different directory is passed as an argument.
    
    Within log_dir, subdirectories will be made for each date that
    has a log file. Each subdirectory is the date of the log files within
    it, e.g. YYYYMMDD, and will contain all log files from that day.
    All log files from that date will also be renamed, to follow the format
    YYYYMMDD.HH.MM-[module] .

    Example usage:
    python3 log_reorganization.py /mnt/borealis_logs/

    """
    return usage_message


def execute_cmd(cmd):
    """
    Execute a shell command and return the output

    :param      cmd:  The command
    :type       cmd:  string

    :returns:   Decoded output of the command.
    :rtype:     string
    """
    output = sp.check_output(cmd, shell=True)
    return output.decode('utf-8')


def unique_dates():
    """
    Get all the unique dates from the log files, and
    stores them in a text file.

    :return:
    """
    dates_cmd = "ls {dir} | grep -o \"^[[:digit:]]\{{4\}}\.[[:digit:]]\{{2\}}\.[[:digit:]]\{{2\}}\" | uniq > /tmp/dates.txt;"

    dates_cmd = dates_cmd.format(dir=args.log_dir)
    execute_cmd(dates_cmd)


parser = ap.ArgumentParser(usage=usage_msg(), description="Updates Borealis log directory")
parser.add_argument("--log_dir", help="Path to the log file directory", default="/data/borealis_logs/")
args = parser.parse_args()

if not os.path.isdir(args.log_dir):
    print("Log directory does not exist: {}".format(args.log_dir))
    sys.exit(1)

unique_dates()

