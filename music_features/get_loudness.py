import os
import numpy as np
import scipy
import scipy.io.wavfile
import scipy.signal
import scipy.interpolate
import pandas as pd
import lowess
import matplotlib.pyplot as plt

import ma_sone


def get_loudness(inputPath, *, export_dir=None, **kwargs):
    """Compute Global Loudness of Audio Files.

    inputPath       : string; folder path or wav audio file path
    columns         : string; which column - 'all' (default), 'raw', 'norm', 'smooth', 'envelope'
    exportLoudness  : boolean; export as csv (true by default)
    export_dir        : string; folder in which to save the export (default: same as input)
    plotLoudness    : boolean; plot results (false by default)
    smoothSpan      : double; number of data points for calculating the smooth curve (0.03 by default)
    noNegative      : boolean; set L(i) < 0 = 0 (true by default)

    returns         :  array; Time (:,1) Loudness (:,2), Normalized (:,3), Normalized-smoothed (:,4), Normalized-envelope (:,5)
    """
    if export_dir is None:
        export_dir = os.path.dirname(inputPath)

    # Dispatch between single or batch run based on path type
    if os.path.isfile(inputPath):  # Single run
        return [compute_loudness(inputPath, export_dir=export_dir, **kwargs)]
    elif os.path.isdir(inputPath):  # Batch run
        files_list = [f for f in os.listdir(inputPath) if f.endswith('.wav') and not f.startswith('._')]
        return [compute_loudness(audioFile, export_dir=export_dir, **kwargs)
                for audioFile in files_list]
    else:
        raise ValueError(f"Invalid path: {inputPath}")


def clipNegative(x_array):
    return [0 if x < 0 else x for x in x_array]


def assign_columns(T, cols):
    if cols == 'all':
        return T
    elif cols == 'raw':
        return T['Loudness']
    elif cols == 'norm':
        return T['Loudness_norm']
    elif cols == 'smooth':
        return T['Loudness_smooth']
    elif cols == 'envelope':
        return T['Loudness_envelope']
    else:
        raise ValueError(f"Unsupported export type: {cols}")


def compute_loudness(audio_path, columns='all', exportLoudness=True, export_dir=None, smoothSpan=0.03, noNegative=True):
    time, raw_loudness = compute_raw_loudness(audio_path)
    norm_loudness = rescale(raw_loudness)
    smooth_loudness = smooth(norm_loudness, smoothSpan)
    min_separation = np.floor(len(time)/time[-1])
    envelope_loudness = peak_envelope(norm_loudness, min_separation)
    # [~, L, ~]  = ma_sone(audio, p);
    # norm_loudness     = normalize(L(:,2), 'range');          % Normalized data with range [0 1]
    # smooth_loudness     = smooth(norm_loudness, smoothSpan, 'loess'); % 2nd degree polynomial smooth
    # [envelope_loudness,~] = envelope(norm_loudness,floor(length(time)/L(end,1)),'peak'); % upper peak envelope

    # Remove values below zero
    if noNegative:
        smooth_loudness = clipNegative(smooth_loudness)
        envelope_loudness = clipNegative(envelope_loudness)
    
    if exportLoudness:
        df = pd.DataFrame({'Time': time, 
            'Loudness': raw_loudness, 
            'Loudness_norm': norm_loudness, 
            'Loudness_smooth': smooth_loudness, 
            'Loudness_envelope': envelope_loudness})
        export_path = os.path.join(export_dir, os.path.basename(audio_path).replace(".wav", "_loudness.csv"))
        write_loudness(df, export_path)
        print(f"Exported {columns} to: {export_path}")

def plot_loudness(time, raw_loudness, norm_loudness, smooth_loudness, envelope_loudness, *, show=True):
    fig, ax1 = plt.subplots()
    ax1.set_ylabel('Loudness (sone)', fontsize=14)
    ax1.set_xlabel('Time (s)', fontsize=14)
    
    p1 = ax1.plot(time, raw_loudness, linestyle='-', linewidth=0.8, color=(0,0,180/255))
    
    ax2 = ax1.twinx()
    
    p2 = ax2.plot(time, norm_loudness, linestyle='-.', linewidth=0.5, color=(1,160/255, 0))
    p3 = ax2.plot(time, smooth_loudness, linestyle='-', linewidth=3.8, color=(139/255, 0, 0))
    p4 = ax2.plot(time, envelope_loudness, linestyle='--', linewidth=1.5, color=(0.5, 0.5, 0.5))

    ax2.set_ylabel('Normalized Loudness (sone)', fontsize=14)
    ax2.set_xlim((time[0], time[-1]))
    ax2.set_ylim((0, 1))
    ax2.legend(p1+p2+p3+p4, ('original','normalized', 'smoothed', 'envelope'))
    
    if show:
        plt.show()


def compute_raw_loudness(audio_path):
    """Compute the raw loudness using the python port of the MA toolbox."""
    audio, fs = scipy.io.wavfile.read(audio_path)
    if np.size(audio, 2) == 2:
        audio = np.mean(audio, 2)

    return ma_sone.maSone(audio, fs=fs)


def rescale(data):
    """Scale data linearly between 0 and 1."""
    return np.interp(data, (data.min(), data.max()), (0, 1))


def smooth(data, span):
    # NYI
    if 0 < span < 1: # span is given as a ratio
        span = np.floor(len(data)*span)
        span+= span%2 - 1
    bandwidth = (span+2)/len(data)
    return lowess.lowess(pd.Series(range(len(data))), data, bandwidth=bandwidth, polynomialDegree=2)


def peak_envelope(data, min_separation):
    peaks_idx,_ = scipy.signal.find_peaks(data, distance=min_separation+1) # +1 for consistency with matlab
    peaks_y = data[peaks_idx]
    spline = scipy.interpolate.InterpolatedUnivariateSpline(peaks_idx, peaks_y)
    return spline(range(len(data)))


def write_loudness(data, path):
    data.to_csv(path, index=False)


def read_loudness(path):
    df = pd.read_csv(path)
    expected_header = ['Time', 'Loudness', 'Loudness_norm', 'Loudness_smooth', 'Loudness_envelope']
    if list(df.columns) != expected_header:
        raise IOError(f"Bad csv header: expected \n{expected_header}\n but got\n{df.columns}")
    return df
