"""Module for wrapping Eita Nakamura's alignment software."""
import collections
import csv
import os
import shutil

from .util import run_doit, string_escape_concat, targets_factory


def get_alignment(ref_path, perf_path, working_folder='tmp', cleanup=True):
    """Run the alignment and return it."""
    paths = collections.namedtuple("Paths", ["score", "perfmidi"])(ref_path, perf_path)
    perf_targets = targets_factory(perf_path, working_folder=working_folder)

    def task_wrapper():
        yield from gen_tasks(os.path.basename(ref_path), paths, working_folder=working_folder)
    task_set = {'task_alignment': task_wrapper}
    run_doit(task_set)

    outFile = os.path.join(working_folder, os.path.basename(perf_path).replace('.mid', "_match.txt"))
    outFile = perf_targets("_match.txt")
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


task_docs = {
    "MIDI_Conversion": "Convert a Musescore file to a stripped down midi"
}


def gen_subtasks_midi(piece_id, ref_path, musescore_exec="/Applications/MuseScore 3.app/Contents/MacOS/mscore",
                      working_folder="tmp", strip_direction=False):
    """Generate doit tasks for the midi conversion and preprocessing."""
    ref_targets = targets_factory(ref_path, working_folder=working_folder)

    _ref_name, ref_ext = os.path.splitext(ref_path)

    if ref_ext not in [".mxl", ".xml", ".mscz"]:
        raise NotImplementedError(f"Unsupported format {ref_ext}")

    ref_mid = ref_targets("_ref.mid")

    yield {
        'basename': 'MIDI_Conversion',
        'name': piece_id,
        'doc': task_docs["MIDI_Conversion"],
        'file_dep': [ref_path, __file__, musescore_exec],
        'targets': [ref_mid],
        'actions': [string_escape_concat([musescore_exec, ref_path, "--export-to", ref_mid])],
        'clean': True,
        'verbosity': 0
    }


def gen_subtasks_Nakamura(piece_id, ref_path, perf_path, working_folder="tmp"):
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

    exe_pianoroll = os.path.join(program_folder, "midi2pianoroll")
    exe_fmt3x = os.path.join(program_folder, "SprToFmt3x")
    exe_hmm = os.path.join(program_folder, "Fmt3xToHmm")
    exe_prealignment = os.path.join(program_folder, "ScorePerfmMatcher")
    exe_errmatch = os.path.join(program_folder, "ErrorDetection")
    exe_realignment = os.path.join(program_folder, "RealignmentMOHMM")

    yield {
        'basename': '_pianoroll_conversion_ref',
        'name': piece_id,
        'file_dep': [ref_path, ref_midi, exe_pianoroll, __file__],
        'targets': [ref_pianoroll],
        'actions': [
            string_escape_concat([exe_pianoroll, str(0), ref_copy_noext])
        ],
        'clean': True
    }
    yield {
        'basename': '_pianoroll_conversion_perf',
        'name': piece_id,
        'file_dep': [perf_path, exe_pianoroll, __file__],
        'targets': [perf_pianoroll, perf_copy_noext+'.mid'],
        'actions': [
            (shutil.copy, [perf_path, perf_copy_noext+'.mid'],),
            string_escape_concat([exe_pianoroll, str(0), perf_copy_noext])
        ],
        'clean': True
    }
    yield {
        'basename': '_FMT3X_conversion',
        'name': piece_id,
        'file_dep': [ref_pianoroll, exe_fmt3x, __file__],
        'targets': [ref_FMT3X],
        'actions': [string_escape_concat([exe_fmt3x, ref_pianoroll, ref_FMT3X])],
        'clean': True
    }
    yield {
        'basename': '_HMM_conversion',
        'name': piece_id,
        'file_dep': [ref_FMT3X, exe_hmm, __file__],
        'targets': [ref_HMM],
        'actions': [string_escape_concat([exe_hmm, ref_FMT3X, ref_HMM])],
        'clean': True
    }
    yield {
        'basename': '_prealignment',
        'name': piece_id,
        'file_dep': [ref_HMM, perf_pianoroll, exe_prealignment, __file__],
        'targets': [perf_prematch],
        'actions': [string_escape_concat([exe_prealignment, ref_HMM, perf_pianoroll, perf_prematch, str(0.01)])],
        'clean': True
    }
    yield {
        'basename': '_error_detection',
        'name': piece_id,
        'file_dep': [ref_FMT3X, ref_HMM, perf_prematch, exe_errmatch, __file__],
        'targets': [perf_errmatch],
        'actions': [string_escape_concat([exe_errmatch, ref_FMT3X, ref_HMM, perf_prematch, perf_errmatch, str(0)])],
        'clean': True
    }
    yield {
        'basename': '_realignment',
        'name': piece_id,
        'file_dep': [ref_FMT3X, ref_HMM, perf_errmatch, __file__],
        'targets': [perf_realigned],
        'actions': [string_escape_concat([exe_realignment, ref_FMT3X, ref_HMM,
                                          perf_errmatch, perf_realigned, str(0.3)])],
        'clean': True
    }


def gen_tasks(piece_id, paths, working_folder="tmp"):
    """Generate doit tasks to call Nakamura's midi to midi alignment software."""
    if paths.score is None:
        return
    yield from gen_subtasks_midi(piece_id, paths.score, working_folder=working_folder)
    if paths.perfmidi is None:
        return
    yield from gen_subtasks_Nakamura(piece_id, paths.score, paths.perfmidi, working_folder)
