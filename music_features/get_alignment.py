#!/usr/bin/python3
# -*- coding: utf-8 -*-
import csv
import os
import argparse
import sys
import subprocess
import collections
import xml.etree.ElementTree as ET

from MIDIToMIDIAlign import runAlignment


def get_score_alignment(refFilename, perfFilename,
                        score2midiExecLocation="./MusicXMLToMIDIAlign.sh",
                        museScoreExec="/Applications/MuseScore 3.app/Contents/MacOS/mscore",
                        cleanup=True, recompute=False):
    """Call Nakamura's Score to Midi alignment software.

    Intermediate files will be removed if cleanup is True
    If recompute is False, existing intermediate files will be reused if present
    """
    # Crop .mid extension as the script doesn't want them
    refFilename, refType = os.path.splitext(refFilename)
    perfFilename, perfType = os.path.splitext(perfFilename)

    if refType not in [".xml"]:
        if refType in [".mscz", ".mxl"]:  # TODO: add other valid formats
            # Generate a midi from the score
            # TODO: check that musescore is correctly found
            # TODO: check if conversion is already done
            subprocess.run([museScoreExec, refFilename+refType, "--export-to", refFilename+".xml"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            raise NotImplementedError

    # Run the alignment (only if needed or requested)
    outFile = perfFilename+"_match.txt"
    if recompute or not os.path.isfile(outFile):
        output = subprocess.run([score2midiExecLocation, refFilename, perfFilename])
    alignment = readAlignmentFile(outFile)

    if cleanup:
        clean_alignment_files(refFilename, perfFilename)
    return alignment


def removeDirections(filename, outfile=None):
    """Remove all directions from a musicxml file."""
    tree = ET.parse(filename)
    for elem in tree.findall(".//direction"):
        elem.clear()  # TODO: actually remove it instad of clearing (causes warnings)
    tree.write(outfile if outfile is not None else filename)


def get_alignment(refFilename, perfFilename,
                  midi2midiExecLocation="./MIDIToMIDIAlign.sh",
                  # score2midiExecLocation="music_features/ScoreToMIDIAlign.sh",
                  museScoreExec="/Applications/MuseScore 3.app/Contents/MacOS/mscore",
                  cleanup=True, recompute=False):
    """Call Nakamura's midi to midi alignment software.

    Intermediate files will be removed if cleanup is True
    If recompute is False, existing intermediate files will be reused if present
    """
    # Crop .mid extension as the script doesn't want them
    refFilename, refType = os.path.splitext(refFilename)
    preprocess_to_midi(refType, museScoreExec, refFilename)
    perfFilename, perfType = os.path.splitext(perfFilename)

    # Run the alignment (only if needed or requested)
    outFile = perfFilename+"_match.txt"
    if recompute or not os.path.isfile(outFile):
        runAlignment(refFilename, perfFilename)
    alignment = readAlignmentFile(outFile)

    if cleanup:
        clean_alignment_files(refFilename, perfFilename)
        clean_preprocess_files(refType, refFilename)

    return alignment


def preprocess_to_midi(refType, museScoreExec, refFilename):
    if refType != ".mid":  # TODO: accept .midi file extension for midi files (needs editing the bash script)
        if refType in [".mxl", ".xml", ".mscz"]:  # TODO: add other valid formats
            # Generate a midi from the score
            # TODO: run the score-to-midi instead (once fixed)
            # TODO: check that musescore is correctly found
            # TODO: check if conversion is already done
            subprocess.run([museScoreExec, refFilename+refType, "--export-to",
                           refFilename+".xml"], stderr=subprocess.DEVNULL)
            removeDirections(refFilename+".xml", refFilename+"_nodir.xml")
            subprocess.run([museScoreExec, refFilename+"_nodir.xml", "--export-to",
                           refFilename+".mid"], stderr=subprocess.DEVNULL)
        else:
            raise NotImplementedError


def clean_preprocess_files(refType, refFilename):
    """Removes the files generated prior to aligment."""
    if refType != ".mid":
        os.remove(refFilename+".mid")
        os.remove(refFilename+"_nodir.xml")
        if refType != '.xml':
            os.remove(refFilename+".xml")


def readAlignmentFile(filename):
    """Read the output of Nakamura's software and extracts relevant information."""
    AlignmentAtom = collections.namedtuple("AlignmentAtom", ('tatum', 'time'))
    with open(filename) as csvFile:
        csvReader = csv.reader(csvFile, delimiter='\t')
        # Extract relevant columns
        return [AlignmentAtom(tatum=int(row[8]), time=float(row[1]))
                for row in csvReader
                if len(row) > 3 and row[8] != '-1' and row[9] != '*'  # Not a metaline and not a mismatch
                ]


def clean_alignment_files(refFilename, perfFilename):
    """Remove intermediate files generated by Nakamura's software."""
    # TODO: Add flag to keep the _match file
    interRefExtensions = ['_fmt3x.txt', '_hmm.txt', '_spr.txt', '_ref.mid']
    interPerfExtensions = ['_spr.txt', '_match.txt', '_perf.mid']
    for ext in interRefExtensions:
        try:
            os.remove(refFilename+ext)
        except FileNotFoundError:
            pass
    for ext in interPerfExtensions:
        try:
            os.remove(perfFilename+ext)
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ref')
    parser.add_argument('--perf')
    parser.add_argument('--keep', action='store_true')
    args = parser.parse_args()

    # Ensure execution directory
    scriptLocation = os.path.dirname(sys.argv[0])
    if scriptLocation != '':
        os.chdir(scriptLocation)

    refFilename = args.ref
    perfFilename = args.perf

    alignment = get_alignment(refFilename=refFilename, perfFilename=perfFilename, cleanup=False)
    print(alignment)
