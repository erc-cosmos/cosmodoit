#!/usr/bin/python3
# -*- coding: utf-8 -*-
import csv
import os
import argparse
import collections
import shutil
import xml.etree.ElementTree as ET

from util import string_escape_concat, run_doit, targets_factory


# def get_score_alignment(refFilename, perfFilename,
#                         score2midiExecLocation="./MusicXMLToMIDIAlign.sh",
#                         museScoreExec="/Applications/MuseScore 3.app/Contents/MacOS/mscore",
#                         cleanup=True, recompute=False):
#     """Call Nakamura's Score to Midi alignment software.

#     Intermediate files will be removed if cleanup is True
#     If recompute is False, existing intermediate files will be reused if present
#     """
#     # Crop .mid extension as the script doesn't want them
#     refFilename, refType = os.path.splitext(refFilename)
#     perfFilename, perfType = os.path.splitext(perfFilename)

#     if refType not in [".xml"]:
#         if refType in [".mscz", ".mxl"]:  # TODO: add other valid formats
#             # Generate a midi from the score
#             # TODO: check that musescore is correctly found
#             # TODO: check if conversion is already done
#             subprocess.run([museScoreExec, refFilename+refType, "--export-to", refFilename+".xml"],
#                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#         else:
#             raise NotImplementedError

#     # Run the alignment (only if needed or requested)
#     outFile = perfFilename+"_match.txt"
#     if recompute or not os.path.isfile(outFile):
#         output = subprocess.run([score2midiExecLocation, refFilename, perfFilename])
#     alignment = readAlignmentFile(outFile)

#     if cleanup:
#         clean_alignment_files(refFilename, perfFilename)
#     return alignment


def _remove_directions(filename, outfile=None):
    """Remove all directions from a musicxml file."""
    tree = ET.parse(filename)
    for elem in tree.findall(".//direction"):
        elem.clear()  # TODO: actually remove it instad of clearing (causes warnings)
    tree.write(outfile if outfile is not None else filename)


def get_alignment(ref_path, perf_path, working_folder='tmp', cleanup=True):
    def task_wrapper():
        yield from gen_tasks(ref_path, perf_path, working_folder)
    task_set = {'task_alignment': task_wrapper}
    run_doit(task_set)
    
    outFile = os.path.join(working_folder, os.path.basename(perf_path).replace('.mid',"_match.txt"))
    alignment = read_alignment_file(outFile)
    
    if cleanup:
        commands = ['clean']
        run_doit(task_set, commands)
    return alignment


def read_alignment_file(file_path):
    """Read the output of Nakamura's software and extracts relevant information."""
    AlignmentAtom = collections.namedtuple("AlignmentAtom", ('tatum', 'time'))
    with open(file_path) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter='\t')
        # Extract relevant columns
        return [AlignmentAtom(tatum=int(row[8]), time=float(row[1]))
                for row in csv_reader
                if len(row) > 3 and row[8] != '-1' and row[9] != '*'  # Not a metaline and not a mismatch
                ]


def gen_subtasks_midi(ref_path, musescore_exec="/Applications/MuseScore 3.app/Contents/MacOS/mscore", working_folder="tmp"):
    """Generate doit tasks for the midi conversion and preprocessing."""
    ref_name, ref_ext = os.path.splitext(ref_path)

    if ref_ext not in [".mxl", ".xml", ".mscz"]:
        raise NotImplementedError(f"Unsupported format {ref_ext}")

    ref_xml = ref_name+".xml"
    yield {
        'basename': '_XML_Conversion',
        'name': ref_name,
        'file_dep': [ref_path, __file__, musescore_exec],
        'targets': [ref_xml],
        'actions': [string_escape_concat([musescore_exec, ref_path, "--export-to", ref_xml])],
        'clean': True,
        'verbosity': 0
    }
    ref_nodir = ref_name+"_nodir.xml"
    yield {
        'basename': '_strip_direction',
        'name': ref_name,
        'file_dep': [ref_xml, __file__],
        'targets': [ref_nodir],
        'actions': [(_remove_directions, [ref_xml, ref_nodir],)],
        'clean': True
    }
    ref_mid = ref_name+".mid"
    yield {
        'basename': 'MIDI_Conversion',
        'name': ref_name,
        'file_dep': [ref_nodir, __file__, musescore_exec],
        'targets': [ref_mid],
        'actions': [string_escape_concat([musescore_exec, ref_nodir, "--export-to", ref_mid])],
        'clean': True,
        'verbosity': 0
    }

def gen_subtasks_Nakamura(ref_path, perf_path, working_folder="tmp"):
    """Generate doit tasks for the alignment."""
    program_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), 'bin'))

    ref_targets = targets_factory(ref_path, working_folder=working_folder)
    perf_targets = targets_factory(perf_path, working_folder=working_folder)
    
    ref_copy_noext = ref_targets("_ref")
    ref_midi = ref_targets("_ref.mid")
    ref_pianoroll = ref_targets("_ref_spr.txt")
    ref_HMM = ref_targets("_hmm.txt")
    ref_FMT3X = ref_targets("_fmt3x.txt")

    perf_copy_noext = perf_targets("_perf")
    perf_pianoroll = perf_targets("_perf_spr.txt")
    perf_prematch = perf_targets("_pre_match.txt")
    perf_errmatch = perf_targets("_err_match.txt")
    perf_realigned = perf_targets("_match.txt")

    exec_pianoroll = os.path.join(program_folder, "midi2pianoroll")
    exec_fmt3x = os.path.join(program_folder, "SprToFmt3x")
    exec_hmm = os.path.join(program_folder, "Fmt3xToHmm")
    exec_prealignment = os.path.join(program_folder, "ScorePerfmMatcher")
    exec_errmatch = os.path.join(program_folder, "ErrorDetection")
    exec_realignment = os.path.join(program_folder, "RealignmentMOHMM")

    yield {
        'basename': '_pianoroll_conversion_ref',
        'name': ref_pianoroll,
        'file_dep': [ref_path, exec_pianoroll, __file__],
        'targets': [ref_pianoroll, ref_midi],
        'actions': [
            (shutil.copy,[ref_path.replace('.mscz', '.mid'), ref_midi],),
            string_escape_concat([exec_pianoroll, str(0), ref_copy_noext])
        ],
        'clean': True
    }
    yield {
        'basename': '_pianoroll_conversion_perf',
        'name': perf_path,
        'file_dep': [perf_path, exec_pianoroll, __file__],
        'targets': [perf_pianoroll, perf_copy_noext+'.mid'],
        'actions': [
            (shutil.copy,[perf_path, perf_copy_noext+'.mid'],),
            string_escape_concat([exec_pianoroll, str(0), perf_copy_noext])
        ],
        'clean': True
    }
    yield {
        'basename': '_FMT3X_conversion',
        'name': perf_path,
        'file_dep': [ref_pianoroll, exec_fmt3x, __file__],
        'targets': [ref_FMT3X],
        'actions': [string_escape_concat([exec_fmt3x, ref_pianoroll, ref_FMT3X])],
        'clean': True
    }
    yield {
        'basename': '_HMM_conversion',
        'name': perf_path,
        'file_dep': [ref_FMT3X, exec_hmm, __file__],
        'targets': [ref_HMM],
        'actions': [string_escape_concat([exec_hmm, ref_FMT3X, ref_HMM])],
        'clean': True
    }
    yield {
        'basename': '_prealignment',
        'name': perf_path,
        'file_dep': [ref_HMM, perf_pianoroll, exec_prealignment, __file__],
        'targets': [perf_prematch],
        'actions': [string_escape_concat([exec_prealignment, ref_HMM, perf_pianoroll, perf_prematch, str(0.01)])],
        'clean': True
    }
    yield {
        'basename': '_error_detection',
        'name': perf_path,
        'file_dep': [ref_FMT3X, ref_HMM, perf_prematch, exec_errmatch, __file__],
        'targets': [perf_errmatch],
        'actions': [string_escape_concat([exec_errmatch, ref_FMT3X, ref_HMM, perf_prematch, perf_errmatch, str(0)])],
        'clean': True
    }
    yield {
        'basename': '_realignment',
        'name': perf_path,
        'file_dep': [ref_FMT3X, ref_HMM, perf_errmatch, __file__],
        'targets': [perf_realigned],
        'actions': [string_escape_concat([exec_realignment, ref_FMT3X, ref_HMM, perf_errmatch, perf_realigned, str(0.3)])],
        'clean': True
    }


def gen_tasks(ref_path, perf_path, working_folder="tmp"):
    """Generate doit tasks to call Nakamura's midi to midi alignment software."""
    yield from gen_subtasks_midi(ref_path, working_folder=working_folder)
    yield from gen_subtasks_Nakamura(ref_path, perf_path, working_folder)
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ref', required=True)
    parser.add_argument('--perf', required=True)
    args = parser.parse_args()

    # # Ensure execution directory
    # script_location = os.path.dirname(__file__)
    # if script_location != '':
    #     os.chdir(script_location)

    ref_path = args.ref
    perf_path = args.perf

    alignment = get_alignment(ref_path=ref_path, perf_path=perf_path, cleanup=False)
    print(alignment)
