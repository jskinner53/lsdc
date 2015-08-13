#!/usr/bin/env python

# This file is closely based on run_tests.py from metadatastore which
# was closely based on tests.py from matplotlib
# 
# This allows running tests from the command line: e.g.
#
#   $ python tests.py -v -d
#
#   or just  ./run-tests.py
#
# The arguments are identical to the arguments accepted by nosetests.
#
# See https://nose.readthedocs.org/ for a detailed description of
# these options.

import os
import uuid

import nose

# from skxray.testing.noseclasses import KnownFailure
# plugins = [KnownFailure]
plugins = []

env = {"NOSE_WITH_COVERAGE": 1,
       'NOSE_COVER_PACKAGE': 'metadatastore',
       'NOSE_COVER_HTML': 1}

# Nose doesn't automatically instantiate all of the plugins in the
# child processes, so we have to provide the multiprocess plugin with
# a list.
from nose.plugins import multiprocess
multiprocess._instantiate_plugins = plugins


# Use an obvious name for test fixture db's so it's clear where they
# came from and that they're junk, if they get left around due to a bug.
suffixroot = '_db_lib__test_tmp_'
suffix = '{0}{1}'.format(suffixroot, str(uuid.uuid4()))
os.environ['DB_LIB_SUFFIXROOT'] = suffixroot
os.environ['DB_LIB_SUFFIX'] = suffix

# enable this to not drop test databases after testing
#os.environ['DB_LIB_KEEP_TEST_DB'] = '1'

def run():
    nose.main(addplugins=[x() for x in plugins], env=env)


if __name__ == '__main__':
    run()
