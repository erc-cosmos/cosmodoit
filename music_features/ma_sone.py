"""Compute loudness matrix and total loudness using Stevens method from the MA Toolbox.

http://www.ofai.at/~elias.pampalk/ma/documentation.html#ma_sone
Created by Elias Pampalk, ported by Daniel Bedoya 2020-06-28
"""

import numpy as np


def ma_sone(wav, fs=44100, *,
            fft_size=1024, hop_size=512,
            outer_ear='terhardt', bark_type='table', db_max=96,
            do_spread=True, do_sone=True):
    """Compute the loudness of an audio file."""
    # frequency of fft bins
    fft_freq = np.arange(0, (fft_size/2)+1)/fft_size*2*fs/2

    # critical band rate scale (Bark-scale)
    cb, bark_upper, _bark_center = compute_bark_scale(bark_type, fs)

    # spreading function & outer ear model
    spread, w_adb = compute_spreading(cb, outer_ear, fft_freq)

    # fft frames
    frames = get_frames(wav, fft_size, hop_size)

    # Rescale to dB max (default is 96dB = 2^16)
    wav_db = wav * (10**(db_max/20))

    # compute power spectrum
    d_linear_outer_ear, _d_linear = get_power_spectrum(wav_db, fft_size, frames, hop_size, w_adb)

    # create sone
    sone = compute_sone(cb, frames, fft_freq, bark_upper, d_linear_outer_ear)
    if do_spread:  # apply spectral masking
        sone = np.matmul(spread, sone)
    sone_db = array2db(sone)  # to dB

    if do_sone:  # convert units from phones to sones
        sone_db = phon2sone(sone_db)

    # compute total loudness vector
    tot_loudness = compute_total_loudness(sone_db, frames, hop_size, fs)

    return sone_db, tot_loudness


def array2db(vector):
    """Replace with 1 values < 1 and convert array to dB."""
    linear_vector = np.copy(vector)
    linear_vector[linear_vector < 1] = 1  # avoid negative values
    db = 10*np.log10(linear_vector)
    return db


def is_numeric(x):
    """Verify if an input is numeric, raise an error otherwise."""
    try:
        float(x)
        return True
    except ValueError:
        return False


def compute_bark_scale(bark_type, fs):
    """
    Generate bark scale according to model.

    input can be a string 'table' or a list with lowear freq, highest freq, and number of values
    """
    if bark_type == 'table':
        # zwicker & fastl: psychoacoustics 1999, page 159
        bark_upper = np.array([10, 20, 30, 40, 51, 63, 77, 92, 108, 127, 148, 172, 200, 232,
                              270, 315, 370, 440, 530, 640, 770, 950, 1200, 1550])*10  # Hz
        bark_center = np.array([5, 15, 25, 35, 45, 57, 70, 84, 100, 117, 137, 160, 185, 215,
                               250, 290, 340, 400, 480, 580, 700, 850, 1050, 1350])*10  # Hz
        # ignore critical bands outside of p.fs range
        cb = min(min(np.append(np.nonzero(bark_upper > fs/2)[0], len(bark_upper))), len(bark_upper))
        bark_center = bark_center[:cb+1]
    else:
        cb = bark_type[2]
        if not(is_numeric(cb)) or np.ceil(cb) != cb or cb < 2:
            print("bark_type should be the str 'table' or list [freq start, freq end, number (2:50)]")
        f = np.arange(bark_type[0], min(bark_type[1], fs/2)+1)
        bark = 13*np.arctan(0.76*f/1000) + 3.5*np.arctan((f/7500)**2)
        f_idx_upper = np.zeros((1, cb), dtype=int)
        b_idx_upper = np.linspace(1, max(bark), cb)
        f_idx_center = np.zeros((1, cb), dtype=int)
        b_idx_center = b_idx_upper-((b_idx_upper[1]-b_idx_upper[0])/2)
        for i in range(0, cb):
            b_minus_b_idx_upper = abs(bark-b_idx_upper[i])
            b_minus_b_idx_center = abs(bark-b_idx_center[i])
            f_idx_upper[:, i] = np.nonzero(b_minus_b_idx_upper == min(b_minus_b_idx_upper))[0][0]
            f_idx_center[:, i] = np.nonzero(b_minus_b_idx_center == min(b_minus_b_idx_center))[0][0]
        bark_upper = f[f_idx_upper]
        bark_center = f[f_idx_center]
    return cb, bark_upper, bark_center


def compute_spreading(cb, outerear, fft_freq):
    """
    Compute spreading function.

    schroeder et al., 1979, JASA,
    Optimizing digital speech coders by exploiting masking properties of the human ear.
    """
    spread = np.zeros((cb, cb))
    cb_v = np.linspace(1, cb, cb, dtype=int)
    for i in range(1, cb+1):
        spread[i-1, :] = 10**((15.81+7.5*((i-cb_v)+0.474)-17.5*np.sqrt(1+((i-cb_v)+0.474)**2))/10)

    w_adb = outer_ear_cases(outerear, fft_freq)
    return spread, w_adb


def outer_ear_cases(outer_ear, fft_freq):
    """Compute model according to case."""
    length = len(fft_freq)
    w_adb = np.ones((1, len(fft_freq)), dtype=float)
    if outer_ear == 'terhardt':  # terhardt 1979 (calculating virtual pitch, hearing research #1, pp 155-182)
        w_adb[0, 0] = 0
        w_adb[0, range(1, len(fft_freq))] = 10**((-3.64*(fft_freq[1:length]/1000)**-0.8
                                                 + 6.5 * np.exp(-0.6 * (fft_freq[1:length]/1000 - 3.3)**2)
                                                 - 0.001*(fft_freq[1:length]/1000)**4)/20)
        w_adb = w_adb**2
        return w_adb
    if outer_ear == 'modified_terhardt':  # less emph around 4Hz, more emphasis on low freqs
        w_adb[0] = 0
        w_adb[0, range(1, len(fft_freq))] = 10**((.6*-3.64*(fft_freq[1:length]/1000)**-0.8
                                                 + 0.5 * np.exp(-0.6 * (fft_freq[1:length]/1000 - 3.3)**2)
                                                 - 0.001*(fft_freq[1:length]/1000)**4)/20)
        w_adb = w_adb**2
        return w_adb
    if outer_ear == 'none':  # all weighted equally
        return w_adb
    else:
        raise ValueError('Unknown outer ear model: outerear = {}'.format(outer_ear))


def get_frames(wav, fft_size, hop_size):
    """Figure out number of fft frames."""
    frames = (len(wav) - fft_size) // hop_size + 1
    return frames


def get_power_spectrum(wav, fft_size, frames, hop_size, w_adb):
    """Compute normalized powerspectrum."""
    half_window_size = fft_size//2+1
    dlinear = np.zeros((half_window_size, frames))  # data from fft (linear freq scale)
    w = np.hanning(fft_size)
    scaling = np.sum(w)/2
    for i in range(frames):  # fft
        x = np.fft.fft(wav[hop_size*i:hop_size*i+fft_size]*w, n=fft_size)
        dlinear[:, i] = abs(x[0:half_window_size]/scaling)**2  # normalized powerspectrum
    d_linear_outer_ear = np.multiply(np.tile(np.transpose(w_adb), (1, dlinear.shape[1])), dlinear)  # outer ear
    return d_linear_outer_ear, dlinear


def compute_sone(cb, frames, fft_freq, bark_upper, d_linear):
    """Compute sone matrix from critical band scale and powerspectrum."""
    sone = np.zeros((cb, frames))
    k = 0
    for i in range(0, cb):  # group into bark bands
        idx = np.nonzero(fft_freq[k:len(fft_freq)] <= bark_upper[i])[0]
        idx = idx + k
        sone[i, :] = np.sum(d_linear[idx, :], axis=0)
        k = np.max(idx)+1
    return sone


def phon2sone(sone_db):
    """
    Convert from phons to sones.

    Bladon and Lindblom, 1981, JASA, modelling the judment of vowel quality differences
    """
    idx = sone_db >= 40
    sone_db[idx] = 2**((sone_db[idx]-40)/10)
    sone_db[~idx] = (sone_db[~idx]/40)**2.642
    return sone_db


def compute_total_loudness(sone_db, frames, hop_size, fs):
    """
    Compute total loudness as a vector with timestamps.

    Stevens' method, see 'Signal sound and sensation' p73, Hartmann
    """
    tot_loudness = np.zeros((sone_db.shape[1], 2))
    factor = 0.15  # Masking factor
    tot_loudness[:, 1] = (1-factor) * np.max(sone_db, 0) + factor * np.sum(sone_db, 0)

    for frame in range(frames):
        tot_loudness[frame, 0] = frame * (hop_size/fs)  # time vector in sec
    return tot_loudness
