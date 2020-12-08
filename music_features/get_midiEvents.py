#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import mido
import os
import sys

def get_midiEvents(perfFilename, verbose=False):
    """ Get a list of midi events from the file
    Only note on and off events and control events are listed
    Reads meta events, but does not return them
    """
    midi = mido.MidiFile(perfFilename)
    
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
    
    for track in midi.tracks:
        for message in track:
            if verbose:
                print(message)
            if message.is_meta:
                if message.type == 'set_tempo':
                    tempo = message.tempo
                    if verbose:
                        print('    Tempo: ' + str(tempo))
                        print('    BPM: ' + str(mido.tempo2bpm(tempo)))
                elif message.type == 'time_signature':
                    if verbose:
                        print('    Time Signature: ' + str(message.numerator) + ' ' + str(message.denominator))
                elif message.type == 'key_signature':
                    if verbose:
                        print('    Key: ' + message.key)
            else:
                event_time += round(mido.tick2second(message.time, ppq, tempo), 5)
                if message.type == 'note_off' or message.type =='note_on' and message.velocity == 0:
                    # note_on with velocity = 0 is the same as note_off
                    for event in event_list:
                        # Must look for note_on events since that is the type used for all notes in this format
                        if event['Type'] == 'note_on':
                            # Find the same note with a None (unset) end time in order to set the end time
                            if message.note == event['Note'] and event['EndTime'] == None:
                                event['EndTime'] = event_time
                                break
                elif message.type == 'note_on' and message.velocity != 0:
                    event_list.append({'StartTime': event_time, 'EndTime': None, 'Type': message.type, 'Note': message.note, 'Velocity': message.velocity})
                elif message.type == 'control_change':
                    event_list.append({'Time': event_time, 'Type': message.type, 'Control': message.control, 'Value': message.value})
    return event_list

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--perf', default='music_features/test_midi/2020-03-12_EC_Chopin_Ballade_N2_Take_2.mid')
    args = parser.parse_args()
    
    events = get_midiEvents(args.perf)
    print(events)