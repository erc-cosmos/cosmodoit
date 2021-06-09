import argparse
import itertools as itt
import os
import sys
import collections

import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
import scipy.interpolate
import pretty_midi as pm

from get_alignment import get_alignment

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

    ticks, _ = filter_outliers(alignment)
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


def get_beats(alignment, reference_beats):
    """Extract beats timing from an alignment of the notes."""

    # Find outliers and prefilter data
    ticks, times = filter_outliers(alignment)

    spline = sp.interpolate.UnivariateSpline(ticks, times, s=0)  # s=0 for pure interpolation
    interpolation = spline(reference_beats)
    tempos = [np.nan, *(60/np.diff(interpolation))]
    beats = [{'count': count,
              'time': time,
              'interpolated': tick not in ticks,
              'tempo': tempo
              }
             for count, (tick, time, tempo) in enumerate(zip(reference_beats, interpolation, tempos))]

    return beats


def filter_outliers(alignment):
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


def plot_beats(beats, interpolation, ticks, quarter_length, times):
    """ Plots score time against real time and tempo against score time
    """
    #plt.plot(np.array([beat['count'] for beat in beats])[1:],60/np.diff(interpolation),label="IOI")
    plt.plot([beat['count'] for beat in beats], interpolation)
    plt.scatter(ticks/quarter_length, times)
    plt.show(block=True)
    plt.plot(60/np.diff([beat['time'] for beat in beats]))
    plt.show(block=True)


def prompt_beat_params(alignment, quarter_length=None, anacrusis_offset=None, force=False):
    """ Prompts for missing information in beat detection
    Does nothing if all it is already known, unless force is True
    """
    if force or quarter_length is None or anacrusis_offset is None:
        [print(it) for it in alignment[:10]]  # Show first 10 lines to give context
        if force or quarter_length is None:
            quarter_length = int(input("Please enter the beat length (in ticks):"))
        if force or anacrusis_offset is None:
            anacrusis_offset = int(input("Please enter the beat offset (in ticks):"))
    return BeatParams(quarter_length, anacrusis_offset)


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

    alignment = get_alignment(refFilename=args.ref, perfFilename=args.perf, cleanup=False)

    quarterLength, anacrusisOffset = prompt_beat_params(alignment, args.quarter, args.offset)
    reference_beats = make_beat_reference(alignment, quarterLength, anacrusisOffset)

    beats = get_beats(alignment, reference_beats, plotting=False)
    print(beats)
