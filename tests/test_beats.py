import get_beats
import get_alignment


def test_sorted_beats():
    ref='tests/test_data/Chopin_Ballade_No2_ref.mscz'
    perf='tests/test_data/Chopin_Ballade_No2_perf.mid'

    alignment = get_alignment.get_alignment(refFilename=ref, perfFilename=perf, cleanup=False, midi2midiExecLocation="music_features/MIDIToMIDIAlign.sh")

    beats = get_beats.get_beats(alignment, plotting=False, guess=True)
    sorted(beats, key=lambda b:b['time']) == beats

