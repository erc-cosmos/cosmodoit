import os
import shutil

import pytest
from get_alignment import get_alignment


@pytest.fixture
def clean_dir():
    reference, performance = ('tests/test_data/scores/Chopin_Ballade_No2_ref.mscz',
                              'tests/test_data/perfs/Chopin_Ballade_No2_perf.mid')
    new_dir = "testDir"
    os.makedirs(new_dir)
    new_ref = shutil.copy(reference, new_dir)
    new_perf = shutil.copy(performance, new_dir)
    yield (new_ref, new_perf)
    shutil.rmtree(new_dir)


def test_cleanup(clean_dir):
    ref_filename, perf_filename = clean_dir
    remote_dir = os.path.dirname(ref_filename)

    remote_dir_content_before = sorted(os.listdir(remote_dir))
    local_dir_content_before = sorted(os.listdir())

    _ = get_alignment(refFilename=ref_filename, perfFilename=perf_filename, cleanup=True, working_folder='testDir')

    remote_dir_content_after = sorted(os.listdir(remote_dir))
    assert remote_dir_content_after == remote_dir_content_before
    local_dir_content_after = sorted(os.listdir())
    assert local_dir_content_before == local_dir_content_after
