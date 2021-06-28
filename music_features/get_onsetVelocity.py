#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import mido
import os
import sys
from get_midiEvents import *

def get_onset_velocity(perfFilename):
    """ Extracts onset velocities from a midi file
    """
    event_list = get_midiEvents(perfFilename)
    # Filter to keep only note_on and extract velocity information
    velocityValues = [{'Time':event['StartTime'],'Velocity':event['Velocity']} for event in event_list 
        if is_noteEvent(event)]

    return velocityValues

def is_noteEvent(event):
    """ Determines whether the passed event is a sustain pedal event
    """
    return event['Type'] == 'note_on'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--perf', default='music_features/test_midi/2020-03-12_EC_Chopin_Ballade_N2_Take_2.mid')
    args = parser.parse_args()
    
    velocities = get_onset_velocity(args.perf)
    print(velocities)