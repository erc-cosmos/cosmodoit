import os
import shutil

import pytest
from music_features.get_alignment import get_alignment


@pytest.fixture
def prepared_dir(clean_dir):
    reference, performance = ('tests/test_data/scores/Mazurka 33-4, Pachmann DA.mscz',
                              'tests/test_data/perfs/Mazurka 33-4, Pachmann DA.mid')
    new_ref = shutil.copy(reference, clean_dir)
    new_perf = shutil.copy(performance, clean_dir)
    yield (clean_dir, new_ref, new_perf)


def test_cleanup(clean_dir):
    ref_filename, perf_filename = ('tests/test_data/scores/Mazurka 33-4, Pachmann DA.mscz',
                                   'tests/test_data/perfs/Mazurka 33-4, Pachmann DA.mid')
    remote_dir = os.path.dirname(ref_filename)

    remote_dir_content_before = sorted(os.listdir(remote_dir))
    local_dir_content_before = sorted(os.listdir())

    _ = get_alignment(ref_path=ref_filename, perf_path=perf_filename, cleanup=True, working_folder=clean_dir)

    remote_dir_content_after = sorted(os.listdir(remote_dir))
    assert remote_dir_content_after == remote_dir_content_before
    local_dir_content_after = sorted(os.listdir())
    assert local_dir_content_before == local_dir_content_after
