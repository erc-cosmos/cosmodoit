import argparse
import itertools as itt
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
import scipy.interpolate

from get_alignment import get_alignment


def get_beats(alignment, quarterLength=None, anacrusisOffset=None, plotting=False, guess=False):
    """ Extracts beats timing from an alignment of the notes
    quarterLength is the number of midi ticks during a beat in the reference
    anacrusisOffset is the offset of the first whole beat (not necessarily the first beat of the first bar) 
    """

    # Find beats' onsets
    maxTatum = alignment[-1]['tatum']

    # Find outliers and prefilter data
    times, indices = np.unique(np.array([tatum['time'] for tatum in alignment]), return_index=True)
    ticks = np.array([tatum['tatum'] for tatum in alignment])[indices]

    # TODO: In progress

    # TODO: determine better which note to use when notes share a tatum
    ticks, indices = np.unique(np.array([tatum['tatum'] for tatum in alignment]), return_index=True)
    times = np.array([tatum['time'] for tatum in alignment])[indices]

    # Ask user for the base beat and anacrusis offset if not provided already
    if guess:
        quarterLength, anacrusisOffset = guess_beatInfo(ticks)
    else:
        quarterLength, anacrusisOffset = prompt_beatInfo(alignment, quarterLength, anacrusisOffset)

    interpolTarget = np.arange(anacrusisOffset, maxTatum, quarterLength)

    spline = sp.interpolate.UnivariateSpline(ticks, times, s=0)  # s controls smoothing of the Spline
    interpolation = spline(interpolTarget)
    tempos = [np.nan, *(60/np.diff(interpolation))]
    beats = [{'count': count,
              'time': time,
              'interpolated': tick not in ticks,
              'tempo': tempo
              }
             for count, (tick, time, tempo) in enumerate(zip(interpolTarget, interpolation, tempos))]

    scoreTime = ticks/quarterLength

    if plotting:
        plot_beats(beats, interpolation, ticks, quarterLength, times)

    if plotting:
        plot_beatRatios(ticks, quarterLength, times, spline)

    return beats


def guess_beatInfo(ticks):
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

    return quarter_length, best_offset


def plot_beatRatios(ticks, quarterLength, times, spline):
    """ Plots the ratio of actual note duration to expected
    Expected note duration is based on neighbouring tempo
    """
    ratios = []
    for (tick, time, tick_next, time_next) in zip(ticks, times, ticks[1:], times[1:]):
        # TODO: Separate by line
        if tick == tick_next:  # Ignore simultaneous notes
            continue
        expectedDuration = spline(tick_next)-spline(tick)
        actualDuration = time_next-time
        ratios.append(actualDuration/expectedDuration)
    plt.plot(ticks[:-1]/quarterLength, ratios)
    plt.plot(ticks[:-1]/quarterLength, np.diff(ticks)/quarterLength)
    plt.hlines(1, xmin=ticks[0], xmax=ticks[-1]/quarterLength)
    plt.show(block=True)


def plot_beats(beats, interpolation, ticks, quarterLength, times):
    """ Plots score time against real time and tempo against score time
    """
    #plt.plot(np.array([beat['count'] for beat in beats])[1:],60/np.diff(interpolation),label="IOI")
    plt.plot([beat['count'] for beat in beats], interpolation)
    plt.scatter(ticks/quarterLength, times)
    plt.show(block=True)
    plt.plot(60/np.diff([beat['time'] for beat in beats]))
    plt.show(block=True)


def prompt_beatInfo(alignment, quarterLength=None, anacrusisOffset=None, force=False):
    """ Prompts for missing information in beat detection
    Does nothing if all it is already known, unless force is True
    """
    if force or quarterLength is None or anacrusisOffset is None:
        [print(it) for it in alignment[:10]]  # Show first 10 lines to give context
        if force or quarterLength is None:
            quarterLength = int(input("Please enter the beat length (in ticks):"))
        if force or anacrusisOffset is None:
            anacrusisOffset = int(input("Please enter the beat offset (in ticks):"))
    return quarterLength, anacrusisOffset


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

    quarterLength, anacrusisOffset = prompt_beatInfo(alignment, args.quarter, args.offset)

    beats = get_beats(alignment, quarterLength, anacrusisOffset, plotting=False)
    print(beats)
