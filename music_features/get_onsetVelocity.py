# -*- coding: utf-8 -*-

import argparse
from get_midiEvents import get_midi_events

def get_onset_velocity(perfFilename):
    """Extract onset velocities from a midi file."""
    return [{'Time':event['StartTime'],'Velocity':event['Velocity']} 
            for event in get_midi_events(perfFilename) 
            if is_note_event(event)]


def is_note_event(event):
    """Test whether the passed event is a note."""
    return event['Type'] == 'note_on'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--perf', default='music_features/test_midi/2020-03-12_EC_Chopin_Ballade_N2_Take_2.mid')
    args = parser.parse_args()
    
    velocities = get_onset_velocity(args.perf)
    print(velocities)