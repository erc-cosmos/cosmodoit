from music_features import get_beats, get_alignment
import pytest

import numpy as np
import helpers
from music_features.util import targets_factory


@pytest.mark.parametrize("ref, perf", helpers.test_files())
def test_sorted_beats(ref, perf):
    cache_folder = 'tmp'
    alignment = get_alignment.get_alignment(ref_path=ref, perf_path=perf, cleanup=False, working_folder=cache_folder)
    ref_midi = targets_factory(ref, working_folder=cache_folder)("_ref.mid")
    reference_beats = get_beats.get_beat_reference_pm(ref_midi)

    beats, _ = get_beats.get_beats(alignment, reference_beats=reference_beats)
    assert not (np.diff(beats.time) < 0).any()


@pytest.mark.parametrize("ref, perf", helpers.test_files())
def test_sorted_ref_beats_prettymidi(ref, perf):
    cache_folder = 'tmp'
    _ = get_alignment.get_alignment(ref_path=ref, perf_path=perf, cleanup=False, working_folder=cache_folder)
    ref_midi = targets_factory(ref, working_folder=cache_folder)("_ref.mid")
    reference_beats = get_beats.get_beat_reference_pm(ref_midi)

    sorted(reference_beats) == reference_beats


@pytest.mark.parametrize("ref, perf", helpers.test_files())
def test_no_outliers(ref, perf):
    cache_folder = 'tmp'
    alignment = get_alignment.get_alignment(ref_path=ref, perf_path=perf, cleanup=False, working_folder=cache_folder)
    ref_midi = targets_factory(ref, working_folder=cache_folder)("_ref.mid")
    reference_beats = get_beats.get_beat_reference_pm(ref_midi)

    beats, _ = get_beats.get_beats(alignment, reference_beats=reference_beats)
    outliers = get_beats.find_outliers(beats, verbose=True)
    assert outliers == []


@pytest.mark.parametrize("ref, perf", helpers.test_files())
def test_reasonable_removal(ref, perf):
    """Check that at most a few values (5%) get removed as outliers."""
    cache_folder = 'tmp'
    alignment = get_alignment.get_alignment(ref_path=ref, perf_path=perf, cleanup=False, working_folder=cache_folder)
    ref_midi = targets_factory(ref, working_folder=cache_folder)("_ref.mid")
    reference_beats = get_beats.get_beat_reference_pm(ref_midi)

    _, removed = get_beats.get_beats(alignment, reference_beats=reference_beats)

    assert 20*len(removed) < len(alignment)
