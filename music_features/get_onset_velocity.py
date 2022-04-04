"""Module to extract velocity information from a midi file."""

import argparse
import warnings

import pandas as pd

from music_features.get_midi_events import get_midi_events

def get_onset_velocity(perfFilename):
    """Extract onset velocities from a midi file."""
    velocities = pd.DataFrame([(event['StartTime'], event['Velocity'])
                               for event in get_midi_events(perfFilename)
                               if is_note_event(event)],
                              columns=('Time', 'Velocity'))
    return velocities


def is_note_event(event):
    """Test whether the passed event is a note."""
    return event['Type'] == 'note_on'


task_docs = {
    "velocities": "Extract onset velocities from a midi file"
}


def gen_tasks(piece_id, targets):
    """Generate velocity-related tasks."""
    if targets("perfmidi") is None:
        return
    perf_velocity = targets("velocity")

    def runner(perf_filename, perf_velocity):
        velocities = get_onset_velocity(targets("perfmidi"))
        if velocities.size == 0:
            warnings.warn("Warning: no note on event detected in " + perf_filename)
        else:
            velocities.to_csv(perf_velocity, index=False)
        return None
    yield {
        'basename': 'velocities',
        'name': piece_id,
        'doc': task_docs["velocities"],
        'file_dep': [targets("perfmidi"), __file__],
        'targets': [perf_velocity],
        'actions': [(runner, [targets("perfmidi"), perf_velocity])]
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--perf', default='music_features/test_midi/2020-03-12_EC_Chopin_Ballade_N2_Take_2.mid')
    args = parser.parse_args()

    velocities = get_onset_velocity(args.perf)
    print(velocities)
