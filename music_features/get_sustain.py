#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import mido
import os
import sys
from get_midiEvents import *

def get_sustain(perfFilename):
    """ Extracts sustain pedal information from a midi file
    """
    #TODO: add flag for binary output
    midiBasename,_ = os.path.splitext(os.path.basename(perfFilename))

    event_list = get_midiEvents(perfFilename)
    # Filter to keep only pedal events
    sustainValues = [{'Time':event['Time'],'Sustain':event['Value']} for event in event_list 
        if is_sustainEvent(event)]

    return sustainValues

def is_sustainEvent(event):
    """ Determines whether the passed event is a sustain pedal event
    """
    return event['Type'] == 'control_change' and event['Control']==64

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--perf', default='music_features/test_midi/2020-03-12_EC_Chopin_Ballade_N2_Take_2.mid')
    args = parser.parse_args()
    
    sustain = get_sustain(args.perf)
    print(sustain)