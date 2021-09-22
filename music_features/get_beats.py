"""Module to extract beat timings from a midi interpretation and corresponding score."""
import argparse
import collections
import os
import shutil
import sys
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pretty_midi as pm
import scipy as sp
import scipy.interpolate

from music_features import get_alignment
from music_features.util import targets_factory

BeatParams = collections.namedtuple("BeatParams",
                                    ("PPQ",  # Pulse per quarter note
                                     "offset"  # Offset of the first beat
                                     ))


def make_beat_reference(alignment, *, quarter_length=None, anacrusis_offset=None, guess=False):
    """
    Generate a simple beat reference based on a constant beat length.

    quarterLength --- the number of midi ticks during a beat in the reference
    anacrusisOffset --- the offset of the first whole beat (not necessarily the first beat of the first bar)
    guess --- flag for whether to guess or ask the beat parameters (overrides the previous parameters if True)
    """
    max_tatum = alignment[-1].tatum

    ticks, _ = preprocess(alignment)
    # Obtain the beat parameters if not provided already
    if guess:
        quarter_length, anacrusis_offset = guess_beat_params(ticks)
    else:
        quarter_length, anacrusis_offset = prompt_beat_params(alignment, quarter_length, anacrusis_offset)
    return np.arange(anacrusis_offset, max_tatum, quarter_length)


def get_beat_reference_pm(ref_filename):
    """Find the beats in the reference according to pretty-midi."""
    pretty = pm.PrettyMIDI(ref_filename)
    return np.round(np.array(pretty.get_beats()) * 1000)  # seconds to milliseconds


def get_bar_reference_pm(ref_filename):
    """Find the bar lines in the reference according to pretty-midi."""
    pretty = pm.PrettyMIDI(ref_filename)
    return np.round(np.array(pretty.get_downbeats()) * 1000)  # seconds to milliseconds


def get_beats(alignment, reference_beats, *, max_tries=3, return_ignored=False):
    """Extract beats timing from an alignment of the notes."""
    ignored = []
    for _ in range(max_tries):
        # Find outliers and prefilter data
        ticks, times = preprocess(alignment)

        spline = sp.interpolate.UnivariateSpline(ticks, times, s=0)  # s=0 for pure interpolation
        interpolation = spline(reference_beats)
        interpolation[(reference_beats < ticks.min()) | (reference_beats > ticks.max())] = np.nan
        # tempos = [np.nan, *(60/np.diff(interpolation))]
        # beats = [{'count': count,
        #           'time': time,
        #           'interpolated':  # TODO: Fix rounding issues
        #           'tempo': tempo}
        #  for count, (tick, time, tempo) in enumerate(zip(reference_beats, interpolation, tempos))]
        
        # beats = pd.DataFrame(((count, time, tick not in ticks)
        #                       for count, (tick, time, tempo) in enumerate(zip(reference_beats, interpolation, tempos))),
        #                      columns=("count", "time", "interpolated"))

        beats = pd.DataFrame({"time": interpolation, "interpolated": [tick not in ticks for tick in reference_beats]})
        anomalies = find_outliers(beats)
        if anomalies == []:
            return (beats, ignored) if return_ignored else beats
        else:
            alignment, new_ignored = attempt_correction(beats, alignment, reference_beats, anomalies)
            ignored.extend(new_ignored)

    warnings.warn(f"Outliers remain after {max_tries} tries to remove them. Giving up on correction.")
    return (beats, ignored) if return_ignored else beats


def attempt_correction(_beats, alignment, reference_beats, anomalies, *, verbose=True):
    """Attempt to correct the beat extraction by removing the values causing outliers."""
    filtered_all = []
    for index_before, index_after in anomalies:
        # Find range to erase
        range_start = next((item.tatum for item in reversed(alignment) if item.tatum <= reference_beats[index_before]),
                           reference_beats[index_before])
        range_end = next((item.tatum for item in alignment if item.tatum >= reference_beats[index_after]),
                         reference_beats[index_after])  # TODO: Add a test with coverage on this
        # Protect the first and last beats
        range_start = (range_start + 1) if range_start == alignment[0].tatum else range_start
        range_end = (range_end - 1) if range_end == alignment[-1].tatum else range_end

        filtered = [item for item in alignment if range_start <= item.tatum <= range_end]
        if verbose:
            [print(f"Removing {item} in correction attempt") for item in filtered]
        alignment = [item for item in alignment if not(range_start <= item.tatum <= range_end)]
        filtered_all.extend(filtered)

    return alignment, filtered_all


def preprocess(alignment):
    """Find outliers and prefilter data."""
    times, indices = np.unique(np.array([alignment_atom.time for alignment_atom in alignment]), return_index=True)
    ticks = np.array([aligment_atom.tatum for aligment_atom in alignment])[indices]

    # TODO: determine better which note to use when notes share a tatum
    ticks, indices = np.unique(np.array([alignment_atom.tatum for alignment_atom in alignment]), return_index=True)
    times = np.array([aligmnent_atom.time for aligmnent_atom in alignment])[indices]
    return ticks, times


def guess_beat_params(ticks):
    """Heuristically guess which note is the starting beat."""
    best = 0
    best_offset = 0
    quarter_length = 500  # Assumed from score to midi generation

    max_tatum = ticks[-1]
    for offset in ticks[:10]:  # Assume one of the first 10 notes is on beat
        interpol_target = np.arange(offset, max_tatum, quarter_length)
        onbeat_count = len([t for t in ticks if t in interpol_target])
        # The best candidate is the one with the most notes on the beat
        if onbeat_count > best:
            best_offset = offset
            best = onbeat_count

    return BeatParams(PPQ=quarter_length, offset=best_offset)


def plot_beat_ratios(ticks, quarter_length, times, spline):
    """Plot the ratio of actual note duration to expected.

    Expected note duration is based on neighbouring tempo
    """
    ratios = []
    for (tick, time, tick_next, time_next) in zip(ticks, times, ticks[1:], times[1:]):
        # TODO: Separate by line
        if tick == tick_next:  # Ignore simultaneous notes
            continue
        expected_duration = spline(tick_next)-spline(tick)
        actual_duration = time_next-time
        ratios.append(actual_duration/expected_duration)
    plt.plot(ticks[:-1]/quarter_length, ratios)
    plt.plot(ticks[:-1]/quarter_length, np.diff(ticks)/quarter_length)
    plt.hlines(1, xmin=ticks[0], xmax=ticks[-1]/quarter_length)
    plt.show(block=True)


def plot_beats(beats):
    """Plot score time against real time and tempo against score time."""
    plt.show(block=True)
    plt.plot(60/np.diff([beat['time'] for beat in beats]))
    plt.show(block=True)


def prompt_beat_params(alignment, quarter_length=None, anacrusis_offset=None, force=False):
    """Prompt for missing information in beat detection.

    Does nothing if all are already known, unless force is True
    """
    if force or quarter_length is None or anacrusis_offset is None:
        [print(it) for it in alignment[:10]]  # Show first 10 lines to give context
        if force or quarter_length is None:
            quarter_length = int(input("Please enter the beat length (in ticks):"))
        if force or anacrusis_offset is None:
            anacrusis_offset = int(input("Please enter the beat offset (in ticks):"))
    return BeatParams(quarter_length, anacrusis_offset)


def find_outliers(beats, *, factor=4, verbose=True):
    """Perform an automated check for outliers."""
    beats = beats.time
    inter_beat_intervals = np.diff(beats)
    mean_IBI = np.mean(inter_beat_intervals)
    anomaly_indices = [(i, i+1) for (i, ibi) in enumerate(inter_beat_intervals)
                       if ibi * factor < mean_IBI]  # Only check values too quick, slow values are likely valid
    if verbose:
        [print(f"Anomaly between beats {i} and {j} detected: {beats[j]-beats[i]}s (max. {factor*mean_IBI}s)")
         for i, j in anomaly_indices]
    return anomaly_indices


task_docs = {
    "beats": "Find beats' positions using Nakamura's HMM alignment and pretty-midi's beat inference",
    "bars": "Find bars' positions using Nakamura's HMM alignment and pretty-midi's beat inference",
    "tempo": "Derive tempo from manual or inferred beats"
}


def gen_tasks(piece_id, paths, working_folder="tmp"):
    """Generate beat-related tasks."""
    # TODO: Split up operations
    backup_targets = targets_factory(piece_id, working_folder=working_folder)
    ref_targets = targets_factory(paths.score, working_folder=working_folder) or backup_targets
    perf_targets = targets_factory(paths.perfmidi, working_folder=working_folder) or backup_targets

    # Attempt using manual annotations
    perf_beats = perf_targets("_beats.csv")
    ref_midi = ref_targets("_ref.mid")
    perf_match = perf_targets("_match.txt")
    if paths.manual_beats is not None:
        def caller(manual_beats, perf_beats):
            shutil.copy(manual_beats, perf_beats)
        yield {
            'basename': "beats",
            'file_dep': [paths.manual_beats, __file__],
            'name': piece_id,
            'doc': "Use authoritative beats annotation",
            'targets': [perf_beats],
            'actions': [(caller, [paths.manual_beats, perf_beats])]
        }
    else:
        if(paths.score is None or paths.perfmidi is None):
            return

        def caller(perf_match, ref_midi, perf_beats, **kwargs):
            alignment = get_alignment.read_alignment_file(perf_match)
            beat_reference = get_beat_reference_pm(ref_midi)
            beats = get_beats(alignment, beat_reference)
            beats.to_csv(perf_beats, index_label="count")
            return True
        yield {
            'basename': "beats",
            'file_dep': [perf_match, ref_midi, __file__],
            'name': piece_id,
            'doc': task_docs["beats"],
            'targets': [perf_beats],
            'actions': [(caller, [perf_match, ref_midi, perf_beats])]
        }

    perf_bars = perf_targets("_bars.csv")
    if paths.manual_bars is not None:
        def caller_bar(manual_beats, perf_beats):
            shutil.copy(manual_beats, perf_beats)
        yield {
            'basename': "bars",
            'file_dep': [paths.manual_bars, __file__],
            'name': piece_id,
            'doc': "Use authoritative bars annotation",
            'targets': [perf_bars],
            'actions': [(caller, [paths.manual_bars, perf_bars])]
        }
    else:
        if(paths.score is None or paths.perfmidi is None):
            return

        def caller_bar(perf_match, ref_midi, perf_bars, **kwargs):
            alignment = get_alignment.read_alignment_file(perf_match)
            bar_reference = get_bar_reference_pm(ref_midi)
            bars = get_beats(alignment, bar_reference)
            bars.to_csv(perf_bars, index_label="count")
            return True
        yield {
            'basename': "bars",
            'file_dep': [perf_match, ref_midi, __file__],
            'name': piece_id,
            'doc': task_docs["bars"],
            'targets': [perf_bars],
            'actions': [(caller_bar, [perf_match, ref_midi, perf_bars])]
        }

    perf_tempo = perf_targets("_tempo.csv")

    def caller2(perf_beats, perf_tempo):
        data = pd.read_csv(perf_beats)
        tempo_frame = pd.DataFrame({'time': data.time[1:], 'tempo': 60/np.diff(data.time)})
        tempo_frame.to_csv(perf_tempo, index=False)

    yield {
        'basename': "tempo",
        'file_dep': [perf_beats, __file__],
        'name': piece_id,
        'doc': task_docs["tempo"],
        'targets': [perf_tempo],
        'actions': [(caller2, [perf_beats, perf_tempo])]
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ref', default='test_midi/Chopin_Ballade_No._2_Piano_solo.mid')
    parser.add_argument('--perf', default='test_midi/2020-03-12_EC_Chopin_Ballade_N2_Take_2.mid')
    parser.add_argument('--quarter', default=None)
    parser.add_argument('--offset', default=None)
    args = parser.parse_args()

    # Ensure execution directory
    scriptLocation = os.path.dirname(sys.argv[0])
    if scriptLocation != '':
        os.chdir(scriptLocation)

    alignment = get_alignment.get_alignment(ref_path=args.ref, perf_path=args.perf, cleanup=False)

    reference_beats = make_beat_reference(alignment, guess=True)

    beats = get_beats(alignment, reference_beats)
    plot_beats(beats)
    print(beats)
