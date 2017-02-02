from scipy import signal
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from scipy.fftpack import fft,ifft,fftshift
import math
import random
import cmath
import test_signals

def plot_fft(samplesa, rate):
    fft_samps=fft(samplesa)
    T= 1.0 /float(rate)
    num_samps=len(samplesa)
    if num_samps%2==1:
        xf = np.linspace(-1.0/(2.0*T), 1.0/(2.0*T), num_samps)
    else:
        #xf = np.arange(-1.0/(2.0*T), 1.0/(2.0*T),1.0/(T*num_samps))
        xf = np.linspace(-1.0/(2.0*T), 1.0/(2.0*T), num_samps)
    fig, smpplt = plt.subplots(1,1)
    fft_to_plot=np.empty([num_samps],dtype=complex)
    fft_to_plot=fftshift(fft_samps)
    smpplt.plot(xf, 1.0/num_samps * np.abs(fft_to_plot))
    return fig

def plot_all_ffts(bpass_filters, rate):
    fig, smpplt = plt.subplots(1,1)
    for filt in bpass_filters:
        fft_samps=fft(filt)
        T= 1.0 /float(rate)
        num_samps=len(filt)
        if num_samps%2==1:
            xf = np.linspace(-1.0/(2.0*T), 1.0/(2.0*T), num_samps)
        else:
            #xf = np.arange(-1.0/(2.0*T), 1.0/(2.0*T),1.0/(T*num_samps))
            xf = np.linspace(-1.0/(2.0*T), 1.0/(2.0*T), num_samps)
        fft_to_plot=np.empty([num_samps],dtype=complex)
        fft_to_plot=fftshift(fft_samps)
        smpplt.plot(xf, 1.0/num_samps * np.abs(fft_to_plot))
    return fig
    

def get_samples(rate,wave_freq,numberofsamps,start_rads):
    rate = float(rate)
    wave_freq = float(wave_freq)
    start_rads = float(start_rads)

    print start_rads
    sampling_freq=2*math.pi*wave_freq/rate
    sampleslen=int(numberofsamps)
    samples=np.empty([sampleslen],dtype=complex)
    for i in range(0,sampleslen):
        amp=1
        rads=math.fmod(start_rads + (sampling_freq * i), 2*math.pi)
        samples[i]=amp*math.cos(rads)+amp*math.sin(rads)*1j
    return samples

def make_pulse_train(fs,wave_freq):
    pullen=300 # us
    mpinc=1500 # us
    pulse_train=[0]
    #freq=10200 # kHz
    wave_freq=wave_freq
    rate=fs #kHz
    sampleslen=int(mpinc*1e-6*(pulse_train[-1]+1)*rate*1000)
    print sampleslen
    samples=np.empty([sampleslen],dtype=complex)
    i=1
    for pulse_time in pulse_train:
        if pulse_train.index(pulse_time)!=0:
            numzeros=(pulse_time-(pulse_train[pulse_train.index(pulse_time)-1]+1))*mpinc*1e-6*rate*1000
            for num in range(0,numzeros):
                samples[i]=0
                i=i+1
        pulse=get_samples(rate*1000,wave_freq*1000,pullen*1e-6*rate*1000)
        for samp in pulse:
            samples[i]=samp
            i=i+1
        for num in range(0,int((mpinc-pullen)*1e-6*rate*1000)):
            samples[i]=0
            i=i+1
    if i!=sampleslen-1:
        print("ERROR Sampleslen")
        print(i,sampleslen)
    return sampleslen, samples

def downsample(samples, rate):
    rate = int(rate)
    sampleslen = len(samples)/rate + 1 # should be an int
    samples_down=np.empty([sampleslen],dtype=complex)
    samples_down[0]=samples[0]
    print sampleslen
    for i in range(1,len(samples)):
        if i%rate==0:
            #print(i/rate)
            samples_down[i/rate]=samples[i]
    return samples_down


def fftnoise(f):
    f = np.array(f, dtype='complex')
    Np = (len(f) - 1) // 2
    phases = np.random.rand(Np) * 2 * np.pi
    phases = np.cos(phases) + 1j * np.sin(phases)
    f[1:Np+1] *= phases
    f[-1:-1-Np:-1] = np.conj(f[1:Np+1])
    return np.fft.ifft(f).real

def band_limited_noise(min_freq, max_freq, samples=1024, samplerate=1):
    freqs = np.abs(np.fft.fftfreq(samples, 1/samplerate))
    f = np.zeros(samples)
    idx = np.where(np.logical_and(freqs>=min_freq, freqs<=max_freq))[0]
    f[idx] = 1
    return fftnoise(f)

# SET VALUES
# Low-pass filter design parameters
fs = 12e6           # Sample rate, Hz
wave_freq = -1.95e6  # 1.8 MHz below centre freq (12.2 MHz if ctr = 14 MHz)
ctrfreq = 14000     # kHz
cutoff = 100e3      # Desired cutoff frequency, Hz
trans_width = 50e3  # Width of transition from pass band to stop band, Hz
numtaps = 512       # Size of the FIR filter.

decimation_rate = 50.0

# Calculate for Frerking's filter, Rf/fs which must be rational.

frerking = abs(decimation_rate * wave_freq / fs)
# find number of filter coefficients

for x in range(1, 100):
    if x*frerking % 1 == 0:
        number_of_coeff_sets = x
        break
else: # no break
    # P is over 100, don't use.
    sys.exit(["Error: number of coefficient sets required is too large."])
 
pulse_samples = test_signals.create_signal_1(wave_freq,4.0e6,10000,fs)
#pulse_samples = 0.008*np.asarray(random.sample(range(-10000,10000),10000))
#pulse_samples = band_limited_noise(-6000000,6000000,10000,fs)

print 'Fs = %d' % fs
print 'F = %d' % wave_freq
print 'R = %d' % decimation_rate
print 'P = %d' % number_of_coeff_sets

fig1= plot_fft(pulse_samples,fs)

lpass = signal.remez(numtaps, [0, cutoff, cutoff + trans_width, 0.5*fs],
                    [1, 0], Hz=fs)

bpass = np.array([])

for i in range(0, number_of_coeff_sets):
    if i == 0:
        print number_of_coeff_sets 
        start_rads = 0
        shift_wave = get_samples(fs,wave_freq,numtaps,start_rads)
        # we need a number of bpass filters depending on number_of_coeff_sets
        bpass = np.array([[l*i for l,i in zip(lpass,shift_wave)]])
    else:
        # shift wave needs to start in a different location
        # start at sampling rate * nth sample we are on (i * decimation_rate)
        start_rads = -math.fmod((2*math.pi*wave_freq/fs)*i*decimation_rate, 2*math.pi)
        print start_rads
        shift_wave = get_samples(fs,wave_freq,numtaps,start_rads)
        bpass = np.append(bpass, [[l*i for l,i in zip(lpass,shift_wave)]], axis=0)


# have to implement special convolution with multiple filters.
if len(lpass) > decimation_rate:
    num_output_samps = int((len(pulse_samples)-len(lpass))/decimation_rate)
else:
    num_output_samps = int(len(pulse_samples)/decimation_rate)

#
#
#
# CALCULATE USING FRERKING'S METHOD OF MULTIPLE COEFF SETS.

if len(lpass) > decimation_rate:
    first_sample_index = len(lpass)
else:
    first_sample_index = decimation_rate

output1=np.array([],dtype=complex)
for x in range(0,num_output_samps):
    bpass_filt_num = x % number_of_coeff_sets
    sum_array = np.array([l*i for l,i in zip(pulse_samples[(first_sample_index + x * decimation_rate - len(lpass)):(first_sample_index + x * decimation_rate)],bpass[bpass_filt_num][::-1])])
    #sum_array = np.array([l*i for l,i in zip(pulse_samples[(x*len(lpass)):((x+1)*len(lpass))],bpass[bpass_filt_num][::-1])])
    output_sum = 0.0
    for element in sum_array:
        output_sum += element
    output1 = np.append(output1,output_sum)

print num_output_samps
# Uncomment to plot the fft after first filter stage.
#response1 = plot_fft(output,fs)
#
# downsample
# FIRST DECIMATION STAGE - 

# noise_seq,noise_fft,noise_freq=get_noise(20,100)
# fig5 = plt.figure()
# plt.plot(np.arange(len(noise_seq)),noise_seq)
# plt.plot(noise_freq,noise_fft)


fig2 = plot_all_ffts(bpass,fs)
fig3 = plot_fft(lpass,fs)

fig4 = plt.figure()
plt.title('Frequency Responses of the P Bandpass Filters (Amp)')
plt.ylabel('Amplitude [dB]', color='b')
plt.xlabel('Frequency [rad/sample]')
plt.grid()
for i in range(0, number_of_coeff_sets):
    w,h = signal.freqz(bpass[i], whole=True)
    #ax1 = fig.add_subplot(111)
    plt.plot(w, 20 * np.log10(abs(h)))
plt.axis('tight')
    
fig5 = plt.figure()
plt.title('Frequency Responses of the P Bandpass Filters (Phase)')
plt.xlabel('Frequency [rad/sample]')
plt.ylabel('Angle (radians)', color='g')
plt.grid()
for i in range(0, number_of_coeff_sets):
    w,h = signal.freqz(bpass[i], whole=True)
    #ax2 = ax1.twinx()
    angles = np.unwrap(np.angle(h))
    plt.plot(w, angles)
plt.axis('tight')

# 
#
#
# CALCULATE USING ALEX'S METHOD, TRANSLATING SAMPLES AFTER DECIMATION.

output2=np.array([],dtype=complex)
for x in range(0,num_output_samps):
    bpass_filt_num = 0
    sum_array = np.array([l*i for l,i in zip(pulse_samples[(first_sample_index + x * decimation_rate - len(lpass)):(first_sample_index + x * decimation_rate)],bpass[bpass_filt_num][::-1])])
    output_sum = 0.0
    for element in sum_array:
        output_sum += element
    output2 = np.append(output2,output_sum)

figx = plot_fft(output2, fs/decimation_rate)

# Phase shift after Convolution.
for i in range(0, number_of_coeff_sets):
    # calculate the offset.
    start_rads = math.fmod((2*math.pi*wave_freq/fs)*i*decimation_rate, 2*math.pi)
    # offset every nth + i sample
    n = i
    while n < num_output_samps:
        output2[n]=output2[n]*cmath.exp(-1j*start_rads)
        n += number_of_coeff_sets

figy = plot_fft(output2, fs/decimation_rate)

#
#
#
# CALCULATE USING MIXING THEN DECIMATION, IN TWO STEPS.

# shifting the signal not the filter so we must shift in the other direction.
# we have to start the shift_wave in the right spot (offset by the first sample index that was used above)
shift_wave = get_samples(fs,-wave_freq,len(pulse_samples),(math.fmod((first_sample_index-1)*2*math.pi*wave_freq/fs, 2*math.pi)))
pulse_samples = [l*i for l,i in zip(pulse_samples,shift_wave)]

# filter before decimating to prevent aliasing
fig7 = plot_fft(pulse_samples,fs)
output = signal.convolve(pulse_samples,lpass,mode='valid') #/ sum(lpass)

# OR, can convolve using the same method as above (which is using the valid method).
#output=np.array([],dtype=complex)
#for x in range(0,len(pulse_samples)-first_sample_index):
#    sum_array = np.array([l*i for l,i in zip(pulse_samples[(first_sample_index + x - len(lpass)):(first_sample_index + x)],lpass[::-1])])
#    output_sum = 0.0
#    for element in sum_array:
#        output_sum += element
#    output = np.append(output,output_sum)

fig8 = plot_fft(output, fs)

# Decimate here.
output3=np.array([],dtype=complex)
for x in range(0,num_output_samps):
    samp = output[x * decimation_rate]
    output3=np.append(output3, samp)
# Plot the output using Frerking's method
new_fs = float(fs) / decimation_rate
#output_down=downsample(output, decimation_rate)

#
#
#
#
# Plot FFTs and Phase responses of all methods
#fig6, smpplt = plt.subplots(1,1)
fig6 = plt.figure()
fft_samps1=fft(output1)
fft_samps2=fft(output2)
fft_samps3=fft(output3)
T= 1.0 /float(new_fs)
num_samps=len(output1)
if num_samps%2==1:
   xf = np.linspace(-1.0/(2.0*T), 1.0/(2.0*T), num_samps)
else:
   #xf = np.arange(-1.0/(2.0*T), 1.0/(2.0*T),1.0/(T*num_samps))
   xf = np.linspace(-1.0/(2.0*T), 1.0/(2.0*T), num_samps)
print(num_samps)
#print(len(fft_samps))
#print(len(xf))
ax1 = fig6.add_subplot(111)
plt.title('Response of All Filters (Amp)')
plt.ylabel('Amplitude [dB]', color='b')
plt.xlabel('Frequency [rad/sample]')
plt.grid()
fft_to_plot1=np.empty([num_samps],dtype=complex)
fft_to_plot1=fftshift(fft_samps1)
fft_to_plot2=np.empty([num_samps],dtype=complex)
fft_to_plot2=fftshift(fft_samps2)
fft_to_plot3=np.empty([num_samps],dtype=complex)
fft_to_plot3=fftshift(fft_samps3)
plt.plot(xf, 1.0/num_samps * np.abs(fft_to_plot1), 'g')
plt.plot(xf, 1.0/num_samps * np.abs(fft_to_plot2), 'y')
plt.plot(xf, 1.0/num_samps * np.abs(fft_to_plot3), 'c')
#plt.plot(xf, 1.0/num_samps * np.abs( np.roll( fft_to_plot3, int(-len(output1) * wave_freq / (1.0/T)))), 'c')
ax2 = ax1.twinx()
plt.ylabel('Phase [rads]', color='g')
angles1=np.angle(fft_to_plot1)
angles2=np.angle(fft_to_plot2)
angles3=np.angle(fft_to_plot3)
plt.plot(xf, angles1, 'm')
plt.plot(xf, angles2, 'g')
plt.plot(xf, angles3, 'r')


plt.show()
