#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import mido
import warnings

def get_midi_events(perfFilename, verbose=False):
    """Get a list of midi events from the file.

    Only note on and off events and control events are listed
    Meta events are read and optionally logged, but not returned
    """
    midi = mido.MidiFile(perfFilename)
    
    # Default value for tempo; might be set by a value for set_tempo later
    tempo = 500000

    # Use default for pulses per quarter note if its not set
    ppq = midi.ticks_per_beat or 96
    
    # For storing the elapsed time for MIDI events in seconds
    event_list = []
    
    for track in midi.tracks:
        event_time = 0
        unmatched_note_on = []
        for message in track:
            if verbose:
                print(message)
            if not message.is_meta:
                event_time += round(mido.tick2second(message.time, ppq, tempo), 5)
                if is_note_off(message):
                    # Pair the note off to the first matching note on without an end time
                    if any(message.note == (match_:=event)['Note'] for event in unmatched_note_on):
                        match_['EndTime'] = event_time
                        unmatched_note_on.remove(match_)
                    else:
                        warnings.warn(f"Found unbalanced note off {message}")
                elif is_note_on(message):
                    event_list.append(event:={'StartTime': event_time, 'EndTime': None, 'Type': message.type, 'Note': message.note, 'Velocity': message.velocity})
                    unmatched_note_on.append(event)
                elif message.type == 'control_change':
                    event_list.append({'Time': event_time, 'Type': message.type, 'Control': message.control, 'Value': message.value})
            elif verbose:
                print_meta(message)
        # Warn if not all note ons have been matched
        if unmatched_note_on:
            warnings.warn(f"Found unbalanced note ons: {unmatched_note_on}")
    return event_list


def is_note_on(message):
    """Test if the message is a (true) note on event."""
    return message.type == 'note_on' and message.velocity != 0


def is_note_off(message):
    """Test if the message is a note off event."""
    return message.type == 'note_off' or message.type =='note_on' and message.velocity == 0


def print_meta(meta_message):
    """Print a human-readable version of some meta-events."""
    if meta_message.type == 'set_tempo':
        tempo = meta_message.tempo
        print(f'\tTempo: {tempo}')
        print(f'\tBPM: {mido.tempo2bpm(tempo)}')
    elif meta_message.type == 'time_signature':
        print(f'\tTime Signature: {meta_message.numerator}/{meta_message.denominator}')
    elif meta_message.type == 'key_signature':
        print(f'\tKey: {meta_message.key}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--perf')
    args = parser.parse_args()
    
    events = get_midi_events(args.perf)
    print(events)