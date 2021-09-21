import pytest
import os
import csv


def test_files():
    scores = [os.path.join("tests", "test_data", "scores", f)
              for f in sorted(os.listdir(os.path.join("tests", "test_data", "scores")))
              if '.mscz' in f]
    perfs = [os.path.join("tests", "test_data", "perfs", f)
             for f in sorted(os.listdir(os.path.join("tests", "test_data", "perfs")))
             if '.mid' in f]
    assert len(scores) == len(perfs)
    return tuple(zip(scores, perfs))


def assert_numeric_equiv_csv(path_a, path_b):
    """Compare 2 csv files as far as import is concerned."""
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
