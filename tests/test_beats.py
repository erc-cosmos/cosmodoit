import get_beats
import get_alignment
import pytest


test_files = [("tests/test_data/Chopin_Ballade_No2_ref.mscz","tests/test_data/Chopin_Ballade_No2_perf.mid"),
              ("tests/test_data/Fur_Elise_ref.mscz","tests/test_data/Fur_Elise_perf.mid")]

@pytest.mark.parametrize("ref, perf", test_files)
def test_sorted_beats(ref, perf):
    alignment = get_alignment.get_alignment(refFilename=ref, perfFilename=perf, cleanup=False, midi2midiExecLocation="music_features/MIDIToMIDIAlign.sh")

    beats = get_beats.get_beats(alignment, plotting=False, guess=True)
    sorted(beats, key=lambda b:b['time']) == beats

