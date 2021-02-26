#!/usr/bin/python3

# from get_midiEvents import *
import csv
import mido


# def findDoubleOnsets():
#     filename = "music_features/test_midi/Variations/Var I.mid"

#     midiNotes = [note for note in get_midiEvents(filename) if note["Type"]=='note_on']

#     doubles = []
#     threshold = 0.005 #10ms
#     for note1 in midiNotes:
#         for note2 in midiNotes:
#             if note1['Note']==note2['Note'] and note2["StartTime"] > note1["StartTime"] and (note1["EndTime"] + threshold) > note2["StartTime"]:
#                 doubles.append((note1,note2))

#     with open("test.csv", mode='w') as csvFile:
#             writer = csv.writer(csvFile)
#             for note1,note2 in doubles:
#                 writer.writerow([note2['StartTime']])

def isNoteOff(message):
    return message.type == 'note_off' or (message.type =='note_on' and message.velocity == 0)

def fixDoubleOnsets(infilename, outfilename, threshold=.005, verbose=False):
    midi = mido.MidiFile(infilename)
    newMid = mido.MidiFile()
    
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
            if skipNext:
                skipNext = False
                carryTime += event.time
                continue
            elif isNoteOff(event) and nextEvent.type == "note_on" and event.note == nextEvent.note and mido.tick2second(nextEvent.time, ppq, tempo) < threshold:
                skipNext = True
                carryTime = event.time
                continue
            else:
                if event.type == 'set_tempo':
                    tempo = event.tempo
                    if verbose:
                        print('    Tempo: ' + str(tempo))
                        print('    BPM: ' + str(mido.tempo2bpm(tempo)))    
                event.time += carryTime
                carryTime = 0
                newTrack.append(event)
        newTrack.append(track[-1])
    midi.tracks = filteredTracks
    midi.save(outfilename)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--inFile')
    parser.add_argument('--outFile')
    args = parser.parse_args()
    
    fixDoubleOnsets(args.inFile, args.outFile)
    
