import get_alignment
import os


def test_cleanup():
    remote_dir = os.path.join('tests', 'test_data')
    refFilename = 'tests/test_data/Chopin_Ballade_No2_ref.mscz'
    perfFilename = 'tests/test_data/Chopin_Ballade_No2_perf.mid'

    remote_dir_content_before = sorted(os.listdir(remote_dir))
    local_dir_content_before = sorted(os.listdir())
    
    alignment = get_alignment.get_alignment(refFilename=refFilename, perfFilename=perfFilename, cleanup=True,
        midi2midiExecLocation="music_features/MIDIToMIDIAlign.sh")
    
    remote_dir_content_after = sorted(os.listdir(remote_dir))
    assert remote_dir_content_after == remote_dir_content_before
    local_dir_content_after = sorted(os.listdir())
    assert local_dir_content_before == local_dir_content_after