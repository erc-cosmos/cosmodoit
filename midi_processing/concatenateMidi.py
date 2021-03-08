#!/usr/bin/python3

import csv
import mido
import argparse

def concatMidi(infilenames, outfilename, outmetafile=None, padding=5):
    ppq = mido.MidiFile(infilenames[0]).ticks_per_beat
    newMid = mido.MidiFile(type=1,ticks_per_beat = ppq)

    offset = 0
    padNext = False
    mainTrack = mido.MidiTrack()
    lastTempoTick = 0
    lastTempoTime = 0
    meta = []
    # Default value for tempo; might be set by a value for set_tempo later
    tempo = 500000

    for infilename in infilenames:
        midi = mido.MidiFile(infilename)

        # Use default for pulses per quarter note if its not set
        if midi.ticks_per_beat and (midi.ticks_per_beat != ppq):
            print("PPQ mismatch", ppq, midi.ticks_per_beat)

        for event in mido.merge_tracks(midi.tracks):
            if padNext:
                padNext = False
                event.time += round(mido.second2tick(padding,ppq,tempo))
            if event.type == 'set_tempo':
                tempo = event.tempo
            if not isinstance(event.time, int):
                print(event)
            mainTrack.append(event)

        duration = midi.length
        meta.append((infilename, offset, offset + duration))
        offset += duration + padding
        padNext=True

    newMid.tracks = [mainTrack]
    newMid.save(outfilename)
    if outmetafile is not None:
        with open(outmetafile,'w') as metafile:
            writer = csv.writer(metafile)
            writer.writerow(("File","Start","End"))
            writer.writerows(meta)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    parser.add_argument('--outFile')
    parser.add_argument('--meta', default=None)
    args = parser.parse_args()
    
    concatMidi(args.files, args.outFile, args.meta)
