"""Module for extracting sustain out of a midi file."""
import argparse

from .get_midi_events import get_midi_events
from .util import targets_factory, write_file


def get_sustain(perf_path):
    """Extract sustain pedal information from a midi file."""
    # TODO: add flag for binary output
    sustain = [{'Time': event['Time'], 'Sustain':event['Value']}
               for event in get_midi_events(perf_path)
               if is_sustain_event(event)]
    # TODO: Switch to pandas dataframes rather than this fallback
    return sustain or [{'Time': None, 'Sustain': None}]


def is_sustain_event(event):
    """Test whether the passed event is a sustain pedal event."""
    # 64 is the Midi code for the sustain pedal
    return event['Type'] == 'control_change' and event['Control'] == 64


task_docs = {
    "sustain": "Extract sustain pedal information from a midi file."
}


def gen_tasks(piece_id, paths, working_folder):
    """Generate sustain-related tasks."""
    if paths.perfmidi is None:
        return
    perf_targets = targets_factory(paths.perfmidi, working_folder)
    perf_sustain = perf_targets("_sustain.csv")

    def runner(perf_path, perf_sustain):
        sustain = get_sustain(perf_path)
        write_file(perf_sustain, sustain)
        return None
    yield {
        'basename': 'sustain',
        'name': piece_id,
        'doc': task_docs["sustain"],
        'file_dep': [paths.perfmidi, __file__],
        'targets': [perf_sustain],
        'actions': [(runner, [paths.perfmidi, perf_sustain])]
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--perf', default='music_features/test_midi/2020-03-12_EC_Chopin_Ballade_N2_Take_2.mid')
    args = parser.parse_args()

    sustain = get_sustain(args.perf)
    print(sustain)
