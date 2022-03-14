"""Wrapping module for Midi-miner's spiral array tension functions."""
import os

import numpy as np
import pandas as pd

from . import tension_calculation as tc
from .util import read_json, set_json_file, write_json


def create_tension_json(tension_file: str) -> None:
    """Create a metadata file for tension from a template.

    Args:
        tension_file (Union[str, os.PathLike]): path to the main tension file
    """
    source_dir = os.path.dirname(__file__)
    jsonObject = read_json(os.path.join(source_dir, 'tension_template.json'))
    exportName = tension_file.replace(".csv", ".json")
    newObject = set_json_file(jsonObject, os.path.basename(tension_file))
    write_json(newObject, exportName)
    return


def createTensionDataFrame(time, momentum, diameter, strain):
    """Create dataframe from results of midi-Miner."""
    beat = np.linspace(1, len(time), len(time), dtype=int)
    tensionDict = {'beat': beat, 'time': time, 'momentum': momentum, 'diameter': diameter, 'strain': strain}
    df = pd.DataFrame.from_dict(tensionDict)
    return df


def computeTension(inputFile, args):
    """Use midi-miner to compute Harmonic Tension data."""
    _, piano_roll, beat_data = tc.extract_notes(inputFile, args['track_num'])
    if args['key_name'] == '':
        # key_name = get_key_name(inputFile)
        # from tension_calculation import all_key_names
        key_name = tc.all_key_names
        tension_result = tc.cal_tension(inputFile, piano_roll, beat_data, args,
                                        args['window_size'], key_name, generate_pickle=False)
    else:
        tension_result = tc.cal_tension(inputFile, piano_roll, beat_data, args, args['window_size'], [
                                        args['key_name']], generate_pickle=False)

    # tension_time, total_tension, diameters, centroid_diff, _, _, _, _ = tension_result
    (tension_time, total_tension, diameters, centroid_diff, key_name,
     _key_change_time, _key_change_bar, _key_change_name, _new_output_folder) = tension_result

    return tension_time, total_tension, diameters, centroid_diff


def getTension(inputFile, args, columns):
    """Compute Harmonic Tension using midi-miner.

    Creates a pandas DataFrame and deletes additional files.
    Parameters
    ----------
    inputFile : str
        The file location of the .mid file
    args : dict
        The arguments for midi-miner (windowSize, verticalStep, keyChanged)
    plotTension : bool, optional
        A flag used to plot the resulting curves
    exportTension : bool, optional
        A flag used to export the resulting dataframe as a csv
    columns : str, optional
        Which columns to export with tension
        ['all', 'time', 'beats'] default is 'all'
    Returns
    -------
    dataframe
        Pandas dataframe of the harmonic tension
    """
    time, strain, diameter, momentum = computeTension(inputFile, args)
    df = createTensionDataFrame(time, momentum, diameter, strain)

    if columns.lower() == 'time':
        df.drop(['beat'], axis=1, inplace=True)
    if columns.lower() == 'beat' or columns.lower() == 'beats':
        df.drop(['time'], axis=1, inplace=True)
    return df


task_docs = {
    "tension": "Compute the tension parameters using midi-miner",
    "tension_bar": "Compute the tension parameters at the bar level"
}


def gen_tasks(piece_id, targets):
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

    def caller(perf_tension, ref_midi, perf_beats, measure_level=False, **kwargs):
        args = {
            'window_size': -1 if measure_level else 1,
            'key_name': '',
            'track_num': 3,
            'end_ratio': .5,
            'key_changed': False,
            'vertical_step': 0.4
        }
        tension = getTension(ref_midi, args=args, columns='time')
        df_beats = pd.read_csv(perf_beats).tail(-1)  # Drop the first beat as tension is not computed there
        tension['time'] = df_beats['time']
        tension['d_diameter'] = [np.nan, *np.diff(tension['diameter'])]
        tension['d_strain'] = [np.nan, *np.diff(tension['strain'])]
        tension.to_csv(perf_tension, sep=',', index=False)
        create_tension_json(perf_tension)
        return True

    if targets("manual_beats") is not None or targets("perfmidi") is not None:
        yield {
            'basename': "tension",
            'file_dep': [ref_midi, perf_beats, __file__],
            'name': piece_id,
            'doc': task_docs["tension"],
            'targets': [perf_tension, perf_tension_json],
            'actions': [(caller, [perf_tension, ref_midi, perf_beats])]
        }
    if targets("manual_bars") is not None or targets("perfmidi") is not None:
        yield {
            'basename': "tension_bar",
            'file_dep': [ref_midi, perf_bars, __file__],
            'name': piece_id,
            'doc': task_docs["tension_bar"],
            'targets': [perf_tension_bar, perf_tension_bar_json],
            'actions': [(caller, [perf_tension_bar, ref_midi, perf_bars, True])]
        }
