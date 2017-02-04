'''
Offline utility tests
'''
from unittest import TestCase
from scutils.argparse_helper import ArgparseHelper
import argparse
from mock import MagicMock
import sys

# from http://stackoverflow.com/questions/4219717/how-to-assert-output-with-nosetest-unittest-in-python
from contextlib import contextmanager
from StringIO import StringIO
@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class TestArgparseHelper(TestCase):

    def test_output(self):
        parser = argparse.ArgumentParser(description='Desc here',
        								 add_help=False)
        parser.add_argument('-h', '--help', action=ArgparseHelper, help='show this help message and exit')

        subparsers = parser.add_subparsers(help='commands', dest='command')

        base_parser = argparse.ArgumentParser(add_help=False)
        base_parser.add_argument('-s', '--settings', action='store',
                                 required=False,
                                 help="The settings file to read from",
                                 default="localsettings.py")

        feed_parser = subparsers.add_parser('feed', help='Feed the script',
                                            parents=[base_parser])
        feed_parser.add_argument('json', help='The JSON object as a string')

        run_parser = subparsers.add_parser('run', help='Run the script',
                                           parents=[base_parser])

        a = ArgparseHelper(MagicMock())

        expected = '''usage: nosetests [-h] {feed,run} ...

Desc here

positional arguments:
  {feed,run}  commands
    feed      Feed the script
    run       Run the script

optional arguments:
  -h, --help  show this help message and exit

Command 'feed'
usage: nosetests feed [-h] [-s SETTINGS] json

Command 'run'
usage: nosetests run [-h] [-s SETTINGS]'''

        try:
            with captured_output() as (out, err):
                a(parser, MagicMock(), MagicMock())
        except SystemExit:
            pass

        output = out.getvalue().strip()
        self.assertEqual(output, expected)
