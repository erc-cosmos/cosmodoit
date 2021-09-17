import os
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from . import tension_calculation as tc
from .util import targets_factory


def genBaseName(inputFile):
    """ Generate full path base name (without extension) from midi file """

    baseName     = os.path.basename(inputFile)
    baseName, _  = os.path.splitext(baseName)
    dirName      = os.path.dirname(inputFile)
    fullBaseName = os.path.join(dirName, baseName)
    return fullBaseName

def createTensionDataFrame(time, momentum, diameter, strain):
    """ Create dataframe from results of midi-Miner """
    
    beat        = np.linspace(1,len(time),len(time), dtype=int)
    tensionDict = {'beat':beat, 'time' : time, 'momentum' : momentum, 'diameter' : diameter, 'strain':strain}
    df          = pd.DataFrame.from_dict(tensionDict)
    return df

def computeTension(inputFile, args):
    """Use midi-miner to compute Harmonic Tension data"""
    _, piano_roll,beat_data = tc.extract_notes(inputFile,args['track_num'])
    if args['key_name'] == '':
        # key_name = get_key_name(inputFile)
        from tension_calculation import all_key_names
        key_name = all_key_names
        tension_result = tc.cal_tension(inputFile, piano_roll, beat_data, args, args['window_size'], key_name, generate_pickle=False)
    else:
        tension_result = tc.cal_tension(inputFile, piano_roll, beat_data, args, args['window_size'],[args['key_name']], generate_pickle=False)

    # tension_time, total_tension, diameters, centroid_diff, _, _, _, _ = tension_result
    tension_time, total_tension, diameters,centroid_diff, key_name, key_change_time, key_change_bar,key_change_name, new_output_folder = tension_result

    return tension_time, total_tension, diameters, centroid_diff

def getTension(inputFile, args, plotTension, exportTension, columns):
    """Compute Harmonic Tension using midi-miner
    Creates a pandas DataFrame and deletes additional files

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

    if plotTension:
        plotTensionCurves(df)
    if columns.lower() == 'time':
        df.drop(['beat'], axis=1, inplace=True)
    if columns.lower() == 'beat' or columns.lower() == 'beats':
        df.drop(['time'], axis=1, inplace=True)
    if exportTension:
        exportTensionCSV(inputFile, df, columns)
    return df

def plotTensionCurves(df, figSize=(16,10)):
    """ Plot tension parameters in 3 rows"""

    _, ax = plt.subplots(nrows=3, ncols=1, figsize=figSize, sharex=True, sharey=False)
    parameters = ['diameter', 'momentum', 'strain']
    colors     = ['orange', 'gold', 'red']
    for i, parameter in enumerate(parameters):
        ax[i].set_ylabel(parameter.upper(), fontweight='bold')
        ax[i].plot(df['time'], df[parameter], color = colors[i], marker='.', markersize=9)
    plt.show()
    return

def exportTensionCSV(inputFile, df, columns):
    """ Export dataframe as a csv file adding a suffix to the inputFile name """

    if columns =='all':
        fileSuffix = '_tension_all.csv'
    else:
        fileSuffix = '_tension.csv'
    exportName = genBaseName(inputFile) + fileSuffix
    df.to_csv(exportName, sep=',', index=False)
    print('Exported to: {}'.format(exportName))
    return

def main(inputPath, args, *, plotTension=False, exportTension=True, columns='all'):
    """
    Compute Harmonic Tension from a MIDI file

     -inputPath,--var <arg>   Input path: .mid file or folder
     -w, windowSize. Integer number of beats or -1 for backbeat
     -v, verticalStep, Float vertical step for the spiral array. Between sqrt(2/15) and sqrt(3/15)
     -k, keyChanged, Look for a key change
     -plotTension,--var <arg>   bool, default False
     -exportTension,--var <arg>   bool, default True
     -columns,--var <arg>   str, columns to export (all, time, beats)
    """

    if os.path.isfile(inputPath):
        tension = getTension(inputPath, args=args, plotTension=plotTension, exportTension=exportTension, columns=columns)
        return tension
    if os.path.isdir(inputPath):
        import glob
        fileList = glob.glob(os.path.join(inputPath, '*.mid'))
        for inputFile in fileList:
            tension = getTension(inputFile, args=args, plotTension=plotTension, exportTension=exportTension, columns=columns)
    return


def gen_tasks(piece_id, paths, working_folder="tmp"):
    if paths.score is None:
        return
    
    backup_targets = targets_factory(piece_id, working_folder=working_folder)
    ref_targets = targets_factory(paths.score, working_folder=working_folder) or backup_targets
    perf_targets = targets_factory(paths.perfmidi, working_folder=working_folder) or backup_targets
    
    ref_midi = ref_targets("_ref.mid")
    perf_beats = perf_targets("_beats.csv")
    perf_bars = perf_targets("_bars.csv")
    perf_tension = perf_targets("_tension.csv")
    perf_tension_bar = perf_targets("_tension_bar.csv")

    def caller(perf_tension, ref_midi, perf_beats, measure_level=False, **kwargs):
        args = {
            'window_size':-1 if measure_level else 1,
            'key_name':'',
            'track_num': 3,
            'end_ratio':.5,
            'key_changed':False,
            'vertical_step':0.4
        }
        tension = getTension(ref_midi, args=args, plotTension=False, exportTension=False, columns='time')
        df_beats = pd.read_csv(perf_beats).tail(-1) # Drop the first beat as tension is not computed there
        tension['time'] = df_beats['time']
        tension['d_diameter'] = [np.nan, *np.diff(tension['diameter'])]
        tension['d_strain'] = [np.nan, *np.diff(tension['strain'])]
        tension.to_csv(perf_tension, sep=',', index=False)
        return True

    if paths.manual_beats is not None or paths.perfmidi is not None:
        yield {
            'basename': "tension",
            'file_dep': [ref_midi, perf_beats, __file__],
            'name': piece_id,
            'doc': "Compute the tension parameters —cloud momentum, tensile strain and cloud diameter— using midi-miner.",
            'targets': [perf_tension],
            'actions': [(caller, [perf_tension, ref_midi, perf_beats])]
        }
    if paths.manual_bars is not None or paths.perfmidi is not None:
        yield {
            'basename': "tension_bar",
            'file_dep': [ref_midi, perf_bars, __file__],
            'name': piece_id,
            'doc': "Compute the tension parameters —cloud momentum, tensile strain and cloud diameter— using midi-miner (at the bar level).",
            'targets': [perf_tension_bar],
            'actions': [(caller, [perf_tension_bar, ref_midi, perf_bars, True])]
        }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('file_name', type=str,
                        help="input MIDI file name or folder path with .mid files")
    parser.add_argument('-i', '--input_folder', default='.', type=str,
                        help="MIDI file input folder")
    parser.add_argument('-o', '--output_folder',default='.',type=str,
                        help="MIDI file output folder")
    parser.add_argument('-w', '--window_size', default=1, type=int,
                        help="Tension calculation window size, 1 for a beat, 2 for 2 beat etc., -1 for a downbeat, default 1 beat")
    parser.add_argument('-n', '--key_name', default='', type=str,
                        help="key name of the song, e.g. B- major, C# minor")
    parser.add_argument('-t', '--track_num', default=0, type=int,
                        help="number of tracks used to calculate tension, e.g. 3 means use first 3 tracks, "
                             "default 0 means use all")
    parser.add_argument('-r', '--end_ratio', default=0.5, type=float,
                        help="the place to find the first key "
                             "of the song, 0.5 means the first key "
                             "is calculate by the first half the song")
    parser.add_argument('-k', '--key_changed', default=False, type=bool,
                        help="try to find key change, default false")
    parser.add_argument('-v', '--vertical_step', default=0.4, type=float,
                        help="the vertical step parameter in the spiral array,"
                             "which should be set between sqrt(2/15) and sqrt(0.2)")
    parser.add_argument("-plot", "--plotTension", action='store_true', help="Plot tension curve, default False", default=False)
    parser.add_argument("-noPlot", "--dontPlot", action='store_false', help="Do not plot tension curve", dest='plotTension')
    parser.add_argument("-exp", "--exportTension", action='store_true', help="Export Tension as csv, default True", default=True)
    parser.add_argument("-noExp", "--dontExport", action='store_false', help="Do not export Tension as csv", dest='exportTension')
    parser.add_argument("-cols", "--columns", type=str,
                        help="Columns to export, all:Beats,Time,Tension - time=Time,Tension - beats:Beats,Tension")
    
    args = parser.parse_args()
    inputPath = args.file_name
    plotTension = args.plotTension
    exportTension = args.exportTension
    if args.columns:
        columns = args.columns
    else:
        columns = 'all'
    main(inputPath, vars(args), plotTension=plotTension, exportTension=exportTension, columns=columns)
