"""Wrapping module for Midi-miner's spiral array tension functions."""
from importlib import resources
import os

from doit.tools import config_changed
import numpy as np
import pandas as pd

from . import _tension_calculation as tc
from .util import read_json
from .util import set_json_file
from .util import write_json


def read_tension(input_path) -> pd.DataFrame:
    """Read a tension file from disk.

    Args:
        filepath (str): path to the file

    Returns:
        pd.DataFrame: DataFrame with the time and tension values
    """
    return pd.read_csv(input_path, usecols=["time", "momentum", "diameter", "strain", "d_diameter", "d_strain"])


def write_tension(output_path: str, tension: pd.DataFrame):
    """Write a tension dataframe to disk.

    Args:
        output_path (str): path to output file
        tension (pd.DataFrame): tension dataframe to write
    """
    tension.to_csv(output_path, columns=["time", "momentum", "diameter",
                   "strain", "d_diameter", "d_strain"], index=False)


def write_tension_json(tension_file: str, json_file: str) -> None:
    """Create a metadata file for tension from a template.

    Args:
        tension_file (str): path to the main tension file
        json_file (str): path to the json tension file to create
    """
    # source_dir = os.path.dirname(__file__)
    template_file = resources.files(__package__) / 'templates' / 'tension_template.json'
    json_template = read_json(template_file)
    new_object = set_json_file(json_template, os.path.basename(tension_file))
    write_json(new_object, json_file)
    return


def get_tension(midi_path: str, *, track_num: int = 3, **kwargs):
    """Compute Harmonic Tension using midi-miner.

    Args:
        midi_path (str): Path to the midi file
        track_num (int): Maximum number of tracks to use

    Returns:
        pd.Dataframe: dataframe of the harmonic tension
    """
    pm, piano_roll, beat_data = tc.extract_notes(midi_path, track_num=track_num)

    (time, strain, diameter, momentum, _key_name,
     _key_change_info) = tc.cal_tension(pm, piano_roll, beat_data, **kwargs)

    tension = pd.DataFrame.from_dict({'time': time, 'momentum': momentum,
                                     'diameter': diameter, 'strain': strain}).rename_axis('beat')

    tension['d_diameter'] = [np.nan, *np.diff(tension['diameter'])]
    tension['d_strain'] = [np.nan, *np.diff(tension['strain'])]
    return tension


task_docs = {
    "tension": "Compute the tension parameters using midi-miner",
    "tension_bar": "Compute the tension parameters at the bar level"
}

param_sources = (get_tension, tc.cal_tension)


def gen_tasks(piece_id, targets, **kwargs):
    """Generate tension-related tasks."""
    if targets("score") is None:
        return

    ref_midi = targets("ref_midi")
    perf_beats = targets("beats")
    perf_bars = targets("bars")
    perf_tension = targets("tension")
    perf_tension_bar = targets("tension_bar")
    perf_tension_json = targets("tension_json")
    perf_tension_bar_json = targets("tension_bar_json")

    def caller(perf_tension, perf_tension_json, ref_midi, perf_beats, kwargs_inner, measure_level=False):
        kwargs_inner = dict({
            'window_size': -1 if measure_level else 1,
            'key_name': '',
            'track_num': 3,
            'end_ratio': .5,
            'key_changed': False,
            'vertical_step': 0.4
        }, **kwargs_inner)
        tension = get_tension(ref_midi, columns='time', **kwargs_inner)
        df_beats = pd.read_csv(perf_beats).tail(-1)  # Drop the first beat as tension is not computed there
        tension['time'] = df_beats['time']
        tension.to_csv(perf_tension, sep=',', index=False)
        write_tension_json(perf_tension, json_file=perf_tension_json)
        return True

    if targets("manual_beats") is not None or targets("perfmidi") is not None:
        yield {
            'basename': "tension",
            'file_dep': [ref_midi, perf_beats, __file__, tc.__file__],
            'name': piece_id,
            'doc': task_docs["tension"],
            'targets': [perf_tension, perf_tension_json],
            'uptodate': [config_changed(kwargs)],
            'actions': [(caller, [perf_tension, perf_tension_json, ref_midi, perf_beats, kwargs])],
        }
    if targets("manual_bars") is not None or targets("perfmidi") is not None:
        yield {
            'basename': "tension_bar",
            'file_dep': [ref_midi, perf_bars, __file__, tc.__file__],
            'name': piece_id,
            'doc': task_docs["tension_bar"],
            'targets': [perf_tension_bar, perf_tension_bar_json],
            'actions': [(caller, [perf_tension_bar, perf_tension_bar_json, ref_midi, perf_bars, kwargs, True])]
        }
