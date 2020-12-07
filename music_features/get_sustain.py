#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import mido
import os
import sys

def get_sustain(perfFilename):
    midi = mido.MidiFile(perfFilename)
    midiBasename = os.path.splitext(os.path.basename(perfFilename))[0]

    event_list = parseMidiEvents(midi, midiBasename)
    # Filter to keep only pedal events
    sustainValues = [{'Time':event['Time'],'Sustain':event['Value']} for event in event_list 
        if event['Type']=='control_change' and event['Control']==64]

    return sustainValues

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    #parser.add_argument('--ref', default='test_midi/Chopin_Ballade_No._2_Piano_solo.mid')
    parser.add_argument('--perf', default='test_midi/2020-03-12_EC_Chopin_Ballade_N2_Take_2.mid')
    args = parser.parse_args()
    
    os.chdir(os.path.dirname(sys.argv[0]))
    #refFilename = args.ref
    perfFilename = args.perf
    
    sustain = get_sustain(perfFilename)
    #processFiles(refFilename,perfFilename)
    print(sustain)