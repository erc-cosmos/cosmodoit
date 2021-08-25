import argparse
import os
import sys
import collections
import warnings

import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
import scipy.interpolate
import pretty_midi as pm
from util import write_file, targets_factory

import get_alignment

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
    return np.array([pretty.time_to_tick(beat_time) for beat_time in pretty.get_beats()])


def get_beats(alignment, reference_beats, *, max_tries=3):
    """Extract beats timing from an alignment of the notes."""
    # beats = None # for scope
    for _ in range(max_tries):
        # Find outliers and prefilter data
        ticks, times = preprocess(alignment)

        spline = sp.interpolate.UnivariateSpline(ticks, times, s=0)  # s=0 for pure interpolation
        interpolation = spline(reference_beats)
        interpolation[(reference_beats<ticks.min()) | (reference_beats>ticks.max())] = np.nan
        tempos = [np.nan, *(60/np.diff(interpolation))]
        beats = [{'count': count,
                'time': time,
                'interpolated': tick not in ticks,
                'tempo': tempo}
                for count, (tick, time, tempo) in enumerate(zip(reference_beats, interpolation, tempos))]

        anomalies = find_outliers(beats)
        if anomalies == []:
            return beats
        else:
            alignment = attempt_correction(beats, alignment, reference_beats, anomalies)

    warnings.warn(f"Outliers remain after {max_tries} tries to remove them. Giving up on correction.")
    return beats


def attempt_correction(beats, alignment, reference_beats, anomalies, *, verbose=True):
    """Attempt to correct the beat extraction by removing the values causing outliers."""
    for index_before, index_after in anomalies:
        # Convert indices to ticks
        tick_before = reference_beats[index_before]
        tick_after = reference_beats[index_after]
        # Remove the alignment entries with these ticks (should interpolate on the next run)
        if verbose:
            [print(f"Removing {item} in correction attempt") for item in alignment if item.tatum in (tick_before, tick_after)]
        alignment = [item for item in alignment if item.tatum not in (tick_before, tick_after)]
        # If the beat is already interpolated, remove the closest value
        if beats[index_before]['interpolated']:
            closest = np.min(np.abs(np.array([item.tatum for item in alignment])-tick_before))
            if verbose:
                [print(f"Removing {item} in correction attempt") for item in alignment if item.tatum - tick_before == closest]
            alignment = [item for item in alignment if item.tatum - tick_before != closest]
        if beats[index_after]['interpolated']:
            closest = np.min(np.abs(np.array([item.tatum for item in alignment])-tick_after))
            if verbose:
                [print(f"Removing {item} in correction attempt") for item in alignment if item.tatum - tick_after == closest]
            alignment = [item for item in alignment if item.tatum - tick_after != closest]
    return alignment

def preprocess(alignment):
    # Find outliers and prefilter data
    times, indices = np.unique(np.array([alignment_atom.time for alignment_atom in alignment]), return_index=True)
    ticks = np.array([aligment_atom.tatum for aligment_atom in alignment])[indices]

    # TODO: In progress

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


# def plot_beats(beats, ticks, quarter_length, times):
def plot_beats(beats):
    """ Plots score time against real time and tempo against score time
    """
    #plt.plot(np.array([beat['count'] for beat in beats])[1:],60/np.diff(interpolation),label="IOI")
    # plt.plot([beat['count'] for beat in beats], interpolation)
    # plt.scatter(ticks/quarter_length, times)
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


def find_outliers(beats, *, factor=3, verbose=True):
    """Perform an automated check for outliers."""
    beats = [beat["time"] for beat in beats]
    inter_beat_intervals = np.diff(beats)
    mean_IBI = np.mean(inter_beat_intervals)
    anomaly_indices = [(i, i+1) for (i, ibi) in enumerate(inter_beat_intervals)
                       if ibi * factor < mean_IBI] # Only check values too quick, slow values are likely valid
    if verbose:
        [print(f"Anomaly between beats {i} and {j} detected") for i,j in anomaly_indices]
    return anomaly_indices


def gen_tasks(piece_id, ref_path, perf_path, working_folder="tmp"):
    ref_targets = targets_factory(ref_path, working_folder=working_folder)
    perf_targets = targets_factory(perf_path, working_folder=working_folder)

    ref_midi = ref_targets("_ref.mid")
    perf_match = perf_targets("_match.txt")
    perf_beats = perf_targets("_beats.csv")

    def caller(perf_match, ref_midi, perf_beats, **kwargs):
        alignment = get_alignment.read_alignment_file(perf_match)
        beat_reference = get_beat_reference_pm(ref_midi)
        beats = get_beats(alignment, beat_reference)
        write_file(perf_beats, beats)
        return True
    yield {
        'basename': "beats",
        'file_dep': [perf_match, ref_midi, __file__],
        'name': piece_id,
        'targets': [perf_beats],
        'actions': [(caller, [perf_match, ref_midi, perf_beats])]
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
