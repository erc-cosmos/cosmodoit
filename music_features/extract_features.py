import csv
import numpy as np
import scipy as sp
import scipy.interpolate
import matplotlib.pyplot as plt
import itertools as itt
import os
import subprocess
import argparse
import mido
import sys

#TODO: Split into separate files

def readAlignmentFile(filename):
    #### Read file
    with open(filename) as csvFile:
        csvReader = csv.reader(csvFile, delimiter='\t')
        # Extract relevant columns
        return [{'tatum':int(row[8]), 'time':float(row[1])}
                for row in csvReader
                if len(row)>3 and row[8]!='-1' # Not a metaline and not a mismatch
                ]

def writeFile(filename,data):
    with open(filename, mode='w') as csvFile:
        fields = data[0].keys()
        writer = csv.DictWriter(csvFile, fieldnames=fields)
        writer.writeheader()
        writer.writerows(data)


def beatExtraction(tatums, quarterLength, anacrusisOffset, outfileName=None, plotting = False):
    #### Find beats' onsets
    beats = []
    maxTatum = tatums[-1]['tatum']
    tatumIter = iter(tatums)
    nextTatum = next(tatumIter)

    ticks,indices = np.unique(np.array([tatum['tatum'] for tatum in tatums]),return_index=True) #TODO: determine better which note to use when notes share a tatum
    times = np.array([tatum['time'] for tatum in tatums])[indices]
    interpolTarget = np.arange(anacrusisOffset,maxTatum,quarterLength)

    spline = sp.interpolate.UnivariateSpline(ticks, times,s=1) # s controls smoothing of the Spline
    interpolation = spline(interpolTarget)
    beats = [{'count': count, 
            'time': time,
            'interpolated': tick not in ticks
            }
            for count,(tick,time) in enumerate(zip(interpolTarget,interpolation))]

    if plotting:
        #plt.plot(np.array([beat['count'] for beat in beats])[1:],60/np.diff(interpolation),label="IOI")
        plt.plot([beat['count'] for beat in beats],interpolation)
        plt.scatter(ticks/quarterLength,times)
        plt.show(block=True)
        plt.plot(60/np.diff([beat['time'] for beat in beats]))
        plt.show(block=True)

    ratios = []
    for (tick,time,tick_next,time_next) in zip(ticks,times, ticks[1:], times[1:]):
        #TODO: Separate by line
        if tick == tick_next: # Ignore simultaneous notes
            continue
        expectedDuration = spline(tick_next)-spline(tick)
        actualDuration = time_next-time
        ratios.append(actualDuration/expectedDuration)

    if plotting:
        plt.plot(ticks[:-1]/quarterLength,ratios)
        plt.plot(ticks[:-1]/quarterLength,np.diff(ticks)/quarterLength)
        plt.hlines(1,xmin=ticks[0],xmax=ticks[-1]/quarterLength)
        plt.show()

    ### Save output if requested    
    if outfileName is not None:
        writeFile(outfileName,beats)

    return beats

def runAlignment(refFilename, perfFilename, 
        midi2midiExecLocation="./MIDIToMIDIAlign.sh",
        #score2midiExecLocation="music_features/ScoreToMIDIAlign.sh",
        cleanup=True, recompute=False):
    # Crop .mid extension as the script doesn't want them
    refFilename,refType = os.path.splitext(refFilename)
    perfFilename = os.path.splitext(perfFilename)[0] 

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
        interRefExtensions = ['_fmt3x.txt','_hmm.txt','_spr.txt']
        interPerfExtensions = ['_spr.txt', '_match.txt']
        refBase = os.path.basename(refFilename)
        perfBase = os.path.basename(perfFilename)
        [os.remove(refBase+ext) for ext in interRefExtensions]
        [os.remove(perfBase+ext) for ext in interPerfExtensions]
    return alignment


def getPedal(perfFilename, pedalFilename=None):
    midi = mido.MidiFile(perfFilename)
    midiBasename = os.path.splitext(os.path.basename(perfFilename))[0]

    event_list = parseMidiEvents(midi, midiBasename)
    # Filter to keep only pedal events
    pedalValues = [{'Time':event['Time'],'Sustain':event['Value']} for event in event_list if event['Type']=='control_change' and event['Control']==64]

    if pedalFilename is not None:
        writeFile(pedalFilename, pedalValues)
    return event_list

def parseMidiEvents(midi, midiBasename, verbose=False):
    # Default value for tempo; might be set by a value for set_tempo later
    tempo = 500000

    # Use default for pulses per quarter note if its not set
    if midi.ticks_per_beat:
        ppq = midi.ticks_per_beat
    else:
        ppq = 96

    # For storing the elapsed time for MIDI events in seconds
    event_time = 0
    event_list = []
    # Use a default for track name in case it is not set later
    track_name = midiBasename

    for track in midi.tracks:
        for message in track:
            #print message
            if message.is_meta:
                if message.type == 'track_name':
                    track_name = message.name
                    #print('    Track Name: ' + message.name)
                elif message.type == 'set_tempo':
                    tempo = message.tempo
                    #print('    Tempo: ' + str(tempo))
                    #print('    BPM: ' + str(mido.tempo2bpm(tempo)))
                # elif message.type == 'time_signature':
                #     print('    Time Signature: ' + str(message.numerator) + ' ' + str(message.denominator))
                # elif message.type == 'key_signature':
                #     print('    Key: ' + message.key)
            else:
                event_time += round(mido.tick2second(message.time, ppq, tempo), 5)
                #event_time += mido.tick2second(message.time, ppq, tempo)
                # note_off = 0, note_on = 1
                if message.type == 'note_off':
                    for event in event_list:
                        # Must look for note_on events since that is the type used for all notes in this format
                        if event['Type'] == 'note_on':
                            # Find the same note with a zero (unset) end time in order to set the end time
                            if message.note == event['Note'] and event['EndTime'] == 0:
                                event['EndTime'] = event_time
                                break
                elif message.type == 'note_on':
                    # velocity = 0 is the same as note_off
                    #c = c+1
                    if message.velocity == 0:
                        for event in event_list:
                            if event['Type'] == 'note_on':
                                # Find the same note with a zero (unset) end time in order to set the end time
                                if message.note == event['Note'] and event['EndTime'] == 0:
                                    event['EndTime'] = event_time
                                    break
                    else:
                        event_list.append({'StartTime': event_time, 'EndTime': 0, 'Type': message.type, 'Note': message.note, 'Velocity': message.velocity})
                elif message.type == 'control_change':
                    event_list.append({'Time': event_time, 'Type': message.type, 'Control': message.control, 'Value': message.value})
                    # Control change 64 is the sustain switch (on or off)
                    # if message.control == 64:
                    #     pedalValues.append({'Time':event_time, ''})
                    #     # Sustain off is 0-63
                    #     if message.value <= 63:
                    #         for event in event_list:
                    #             if event['Type'] == 'control_change':
                    #                 if message.control == event['Control'] and event['EndTime'] == 0:
                    #                     event['EndTime'] = event_time
                    #                     break
                    #     # Sustain on is 64-127
                    #     elif message.value >= 64:
                    #         event_list.append({'StartTime': event_time, 'EndTime': 0, 'Type': message.type, 'Control': message.control, 'Value': message.value})
    return event_list


def processFiles(refFilename,perfFilename):
    """ One stopper to process from start to finish
    """
    alignment = runAlignment(refFilename,perfFilename,cleanup=True)
    basePerf = os.path.basename(perfFilename)

    ### Ask User for the base beat and anacrusis offset
    #TODO: Determine automatically
    print(alignment[:10]) # Show first 10 lines to give context
    quarterLength = int(input("Please enter the beat length (in ticks):"))
    anacrusisOffset = int(input("Please enter the beat offset (in ticks):"))
    
    beats = beatExtraction(alignment,quarterLength,anacrusisOffset,basePerf+"_beats.csv",False)
    sustain = getPedal(perfFilename,basePerf+"_sustain.csv")
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
    