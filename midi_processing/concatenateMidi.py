#!/usr/bin/python3

import csv
import mido
import argparse

def concatMidi(infilenames, outfilename, outmetafile=None, padding=5):
    """
    Concatenates the input midi files into a large one
    infilenames -- iterable of paths containing the files to concatenate
    outfilename -- path to output file
    outmetafile -- path to the output meta-descriptor file (optional)
    padding -- gap, in seconds, between files (default=5)
    """
    ppq = mido.MidiFile(infilenames[0]).ticks_per_beat
    
    offset = 0
    padNext = False
    mainTrack = mido.MidiTrack()
    meta = []
    # Default value for tempo; might be set by a value for set_tempo later
    tempo = 500000

    for infilename in infilenames:
        midi = mido.MidiFile(infilename)
        # Warning if PPQ changes
        if midi.ticks_per_beat and (midi.ticks_per_beat != ppq):
            print("PPQ mismatch", ppq, midi.ticks_per_beat)
        # Concatenate events
        for event in mido.merge_tracks(midi.tracks):
            if padNext:
                padNext = False
                event.time += round(mido.second2tick(padding,ppq,tempo))
            if event.type == 'set_tempo':
                tempo = event.tempo
            mainTrack.append(event)
        # Meta information
        duration = midi.length
        meta.append((infilename, offset, offset + duration))
        offset += duration + padding
        # Setup next iteration
        padNext=True

    newMid = mido.MidiFile(type=1,ticks_per_beat = ppq)
    newMid.tracks = [mainTrack]
    newMid.save(outfilename)
    
    if outmetafile is not None:
        writeCsv(metafile, meta, ("File", "Start", "End") )

def writeCsv(outputFile, data, header):
    with open(outmetafile,'w') as outputFile:
        writer = csv.writer(outputFile)
        writer.writerow(header)
        writer.writerows(meta)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    parser.add_argument('--outFile')
    parser.add_argument('--meta', default=None)
    args = parser.parse_args()
    
    concatMidi(args.files, args.outFile, args.meta)
