import argparse
import os
import numpy as np
import scipy as sp
import scipy.interpolate
import matplotlib.pyplot as plt
import itertools as itt
from get_alignment import *


def get_beats(alignment, quarterLength, anacrusisOffset, outfileName=None, plotting = False):
    #### Find beats' onsets
    maxTatum = alignment[-1]['tatum']

    # Ask user for the base beat and anacrusis offset if not provided already
    #TODO: Determine automatically
    quarterLength,anacrusisOffset = prompt_beatInfo(quarterLength,anacrusisOffset)

    ticks,indices = np.unique(np.array([tatum['tatum'] for tatum in alignment]),return_index=True) #TODO: determine better which note to use when notes share a tatum
    times = np.array([tatum['time'] for tatum in alignment])[indices]
    interpolTarget = np.arange(anacrusisOffset,maxTatum,quarterLength)

    spline = sp.interpolate.UnivariateSpline(ticks, times,s=1) # s controls smoothing of the Spline
    interpolation = spline(interpolTarget)
    beats = [{'count': count, 
            'time': time,
            'interpolated': tick not in ticks
            }
            for count,(tick,time) in enumerate(zip(interpolTarget,interpolation))]

    scoreTime = ticks/quarterLength
    
    if plotting:
        plot_beats(beats, interpolation, ticks, quarterLength, times)

    if plotting:
        plot_beatRatios(ticks, quarterLength, times, spline)

    return beats

def plot_beatRatios(ticks, quarterLength, times, spline):
    ratios = []
    for (tick,time,tick_next,time_next) in zip(ticks,times, ticks[1:], times[1:]):
        #TODO: Separate by line
        if tick == tick_next: # Ignore simultaneous notes
            continue
        expectedDuration = spline(tick_next)-spline(tick)
        actualDuration = time_next-time
        ratios.append(actualDuration/expectedDuration)
    plt.plot(ticks[:-1]/quarterLength,ratios)
    plt.plot(ticks[:-1]/quarterLength,np.diff(ticks)/quarterLength)
    plt.hlines(1,xmin=ticks[0],xmax=ticks[-1]/quarterLength)
    plt.show(block=True)

def plot_beats(beats, interpolation, ticks, quarterLength, times):
    #plt.plot(np.array([beat['count'] for beat in beats])[1:],60/np.diff(interpolation),label="IOI")
    plt.plot([beat['count'] for beat in beats],interpolation)
    plt.scatter(ticks/quarterLength,times)
    plt.show(block=True)
    plt.plot(60/np.diff([beat['time'] for beat in beats]))
    plt.show(block=True)


def prompt_beatInfo(alignment,quarterLength=None,anacrusisOffset=None):
    if quarterLength is None or anacrusisOffset is None:
        print(alignment[:10]) # Show first 10 lines to give context
        if quarterLength is None:
            quarterLength = int(input("Please enter the beat length (in ticks):"))
        if anacrusisOffset is None:
            anacrusisOffset = int(input("Please enter the beat offset (in ticks):"))
    return quarterLength, anacrusisOffset

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ref', default='test_midi/Chopin_Ballade_No._2_Piano_solo.mid')
    parser.add_argument('--perf', default='test_midi/2020-03-12_EC_Chopin_Ballade_N2_Take_2.mid')    
    parser.add_argument('--quarter', default=None)
    parser.add_argument('--offset', default=None)
    args = parser.parse_args()

    os.chdir(os.path.dirname(sys.argv[0]))
    alignment = get_alignment(refFilename=args.ref, perfFilename=args.perf,cleanup=False)

    quarterLength, anacrusisOffset = prompt_beatInfo(alignment,args.quarter,args.offset)

    beats = get_beats(alignment,quarterLength,anacrusisOffset, plotting=False)
    print(beats)