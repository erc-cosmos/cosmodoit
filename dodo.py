"""Main doit task definitions."""
import os

import doit
import argparse
import warnings
from collections import namedtuple

from music_features import get_alignment, get_beats, get_loudness, get_onset_velocity, get_sustain, get_tension
from music_features.util import run_doit, gen_default_tasks


DOIT_CONFIG = {'action_string_formatting': 'both'}
INPLACE_WRITE = True
default_working_folder = 'tmp'


def discover_files_by_type(base_folder="tests/test_data"):
    """Find targets in a feature-type first directory structure."""
    # Outdated output format
    scores = [os.path.join(base_folder, "scores", f)
              for f in sorted(os.listdir(os.path.join(base_folder, "scores")))
              if '.mscz' in f]
    perfs = [os.path.join(base_folder, "perfs", f)
             for f in sorted(os.listdir(os.path.join(base_folder, "perfs")))
             if '.mid' in f]
    wavs = [os.path.join(base_folder, "perfs", f)
            for f in sorted(os.listdir(os.path.join(base_folder, "perfs")))
            if '.wav' in f]
    assert len(scores) == len(perfs)
    assert len(scores) == len(wavs)
    piece_ids = (os.path.splitext(perf)[0] for perf in perfs)
    return tuple(zip(piece_ids, scores, perfs, wavs))


FileDescriptor = namedtuple('FileDescriptor', ('filetype', 'patterns', 'antipatterns', 'optional'))


def find_ext(path: os.PathLike, file_descriptor: FileDescriptor):
    """Scan a directory for a file type."""
    filetype, patterns, antipatterns, required = file_descriptor
    files = [os.path.join(path, f) for f in os.listdir(path)
             if any(ext in f for ext in patterns)
             and not (any(ext in f for ext in antipatterns))
             and not f.startswith('.')]
    if len(files) == 0:
        if required:
            warnings.warn(f"Found no file of type {filetype} in {path} (expected extensions {patterns})")
        return None
    elif len(files) > 1:
        warnings.warn(f"Found more than one file of type {filetype} in {path} (using {files[0]})")
    return files[0]


def discover_files_by_piece(base_folder='tests/test_data/piece_directory_structure'):
    """
    Find targets in a piece first directory structure.

    This expects pieces to be in one folder each
    """
    file_types = (
        FileDescriptor('score', ('.mscz',), (), True),
        FileDescriptor('perfmidi', ('.mid',), ('_ref.mid', '_perf.mid'), True),
        FileDescriptor('perfaudio', ('.wav',), (), True),
        FileDescriptor('manual_beats', ('_beats_manual.csv',), (), False),
        FileDescriptor('manual_bars', ('_bars_manual.csv',), (), False)
    )
    if doit.get_initial_workdir() != os.getcwd():
        base_folder = os.getcwd()
    piece_folders = [os.path.join(base_folder, folder)
                     for folder in os.listdir(base_folder)
                     if os.path.isdir(os.path.join(base_folder, folder)) and folder != 'tmp']

    FileSet = namedtuple('FileSet', (descriptor.filetype for descriptor in file_types))
    grouped_files = [(folder, FileSet(*(find_ext(folder, file_descriptor) for file_descriptor in file_types)))
                     for folder in piece_folders]
    return grouped_files


# Switch between discovery modes
discover_files = discover_files_by_piece
# discover_files= discover_files_by_type


def task_generator():
    """Generate tasks for all files."""
    if not INPLACE_WRITE:
        working_folder = default_working_folder
        os.makedirs(working_folder, exist_ok=True)
    filesets = discover_files()
    submodules = (get_loudness, get_onset_velocity, get_sustain, get_tension,
                  get_beats, get_alignment)
    for module in submodules:
        try:
            docs = module.task_docs
        except AttributeError:
            warnings.warn(f"No docs for submodule {module.__name__}")
        else:
            yield from gen_default_tasks(docs)

        try:
            task_gen = module.gen_tasks
        except AttributeError:
            warnings.warn(f"Missing task generator in submodule {module.__name__}")
        else:
            for (folder, paths) in filesets:
                piece_id = os.path.basename(folder)
                if INPLACE_WRITE:
                    working_folder = folder
                yield from task_gen(piece_id, paths, working_folder=working_folder)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ref', required=False)
    parser.add_argument('--perf', required=False)
    parser.add_argument('--wav', required=False)

    args = parser.parse_args()

    if args.ref and args.perf:
        globals['discover_files'] = lambda: [(args.ref, args.perf, args.wav)]
    run_doit(globals)
