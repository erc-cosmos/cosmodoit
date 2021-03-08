#!/usr/bin/python3
import argparse
import os
import numpy as np
import scipy as sp
import scipy.interpolate
import matplotlib.pyplot as plt
import itertools as itt
from get_alignment import *

from extract_features import writeFile

def extractITempoForwards(alignment):
    data = []

    averageTatumTime = alignment[-1]['time']/alignment[-1]['tatum']

    last_tatum = alignment[0]['tatum'] # Last valid tatum (inferior to current)
    last_time = alignment[0]['time'] # 
    current_tatum = last_tatum
    current_time = last_time
    for nextItem in alignment[1:]:
        next_tatum = nextItem['tatum']
        next_time = nextItem['time']
        if next_tatum < current_tatum:
            continue # Alignment crosses itself
        elif next_tatum == current_tatum:
            current_time = next_time
            if current_tatum == last_tatum: # Should only happen in the first iterations
                continue
        else:
            last_tatum = current_tatum
            last_time = current_time
            current_tatum = next_tatum
            current_time = next_time
        datum = nextItem.copy()
        datum['itempo'] = (next_tatum-last_tatum)/(next_time-last_time)*averageTatumTime
        data.append(datum)
    return data

def extractITempoBackwards(alignment):
    data = []

    averageTatumTime = alignment[-1]['time']/alignment[-1]['tatum']

    last_tatum = alignment[-1]['tatum'] # Last valid tatum (inferior to current)
    last_time = alignment[-1]['time'] # 
    current_tatum = last_tatum
    current_time = last_time
    for nextItem in reversed(alignment[1:]):
        next_tatum = nextItem['tatum']
        next_time = nextItem['time']
        if next_tatum > current_tatum:
            continue # Alignment crosses itself
        elif next_tatum == current_tatum:
            current_time = next_time
            if current_tatum == last_tatum: # Should only happen in the first iterations
                continue
        else:
            last_tatum = current_tatum
            last_time = current_time
            current_tatum = next_tatum
            current_time = next_time
        datum = nextItem.copy()
        datum['itempo'] = (next_tatum-last_tatum)/(next_time-last_time)*averageTatumTime
        data.append(datum)
    return data

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ref', default='test_midi/Chopin_Ballade_No._2_Piano_solo.mscz')
    parser.add_argument('--perf', default='test_midi/2020-03-12_EC_Chopin_Ballade_N2_Take_2.mid')
    parser.add_argument('--quarter', default=None)
    parser.add_argument('--offset', default=None)
    args = parser.parse_args()
    # Ensure execution directory
    scriptLocation = os.path.dirname(sys.argv[0])
    if scriptLocation != '':
        os.chdir(scriptLocation)
    
    alignment = get_alignment(refFilename=args.ref, perfFilename=args.perf,cleanup=False)

    dataBackwards = extractITempoBackwards(alignment)[:]
    dataForwards = extractITempoForwards(alignment)
    # scoreTimes,realTimes,instantTempo_unscaled = zip(*
    #     [ (curr['tatum'], curr["time"], ((curr['tatum']-last['tatum']) / (curr["time"]-last["time"]))) 
    #     for last, curr in zip(alignment, alignment[1:])
    #     if (curr["time"]-last["time"])>0 and (curr['tatum']-last['tatum']) !=0
    #     ]
    # )

    # data = [{'tatum':b,'time':t,'tempo':it/1000} for (b,t,it) in zip(scoreTimes,realTimes,instantTempo_unscaled) if it < 0000]
    writeFile("itempoForward.csv",dataForwards)
    writeFile("itempoBackward.csv",dataBackwards)
    # plt.plot(scoreTimes,instantTempo_unscaled)
    # plt.show(block=False)
    # plt.figure()
    # plt.plot(realTimes,instantTempo_unscaled)
    # plt.show(block=True)
    # print(instantTempo_unscaled)