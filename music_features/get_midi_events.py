"""Module to extract midi events in a more convenient format."""
import argparse
import warnings

import mido


def get_midi_events(perf_filename, verbose=False):
    """Get a list of midi events from the file.

    Only note on and off events and control events are listed
    Meta events are read and optionally logged, but not returned
    """
    midi = mido.MidiFile(perf_filename)

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
                print_message(message)
            if not message.is_meta:
                event_time += mido.tick2second(message.time, ppq, tempo)
                if is_note_off(message):
                    # Pair the note off to the first matching note on without an end time
                    try:
                        match_ = next(event for event in unmatched_note_on if message.note == event['Note'])
                    except StopIteration:
                        warnings.warn(f"Found unbalanced note off {message}")
                    else:
                        match_['EndTime'] = event_time
                        unmatched_note_on.remove(match_)
                elif is_note_on(message):
                    event_list.append(event := {'StartTime': event_time, 'EndTime': None,
                                      'Type': message.type, 'Note': message.note, 'Velocity': message.velocity})
                    unmatched_note_on.append(event)
                elif message.type == 'control_change':
                    event_list.append({'Time': event_time, 'Type': message.type,
                                      'Control': message.control, 'Value': message.value})
        # Warn if not all note ons have been matched
        if unmatched_note_on:
            warnings.warn(f"Found unbalanced note ons: {unmatched_note_on}")
    return event_list


def is_note_on(message):
    """Test if the message is a (true) note on event."""
    return message.type == 'note_on' and message.velocity != 0


def is_note_off(message):
    """Test if the message is a note off event."""
    return message.type == 'note_off' or message.type == 'note_on' and message.velocity == 0


def print_message(message):
    """Print a human-readable version of some meta-events or the raw event otherwise."""
    if message.is_meta:
        if message.type == 'set_tempo':
            tempo = message.tempo
            print(f'\tTempo: {tempo}')
            print(f'\tBPM: {mido.tempo2bpm(tempo)}')
        elif message.type == 'time_signature':
            print(f'\tTime Signature: {message.numerator}/{message.denominator}')
        elif message.type == 'key_signature':
            print(f'\tKey: {message.key}')
        else:
            print(message)
    else:
        print(message)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--perf')
    args = parser.parse_args()

    events = get_midi_events(args.perf)
    print(events)
