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

#TODO: Split into separate files

def writeFile(filename,data):
    with open(filename, mode='w') as csvFile:
        fields = data[0].keys()
        writer = csv.DictWriter(csvFile, fieldnames=fields)
        writer.writeheader()
        writer.writerows(data)


def processFiles(refFilename,perfFilename):
    """ One stopper to process from start to finish
    """
    alignment = get_alignment(refFilename,perfFilename,cleanup=True)
    basePerf,_ = os.path.splitext(os.path.basename(perfFilename))

    ### Ask User for the base beat and anacrusis offset
    #TODO: Determine automatically
    print(alignment[:10]) # Show first 10 lines to give context
    quarterLength = int(input("Please enter the beat length (in ticks):"))
    anacrusisOffset = int(input("Please enter the beat offset (in ticks):"))
    
    beats = get_beats(alignment,quarterLength,anacrusisOffset,plotting=False)
    beatsFilename = basePerf+"_beats.csv"
    writeFile(beatsFilename, beats)
    
    sustain = get_sustain(perfFilename)
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
    