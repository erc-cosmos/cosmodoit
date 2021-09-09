# -*- coding: utf-8 -*-

import argparse
import warnings
from get_midi_events import get_midi_events
from util import targets_factory, write_file

def get_onset_velocity(perfFilename):
    """Extract onset velocities from a midi file."""
    velocities = [{'Time':event['StartTime'],'Velocity':event['Velocity']} 
            for event in get_midi_events(perfFilename) 
            if is_note_event(event)]
    #TODO: Switch to pandas dataframes rather than this fallback
    return velocities or [{'Time':None, 'Velocity':None}]


def is_note_event(event):
    """Test whether the passed event is a note."""
    return event['Type'] == 'note_on'


def gen_tasks(piece_id, paths, working_folder):
    if paths.perfmidi is None:
        return
    perf_targets = targets_factory(paths.perfmidi, working_folder)
    perf_velocity = perf_targets("_velocity.csv")
    def runner(perf_filename, perf_velocity):
        velocities = get_onset_velocity(paths.perfmidi)
        if velocities == []:
            warnings.warn("Warning: no note on event detected in " + perf_filename)
        else:
            write_file(perf_velocity, velocities)
        return None
    yield {
        'basename': 'velocities',
        'name': piece_id, 
        'doc': "Extract onset velocities from a midi file.",
        'file_dep': [paths.perfmidi, __file__],
        'targets': [perf_velocity],
        'actions': [(runner, [paths.perfmidi, perf_velocity])]
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--perf', default='music_features/test_midi/2020-03-12_EC_Chopin_Ballade_N2_Take_2.mid')
    args = parser.parse_args()
    
    velocities = get_onset_velocity(args.perf)
    print(velocities)