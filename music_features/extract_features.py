#!/usr/bin/python3
# -*- coding: utf-8 -*-
import csv
import numpy as np
import scipy as sp
import scipy.interpolate
import matplotlib.pyplot as plt
import itertools as itt
import os
import subprocess
import argparse
import mido
import sys
from get_sustain import *

#TODO: Split into separate files

def readAlignmentFile(filename):
    #### Read file
    with open(filename) as csvFile:
        csvReader = csv.reader(csvFile, delimiter='\t')
        # Extract relevant columns
        return [{'tatum':int(row[8]), 'time':float(row[1])}
                for row in csvReader
                if len(row)>3 and row[8]!='-1' # Not a metaline and not a mismatch
                ]

def writeFile(filename,data):
    with open(filename, mode='w') as csvFile:
        fields = data[0].keys()
        writer = csv.DictWriter(csvFile, fieldnames=fields)
        writer.writeheader()
        writer.writerows(data)


def beatExtraction(tatums, quarterLength, anacrusisOffset, outfileName=None, plotting = False):
    #### Find beats' onsets
    beats = []
    maxTatum = tatums[-1]['tatum']
    tatumIter = iter(tatums)
    nextTatum = next(tatumIter)

    ticks,indices = np.unique(np.array([tatum['tatum'] for tatum in tatums]),return_index=True) #TODO: determine better which note to use when notes share a tatum
    times = np.array([tatum['time'] for tatum in tatums])[indices]
    interpolTarget = np.arange(anacrusisOffset,maxTatum,quarterLength)

    spline = sp.interpolate.UnivariateSpline(ticks, times,s=1) # s controls smoothing of the Spline
    interpolation = spline(interpolTarget)
    beats = [{'count': count, 
            'time': time,
            'interpolated': tick not in ticks
            }
            for count,(tick,time) in enumerate(zip(interpolTarget,interpolation))]

    if plotting:
        #plt.plot(np.array([beat['count'] for beat in beats])[1:],60/np.diff(interpolation),label="IOI")
        plt.plot([beat['count'] for beat in beats],interpolation)
        plt.scatter(ticks/quarterLength,times)
        plt.show(block=True)
        plt.plot(60/np.diff([beat['time'] for beat in beats]))
        plt.show(block=True)

    ratios = []
    for (tick,time,tick_next,time_next) in zip(ticks,times, ticks[1:], times[1:]):
        #TODO: Separate by line
        if tick == tick_next: # Ignore simultaneous notes
            continue
        expectedDuration = spline(tick_next)-spline(tick)
        actualDuration = time_next-time
        ratios.append(actualDuration/expectedDuration)

    if plotting:
        plt.plot(ticks[:-1]/quarterLength,ratios)
        plt.plot(ticks[:-1]/quarterLength,np.diff(ticks)/quarterLength)
        plt.hlines(1,xmin=ticks[0],xmax=ticks[-1]/quarterLength)
        plt.show()

    ### Save output if requested    
    if outfileName is not None:
        writeFile(outfileName,beats)

    return beats

def runAlignment(refFilename, perfFilename, 
        midi2midiExecLocation="./MIDIToMIDIAlign.sh",
        #score2midiExecLocation="music_features/ScoreToMIDIAlign.sh",
        cleanup=True, recompute=False):
    # Crop .mid extension as the script doesn't want them
    refFilename,refType = os.path.splitext(refFilename)
    perfFilename = os.path.splitext(perfFilename)[0] 

    if refType != ".mid": #TODO: accept .midi file extension for midi files
        # NYI
        # Generate a midi from the score or run the score-to-midi (once fixed)
        raise NotImplementedError

    # Run the alignment (only if needed or requested)
    outFile = os.path.basename(perfFilename)+"_match.txt"
    if recompute or not os.path.isfile(outFile):
        output = subprocess.run([midi2midiExecLocation,refFilename,perfFilename])
    alignment = readAlignmentFile(outFile)
    
    if cleanup:
        interRefExtensions = ['_fmt3x.txt','_hmm.txt','_spr.txt']
        interPerfExtensions = ['_spr.txt', '_match.txt']
        refBase = os.path.basename(refFilename)
        perfBase = os.path.basename(perfFilename)
        [os.remove(refBase+ext) for ext in interRefExtensions]
        [os.remove(perfBase+ext) for ext in interPerfExtensions]
    return alignment


def processFiles(refFilename,perfFilename):
    """ One stopper to process from start to finish
    """
    alignment = runAlignment(refFilename,perfFilename,cleanup=True)
    basePerf = os.path.basename(perfFilename)

    ### Ask User for the base beat and anacrusis offset
    #TODO: Determine automatically
    print(alignment[:10]) # Show first 10 lines to give context
    quarterLength = int(input("Please enter the beat length (in ticks):"))
    anacrusisOffset = int(input("Please enter the beat offset (in ticks):"))
    
    beats = beatExtraction(alignment,quarterLength,anacrusisOffset,basePerf+"_beats.csv",False)
    
    sustain = getPedal(perfFilename)
    pedalFilename = basePerf+"_sustain.csv"
    writeFile(pedalFilename, sustain)
    return beats,sustain


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ref', default='test_midi/Chopin_Ballade_No._2_Piano_solo.mid')
    parser.add_argument('--perf', default='test_midi/2020-03-12_EC_Chopin_Ballade_N2_Take_2.mid')
    args = parser.parse_args()
    
    os.chdir(os.path.dirname(sys.argv[0]))
    print(os.getcwd())
    refFilename = args.ref
    perfFilename = args.perf

    processFiles(refFilename,perfFilename)
    