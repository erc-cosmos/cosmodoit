import pytest
import os
import shutil
import uuid

@pytest.fixture
def clean_dir():
    new_dir = "testDir"+uuid.uuid4().hex
    os.makedirs(new_dir)
    yield new_dir
    shutil.rmtree(new_dir)