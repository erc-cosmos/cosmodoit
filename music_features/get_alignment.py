"""Module for wrapping Eita Nakamura's alignment software."""
import collections
from importlib import resources
import os
import shutil
from typing import NamedTuple

from numpy import float64
import pandas as pd

from .util import default_naming_scheme
from .util import run_doit
from .util import string_escape_concat
from .util import targets_factory_new


class AlignmentAtom(NamedTuple):
    """Named tuple for alignment elements."""

    tatum: int
    time: float


def get_alignment(ref_path: str, perf_path: str, working_folder: str = 'tmp', cleanup: bool = True) -> pd.DataFrame:
    """Run the alignment and return it."""
    paths = collections.namedtuple("Paths", ["score", "perfmidi"])(ref_path, perf_path)
    piece_id = os.path.basename(ref_path)
    targets = targets_factory_new(default_naming_scheme, piece_id, paths, working_folder)

    def task_wrapper():
        yield from gen_tasks(os.path.basename(ref_path), targets)
    task_set = {'task_alignment': task_wrapper}
    run_doit(task_set)

    out_file = targets("match")
    alignment = read_alignment(out_file)

    if cleanup:
        commands = ['clean']
        run_doit(task_set, commands)
    return alignment


def read_alignment(file_path: str) -> pd.DataFrame:
    """Read the output of Nakamura's software and extracts relevant information."""
    # From https://midialignment.github.io/MANUAL.pdf #4.4
    # This included 1 column too many so offset velocity was dropped.
    # The superfluous column might be match status instead, in which case channel is wrong
    col_names = ["index", "note_on", "note_off", "pitch_name", "pitch_midi", "velocity", "channel",
                 "match_status", "score_time", "note_id", "error_index", "skip_index"]
    df = pd.read_csv(file_path, sep="\t", skiprows=4, index_col=0, names=col_names,
                     dtype={'score_time': int, 'note_on': float64}, comment='/')
    # Select relevant data
    df = df.loc[(df['note_id'] != '*') & (df['score_time'] >= 0), ["score_time", "note_on"]]
    return df


task_docs = {
    "MIDI_Conversion": "Convert a Musescore file to a stripped down midi"
}


def gen_subtasks_midi(piece_id: str, targets):
    """Generate doit tasks for the midi conversion and preprocessing."""
    # ref_targets = targets_factory(ref_path, working_folder=working_folder)
    ref_path = targets("score")
    _ref_name, ref_ext = os.path.splitext(ref_path)

    if ref_ext not in [".mxl", ".xml", ".mscz"]:
        raise NotImplementedError(f"Unsupported format {ref_ext}")

    ref_mid = targets("ref_midi")

    musescore_exec = locate_musescore()

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


def locate_musescore() -> str:
    """Locate the executable for Musescore.

    Returns:
        str: Best guess of the path to Musescore's executable
    """
    # TODO: Find a deployable way to search the mscore executable
    # Music21 does it for Lilypond with an 'environment' setting or a set of known possible paths
    for musescore_exec in ["/Applications/MuseScore 3.app/Contents/MacOS/mscore"]:
        if os.path.exists(musescore_exec):
            return musescore_exec
    else:  # Not found
        return 'mscore'  # Hope it is on the PATH
        # TODO test before returning


def gen_subtasks_Nakamura(piece_id: str, targets):
    """Generate doit tasks for the alignment."""
    ref_path = targets("score")
    ref_copy_noext = targets("ref_copy_noext")
    ref_midi = targets("ref_midi")
    ref_pianoroll = targets("ref_pianoroll")
    ref_HMM = targets("ref_HMM")
    ref_FMT3X = targets("ref_FMT3X")

    perf_path = targets("perfmidi")
    perf_copy_noext = targets("perf_copy_noext")
    perf_pianoroll = targets("perf_pianoroll")
    perf_prematch = targets("perf_prematch")
    perf_errmatch = targets("perf_errmatch")
    perf_realigned = targets("perf_realigned")

    resource_bins = resources.files(__package__) / 'bin'
    exe_pianoroll = resource_bins / "midi2pianoroll"
    exe_fmt3x = resource_bins / "SprToFmt3x"
    exe_hmm = resource_bins / "Fmt3xToHmm"
    exe_prealignment = resource_bins / "ScorePerfmMatcher"
    exe_errmatch = resource_bins / "ErrorDetection"
    exe_realignment = resource_bins / "RealignmentMOHMM"

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


def gen_tasks(piece_id, targets):
    """Generate doit tasks to call Nakamura's midi to midi alignment software."""
    if targets("score") is None:
        return
    yield from gen_subtasks_midi(piece_id, targets)
    if targets("perfmidi") is None:
        return
    yield from gen_subtasks_Nakamura(piece_id, targets)
