#!/usr/bin/python3

import csv
import mido

def concatMidi(infilenames, outfilename, outmetafile=None, padding=5):
    newMid = mido.MidiFile(infilenames[0])
    offset = 0
    allTracks = []
    meta = []

    for infilename in infilenames:
        midi = mido.MidiFile(infilename)
        # Default value for tempo; might be set by a value for set_tempo later
        tempo = 500000

        # Use default for pulses per quarter note if its not set
        if midi.ticks_per_beat:
            ppq = midi.ticks_per_beat
        else:
            ppq = 96

        trackMaxTimes = []
        for track in midi.tracks:
            newTrack = mido.MidiTrack()
            allTracks.append(newTrack)
            
            trackTime = 0
            firstEvent = True
            for event in track:
                trackTime += round(mido.tick2second(event.time, ppq, tempo), 5)
                if firstEvent:
                    event.time += round(mido.second2tick(offset,ppq,tempo))
                    firstEvent = False
                if event.type == 'set_tempo':
                    tempo = event.tempo
                newTrack.append(event)
            trackMaxTimes.append(trackTime)

        # midi.tracks.extend(filteredTracks)
        duration = max(trackMaxTimes)
        meta.append((infilename, offset, offset+duration))
        offset += duration + padding
    newMid.tracks = allTracks
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