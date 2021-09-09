# Compute harmonic tension from a MIDI file
# uses the midi-miner library https://github.com/ruiguo-bio/midi-miner
import os
import argparse
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from subprocess import Popen, PIPE, call

def callTensionCalculator(inputFile, outputFile, args):
    """ Use subprocess to execute tension_calculation.py from midi-miner """

    # TODO: Refer to relative path
    tensionScript = '/Users/bedoya/OneDrive/COSMOS/Software/midi-miner/tension_calculation.py'
    command_list = ['python', tensionScript,
                    '-f', inputFile,
                    '-o', outputFile,
                    '-k', str(args['k']),
                    '-w', str(args['w']),
                    '-v', str(args['v'])
                   ]
    process = Popen(command_list, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    print(stdout.decode('utf-8'))

def removeExtraFiles(inputFile):
    """ Check if TensionVisualiser generated excess files and remove them """

    dirName    = os.path.dirname(inputFile)
    baseName   = genBaseName(inputFile)
    extraFiles =   [os.path.join(dirName, 'tension_calculate.log'),
                    os.path.join(dirName, 'files_result.json'),
                    baseName + '.centroid_diff',
                    baseName + '.diameter',
                    baseName + '.tensile',
                    baseName + '.time']
    for extra_file in extraFiles:
        if os.path.isfile(extra_file):
            os.remove(extra_file)
            # print('removed: ' + os.path.basename(extra_file))
    return

def genBaseName(inputFile):
    """ Generate full path base name (without extension) from midi file """

    baseName     = os.path.basename(inputFile)
    baseName, _  = os.path.splitext(baseName)
    dirName      = os.path.dirname(inputFile)
    fullBaseName = os.path.join(dirName, baseName)
    return fullBaseName

def openTension(inputFile):
    """ Create dataframe from results of midi-Miner """
    
    baseName    = genBaseName(inputFile)
    diameter    = pickle.load(open(baseName + '.diameter','rb'))
    momentum    = pickle.load(open(baseName + '.centroid_diff','rb'))
    strain      = pickle.load(open(baseName + '.tensile','rb'))
    time        = pickle.load(open(baseName + '.time','rb'))
    beat        = np.linspace(1,len(time),len(time), dtype=int)
    tensionDict = {'beat':beat, 'time' : time, 'momentum' : momentum, 'diameter' : diameter, 'strain':strain}
    df          = pd.DataFrame.from_dict(tensionDict)
    return df

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

    outputPath = os.path.dirname(inputFile)
    callTensionCalculator(inputFile, outputPath, args)
    df = openTension(inputFile)
    removeExtraFiles(inputFile)
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

    fig, ax = plt.subplots(nrows=3, ncols=1, figsize=figSize, sharex=True, sharey=False)
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

def main(inputFile, args, plotTension=False, exportTension=True, columns='all'):
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
        tension = getTension(inputPath, args= args, plotTension=plotTension, exportTension=exportTension, columns=columns)
        return tension
    if os.path.isdir(inputPath):
        import glob
        fileList = glob.glob(os.path.join(inputPath, '*.mid'))
        for inputFile in fileList:
            tension = getTension(inputFile, args= args, plotTension=plotTension, exportTension=exportTension, columns=columns)
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("inputPath", type=str,
                        help="Input path, .mid file or folder path with .mid files")
    parser.add_argument("-w", "--windowSize", type=int, help="Window size, default 1 beat", default=1)
    parser.add_argument("-v", "--verticalStep", type=float, help="Vertical step for spiral array, default sqrt(2/15)", default=np.sqrt(2/15))
    parser.add_argument("-k", "--keyChanged", action='store_true', help="Try to find key change, default False", default=False)
    parser.add_argument("-plot", "--plotTension", action='store_true', help="Plot tension curve, default False", default=False)
    parser.add_argument("-noPlot", "--dontPlot", action='store_false', help="Do not plot tension curve", dest='plotTension')
    parser.add_argument("-exp", "--exportTension", action='store_true', help="Export Tension as csv, default True", default=True)
    parser.add_argument("-noExp", "--dontExport", action='store_false', help="Do not export Tension as csv", dest='exportTension')
    parser.add_argument("-cols", "--columns", type=str,
                        help="Columns to export, all:Beats,Time,Tension - time=Time,Tension - beats:Beats,Tension")

    args          = parser.parse_args()
    inputPath     = args.inputPath
    tensionArgs   = {
                    'k':args.keyChanged,
                    'w':args.windowSize,
                    'v':args.verticalStep
                    }
    plotTension   = args.plotTension
    exportTension = args.exportTension
    if args.columns:
        columns = args.columns
    else:
        columns = 'all'

    main(inputPath, args=tensionArgs, plotTension=plotTension, exportTension=exportTension, columns=columns)
    print('Done!')
