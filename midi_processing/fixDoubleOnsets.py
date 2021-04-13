#!/usr/bin/python3

import csv
import mido

def isNoteOff(message):
    return message.type == 'note_off' or (message.type =='note_on' and message.velocity == 0)

def isDoubleOnset(threshold, tempo, ppq, event, nextEvent):
    return (isNoteOff(event) and nextEvent.type == "note_on" and event.note == nextEvent.note 
        and mido.tick2second(nextEvent.time, ppq, tempo) < threshold)

def fixDoubleOnsets(infilename, outfilename, threshold=.005):
    midi = mido.MidiFile(infilename)
    
    # Default value for tempo; might be set by a value for set_tempo later
    tempo = 500000
    # Use default for pulses per quarter note if its not set
    if midi.ticks_per_beat:
        ppq = midi.ticks_per_beat
    else:
        ppq = 96

    filteredTracks = []
    for track in midi.tracks:
        newTrack = mido.MidiTrack()
        filteredTracks.append(newTrack)
        skipNext = False
        itNext = iter(track)
        next(itNext)

        carryTime = 0
        for event,nextEvent in zip(track,itNext):
            if skipNext: # Spurious onset
                skipNext = False
                carryTime += event.time
                continue
            elif isDoubleOnset(threshold, tempo, ppq, event, nextEvent): # Spurious release
                skipNext = True
                carryTime += event.time
                continue
            else:
                if event.type == 'set_tempo':
                    tempo = event.tempo
                event.time += carryTime
                carryTime = 0
                newTrack.append(event)
        newTrack.append(track[-1])
    midi.tracks = filteredTracks
    midi.save(outfilename)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--inFile',
                        help="File containing doubled onsets")
    parser.add_argument('--outFile',
                        help="Path to save the fixed file")
    parser.add_argument('--threshold', default=0.005, type=float,
                        help="Sensitivity of double onset detection")
    args = parser.parse_args()
    
    fixDoubleOnsets(args.inFile, args.outFile, args.threshold)
    
