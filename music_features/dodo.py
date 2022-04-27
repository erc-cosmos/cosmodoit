"""Main doit task definitions."""
import os
import sys
from typing import Iterable, NamedTuple
import warnings

from doit import task_params
from music_features import get_alignment
from music_features import get_beats
from music_features import get_loudness
from music_features import get_onset_velocity
from music_features import get_sustain
from music_features import get_tension
from music_features.util import collect_kw_parameters
from music_features.util import default_naming_scheme
from music_features.util import gen_default_tasks
from music_features.util import targets_factory_new

DOIT_CONFIG = {'action_string_formatting': 'both'}
INPLACE_WRITE = True
default_working_folder = 'tmp'


class InputDescriptor(NamedTuple):
    """Named tuple for describing input file types."""

    filetype: str
    patterns: Iterable[str]
    antipatterns: Iterable[str]
    expected: bool


def find_ext(path: str, file_descriptor: InputDescriptor):
    """Scan a directory for a file type."""
    filetype, patterns, antipatterns, required = file_descriptor
    files = [os.path.join(path, f) for f in os.listdir(path)
             if any(f.endswith(ext) for ext in patterns)
             and not (any(f.endswith(ext) for ext in antipatterns))
             and not f.startswith('.')]
    if len(files) == 0:
        if required:
            warnings.warn(
                f"Found no file of type {filetype} in {path} (expected extensions {patterns}). "
                "Some tasks will be skipped.")
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
        InputDescriptor('score', ('.mscz', '.xml', '.mxl'), (), True),
        InputDescriptor('perfmidi', ('.mid',), ('_ref.mid', '_perf.mid'), True),
        InputDescriptor('perfaudio', ('.wav',), (), True),
        InputDescriptor('manual_beats', ('_beats_manual.csv',), (), False),
        InputDescriptor('manual_bars', ('_bars_manual.csv',), (), False)
    )
    # Overwrite default folder if a folder was given
    if os.getcwd() != os.path.dirname(__file__):
        base_folder = os.getcwd()

    piece_folders = [os.path.join(base_folder, folder)
                     for folder in os.listdir(base_folder)
                     if os.path.isdir(os.path.join(base_folder, folder)) and folder != 'tmp']

    FileSet = NamedTuple('FileSet', ((descriptor.filetype, str) for descriptor in file_types))
    grouped_files = [(folder, FileSet(*(find_ext(folder, file_descriptor) for file_descriptor in file_types)))
                     for folder in piece_folders]
    return grouped_files


# Switch between discovery modes
discover_files = discover_files_by_piece


def gen_tasks_template(module):
    try:
        param_sources = module.param_sources
    except AttributeError:
        param_sources = []

    @task_params(collect_kw_parameters(*param_sources))
    def generator(**kwargs):
        filesets = discover_files()
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
                else:
                    working_folder = default_working_folder
                    os.makedirs(working_folder, exist_ok=True)
                target_factory = targets_factory_new(default_naming_scheme, piece_id, paths, working_folder)
                yield from task_gen(piece_id, target_factory, **kwargs)
    return generator


# Register the generators in the module namespace
submodules = (get_loudness, get_onset_velocity, get_sustain, get_tension,
              get_beats, get_alignment)
for module in submodules:
    name = module.__name__[19:]  # Assumes get_X convention is respected
    globals()[f"task_{name}"] = gen_tasks_template(module)


def main():
    """Entry point."""
    import argparse
    from doit.doit_cmd import DoitMain
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', default=os.getcwd())
    args, unknownargs = parser.parse_known_args()
    DoitMain().run(["-f", __file__, "--dir", args.dir, *unknownargs])


if __name__ == '__main__':
    sys.exit(main())
