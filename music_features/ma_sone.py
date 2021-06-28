# Compute loudness matrix and total loudness using Stevens method from the MA Toolbox
# 
# http://www.ofai.at/~elias.pampalk/ma/documentation.html#ma_sone
# Created by Elias Pampalk, ported by Daniel Bedoya 2020-06-28

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

testFile = '/Users/bedoya/OneDrive/COSMOS/Code/test.txt'
wav      = np.loadtxt(testFile, dtype='float')

# defaults
Ltype     = 'sone'
outerear  = 'terhardt'
bark_type = 'table' # test 1st case 
# bark_type = [20, 20000, 50] # test 2nd case
dB_max       = 96
plotLoudness = True
doSpread  = True
doSone    = True
fs        = 44100
fft_size  = 512
hop_size  = 256

def maSone(wav,
           Ltype        = 'sone',
           outerear     = 'terhardt',
           bark_type    = 'table',
           dB_max       = 96,
           plotLoudness = True,
           doSpread     = True,
           doSone       = True,
           fs           = 44100,
           fft_size     = 512,
           hop_size     = 256):
    pass

def array2dB(vector):
    vector[vector < 1] = 1 # avoid negative values
    dB = 10*np.log10(vector)
    return dB

def isNumeric(x):
    try:
        float(x)
        return True
    except ValueError:
        return False
    
def outerEarCases(outerear, fft_freq):
    """Compute model according to case"""
    N = len(fft_freq)
    w_Adb = np.ones((1, len(fft_freq)), dtype=float)
    if outerear == 'terhardt': # terhardt 1979 (calculating virtual pitch, hearing research #1, pp 155-182)
        w_Adb[0,0] = 0;
        w_Adb[0, range(1,len(fft_freq))] = 10**((-3.64*(fft_freq[1:N]/1000)**-0.8
                                        + 6.5 * np.exp(-0.6 * (fft_freq[1:N]/1000 - 3.3)**2)
                                        - 0.001*(fft_freq[1:N]/1000)**4)/20)
        w_Adb = w_Adb**2
        return w_Adb
    if outerear == 'modified_terhardt': # less emph around 4Hz, more emphasis on low freqs
        w_Adb[0] = 0
        w_Adb[0, range(1,len(fft_freq))] = 10**((.6*-3.64*(fft_freq[1:N]/1000)**-0.8
                                         + 0.5 * np.exp(-0.6 * (fft_freq[1:N]/1000 - 3.3)**2)
                                         - 0.001*(fft_freq[1:N]/1000)**4)/20)
        w_Adb = w_Adb**2
        return w_Adb
    if outerear == 'none': # all weighted equally
        return w_Adb
    else:
        raise ValueError('Unknown outer ear model: outerear = {}'.format(outerear))

# frequency of fft bins
fft_freq = np.arange(0,(fft_size/2)+1)/fft_size*2*fs/2

if bark_type == 'table':
    # zwicker & fastl: psychoacoustics 1999, page 159
    bark_upper  = np.array([10, 20, 30, 40, 51, 63, 77, 92, 108, 127, 148, 172, 200, 232, 270, 315, 370, 440, 530, 640, 770, 950, 1200, 1550])*10 # Hz
    bark_center = np.array([5, 15, 25, 35, 45, 57, 70, 84, 100, 117, 137, 160, 185, 215, 250, 290, 340, 400, 480, 580, 700, 850, 1050, 1350])*10  # Hz
    # ignore critical bands outside of p.fs range
    cb = min(min(np.append(np.nonzero(bark_upper>fs/2)[0], len(bark_upper))), len(bark_upper))
    bark_center = bark_center[:cb+1]
else:
    cb = bark_type[2]
    if not(isNumeric(cb)) or np.ceil(cb)!=cb or cb<2:
        print("bark_type should be the str 'table' or list [freq start, freq end, number (2:50)]")
    f    = np.arange(bark_type[0], min(bark_type[1], fs/2)+1)
    bark = 13*np.arctan(0.76*f/1000) + 3.5*np.arctan((f/7500)**2)
    f_idx_upper = np.zeros((1, cb), dtype=int)
    b_idx_upper = np.linspace(1,max(bark),cb)
    f_idx_center = np.zeros((1, cb), dtype=int)
    b_idx_center = b_idx_upper-((b_idx_upper[1]-b_idx_upper[0])/2)
    for i in range(0,cb):
        b_minus_b_idx_upper = abs(bark-b_idx_upper[i])
        b_minus_b_idx_center = abs(bark-b_idx_center[i])
        f_idx_upper[:,i] = np.nonzero(b_minus_b_idx_upper == min(b_minus_b_idx_upper))[0][0]
        f_idx_center[:,i] = np.nonzero(b_minus_b_idx_center == min(b_minus_b_idx_center))[0][0]
    bark_upper = f[f_idx_upper]
    bark_center = f[f_idx_center]

# spreading function: schroeder et al., 1979, JASA, optimizing digital speech coders by exploiting masking properties of the human ear
spread = np.zeros((cb,cb))
cbV = np.linspace(1,cb,cb, dtype=int)
for i in range(1,cb+1):
    spread[i-1,:] = 10**((15.81+7.5*((i-cbV)+0.474)-17.5*np.sqrt(1+((i-cbV)+0.474)**2))/10)
    
w_Adb = outerEarCases(outerear, fft_freq)

# figure out number of fft frames
frames = 0
idx = fft_size
while idx <= len(wav):
    frames = frames + 1; 
    idx    = idx + hop_size

wav = wav * (10**(dB_max/20)) # Rescale to dB max (default is 96dB = 2^16)
dlinear = np.zeros((int(fft_size/2+1),frames)) # data from fft (linear freq scale)
sone    = np.zeros((cb,frames))                # data after bark scale

idx = np.linspace(0,fft_size-1,fft_size, dtype=int) # not used
w   = np.hanning(fft_size)
for i in range(0, frames): # fft
    X = np.fft.fft(wav[idx]*w,n=fft_size)
    dlinear[:,i] = abs(X[0:int(fft_size/2+1),]/np.sum(w)*2)**2 # normalized powerspectrum
    idx = idx + hop_size
    
dlinear2 = np.multiply(np.tile(np.transpose(w_Adb), (1, dlinear.shape[1])), dlinear) # outer ear
# dlinear2 = np.tile(np.transpose(w_Adb), (1, dlinear.shape[1]))*dlinear # outer ear

k = 0  
for i in range(0,cb): # group into bark bands
    idx = np.nonzero(fft_freq[k:len(fft_freq)]<=bark_upper[i])[0]
    idx = idx + k
    sone[i,:] = np.sum(dlinear2[idx,:], axis=0)
    k = np.max(idx)+1

soneNoSpread_dB = array2dB(sone)
doSpread = True
if doSpread:
    sone = np.matmul(spread, sone)
sone_dB        = array2dB(sone)
soneMasking_dB = array2dB(sone)

# bladon and lindblom, 1981, JASA, modelling the judment of vowel quality differences
if doSone:
    idx = sone_dB>=40
    sone_dB[idx] = 2**((sone_dB[idx]-40)/10)
    sone_dB[~idx] = (sone_dB[~idx]/40)**2.642

# Ntot requested
Ntot = np.zeros((sone_dB.shape[1],2))
notIdx = np.full((1,sone_dB.shape[0]),True)[0]
for i in range(sone_dB.shape[1]):
    maxi = np.max(sone_dB[:,i])
    idx  = np.nonzero(sone_dB==maxi)[0][0]
    notIdx[idx] = False
    Ntot[i,1]   = maxi + 0.15*np.sum(sone_dB[notIdx,i])
for frame in range(frames):
    Ntot[frame,0] = frame * (hop_size/fs) # time vector in sec

if plotLoudness:
    cbW_T = (-3.64*(bark_center/1000)**-0.8
            +6.5 * np.exp(-0.6 * (bark_center/1000 - 3.3)**2)
            -0.001*(bark_center/1000)**4)
    L = len(fft_freq)
    W_Adb_T = np.zeros((L,1))
    W_Adb_T[1:L,0] = 10**((-3.64*(fft_freq[1:L]/1000)**-0.8 + 6.5 * np.exp(-0.6 * (fft_freq[1:L]/1000 - 3.3)**2) - 0.001*(fft_freq[1:L]/1000)**4)/20)
    W_Adb_T = W_Adb_T**2
    
    fig = plt.figure(tight_layout=True, figsize=[12,7]) # psychoacoustic model
    gs = gridspec.GridSpec(2, 2)

    ax0 = fig.add_subplot(gs[0, :]) # outer ear weighting function and width of bark bands 
    ax0.semilogx(fft_freq[1:len(fft_freq)], 10*np.log10(W_Adb_T[1:len(W_Adb_T)]), color='r') # avoid log10(0)
    ax0.plot(cb, w_Adb, color = 'k', linestyle='', marker='.')
    ax0.set(xlabel='Frequency [Hz]', ylabel='Response [dB]')
    ax0.set_title('Outer Ear', fontweight='bold')
    ax0.legend(['Terhardt'],loc= 'upper left', fontsize=12)
    ax0.set(xlim=[30, 16e3], ylim=[-50, 10])
#     ax0.set_xticks([50,100,200,400,800,1600,3200,6400,12800], minor=False)
    
    for bc in bark_center:
        ax0.axvline(bc, color='k', linestyle=':')
    # set(gca,'xtick',[50,100,200,400,800,1600,3200,6400,12800],'XMinorTick','off')

    ax1 = fig.add_subplot(gs[1, 0]) # bark-scale
    z   = 13*np.arctan(0.76*fft_freq/1000)+3.5*np.arctan(fft_freq/7.5/1000)**2
    cbz = 13*np.arctan(0.76*(bark_center[0:cb+1])/1000)+3.5*np.arctan((bark_center[0:cb+1])/7.5/1000)**2
    ax1.plot(fft_freq, z)
    ax1.plot(bark_center[0:cb+1], cbz,'.r')
    ax1.set(xlabel='Frequency [Hz]', ylabel='Bark')
    ax1.set_title('Bark Scale', fontweight='bold')
    
    ax2 = fig.add_subplot(gs[1, 1]) # spreading function
    k   = 10
    cbV = np.linspace(start=1,stop=cb,num=cb) 
    ax2.plot(((15.81+7.5*((k-cbV)+0.474)-17.5*(1+((k-cbV)+0.474)**2)**0.5)))
    ax2.set(xlabel='Bark', ylabel='dB')
    ax2.set_title('Spreading function for 10th band', fontweight='bold')
    ax2.set(xlim=[0, 24], ylim=[-80, 5]) # TODO:check lim
    plt.show()

    dlinear_dB  = array2dB(dlinear)
    dlinear2_dB = array2dB(dlinear2)

    fig2, ax = plt.subplots(nrows=6, ncols=1, sharex=False, sharey=False, figsize=(16, 9))
    ax[0].plot(wav, color='gray')
    ax[1].imshow(dlinear_dB, aspect='auto', origin='lower')
    ax[2].imshow(dlinear2_dB, aspect='auto', origin='lower')
    ax[3].imshow(soneNoSpread_dB, aspect='auto', origin='lower')
    ax[4].imshow(soneMasking_dB, aspect='auto', origin='lower')
    ax[5].imshow(sone_dB, aspect='auto', origin='lower')

    ax[0].set(ylabel ='PCM', xlim =[0, len(wav)], xticklabels='')
    ax[1].set(ylabel='FFT', xticklabels='')
    ax[2].set(ylabel='Outer Ear', xticklabels='')
    ax[3].set(ylabel='Bark Scale', xticklabels='')
    ax[4].set(ylabel='Masking', xticklabels='')
    ax[5].set_ylabel('Sone');
    plt.show()

    fig3, ax = plt.subplots(nrows=1, ncols=1, figsize=(12, 7))
    ax.plot(Ntot[:,0],Ntot[:,1])
    ax.set(xlabel='Time [s]', ylabel='Loudness [sones]', title='Ntot');
    plt.show()

