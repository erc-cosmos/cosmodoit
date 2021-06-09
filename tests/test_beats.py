import get_beats
import pytest


test_files = [("tests/test_data/Chopin_Ballade_No2_ref.mscz","tests/test_data/Chopin_Ballade_No2_perf.mid"),
              ("tests/test_data/Fur_Elise_ref.mscz","tests/test_data/Fur_Elise_perf.mid")]

@pytest.mark.parametrize("ref, perf", test_files)
def test_sorted_beats(ref, perf):
    alignment = get_beats.get_alignment(refFilename=ref, perfFilename=perf, cleanup=False, midi2midiExecLocation="music_features/MIDIToMIDIAlign.sh")
    reference_beats = get_beats.make_beat_reference(alignment, guess=True)

    beats = get_beats.get_beats(alignment, reference_beats=reference_beats)
    sorted(beats, key=lambda b:b['time']) == beats


@pytest.mark.parametrize("ref, perf", test_files)
def test_sorted_ref_beats_manual(ref, perf):
    alignment = get_beats.get_alignment(refFilename=ref, perfFilename=perf, cleanup=False, midi2midiExecLocation="music_features/MIDIToMIDIAlign.sh")
    reference_beats = get_beats.make_beat_reference(alignment, guess=True)

    sorted(reference_beats) == reference_beats


@pytest.mark.parametrize("ref, perf", test_files)
def test_sorted_ref_beats_prettymidi(ref, perf):
    alignment = get_beats.get_alignment(refFilename=ref, perfFilename=perf, cleanup=False, midi2midiExecLocation="music_features/MIDIToMIDIAlign.sh")
    ref_midi = ref.replace(".mscz", ".mid")
    reference_beats = get_beats.get_beat_reference_pm(ref_midi)

    sorted(reference_beats) == reference_beats