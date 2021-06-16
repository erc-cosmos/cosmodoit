import pytest
import os
import shutil
import uuid
import csv

@pytest.fixture
def clean_dir():
    new_dir = "testDir"+uuid.uuid4().hex
    os.makedirs(new_dir)
    yield new_dir
    shutil.rmtree(new_dir)


def assert_numeric_equiv_csv(path_a, path_b):
    """Compares 2 csv files as far as  is concerned."""
    with open(path_a) as file_a:
        with open(path_b) as file_b:
            reader_a = csv.reader(file_a)
            reader_b = csv.reader(file_b)
            # Headers are equal
            assert next(reader_a) == next(reader_b)
            for line_a, line_b in zip(reader_a, reader_b):
                for elem_a, elem_b in zip(line_a, line_b):
                    try:
                        assert float(elem_a) == pytest.approx(float(elem_b))
                    except AssertionError as e:
                        print(elem_a, elem_b)
                        raise e