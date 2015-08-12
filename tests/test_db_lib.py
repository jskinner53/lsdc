from __future__ import print_function

import sys
import time as ttime

from nose.tools import assert_equal, assert_raises, raises


from lsdc.dev_utils.testing import (dbtest_setup, dbtest_teardown)

from lsdc.odm_templates import *

def teardown():
    print('in teardown', file=sys.stderr)
    dbtest_teardown(collections)  # can pass drop_db=False to keep db for debugging


def setup():
    print('in setup', file=sys.stderr)
    dbtest_setup(collections)
    print('test_db_lib: setup done, sleeping briefly...', file=sys.stderr)
    #ttime.sleep(20)


def test_setup():
    t=Types(name='nombre', description='desc', base_type='test')
    t.save()

    assert_equal(1, 1)
