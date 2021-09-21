"""Config and fixtures for Pytest."""
import pytest
import uuid
import shutil
import os


@pytest.fixture
def clean_dir():
    """Make a new directory and cleanup after the test."""
    new_dir = "testDir"+uuid.uuid4().hex
    os.makedirs(new_dir)
    yield new_dir
    shutil.rmtree(new_dir)
