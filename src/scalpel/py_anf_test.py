import io
import os
import sys

import pytest
from .py_anf_transformer import test_link



def pytest_generate_tests(metafunc):
    filenames = []
    directory = './test_samples'
    if 'filename' in metafunc.fixturenames:
        for file in os.listdir(directory):
            if not file == '__init__.py':
                filenames.append(file)
        metafunc.parametrize("filename", filenames)


# Testing df_index shape against the dummy dataframe
def test_back_transformation(filename: str):
    directory = './test_samples'
    f = '/'.join([directory, filename])
    if os.path.isfile(f) and not f.endswith('_out.anf'):
        file = open(f, "r")
        captured_output = io.StringIO()  # Create StringIO object
        sys.stdout = captured_output  # and redirect stdout.
        test_link(f, True)  # Call unchanged function.
        sys.stdout = sys.__stdout__
        assert(captured_output.getvalue() == file.read())