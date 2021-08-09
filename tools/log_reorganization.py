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
    """
    dates_cmd = "ls {dir} | grep -o \"^[[:digit:]]\{{4\}}\.[[:digit:]]\{{2\}}\.[[:digit:]]\{{2\}}\" | uniq > /tmp/dates.txt;"

    dates_cmd = dates_cmd.format(dir=args.log_dir)
    execute_cmd(dates_cmd)


def create_dirs_and_move_files():
    """
    Creates a directory for each unique day that has log files,
    and moves the respective log files into it.
    """
    date_file = "/tmp/dates.txt"

    with open(date_file, 'r') as f:
        for line in f:
            date = line.strip().split(".")

            # Check that the directory doesn't already exist
            check_dir_cmd = "find /data/borealis_logs/ -name \"{date}\";".format(date="".join(date))
            output = execute_cmd(check_dir_cmd)
            if "".join(date) not in output:
                # Make a new directory for that date
                mkdir_cmd = "mkdir {log_dir}{year}{month}{day};"
                mkdir_cmd = mkdir_cmd.format(log_dir=args.log_dir, year=date[0], month=date[1], day=date[2])
                execute_cmd(mkdir_cmd)

            # Move all files from the date to the its respective directory
            mv_cmd = "mv {log_dir}{date_split}.* {log_dir}{date_joined}/;"
            mv_cmd = mv_cmd.format(date_split=line.strip(), log_dir=args.log_dir, date_joined="".join(date))
            execute_cmd(mv_cmd)


def rename_files():
    """
    Renames the log files from YYYY.MM.DD.HH:MM-[module] to YYYYMMDD.HH.MM-[module].
    """
    ls_dir_cmd = "ls -d {log_dir}*/".format(log_dir=args.log_dir)
    output = execute_cmd(ls_dir_cmd)

    dates = output.strip().split()

    for date in dates:
        ls_logs_cmd = "ls {date}".format(date=date)
        output = execute_cmd(ls_logs_cmd)
        logs = output.strip().split()

        for log in logs:
            timestamp = log.split(".")
            timestamp = "".join(timestamp[0:3]) + "." + ".".join(timestamp[3].split(":"))
            mv_cmd = "mv {date}{log} {date}{timestamp};".format(date=date, log=log, timestamp=timestamp)
            execute_cmd(mv_cmd)


parser = ap.ArgumentParser(usage=usage_msg(), description="Updates Borealis log directory")
parser.add_argument("--log_dir", help="Path to the log file directory", default="/data/borealis_logs/")
args = parser.parse_args()

if not os.path.isdir(args.log_dir):
    print("Log directory does not exist: {}".format(args.log_dir))
    sys.exit(1)

unique_dates()
create_dirs_and_move_files()
rename_files()

