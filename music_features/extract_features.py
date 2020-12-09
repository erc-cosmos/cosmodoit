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
    alignment = get_alignment(refFilename,perfFilename,cleanup=True)
    basePerf,_ = os.path.splitext(os.path.basename(perfFilename))

    beats = get_beats(alignment,quarterLength,anacrusisOffset,plotting=False)
    beatsFilename = basePerf+"_beats.csv"
    writeFile(beatsFilename, beats)
    
    sustain = get_sustain(perfFilename)
    pedalFilename = basePerf+"_sustain.csv"
    writeFile(pedalFilename, sustain)    
    
    velocities = get_onsetVelocity(perfFilename)
    velocityFilename = basePerf+"_velocity.csv"
    writeFile(velocityFilename, velocities)
    
    #TODO: add other features
    return beats,sustain,velocities


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ref', default='test_midi/Chopin_Ballade_No._2_Piano_solo.mid')
    parser.add_argument('--perf', default='test_midi/2020-03-12_EC_Chopin_Ballade_N2_Take_2.mid')
    parser.add_argument('--quarter', default=None)
    parser.add_argument('--offset', default=None)
    args = parser.parse_args()
    
    print(os.getcwd())
    refFilename = args.ref
    perfFilename = args.perf

    processFiles(args.ref,args.perf,quarterLength=args.quarter, anacrusisOffset=args.offset)
    