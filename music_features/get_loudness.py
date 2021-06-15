import os

def get_loudness(inputPath, *, column='all', exportLoudness=True, dest_dir=None, plotLoudness=False, smoothSpan=0.03, noNegative=True):
    """Compute Global Loudness of Audio Files.
    
    inputPath       : string; folder path or wav audio file path
    columns         : string; which column - 'all' (default), 'raw', 'norm', 'smooth', 'envelope'
    exportLoudness  : boolean; export as csv (true by default)
    dest_dir        : string; folder in which to save the export (default: same as input)
    plotLoudness    : boolean; plot results (false by default)
    smoothSpan      : double; number of data points for calculating the smooth curve (0.03 by default)
    noNegative      : boolean; set L(i) < 0 = 0 (true by default)
    
    returns         :  array; Time (:,1) Loudness (:,2), Normalized (:,3), Normalized-smoothed (:,4), Normalized-envelope (:,5)
    """
    if dest_dir is None:
        dest_dir=os.path.dirname(inputPath)

    return None