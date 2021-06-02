# -*- coding: utf-8 -*-
import os
import argparse
import numpy as np
import pandas as pd

def importBeats(inputPath):
    """ Import annotated csv file. Must include a header named 'beats' """
    df      = pd.read_csv(inputPath)
    beats_v = df['beats'].to_numpy()
    return beats_v

def genExportName(inputPath):
    """ Generate export file name from input.
    Beat annotation files must include _beats before extension"""
    baseName    = os.path.basename(inputPath)
    baseName, _ = os.path.splitext(baseName)
    baseName, _ = baseName.split('_beats')
    dirName     = os.path.dirname(inputPath)
    exportName  = os.path.join(dirName, baseName + '_tempo.csv')
    return exportName

def computeTempo(beats_v):
    """ Compute tempo from beat onsets """
    N         = len(beats_v)
    beatCount = np.linspace(1,N-1,N-1, dtype='int') # beat count starting from 1
    beatTime  = (beats_v[0:N-1] + beats_v[1:N])/2   # time from midpoint between two bars
    tempo_v   = 60/(beats_v[1:N]-beats_v[0:N-1])    # tempo vector
    return [beatCount, beatTime, tempo_v]

def makeTempoTable(beats_v):
    """ Create a pandas DataFrame from tempo computation """
    [beatCount, beatTime, tempo_v] = computeTempo(beats_v)
    data  = {'Beats':beatCount, 'Time':beatTime, 'Tempo':tempo_v}
    tempo = pd.DataFrame.from_dict(data)
    return tempo

def getTempo(inputPath, plotTempo, exportTempo, columns):
    """
    Import beat annotations and compute tempo table with beat counts
    Input
        beats_v    : 1D numpy array
        plotTempo  : bool, default False
        exportTempo: bool, default True
        columns    : str, default 'all' ('all', 'time', 'beats')
    Output
        tempo      : pandas DataFrame with selected columns
    """
    beats_v = importBeats(inputPath)
    tempo   = makeTempoTable(beats_v)
    if plotTempo:
        import matplotlib.pyplot as plt
        plt.plot(tempo['Time'], tempo['Tempo'], c='black')
        plt.xlabel('Time [s]')
        plt.ylabel('Tempo [BPM]')
        plt.grid()
        plt.show()
    if columns.lower() == 'time':
        tempo.drop('Beats', axis=1, inplace=True)
    if columns.lower() == 'beats':
        tempo.drop('Time', axis=1, inplace=True)
    if exportTempo:
        exportName = genExportName(inputPath)
        tempo.to_csv(exportName, sep=',', index=False)
        print('Exported to: {}'.format(exportName))
    return tempo

def main(inputPath, plotTempo=False, exportTempo=True, columns='all'):
    """
    Compute Tempo from the beat annotations of a labeled csv file
     -inputPath,--var <arg>   Input path: csv file or folder
     -plotTempo,--var <arg>   bool, default False
     -exportTempo,--var <arg>   bool, default True
     -columns,--var <arg>   str, columns to export (all, time, beats)
    """
    if os.path.isfile(inputPath):
        tempo = getTempo(inputPath, plotTempo=plotTempo, exportTempo=exportTempo, columns=columns)
        return tempo
    if os.path.isdir(inputPath):
        import glob
        fileList = glob.glob(os.path.join(inputPath, '*_beats.csv'))
        for inputFile in fileList:
            tempo = getTempo(inputFile, plotTempo=plotTempo, exportTempo=exportTempo, columns=columns)
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("inputPath", type=str,
                        help="Input path, csv file or folder path with csv files")
    parser.add_argument("-plot", "--plotTempo",   action='store_true', help="Plot tempo curve, default False", default=False)
    parser.add_argument("-noPlot", "--dontPlot",  action='store_false', help="Do not plot tempo curve", dest='plotTempo')
    parser.add_argument("-exp", "--exportTempo",  action='store_true', help="Export tempo as csv, default True", default=True)
    parser.add_argument("-noExp", "--dontExport", action='store_false', help="Do not export tempo as csv", dest='exportTempo')
    parser.add_argument("-cols", "--columns", type=str,
                        help="Columns to export, all:Beats,Time,Tempo - time=Time,Tempo - beats:Beats,Tempo")

    args        = parser.parse_args()
    inputPath   = args.inputPath
    plotTempo   = args.plotTempo
    exportTempo = args.exportTempo
    if args.columns:
        columns = args.columns
    else:
        columns = 'all'

    main(inputPath, plotTempo=plotTempo, exportTempo=exportTempo, columns=columns)
    print('Done!')
    