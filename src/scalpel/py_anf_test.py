import unittest
import os
import io
import sys

from scalpel.py_anf_transformer import test_link


class PyToANFTests(): # unittest.TestCase):

    def test_functioning(self):
        directory = './python_code_samples'

        for filename in os.listdir(directory):
            f = os.path.join(directory, filename)
            if os.path.isfile(f) and not f.endswith('_out.anf'):
                file = open(f[:len(f) - 3] + '_out.anf', "r")
                capturedOutput = io.StringIO()  # Create StringIO object
                sys.stdout = capturedOutput  # and redirect stdout.
                test_link(f)  # Call unchanged function.
                sys.stdout = sys.__stdout__
                print(capturedOutput.getvalue())
                self.assertEqual(capturedOutput.getvalue(), file.read())

    def test_back_transformation(self):
        directory = './python_code_samples'

        for filename in os.listdir(directory):
            f = os.path.join(directory, filename)
            if os.path.isfile(f) and not f.endswith('_out.anf'):
                # file = open(f[:len(f)-3] + '_out.anf', "r")
                file = open(f, "r")

                capturedOutput = io.StringIO()  # Create StringIO object
                sys.stdout = capturedOutput  # and redirect stdout.
                test_link(f, True)  # Call unchanged function.
                sys.stdout = sys.__stdout__
                content = file.read()
                print(filename)
                print(content)
                print()
                print(capturedOutput.getvalue())
                print()
                print(capturedOutput.getvalue() == content)
                print()
                print()
                print()
                # self.assertEqual(capturedOutput.getvalue(), f.read())


if __name__ == '__main__':
    # unittest.main()
    PyToANFTests().test_back_transformation()