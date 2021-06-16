import filecmp
import os
import pytest

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
    return tuple(zip(audios,old_loudness))


@pytest.mark.parametrize('wav_file, old_file', loudness_old_pairs())
def test_same_as_matlab(wav_file, old_file, clean_dir):
    get_loudness.get_loudness(wav_file, export_dir=clean_dir)
    new_file = os.path.join(clean_dir,os.path.basename(wav_file).replace('.wav', '_loudness.csv'))
    assert filecmp.cmp(new_file, old_file, shallow=False)
