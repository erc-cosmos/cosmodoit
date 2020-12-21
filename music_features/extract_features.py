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
import sys
from get_sustain import *
from get_alignment import *
from get_beats import *
from get_onsetVelocity import *

def writeFile(filename,data):
    """ Writes a list of dictionaries with identical keys to disk
    """
    with open(filename, mode='w') as csvFile:
        fields = data[0].keys()
        writer = csv.DictWriter(csvFile, fieldnames=fields)
        writer.writeheader()
        writer.writerows(data)


def processFiles(refFilename,perfFilename,quarterLength=None,anacrusisOffset=None):
    """ One-stopper to process a performance from start to finish
    """

    basePerf,_ = os.path.splitext(os.path.basename(perfFilename))

    if refFilename is not None: # Skip features requiring a reference if there isn't one
        alignment = get_alignment(refFilename,perfFilename,cleanup=True)

        beats = get_beats(alignment,quarterLength,anacrusisOffset,plotting=False)
        beatsFilename = basePerf+"_beats.csv"
        writeFile(beatsFilename, beats)
    else:
        beats = None

    sustain = get_sustain(perfFilename)
    if sustain == []:
        print("Warning: no sustain event detected in "+perfFilename)
    else:
        pedalFilename = basePerf+"_sustain.csv"
        writeFile(pedalFilename, sustain)    
    
    velocities = get_onsetVelocity(perfFilename)
    if velocities == []:
        print("Warning: no note on event detected in "+perfFilename)
    else:
        velocityFilename = basePerf+"_velocity.csv"
        writeFile(velocityFilename, velocities)
    
    #TODO: add other features
    return beats,sustain,velocities


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ref', default='test_midi/Chopin_Ballade_No._2_Piano_solo.mid')
    parser.add_argument('--perf', default=None)
    #TODO: Add a warning if default ref or perf files are used
    parser.add_argument('--quarter', default=None, type=int)
    parser.add_argument('--offset', default=None, type=int)
    args = parser.parse_args()
    
    # Ensure execution directory
    scriptLocation = os.path.dirname(sys.argv[0])
    if scriptLocation != '':
        os.chdir(scriptLocation)
    
    refFilename = args.ref
    perfFilename = args.perf

    processFiles(args.ref,args.perf,quarterLength=args.quarter, anacrusisOffset=args.offset)
    