"""Module to extract beat timings from a midi interpretation and corresponding score."""
import shutil
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pretty_midi as pm
import scipy.interpolate

from music_features import get_alignment
from music_features.util import targets_factory

from typing import NamedTuple, List, Tuple


class BeatParams(NamedTuple):
    """Named tuple for beat reference parameters."""

    PPQ: int  # Pulse per quarter note
    offset: int  # Offset of the first beat


def make_beat_reference(new_alignment, *, quarter_length: int = None, anacrusis_offset: int = None, guess: bool = False):
    """
    Generate a simple beat reference based on a constant beat length.

    quarterLength --- the number of midi ticks during a beat in the reference
    anacrusisOffset --- the offset of the first whole beat (not necessarily the first beat of the first bar)
    guess --- flag for whether to guess or ask the beat parameters (overrides the previous parameters if True)
    """
    alignment = [get_alignment.AlignmentAtom(tatum, time) for _, (tatum, time) in new_alignment.iterrows()]
    max_tatum = alignment[-1].tatum

    ticks, _ = remove_outliers_and_duplicates(alignment)
    # Obtain the beat parameters if not provided already
    if guess:
        quarter_length, anacrusis_offset = guess_beat_params(ticks)
    else:
        quarter_length, anacrusis_offset = prompt_beat_params(alignment, quarter_length, anacrusis_offset)
    return np.arange(anacrusis_offset, max_tatum, quarter_length)


def get_beat_reference_pm(ref_filename):
    """Find the beats in the reference according to pretty-midi."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        pretty = pm.PrettyMIDI(ref_filename)
    return np.round(np.array(pretty.get_beats()) * 1000)  # seconds to milliseconds


def get_bar_reference_pm(ref_filename):
    """Find the bar lines in the reference according to pretty-midi."""
    pretty = pm.PrettyMIDI(ref_filename)
    return np.round(np.array(pretty.get_downbeats()) * 1000)  # seconds to milliseconds


def get_beats(alignment: pd.DataFrame, reference_beats, *, max_tries: int = 5):
    """Extract beats timing from an alignment of the notes."""
    ignored = []
    beats = interpolate_beats(alignment, reference_beats)
    for _ in range(max_tries):
        # Find outliers and prefilter data
        anomalies = find_outliers(beats)
        if anomalies == []:
            return (beats, ignored)
        else:
            alignment, new_ignored = attempt_correction(beats, alignment, reference_beats, anomalies)
            ignored.extend(new_ignored)
            beats = interpolate_beats(alignment, reference_beats)

    if find_outliers(beats) != []:
        warnings.warn(f"Outliers remain after {max_tries} tries to remove them. Giving up on correction.")
    return (beats, ignored)


def interpolate_beats(alignment, reference_beats: List[int]):
    """Interpolate beats based on an alignment and a reference beat to ticks match.

    Args:
        alignment (List[AlignmentAtom]): The aligment to interpolate
        reference_beats (List[int]): Ticks position of the reference beats 

    Returns:
        DataFrame: Two column dataframe with the interpolated beats' times and whether they were inferred or not.
    """
    # Temporary: convert to old format
    alignment = [get_alignment.AlignmentAtom(tatum, time) for _, (tatum, time) in alignment.iterrows()]
    ticks, times = remove_outliers_and_duplicates(alignment)

    spline = scipy.interpolate.UnivariateSpline(ticks, times, s=0)  # s=0 for pure interpolation
    interpolation = spline(reference_beats)
    # Do not extrapolate with a spline!
    interpolation[(reference_beats < ticks.min()) | (reference_beats > ticks.max())] = np.nan

    beats = pd.DataFrame({"time": interpolation, "interpolated": [tick not in ticks for tick in reference_beats]})
    return beats


def attempt_correction(_beats, alignment: pd.DataFrame, reference_beats: List[int], anomalies: List[Tuple[int, int]], *, verbose=True):
    """Attempt to correct the beat extraction by removing the values causing outliers."""
    mask = alignment.score_time > 0

    filtered = pd.DataFrame()
    for index_before, index_after in anomalies:
        # Find range to erase
        range_start = alignment[alignment.score_time <= reference_beats[index_before]].iloc[-1].score_time
        range_end = alignment[alignment.score_time >= reference_beats[index_after]].iloc[0].score_time

        mask &= ((alignment.score_time < range_start) | (alignment.score_time > range_end))
    # Ensure first and last are preserved
    mask.iloc[0] = True
    mask.iloc[-1] = True

    filtered = alignment[~mask]
    alignment = alignment.loc[mask]

    if verbose:
        [print(f"Removing {item} in correction attempt") for item in filtered.iterrows()]

    # Temporary: convert to old format
    filtered_old = [get_alignment.AlignmentAtom(tatum, time) for _, (tatum, time) in filtered.iterrows()]
    return alignment, filtered_old


def remove_outliers_and_duplicates(alignment):
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
    # Only check values too quick, slow values are likely valid
    anomaly_indices = [(i, i+1) for (i, ibi) in enumerate(inter_beat_intervals)
                       if ibi * factor < mean_IBI or ibi <= 0]
    if verbose:
        [print(f"Anomaly between beats {i} and {j} detected: {beats[j]-beats[i]}s (max. {factor*mean_IBI}s)")
         for i, j in anomaly_indices]
    return anomaly_indices


task_docs = {
    "beats": "Find beats' positions using Nakamura's HMM alignment and pretty-midi's beat inference",
    "bars": "Find bars' positions using Nakamura's HMM alignment and pretty-midi's beat inference",
    "tempo": "Derive tempo from manual or inferred beats"
}


def gen_tasks(piece_id: str, targets):
    """Generate beat-related tasks."""
    yield from gen_task_beats(piece_id, targets)
    yield from gen_task_bars(piece_id, targets)
    yield from gen_task_tempo(piece_id, targets)


def gen_task_beats(piece_id: str, targets):
    """Generate tasks for bars."""
    # Attempt using manual annotations
    perf_beats = targets("beats")
    ref_midi = targets("ref_midi")
    perf_match = targets("match")
    if targets("manual_beats") is not None:
        yield {
            'basename': "beats",
            'file_dep': [targets("manual_beats"), __file__],
            'name': piece_id,
            'doc': "Use authoritative beats annotation",
            'targets': [perf_beats],
            'actions': [(shutil.copy, [targets("manual_beats"), perf_beats])]
        }
    else:
        if(targets("score") is None or targets("perfmidi") is None):
            return

        def caller(perf_match, ref_midi, perf_beats):
            alignment = get_alignment.read_alignment_file(perf_match)
            beat_reference = get_beat_reference_pm(ref_midi)
            beats, _ = get_beats(alignment, beat_reference)
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


def gen_task_bars(piece_id: str, targets):
    """Generate tasks for bars."""
    perf_bars = targets("bars")
    ref_midi = targets("ref_midi")
    perf_match = targets("match")

    if targets("manual_bars") is not None:
        yield {
            'basename': "bars",
            'file_dep': [targets("manual_bars"), __file__],
            'name': piece_id,
            'doc': "Use authoritative bars annotation",
            'targets': [perf_bars],
            'actions': [(shutil.copy, [targets("manual_bars"), perf_bars])]
        }
    elif not (targets("score") is None or targets("perfmidi") is None):
        def caller_bar(perf_match, ref_midi, perf_bars):
            alignment = get_alignment.read_alignment_file(perf_match)
            bar_reference = get_bar_reference_pm(ref_midi)
            bars, _ = get_beats(alignment, bar_reference)
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


def gen_task_tempo(piece_id: str, targets):
    """Generate tempo tasks."""
    # Attempt using manual annotations
    perf_beats = targets("beats")

    if not (targets("score") is None or targets("perfmidi") is None) or targets("manual_beats") is not None:
        perf_tempo = targets("tempo")

        def caller(perf_beats, perf_tempo):
            data = pd.read_csv(perf_beats)
            tempo_frame = pd.DataFrame({'time': data.time[1:], 'tempo': 60/np.diff(data.time)})
            tempo_frame.to_csv(perf_tempo, index=False)

        yield {
            'basename': "tempo",
            'file_dep': [perf_beats, __file__],
            'name': piece_id,
            'doc': task_docs["tempo"],
            'targets': [perf_tempo],
            'actions': [(caller, [perf_beats, perf_tempo])]
        }
