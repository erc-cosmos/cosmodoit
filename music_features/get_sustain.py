"""Module for extracting sustain out of a midi file."""
import pandas as pd

from .get_midi_events import get_midi_events


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


def read_sustain(filepath: str) -> pd.DataFrame:
    """Read a sustain file from disk.

    Args:
        filepath (str): path to the file

    Returns:
        pd.DataFrame: DataFrame with the time and sustain values
    """
    return pd.read_csv(filepath, usecols=('Time', 'Sustain'))


def write_sustain(filepath: str, data: pd.DataFrame) -> None:
    """Write a sustain Dataframe to disk.

    Args:
        filepath (str): path to output file
        data (pd.DataFrame): data to write
    """
    data.to_csv(filepath, index=False, columns=('Time', 'Sustain'))


task_docs = {
    "sustain": "Extract sustain pedal information from a midi file."
}


def gen_tasks(piece_id: str, targets, **kwargs):
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
