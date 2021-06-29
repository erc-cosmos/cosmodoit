import numpy as np
from scipy.io.wavfile import write
import matplotlib.pyplot as plt

def create_wav(fs   = 22050,
               freq = np.array([100, 200, 300, 400, 510, 630, 770, 920, 1080, 1270, 1480,
                                1720, 2000, 2320, 2700, 3150, 3700, 4400, 5300, 6400,
                                7700, 9500, 12000, 15500]),
               loudness  = np.linspace(0.2, 1, 3),
               duration  = 0.2,
               filename  = 'test.wav',
               wavExport = False,
               wavPlot   = False):
    """y = create_wav(fs,freq,loudness,duration,filename)

    create a wav file for testing some of the functions
    sinus with different frequencies and loudness
    default settings: frequency based on bark scale

    usage e.g.:
            sound(ma_test_create_wav)  listen to defaults
            freq = repmat([150,350,350,0],1,10);
            sound(ma_test_create_wav(22050,freq,.2,0.2))  periodic pattern

    fs       ... sampling frequency (default = 22050 Hz)
    freq     ... frequencies of sinus tones [Hz] (use [] for default)
    loudness ... loudness levels to use [0..1] (use [] for default)
    duration ... duration of sinus tones in sec (use [] for default = 0.2 sec)
    filename ... if given, wav file is created
    wavExport... export array as mono 16 bit wav file
    wavPlot  ... plot resulting waveform

    y        ... output vector [0..1]

    elias 16.5.2004 ported by Daniel Bedoya 29.6.2021 """
    
    freq = freq[freq<fs/2]
    N = 1024
    y = np.zeros((len(freq)*len(loudness)*int(np.round(duration*fs)),1))
    x = np.reshape(np.arange(0,N),(1,N))
    w = 0.5*(1-np.cos(2*np.pi*x/(N-1))) # hann
    n = int(N/2)

    L = int(np.round(fs*duration))
    idx = np.reshape(np.linspace(0,np.round(fs*duration)-1, L, dtype=int),(L,1))
    for i in range(0,len(loudness)):
        for j in range(0,len(freq)):
            y_tmp = np.sin(np.linspace(0,freq[j]*2*np.pi*duration, int(fs*duration)))
            y_tmp[0:n] = y_tmp[0:n]* np.transpose(w[0,0:n])
            y_tmp[L-n-1:L] = y_tmp[L-n-1:L] * np.transpose(w[0,n-1:N])
            y[idx[:,0]] = np.reshape(y_tmp*loudness[i],(L,1))
            idx = idx + L
    if wavExport:
        data = np.int16(y/np.max(np.abs(y))*32767)
        write(filename=filename, rate=fs, data=data)
    if wavPlot:
        plt.plot(y)
        plt.show()
    return y
