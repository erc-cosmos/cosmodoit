import sys
sys.path.append("music_features")
import get_alignment
import get_sustain
import get_beats
import extract_features
import os


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
    for _,perf_path in paths:
        yield {
            'name': perf_path,
            'file_dep': [perf_path],
            # 'targets': [target],
            'actions': [(lambda path:{'sustain': get_sustain.get_sustain(path)}, [perf_path])]
        }


def task_alignment():
    paths = discover_files()
    for (ref_path, perf_path) in paths:
        # yield from MIDIToMIDIAlign.gen_tasks(ref_path, perf_path, working_folder=working_folder)
        yield from get_alignment.gen_tasks(ref_path, perf_path, working_folder=working_folder)


def task_beats():
    paths = discover_files()
    for (ref_path, perf_path) in paths:
        ref_noext, _ = os.path.splitext(os.path.basename(ref_path))
        ref_midi = os.path.join(working_folder, ref_noext+"_ref.mid")
        perf_noext, _ = os.path.splitext(os.path.basename(perf_path))
        perf_match = os.path.join(working_folder, perf_noext+"_match.txt")
        perf_beats = os.path.join(working_folder, perf_noext+"_beats.csv")
        # yield {
        #     'basename': "read_match",
        #     'name': perf_noext,
        #     'file_dep': [perf_match],
        #     'actions': [(lambda path:{'alignment': get_alignment.readAlignmentFile(path)}, [perf_match])]
        # }
        # yield {
        #     'basename': "beats_ref",
        #     'name': ref_noext,
        #     'file_dep': [ref_midi],
        #     'actions': [(lambda path:{'ref_beats': get_beats.get_beat_reference_pm(path)}, [ref_midi])]
        # }
        def caller(perf_match, ref_midi, perf_beats, **kwargs):
            alignment = get_alignment.readAlignmentFile(perf_match)
            beat_reference = get_beats.get_beat_reference_pm(ref_midi)
            beats = get_beats.get_beats(alignment, beat_reference)
            extract_features.writeFile(perf_beats, beats)
            return True
        yield {
            'basename': "beats",
            'file_dep': [perf_match, ref_midi],
            'name': perf_noext,
            # 'getargs': {
            #     'alignment': (f'read_match:{perf_noext}', 'alignment'),
            #     'reference_beats': (f'beats_ref:{ref_noext}', 'ref_beats')},
            'targets': [perf_beats],
            'actions': [(caller, [perf_match, ref_midi, perf_beats])]
        }