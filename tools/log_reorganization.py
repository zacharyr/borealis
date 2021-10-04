#!/bin/python3

"""
Copyright SuperDARN Canada 2021
Remington Rohel

Script for reorganizing Borealis log file directories.
"""


def usage_msg():
    """
    Return the usage message for this process.

    This is used if a -h flag or invalid arguments are provided.

    :returns: the usage message
    """

    usage_message = """ log_reorganization.py [-h] [log_directory]

    This script will reorganize the Borealis log file directory structure
    and naming convention. The default log_directory is /data/borealis_logs 
    unless a different directory is passed as an argument.
    
    Within log_directory, subdirectories will be made for each date that
    has a log file. Each subdirectory is the date of the log files within
    it, e.g. YYYYMMDD, and will contain all log files from that day.
    All log files from that date will also be renamed, to follow the format
    YYYYMMDD.HH.MM-[module] .

    Example usage:
    python3 log_reorganization.py /mnt/borealis_logs/

    """
    return usage_message


def main():
    print(usage_msg())


if __name__ == '__main__':
    main()
