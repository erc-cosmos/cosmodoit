"""Module for extracting sustain out of a midi file."""
import pandas as pd

from music_features.get_midi_events import get_midi_events
from music_features.util import targets_factory


def get_sustain(perf_path, *, binary=False):
    """Extract sustain pedal information from a midi file."""
    sustain = pd.DataFrame([(event['Time'], (event['Value'] >= 64 if binary else event['Value']))
                            for event in get_midi_events(perf_path)
                            if is_sustain_event(event)],
                           columns=('Time', 'Sustain'))
    return sustain


def is_sustain_event(event):
    """Test whether the passed event is a sustain pedal event."""
    # 64 is the Midi code for the sustain pedal
    return event['Type'] == 'control_change' and event['Control'] == 64


task_docs = {
    "sustain": "Extract sustain pedal information from a midi file."
}


def gen_tasks(piece_id, targets):
    """Generate sustain-related tasks."""
    if targets("perfmidi") is None:
        return
    perf_sustain = targets("sustain")

    def caller(perf_path, perf_sustain):
        sustain = get_sustain(perf_path)
        sustain.to_csv(perf_sustain, index=False)
        return None
    yield {
        'basename': 'sustain',
        'name': piece_id,
        'doc': task_docs["sustain"],
        'file_dep': [targets("perfmidi"), __file__],
        'targets': [perf_sustain],
        'actions': [(caller, [targets("perfmidi"), perf_sustain])]
    }
