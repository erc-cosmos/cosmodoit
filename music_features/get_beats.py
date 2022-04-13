"""Module to extract beat timings from a midi interpretation and corresponding score."""
from typing import List, Tuple
import warnings

import numpy as np
import pandas as pd
import pretty_midi as pm
import scipy.interpolate

from music_features import get_alignment


def get_beats(alignment: pd.DataFrame, reference_beats, *,
              max_tries: int = 5, **kwargs) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Extract beats timing from an alignment of the notes."""
    ignored = pd.DataFrame()
    beats = interpolate_beats(alignment, reference_beats)
    for _ in range(max_tries):
        # Find outliers and prefilter data
        anomalies = find_outliers(beats, **kwargs)
        if anomalies == []:
            return (beats, ignored)
        else:
            alignment, new_ignored = attempt_correction(alignment, reference_beats, anomalies)
            ignored = pd.concat([ignored, new_ignored])
            beats = interpolate_beats(alignment, reference_beats)

    if find_outliers(beats) != []:
        warnings.warn(f"Outliers remain after {max_tries} tries to remove them. Giving up on correction.")
    return (beats, ignored)


def read_beats(beat_path: str) -> pd.DataFrame:
    """Read beats from disk."""
    return pd.read_csv(beat_path, usecols=['time'])


def write_beats(beat_path: str, beats: pd.DataFrame) -> None:
    """Write beats to disk."""
    beats.to_csv(beat_path, index=False)


def get_beat_reference_pm(ref_filename: str):
    """Find the beats in the reference according to pretty-midi."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        pretty = pm.PrettyMIDI(ref_filename)
    return np.round(np.array(pretty.get_beats()) * 1000)  # seconds to milliseconds


def get_bar_reference_pm(ref_filename: str):
    """Find the bar lines in the reference according to pretty-midi."""
    pretty = pm.PrettyMIDI(ref_filename)
    return np.round(np.array(pretty.get_downbeats()) * 1000)  # seconds to milliseconds


def interpolate_beats(alignment: pd.DataFrame, reference_beats: List[int]):
    """Interpolate beats based on an alignment and a reference beat to ticks match.

    Args:
        alignment (List[AlignmentAtom]): The aligment to interpolate
        reference_beats (List[int]): Ticks position of the reference beats

    Returns:
        DataFrame: Two column dataframe with the interpolated beats' times and whether they were inferred or not.
    """
    ticks, times = remove_outliers_and_duplicates(alignment)

    spline = scipy.interpolate.UnivariateSpline(ticks, times, s=0)  # s=0 for pure interpolation
    interpolation = spline(reference_beats)
    # Do not extrapolate with a spline!
    interpolation[(reference_beats < ticks.min()) | (reference_beats > ticks.max())] = np.nan

    beats = pd.DataFrame({"time": interpolation, "interpolated": [tick not in ticks for tick in reference_beats]})
    return beats


def attempt_correction(alignment: pd.DataFrame, reference_beats: List[int], anomalies: List[Tuple[int, int]],
                       *, verbose=True) -> Tuple[pd.DataFrame, pd.DataFrame]:
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

    filtered = alignment.loc[~mask]
    alignment = alignment.loc[mask]

    if verbose:
        [print(f"Removing {item} in correction attempt") for item in filtered.iterrows()]

    return alignment, filtered


def remove_outliers_and_duplicates(alignment: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """Prefilter data by removing duplicates and resorting."""
    # TODO: determine better which note to use when notes share a tatum
    alignment_filtered = alignment.drop_duplicates(subset=["score_time"]).sort_values("score_time")
    (_, ticks), (_, times) = alignment_filtered.iteritems()

    return np.array(ticks), np.array(times)


def find_outliers(beats, *, factor=4, verbose=True):
    """Perform an automated check for outliers."""
    beats = beats.time
    inter_beat_intervals = np.diff(beats)
    mean_IBI = np.mean(inter_beat_intervals)
    # Only check values too quick, slow values are likely valid
    anomaly_indices = [(i, i+1) for (i, ibi) in enumerate(inter_beat_intervals)
                       if ibi * factor < mean_IBI or ibi <= 0]
    if verbose:
        [print(f"Anomaly between beats {i} and {j} detected: {beats[j]-beats[i]}s (min. {factor*mean_IBI}s)")
         for i, j in anomaly_indices]
    return anomaly_indices


task_docs = {
    "beats": "Find beats' positions using Nakamura's HMM alignment and pretty-midi's beat inference",
    "bars": "Find bars' positions using Nakamura's HMM alignment and pretty-midi's beat inference",
    "tempo": "Derive tempo from manual or inferred beats"
}

param_sources = (get_beats, find_outliers)


def gen_tasks(piece_id: str, targets, **kwargs):
    """Generate beat-related tasks."""
    yield from gen_task_beats(piece_id, targets, **kwargs)
    yield from gen_task_bars(piece_id, targets, **kwargs)
    yield from gen_task_tempo(piece_id, targets)


def gen_task_beats(piece_id: str, targets, **kwargs):
    """Generate tasks for bars."""
    # Attempt using manual annotations
    perf_beats = targets("beats")
    ref_midi = targets("ref_midi")
    perf_match = targets("match")
    if targets("manual_beats") is not None:
        def manual_caller(manual_beats, perf_beats):
            beats = read_beats(manual_beats)
            if find_outliers(beats, factor=10, verbose=True) != []:
                warnings.warn(
                    f"Found anomalous beats in manually annotated {manual_beats}. Consider checking the annotation.")
            write_beats(beat_path=perf_beats, beats=beats)
        yield {
            'basename': "beats",
            'file_dep': [targets("manual_beats"), __file__],
            'name': piece_id,
            'doc': "Use authoritative beats annotation",
            'targets': [perf_beats],
            'actions': [(manual_caller, [targets("manual_beats"), perf_beats])]
        }
    else:
        if(targets("score") is None or targets("perfmidi") is None):
            return

        def caller(perf_match, ref_midi, perf_beats):
            alignment = get_alignment.read_alignment(perf_match)
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


def gen_task_bars(piece_id: str, targets, **kwargs):
    """Generate tasks for bars."""
    perf_bars = targets("bars")
    ref_midi = targets("ref_midi")
    perf_match = targets("match")

    if targets("manual_bars") is not None:
        def manual_caller_bar(manual_beats, perf_beats):
            beats = read_beats(manual_beats)
            if find_outliers(beats, factor=10, verbose=True) != []:
                warnings.warn(
                    f"Found anomalous beats in manually annotated {manual_beats}. Consider checking the annotation.")
            write_beats(beat_path=perf_beats, beats=beats)
        yield {
            'basename': "bars",
            'file_dep': [targets("manual_bars"), __file__],
            'name': piece_id,
            'doc': "Use authoritative bars annotation",
            'targets': [perf_bars],
            'actions': [(manual_caller_bar, [targets("manual_bars"), perf_bars])]
        }
    elif not (targets("score") is None or targets("perfmidi") is None):
        def caller_bar(perf_match, ref_midi, perf_bars):
            alignment = get_alignment.read_alignment(perf_match)
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
