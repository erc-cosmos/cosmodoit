from genericpath import samefile
import os
import sys
import shutil
import subprocess
import argparse


def runAlignment(reference, performance, workingFolder=None):
    """Run the aligmnent executables in sequence."""
    ref_base = os.path.basename(reference)
    perf_base = os.path.basename(performance)

    # Folder for the compiled C++ programs
    ProgramFolder = os.path.abspath(os.path.join(os.path.dirname(__file__), 'bin'))

    # Folder to use for operations
    if workingFolder is None:
        workingFolder = os.path.dirname(performance)
    # Copy (if required) to working directory    
    for originalFile in [reference+".mid", performance+".mid"]:
        try:
            shutil.copy(originalFile, workingFolder)
        except shutil.SameFileError:
            pass


    # File paths
    ref_pianoroll = os.path.join(workingFolder, ref_base+"_spr.txt")
    ref_HMM = os.path.join(workingFolder, ref_base+"_hmm.txt")
    ref_FMT3X = os.path.join(workingFolder, ref_base+"_fmt3x.txt")
    perf_pianoroll = os.path.join(workingFolder, perf_base+"_spr.txt")
    perf_prematch = os.path.join(workingFolder, perf_base+"_pre_match.txt")
    perf_errmatch = os.path.join(workingFolder, perf_base+"_err_match.txt")
    perf_realigned = os.path.join(workingFolder, perf_base+"_realigned_match.txt")
    perf_match = os.path.join(workingFolder, perf_base+"_match.txt")
    
    subprocess.run([os.path.join(ProgramFolder, "midi2pianoroll"), str(0), os.path.join(workingFolder, ref_base)])
    subprocess.run([os.path.join(ProgramFolder, "midi2pianoroll"), str(0), os.path.join(workingFolder, perf_base)])

    subprocess.run([os.path.join(ProgramFolder, "SprToFmt3x"), ref_pianoroll, ref_FMT3X])
    subprocess.run([os.path.join(ProgramFolder, "Fmt3xToHmm"), ref_FMT3X, ref_HMM])

    subprocess.run([os.path.join(ProgramFolder, "ScorePerfmMatcher"),
                   ref_HMM, perf_pianoroll, perf_prematch, str(0.01)])
    subprocess.run([os.path.join(ProgramFolder, "ErrorDetection"),
                   ref_FMT3X, ref_HMM, perf_prematch, perf_errmatch, str(0)])
    subprocess.run([os.path.join(ProgramFolder, "RealignmentMOHMM"), 
                   ref_FMT3X, ref_HMM, perf_errmatch, perf_realigned, str(0.3)])

    shutil.move(perf_realigned, perf_match)

    os.remove(perf_errmatch)
    os.remove(perf_prematch)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ref', required=True)
    parser.add_argument('--perf', required=True)
    parser.add_argument('--wd', default=None)
    args = parser.parse_args()
    runAlignment(args.ref, args.perf, workingFolder=args.wd)