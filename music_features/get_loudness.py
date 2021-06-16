import os
import csv
from tempfile import SpooledTemporaryFile
import numpy as np
import scipy
import scipy.io.wavfile
import scipy.signal
import scipy.interpolate
from extract_features import writeFile


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
        export_dir=os.path.dirname(inputPath)

    #Dispatch between single or batch run based on path type
    if os.path.isfile(inputPath): # Single run
        return [compute_loudness(inputPath, export_dir=export_dir, **kwargs)]
    elif os.path.isdir(inputPath): # Batch run
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


def compute_loudness(audioFile, columns='all', exportLoudness=True, export_dir=None, plotLoudness=False, smoothSpan=0.03, noNegative=True):
    audio, fs = scipy.io.wavfile.read(audioFile)
    if np.size(audio, 2) == 2:
        audio = np.mean(audio,2)
    
    time, raw_loudness = ma_sone(audio, fs)
    norm_loudness = rescale(raw_loudness)
    smooth_loudness = smooth(norm_loudness, smoothSpan)
    min_separation = np.floor(len(time)/time[-1])
    enveloppe_loudness = peak_envelope(norm_loudness, min_separation)
    # [~, L, ~]  = ma_sone(audio, p);
    # L(:,3)     = normalize(L(:,2), 'range');          % Normalized data with range [0 1]
    # L(:,4)     = smooth(L(:,3), smoothSpan, 'loess'); % 2nd degree polynomial smooth
    # [L(:,5),~] = envelope(L(:,3),floor(length(L(:,1))/L(end,1)),'peak'); % upper peak envelope

    # Remove values below zero
    if noNegative:
        smooth_loudness = clipNegative(smooth_loudness)
        enveloppe_loudness = clipNegative(enveloppe_loudness)

    if plotLoudness:
        ### NYI
        # figure('Name','Loudness','NumberTitle','off');
        # colororder({'k','k'})
        # plot(L(:,1), L(:,2), 'LineStyle', '-',  'LineWidth', 0.8, 'Color', [0   0 180]/255)
        # ylabel('Loudness (sone)', 'FontSize', 14)
        # xlabel('Time (s)', 'FontSize', 14)
        # yyaxis right
        # hold on
        # plot(L(:,1), L(:,3), 'LineStyle', '-.', 'LineWidth', 0.2, 'Color', [255 160 0]/255)
        # plot(L(:,1), L(:,4), 'LineStyle', '-',  'LineWidth', 3.8, 'Color', [139 0   0]/255)
        # plot(L(:,1), L(:,5), 'LineStyle', '--', 'LineWidth', 1.5, 'Color', [0.5 0.5 0.5])
        # ylabel('Normalized Loudness (sone)', 'FontSize', 14)
        # xlim([L(1,1) L(end,1)])
        # ylim([0 1])
        # legend('original', 'normalized', 'smoothed', 'envelope')
        pass

    if exportLoudness:
        loudness_table = [{'Time':t, 'Loudness':l, 'Loudness_norm':n, 'Loudness_smooth':s, 'Loudness_envelope':e}
            for t,l,n,s,e in zip(time, raw_loudness, norm_loudness, smooth_loudness, enveloppe_loudness)]
        export_path = os.path.join(export_dir, os.path.basename(audioFile).replace(".wav","_loudness.csv"))
        writeFile(export_path, loudness_table)
        print(f"Exported {columns} to: {export_path}")


    
def ma_sone(audio, fs):
    ## NYI
    pass

def rescale(data):
    """Scale data linearly between 0 and 1."""
    return np.interp(data, (data.min(), data.max()), (0, +1))

def smooth(data, span):
    ## NYI
    return data

def peak_envelope(data, min_separation):
    peaks_idx = scipy.signal.find_peaks(data, distance=min_separation)
    peaks_y = data[peaks_idx]
    spline = scipy.interpolate.InterpolatedUnivariateSpline(peaks_idx, peaks_y)
    return spline(range(len(data)))

