"""Module wrapping a port of MA toolbox's loudness computation."""
import os
from typing import Iterable, List, Optional

from doit.tools import config_changed
import lowess
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import scipy.interpolate
import scipy.signal
import soundfile as sf

from . import _ma_sone


def get_loudness(input_path: str, *, export_loudness: bool = True, export_dir: Optional[str] = None, **kwargs):
    """
    Compute Global Loudness of Audio Files.

    input_path    : string; folder path or wav audio file path
    exportLoudness: boolean; export as csv (true by default)
    export_dir    : string; folder in which to save the export (default: same as input)
    smoothSpan    : double; number of data points for calculating the smooth curve (0.03 by default)
    no_negative   : boolean; set L(i) < 0 = 0 (true by default)
    columns       : string; which column - 'all' (default), 'raw', 'norm', 'smooth', 'envelope'

    returns       :  array; Time (:,1) Loudness (:,2), Scaled (:,3), Scaled-smoothed (:,4), Scaled-envelope (:,5)
    """
    # Dispatch between single or batch run based on path type
    if os.path.isfile(input_path):  # Single run
        files_list = [input_path]
    elif os.path.isdir(input_path):  # Batch run
        files_list = [f for f in os.listdir(input_path) if f.endswith('.wav') and not f.startswith('._')]
    else:
        raise ValueError(f"Invalid path: {input_path}")

    loudness_all = [compute_loudness(audio_file, export_dir=export_dir, **kwargs) for audio_file in files_list]
    if export_loudness:
        export_dir = export_dir or os.path.dirname(input_path)
        for loud, infile in zip(loudness_all, files_list):
            write_loudness(loud, audio_path=infile, export_dir=export_dir, **kwargs)
    return loudness_all


def clip_negative(x_array: Iterable[float]) -> List[float]:
    """Set negative values to zero."""
    return [0 if x < 0 else x for x in x_array]


def compute_loudness(audio_path, *, smooth_span=0.03, no_negative=True, **kwargs):
    """Compute the raw loudness and its post-processed versions."""
    time, raw_loudness = compute_raw_loudness(audio_path, **kwargs)
    norm_loudness = rescale(raw_loudness)
    smooth_loudness = smooth(norm_loudness, smooth_span)
    min_separation = len(time) // time[-1]
    envelope_loudness = peak_envelope(norm_loudness, min_separation)

    # Remove values below zero
    if no_negative:
        smooth_loudness = clip_negative(smooth_loudness)
        envelope_loudness = clip_negative(envelope_loudness)

    df = pd.DataFrame({'Time': time,
                       'Loudness': raw_loudness,
                       'Loudness_norm': norm_loudness,
                       'Loudness_smooth': smooth_loudness,
                       'Loudness_envelope': envelope_loudness})
    return df


def write_loudness(data, columns='all', export_dir=None, export_path=None, audio_path=None, **_kwargs):
    """Export loudness data to disk."""
    if export_path is None:
        export_path = os.path.join(export_dir, os.path.basename(audio_path).replace(".wav", "_loudness.csv"))
    if columns != 'all':
        column_map = {'raw': 'Loudness',
                      'norm': 'Loudness_norm',
                      'smooth': 'Loudness_smooth',
                      'envelope': 'Loudness_envelope'}
        data.to_csv(export_path, columns=['Time', column_map[columns]], index=False)
    else:
        data.to_csv(export_path, index=False)


def plot_loudness(time, raw_loudness, norm_loudness, smooth_loudness, envelope_loudness, *, show=True):
    """Display a pyplot graph of the loudness."""
    fig, ax1 = plt.subplots()
    ax1.set_ylabel('Loudness (sone)', fontsize=14)
    ax1.set_xlabel('Time (s)', fontsize=14)

    p1 = ax1.plot(time, raw_loudness, linestyle='-', linewidth=0.8, color=(0, 0, 180/255))

    ax2 = ax1.twinx()

    p2 = ax2.plot(time, norm_loudness, linestyle='-.', linewidth=0.5, color=(1, 160/255, 0))
    p3 = ax2.plot(time, smooth_loudness, linestyle='-', linewidth=3.8, color=(139/255, 0, 0))
    p4 = ax2.plot(time, envelope_loudness, linestyle='--', linewidth=1.5, color=(0.5, 0.5, 0.5))

    ax2.set_ylabel('Normalized Loudness (sone)', fontsize=14)
    ax2.set_xlim((time[0], time[-1]))
    ax2.set_ylim((0, 1))
    ax2.legend(p1+p2+p3+p4, ('original', 'normalized', 'smoothed', 'envelope'))

    if show:
        plt.show()


def compute_raw_loudness(audio_path, **kwargs):
    """Compute the raw loudness using the python port of the MA toolbox."""
    audio, fs = sf.read(audio_path)
    if audio.ndim == 2:
        audio = np.mean(audio, 1)

    _, tmp = _ma_sone.ma_sone(audio, fs=fs, **kwargs)
    time, raw_loudness = tmp.T  # Unpack by column
    return time, raw_loudness


def rescale(data):
    """Scale data linearly between 0 and 1."""
    return np.interp(data, (data.min(), data.max()), (0, 1))


def smooth(data, span):
    """Use lowess regression to smooth loudness."""
    if 0 < span < 1:  # span is given as a ratio
        span = np.floor(len(data)*span)
        span += span % 2 - 1
    bandwidth = (span+2)/len(data)
    return lowess.lowess(pd.Series(range(len(data))), pd.Series(data), bandwidth=bandwidth, polynomialDegree=2)


def peak_envelope(data, min_separation):
    """Find the peak envelope of loudness."""
    peaks_idx, _ = scipy.signal.find_peaks(data, distance=min_separation+1)  # +1 for consistency with matlab
    peaks_y = data[peaks_idx]
    spline = scipy.interpolate.InterpolatedUnivariateSpline(peaks_idx, peaks_y)
    return spline(range(len(data)))


def resample(loud_path, beat_path, out_path):
    """Interpolate the loudness at the position of beats."""
    data = read_loudness(loud_path)
    beats = pd.read_csv(beat_path)
    spline = scipy.interpolate.InterpolatedUnivariateSpline(data.Time, data.Loudness_smooth)
    interp = spline(beats.time)
    frame = pd.DataFrame({'Time': beats.time, 'Loudness_resampled': interp})
    frame.to_csv(out_path)


def read_loudness(path):
    """Read a loudness table from disk."""
    df = pd.read_csv(path)
    expected_header = ['Time', 'Loudness', 'Loudness_norm', 'Loudness_smooth', 'Loudness_envelope']
    if list(df.columns) != expected_header:
        raise IOError(f"Bad csv header: expected \n{expected_header}\n but got\n{df.columns}")
    return df


task_docs = {
    "loudness": "Compute loudness using a port of the MA matlab toolbox",
    "loudness_resample": "Resample loudness at the time of the beats"
}

param_sources = (compute_loudness, _ma_sone.ma_sone)


def gen_tasks(piece_id, targets, **kwargs):
    """Generate loudness-based tasks."""
    if targets("perfaudio") is None:
        return

    perf_loudness = targets("loudness")
    perf_loudness_simple = targets("loudness_simple")

    def caller(perf_path, perf_loudness, perf_loudness_simple, **kwargs):
        loudness = compute_loudness(perf_path, **kwargs)
        write_loudness(loudness, export_path=perf_loudness)
        write_loudness(loudness, export_path=perf_loudness_simple, columns="smooth")
        return True
    yield {
        'basename': "loudness",
        'file_dep': [targets("perfaudio"), __file__],
        'name': piece_id,
        'doc': task_docs["loudness"],
        'targets': [perf_loudness, perf_loudness_simple],
        'uptodate': [config_changed(kwargs)],
        'actions': [(caller, [targets("perfaudio"), perf_loudness, perf_loudness_simple])]
    }

    if targets("manual_beats") is None and (targets("score") is None or targets("perfmidi") is None):
        return

    perf_beats = targets("beats")

    perf_resampled_loudness = targets("loudness_resampled")
    yield {
        'basename': "loudness_resample",
        'file_dep': [perf_loudness, perf_beats, __file__],
        'name': piece_id,
        'doc': task_docs["loudness_resample"],
        'targets': [perf_resampled_loudness],
        'uptodate': [config_changed(kwargs)],
        'actions': [(resample, [perf_loudness, perf_beats, perf_resampled_loudness])]
    }
