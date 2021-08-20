from genericpath import isdir
import sys
import warnings

sys.path.append("music_features")
import get_loudness
import get_alignment
import get_sustain
import get_beats
import get_onsetVelocity
import os
import argparse

from util import write_file, run_doit


DOIT_CONFIG = {'action_string_formatting': 'both'}
working_folder = "tmp"


def discover_files(base_folder="tests/test_data"):
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
    return tuple(zip(scores, perfs, wavs))


def discover_by_piece(base_folder):
    """Find targets in a piece first directory structure."""
    piece_folders = [os.path.join('base_folder', folder) 
        for folder in os.listdir(base_folder) 
        if os.path.isdir(folder)]
    def find_ext(path, ext):
        files = [os.path.join(path,f) for f in os.listdir(path) if ext in f]
        if len(files) == 0:
            warnings.warn(f"Found no file with extension {ext} in {path}")
            return None
        if len(files) > 1:
            warnings.warn(f"Found more than one file matching extension {ext} in {path} (using {files[0]})")
        return files[0]
    return [tuple(find_ext(folder, ext) for ext in ('mscz', 'mid', 'wav')) for folder in piece_folders]

def task_sustain():
    paths = discover_files()
    for _, perf_path, _ in paths:
        yield {
            'name': perf_path,
            'file_dep': [perf_path],
            # 'targets': [target],
            'actions': [(lambda path:{'sustain': get_sustain.get_sustain(path)}, [perf_path])]
        }


def task_velocities():
    paths = discover_files()
    def runner(perf_filename):
        perf_noext, _ = os.path.splitext(os.path.basename(perf_filename))
        velocityFilename = os.path.join(working_folder, perf_noext+"_velocity.csv")

        velocities = get_onsetVelocity.get_onset_velocity(perf_filename)
        if velocities == []:
            warnings.warn("Warning: no note on event detected in " + perf_filename)
        else:
            write_file(velocityFilename, velocities)
        return None
    for _, perf_path, _ in paths:
        yield {
            'name': perf_path,
            'file_dep': [perf_path],
            # 'targets': [target],
            'actions': [(runner, [perf_path])]
        }



def task_alignment():
    paths = discover_files()
    for (ref_path, perf_path, _) in paths:
        yield from get_alignment.gen_tasks(ref_path, perf_path, working_folder=working_folder)


def task_beats():
    paths = discover_files()
    for (ref_path, perf_path, _) in paths:
        yield from get_beats.gen_tasks(ref_path, perf_path, working_folder=working_folder)


def task_loudness():
    paths = discover_files()
    for (_, _, audio_path) in paths:
        yield from get_loudness.gen_tasks(audio_path, working_folder=working_folder)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ref', required=True)
    parser.add_argument('--perf', required=True)

    args = parser.parse_args()

    globals['discover_files'] = lambda:[(args.ref, args.perf)]
    run_doit(globals)
    