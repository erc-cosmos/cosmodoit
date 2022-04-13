import os

from music_features import get_loudness
import numpy as np
import pytest

import helpers


def loudness_old_pairs():
    audios = [os.path.join("tests", "test_data", "audios", f)
              for f in sorted(os.listdir(os.path.join("tests", "test_data", "audios")))
              if '.wav' in f]
    old_loudness = [os.path.join("tests", "test_data", "old_output", f)
                    for f in sorted(os.listdir(os.path.join("tests", "test_data", "old_output")))
                    if '.csv' in f]
    assert len(audios) == len(old_loudness)
    return tuple(zip(audios, old_loudness))


@pytest.mark.parametrize('wav_path, old_path', loudness_old_pairs())
def test_raw_same_as_matlab(wav_path, old_path):
    loudness_table = get_loudness.read_loudness(old_path)

    time, raw_loudness = get_loudness.compute_raw_loudness(wav_path)

    np.testing.assert_allclose(time, loudness_table.Time, atol=1e-3)
    np.testing.assert_allclose(raw_loudness, loudness_table.Loudness, atol=0.01)


@pytest.mark.parametrize('_, old_path', loudness_old_pairs())
def test_read_write_identity(_, old_path, clean_dir):
    data = get_loudness.read_loudness(old_path)
    new_path = os.path.join(clean_dir, "idem.csv")
    get_loudness.write_loudness(data, export_path=new_path)

    helpers.assert_numeric_equiv_csv(old_path, new_path)


@pytest.mark.parametrize('_, old_file', loudness_old_pairs())
def test_read_write_read_is_read(_, old_file, clean_dir):
    # TODO: actually test write_read identity
    data_before = get_loudness.read_loudness(old_file)

    new_path = os.path.join(clean_dir, "idem.csv")
    get_loudness.write_loudness(data_before, export_path=new_path)
    data_after = get_loudness.read_loudness(new_path)

    assert (data_after == data_before).all().all()


@pytest.mark.parametrize('_, old_file', loudness_old_pairs())
def test_rescale_same_as_matlab(_, old_file):
    loudness_table = get_loudness.read_loudness(old_file)

    new_rescale = get_loudness.rescale(loudness_table.Loudness)

    assert (abs(new_rescale - loudness_table.Loudness_norm) < 1e-6).all()


@pytest.mark.parametrize('_, old_file', loudness_old_pairs())
def test_rescale_keeps_size(_, old_file):
    loudness_table = get_loudness.read_loudness(old_file)

    new_rescale = get_loudness.rescale(loudness_table.Loudness)

    assert len(loudness_table.Loudness) == len(new_rescale)


@pytest.mark.parametrize('_, old_file', loudness_old_pairs())
def test_rescale_tight_interval(_, old_file):
    loudness_table = get_loudness.read_loudness(old_file)

    new_rescale = get_loudness.rescale(loudness_table.Loudness)

    assert new_rescale.max() == 1.0
    assert new_rescale.min() == 0.0


@pytest.mark.parametrize('_, old_file', loudness_old_pairs())
def test_envelope_same_as_matlab(_, old_file):
    loudness_table = get_loudness.read_loudness(old_file)

    min_separation = np.floor(len(loudness_table.Time)/list(loudness_table.Time)[-1])
    new_envelope = get_loudness.clip_negative(get_loudness.peak_envelope(
        np.array(loudness_table.Loudness_norm), min_separation))

    assert (abs(new_envelope - loudness_table.Loudness_envelope) < 1e-6).all()


@pytest.mark.parametrize('_, old_file', loudness_old_pairs())
def test_enveloppe_keeps_size(_, old_file):
    loudness_table = get_loudness.read_loudness(old_file)

    min_separation = np.floor(len(loudness_table.Time)/list(loudness_table.Time)[-1])
    new_envelope = get_loudness.clip_negative(get_loudness.peak_envelope(
        np.array(loudness_table.Loudness_norm), min_separation))

    assert len(new_envelope) == len(loudness_table.Loudness_envelope)


@pytest.mark.skip(reason="Known boundary effects")
@pytest.mark.parametrize('_, old_file', loudness_old_pairs())
def test_smoothing_same_as_matlab(_, old_file):
    loudness_table = get_loudness.read_loudness(old_file)

    span = 0.03
    smoothed = get_loudness.clip_negative(get_loudness.smooth(loudness_table.Loudness_norm, span))
    halfspan = int(np.floor(np.floor(len(loudness_table.Loudness_norm)*span)/2))

    np.testing.assert_allclose(smoothed[halfspan:-halfspan],
                               loudness_table.Loudness_smooth[halfspan:-halfspan], atol=1e-3)


@pytest.mark.parametrize('_, old_file', loudness_old_pairs())
def test_smoothing_keeps_size(_, old_file):
    loudness_table = get_loudness.read_loudness(old_file)

    smoothed = get_loudness.smooth(loudness_table.Loudness_norm, 0.03)

    assert len(smoothed) == len(loudness_table.Loudness_smooth)
