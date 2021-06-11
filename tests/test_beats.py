import get_beats
import pytest
import os

def test_files():
    scores = [os.path.join("tests", "test_data", "scores", f) 
        for f in sorted(os.listdir(os.path.join("tests", "test_data", "scores"))) 
        if '.mscz' in f]
    perfs = [os.path.join("tests", "test_data", "perfs", f) 
        for f in sorted(os.listdir(os.path.join("tests", "test_data", "perfs"))) 
        if '.mid' in f]
    assert len(scores) == len(perfs)
    return tuple(zip(scores,perfs))

@pytest.mark.parametrize("ref, perf", test_files())
def test_sorted_beats(ref, perf):
    alignment = get_beats.get_alignment(refFilename=ref, perfFilename=perf, cleanup=False, midi2midiExecLocation="music_features/MIDIToMIDIAlign.sh")
    reference_beats = get_beats.make_beat_reference(alignment, guess=True)

    beats = get_beats.get_beats(alignment, reference_beats=reference_beats)
    sorted(beats, key=lambda b:b['time']) == beats


@pytest.mark.parametrize("ref, perf", test_files())
def test_sorted_ref_beats_manual(ref, perf):
    alignment = get_beats.get_alignment(refFilename=ref, perfFilename=perf, cleanup=False, midi2midiExecLocation="music_features/MIDIToMIDIAlign.sh")
    reference_beats = get_beats.make_beat_reference(alignment, guess=True)

    sorted(reference_beats) == reference_beats


@pytest.mark.parametrize("ref, perf", test_files())
def test_sorted_ref_beats_prettymidi(ref, perf):
    alignment = get_beats.get_alignment(refFilename=ref, perfFilename=perf, cleanup=False, midi2midiExecLocation="music_features/MIDIToMIDIAlign.sh")
    ref_midi = ref.replace(".mscz", ".mid")
    reference_beats = get_beats.get_beat_reference_pm(ref_midi)

    sorted(reference_beats) == reference_beats


@pytest.mark.parametrize("ref, perf", test_files())
def test_no_outliers(ref, perf):
    alignment = get_beats.get_alignment(refFilename=ref, perfFilename=perf, cleanup=False, midi2midiExecLocation="music_features/MIDIToMIDIAlign.sh")
    reference_beats = get_beats.make_beat_reference(alignment, guess=True)

    beats = get_beats.get_beats(alignment, reference_beats=reference_beats)
    outliers = get_beats.find_outliers(beats, verbose=True)
    assert outliers == []