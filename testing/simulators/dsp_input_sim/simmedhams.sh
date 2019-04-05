#!/bin/bash

# ARGS:
# $1 :  run-type, including release, debug, and python-profiling
# $2 :  file to run sim on

echo ""
echo "Simulator Boot"

rm -r /dev/shm/*

# These are the commands to in each window.
if [ "$1" = "release" ]; then
    start_brian="python3 -O brian/brian.py --router-only; bash"
    start_sim="sleep 0.001s; python3 -O testing/simulators/dsp_input_sim/dsp_input_sim.py "$2"; bash"
    start_datawrite="sleep 0.001s;python3 -O data_write/data_write.py --file-type=hdf5 --enable-pre-bfiq; bash;"
    start_dsp="sleep 0.001s; source mode "$1"; signal_processing; bash;"
elif [ "$1" = "python-profiling" ]; then  # uses source mode release for C code.
    start_brian="python3 -O -m cProfile -o testing/python_testing/brian.cprof brian/brian.py --router-only; bash"
    start_sim="sleep 0.001s; python3 testing/simulators/dsp_input_sim/dsp_input_sim.py "$2"; bash;"
    start_datawrite="sleep 0.001s; python3 -O -m cProfile -o testing/python_testing/data_write.cprof data_write/data_write.py; bash;"
    start_dsp="sleep 0.001s; source mode "$1"; signal_processing; bash;"
elif [ "$1" = "debug" ] || [ "$2" = "engineeringdebug" ]; then
    start_brian="python3 brian/brian.py --router-only; bash"
    start_sim="sleep 10s; python3 testing/simulators/dsp_input_sim/dsp_input_sim.py "$2"; bash;"
    #start_datawrite="sleep 0.001s; python3 data_write/data_write.py --enable-bfiq --enable-pre-bfiq --enable-tx --enable-raw-rf; bash"
    start_datawrite="sleep 0.001s; python3 data_write/data_write.py --enable-pre-bfiq --enable-raw-rf; bash"
    start_dsp="sleep 0.001s; source mode "$1"; /usr/local/cuda/bin/cuda-gdb -ex start signal_processing; bash"
else
    echo "Mode '$1' is unknown, exiting without running Borealis"
    exit -1
fi

# Modify screen rc file
sed -i.bak "s#START_BRIAN#$start_brian#; \
            s#START_DATAWRITE#$start_datawrite#; \
            s#START_SIM#$start_sim#; \
            s#START_DSP#$start_dsp#;" simscreenrc

# Launch a detached screen with editted layout.
screen -S sim -c simscreenrc
# Return the original config file
mv simscreenrc.bak simscreenrc
