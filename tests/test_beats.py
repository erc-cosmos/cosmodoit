import get_beats
import get_alignment
import pytest
import os

from helpers import test_files
from util import targets_factory


@pytest.mark.parametrize("ref, perf", test_files())
def test_sorted_beats(ref, perf):
    cache_folder = 'tmp'
    alignment = get_alignment.get_alignment(ref_path=ref, perf_path=perf, cleanup=False, working_folder=cache_folder)
    ref_midi = targets_factory(ref,working_folder=cache_folder)("_ref.mid")
    reference_beats = get_beats.get_beat_reference_pm(ref_midi)

    beats = get_beats.get_beats(alignment, reference_beats=reference_beats)
    sorted(beats, key=lambda b:b['time']) == beats


@pytest.mark.parametrize("ref, perf", test_files())
def test_sorted_ref_beats_manual(ref, perf):
    alignment = get_alignment.get_alignment(ref_path=ref, perf_path=perf, cleanup=False)
    reference_beats = get_beats.make_beat_reference(alignment, guess=True)

    sorted(reference_beats) == reference_beats


@pytest.mark.parametrize("ref, perf", test_files())
def test_sorted_ref_beats_prettymidi(ref, perf):
    alignment = get_alignment.get_alignment(ref_path=ref, perf_path=perf, cleanup=False)
    ref_midi = ref.replace(".mscz", ".mid")
    reference_beats = get_beats.get_beat_reference_pm(ref_midi)

    sorted(reference_beats) == reference_beats


@pytest.mark.parametrize("ref, perf", test_files())
def test_no_outliers(ref, perf):
    cache_folder = 'tmp'
    alignment = get_alignment.get_alignment(ref_path=ref, perf_path=perf, cleanup=False, working_folder=cache_folder)
    ref_midi = targets_factory(ref,working_folder=cache_folder)("_ref.mid")
    reference_beats = get_beats.get_beat_reference_pm(ref_midi)

    beats = get_beats.get_beats(alignment, reference_beats=reference_beats)
    outliers = get_beats.find_outliers(beats, verbose=True)
    assert outliers == []