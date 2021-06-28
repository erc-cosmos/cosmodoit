import sys
import warnings
sys.path.append("music_features")
import get_alignment
import get_sustain
import get_beats
import get_onsetVelocity
import os
import argparse

from util import write_file, run_doit


DOIT_CONFIG = {'action_string_formatting': 'both'}
working_folder = "tmp"


def discover_files():
    scores = [os.path.join("tests", "test_data", "scores", f)
              for f in sorted(os.listdir(os.path.join("tests", "test_data", "scores")))
              if '.mscz' in f]
    perfs = [os.path.join("tests", "test_data", "perfs", f)
             for f in sorted(os.listdir(os.path.join("tests", "test_data", "perfs")))
             if '.mid' in f]
    assert len(scores) == len(perfs)
    return tuple(zip(scores, perfs))


def task_sustain():
    paths = discover_files()
    for _, perf_path in paths:
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
    for _, perf_path in paths:
        yield {
            'name': perf_path,
            'file_dep': [perf_path],
            # 'targets': [target],
            'actions': [(runner, [perf_path])]
        }



def task_alignment():
    paths = discover_files()
    for (ref_path, perf_path) in paths:
        yield from get_alignment.gen_tasks(ref_path, perf_path, working_folder=working_folder)


def task_beats():
    paths = discover_files()
    for (ref_path, perf_path) in paths:
        yield from get_beats.gen_tasks(ref_path, perf_path, working_folder=working_folder)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ref', required=True)
    parser.add_argument('--perf', required=True)

    args = parser.parse_args()

    globals['discover_files'] = lambda:[(args.ref, args.perf)]
    run_doit(globals)
    