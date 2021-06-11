# Compute tempo using manual beat annotations
import os
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def importBeats(inputPath):
    """ Import annotated csv file. Must include a header named 'beats' """

    df       = pd.read_csv(inputPath)
    beatTime = df['beats'].to_numpy()
    return beatTime

def genExportName(inputPath, columns):
    """ Generate export file name from input.
    Beat annotation files must include _beats before extension """

    baseName    = os.path.basename(inputPath)
    baseName, _ = os.path.splitext(baseName)
    baseName, _ = baseName.split('_beats')
    dirName     = os.path.dirname(inputPath)
    if columns.lower() == 'all':
        fileSuffix  = '_tempo_all'
    else:
        fileSuffix  = '_tempo'
    exportName  = os.path.join(dirName, baseName + fileSuffix + '.csv')
    return exportName

def computeTempo(beatTime):
    """ Compute tempo from beat onsets """

    N            = len(beatTime)
    beatCount    = np.linspace(0, N-1, N, dtype='int')  # beat count starting from 0
    beatMidpoint =    (beatTime[1:N] + beatTime[0:N-1])/2 # time from midpoint between two bars
    tempo_v      = 60/(beatTime[1:N] - beatTime[0:N-1])   # tempo vector
    beatMidpoint = np.append(np.nan, beatMidpoint)      # account for first sample
    tempo_v      = np.append(np.nan, tempo_v)           # account for first sample
    return [beatCount, beatMidpoint, tempo_v]

def makeTempoTable(beatTime):
    """ Create a pandas DataFrame from tempo computation """

    [beatCount, beatMidpoint, tempo_v] = computeTempo(beatTime)
    data  = {'Count':beatCount, 'Time':beatTime, 'beatMidpoint':beatMidpoint, 'Tempo':tempo_v}
    tempo = pd.DataFrame.from_dict(data)
    return tempo

def plotTempoCurve(tempo):
    """ Plot tempo curve over time """

    plt.plot(tempo['Time'], tempo['Tempo'], c='black')
    plt.xlabel('Time [s]')
    plt.ylabel('Tempo [BPM]')
    plt.grid()
    plt.show()

def getTempo(inputPath, plotTempo, exportTempo, columns):
    """
    Import beat annotations and compute tempo table with beat counts

    Input
        beatTime   : 1D numpy array
        plotTempo  : bool, default False
        exportTempo: bool, default True
        columns    : str, default 'all' ('all', 'time', 'beats', 'midpoint')
    Output
        tempo      : pandas DataFrame with selected columns
    """

    beatTime = importBeats(inputPath)
    tempo    = makeTempoTable(beatTime)
    if plotTempo:
        plotTempoCurve(tempo)
    if columns.lower() == 'time':
        tempo.drop(['Count', 'beatMidpoint'], axis=1, inplace=True)
    if columns.lower() == 'beats':
        tempo.drop(['Time', 'beatMidpoint'], axis=1, inplace=True)
    if columns.lower() == 'midpoint':
        tempo.drop(['Count', 'Time'], axis=1, inplace=True)
        tempo.drop(tempo.index[0], inplace=True)
    if exportTempo:
        exportName = genExportName(inputPath, columns)
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
    