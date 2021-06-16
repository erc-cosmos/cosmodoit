import os
import pytest
import numpy as np

from helpers import *

import get_loudness


def loudness_old_pairs():
    audios = [os.path.join("tests", "test_data", "audios", f)
              for f in sorted(os.listdir(os.path.join("tests", "test_data", "audios")))
              if '.wav' in f]
    old_loudness = [os.path.join("tests", "test_data", "old_output", f)
                    for f in sorted(os.listdir(os.path.join("tests", "test_data", "old_output")))
                    if '.csv' in f]
    assert len(audios) == len(old_loudness)
    return tuple(zip(audios, old_loudness))


@pytest.mark.parametrize('wav_file, old_path', loudness_old_pairs())
def test_same_as_matlab(wav_file, old_path, clean_dir):
    get_loudness.get_loudness(wav_file, export_dir=clean_dir)
    new_path = os.path.join(clean_dir, os.path.basename(wav_file).replace('.wav', '_loudness.csv'))

    assert_numeric_equiv_csv(old_path, new_path)


@pytest.mark.parametrize('_, old_path', loudness_old_pairs())
def test_read_write_identity(_, old_path, clean_dir):
    data = get_loudness.read_loudness(old_path)
    new_path = os.path.join(clean_dir, "idem.csv")
    get_loudness.write_loudness(data, new_path)

    assert_numeric_equiv_csv(old_path, new_path)


@pytest.mark.parametrize('_, old_file', loudness_old_pairs())
def test_read_write_read_is_read(_, old_file, clean_dir):
    # TODO: actually test write_read identity
    data_before = get_loudness.read_loudness(old_file)

    new_path = os.path.join(clean_dir, "idem.csv")
    get_loudness.write_loudness(data_before, new_path)
    data_after = get_loudness.read_loudness(new_path)

    assert (data_after == data_before).all().all()


@pytest.mark.parametrize('_, old_file', loudness_old_pairs())
def test_rescale_same_as_matlab(_, old_file):
    loudnessTable = get_loudness.read_loudness(old_file)

    new_rescale = get_loudness.rescale(loudnessTable.Loudness)

    assert (abs(new_rescale - loudnessTable.Loudness_norm) < 1e-6).all()


@pytest.mark.parametrize('_, old_file', loudness_old_pairs())
def test_envelope_same_as_matlab(_, old_file):
    loudnessTable = get_loudness.read_loudness(old_file)

    min_separation = np.floor(len(loudnessTable.Time)/list(loudnessTable.Time)[-1])
    new_envelope = get_loudness.clipNegative(get_loudness.peak_envelope(
        np.array(loudnessTable.Loudness_norm), min_separation))

    assert (abs(new_envelope - loudnessTable.Loudness_envelope) < 1e-6).all()
