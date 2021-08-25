from genericpath import isdir
import sys
import warnings
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "music_features"))
import get_loudness
import get_alignment
import get_sustain
import get_beats
import get_onset_velocity
import get_tension
import argparse
import doit

from util import run_doit


DOIT_CONFIG = {'action_string_formatting': 'both'}

default_working_folder = os.path.join(doit.get_initial_workdir(), 'tmp')


def discover_files_by_type(base_folder="tests/test_data"):
    """Find targets in a feature-type first directory structure."""
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


def discover_files_by_piece(base_folder='tests/test_data/piece_directory_structure'):
    """Find targets in a piece first directory structure.
    
    This expects pieces to be in one folder each"""

    if doit.get_initial_workdir() != os.getcwd():
        base_folder = os.getcwd()
    piece_folders = [os.path.join(base_folder, folder) 
        for folder in os.listdir(base_folder) 
        if os.path.isdir(os.path.join(base_folder, folder))]
    def find_ext(path, ext):
        files = [os.path.join(path,f) for f in os.listdir(path) if ext in f]
        if len(files) == 0:
            warnings.warn(f"Found no file with extension {ext} in {path}")
            return None
        if len(files) > 1:
            warnings.warn(f"Found more than one file matching extension {ext} in {path} (using {files[0]})")
        return files[0]
    grouped_files = [(folder, *(find_ext(folder, ext) for ext in ('.mscz', '.mid', '.wav'))) for folder in piece_folders]
    return grouped_files


# Switch between discovery modes
discover_files= discover_files_by_piece
# discover_files= discover_files_by_type


def task_generator():
    #"""Generates tasks for all files."""
    working_folder = default_working_folder
    paths = discover_files()
    for (piece_id, ref_path, perf_path, audio_path) in paths:
        yield from get_tension.gen_tasks(piece_id, ref_path, perf_path, working_folder=working_folder)
        yield from get_loudness.gen_tasks(piece_id, audio_path, working_folder=working_folder)
        yield from get_beats.gen_tasks(piece_id, ref_path, perf_path, working_folder=working_folder)
        yield from get_alignment.gen_tasks(piece_id, ref_path, perf_path, working_folder=working_folder)
        yield from get_sustain.gen_tasks(piece_id, perf_path, working_folder=working_folder)
        yield from get_onset_velocity.gen_tasks(piece_id, perf_path, working_folder=working_folder)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ref', required=False)
    parser.add_argument('--perf', required=False)

    args = parser.parse_args()

    if args.ref and args.perf:
        globals['discover_files'] = lambda:[(args.ref, args.perf)]
    run_doit(globals)
    