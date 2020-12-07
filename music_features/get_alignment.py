#!/usr/bin/python3
# -*- coding: utf-8 -*-
import csv
import os
import argparse
import sys
import subprocess

def get_alignment(refFilename, perfFilename, 
        midi2midiExecLocation="./MIDIToMIDIAlign.sh",
        #score2midiExecLocation="music_features/ScoreToMIDIAlign.sh",
        cleanup=True, recompute=False):
    # Crop .mid extension as the script doesn't want them
    refFilename,refType = os.path.splitext(refFilename)
    perfFilename,perfType = os.path.splitext(perfFilename)

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
        cleanAlignmentFiles(refFilename, perfFilename)
    return alignment

def readAlignmentFile(filename):
    #### Read file
    with open(filename) as csvFile:
        csvReader = csv.reader(csvFile, delimiter='\t')
        # Extract relevant columns
        return [{'tatum':int(row[8]), 'time':float(row[1])}
                for row in csvReader
                if len(row)>3 and row[8]!='-1' # Not a metaline and not a mismatch
                ]


def cleanAlignmentFiles(refFilename, perfFilename):
    interRefExtensions = ['_fmt3x.txt','_hmm.txt','_spr.txt']
    interPerfExtensions = ['_spr.txt', '_match.txt']
    refBase = os.path.basename(refFilename)
    perfBase = os.path.basename(perfFilename)
    [os.remove(refBase+ext) for ext in interRefExtensions]
    [os.remove(perfBase+ext) for ext in interPerfExtensions]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ref', default='test_midi/Chopin_Ballade_No._2_Piano_solo.mid')
    parser.add_argument('--perf', default='test_midi/2020-03-12_EC_Chopin_Ballade_N2_Take_2.mid')
    args = parser.parse_args()
    
    os.chdir(os.path.dirname(sys.argv[0]))
    
    refFilename = args.ref
    perfFilename = args.perf
    
    alignment = get_alignment(refFilename=refFilename, perfFilename=perfFilename)
    print(alignment)