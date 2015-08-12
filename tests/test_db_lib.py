from __future__ import print_function

import sys
import time as ttime

from nose.tools import assert_equal, assert_raises, raises


from lsdc.dev_utils.testing import (dbtest_setup, dbtest_teardown)

from lsdc.odm_templates import *


# setup db fixtures

def teardown():
    print('in teardown', file=sys.stderr)
    dbtest_teardown(collections, drop_db=False)  # can pass drop_db=False to keep db for debugging

def setup():
    print('in setup', file=sys.stderr)
    dbtest_setup(collections)
    print('test_db_lib: setup done, sleeping briefly...', file=sys.stderr)
    #ttime.sleep(20)


# test stuff

# createTestDB() in dbtest_setup() inherently tests basic functionality of:
#     createType, createContainer, insertIntoContainer, createSample, type_from_name
#     createRequest, createResult, addRequesttoSample, addResultforRequest

# testing itself tests:
#     db_connect, db_disconnect

# untested routines:
#     find_{container, sample, request, result, sample_request}
#     getRasters, addRaster, clearRasters, getNextRunRaster, getNextDisplayRaster
#     _try0_dict_key, _try0_maybe_mongo
#     getSampleByID, getSampleIDbyName, getSampleNamebyID
#     getContainerIDbyName, getContainerNameByID           # inconsistent 'By' capitalization :(
#     getResult, deleteResult, 
#     getResultsforRequest, getResultsforSample, createResult  # duplicate decl of createResult!!!
#     addFile, getFile
#     createDefaultRequest, _ret_list, getContainers, getContainersByType, getAllPucks
#     getPrimaryDewar, getContainerByName, getContainerByID
#     insertCollectionRequest, getQueue, getDewarPosfromSampleID
#     getAbsoluteDewarPosfromSampleID                     # doesn't make sense with mixed puck types
#     getSampleIDfromAbsoluteDewarPos                     # doesn't make sense with mixed puck types
#     getCoordsfromSampleID, getSampleIDfromCoords
#     popNextRequest, getRequest, updateRequest, deleteRequest
#     deleteSample, removePuckFromDewar, emptyLiveQueue
#     getSortedPriorityList, getOrderedRequestList
#     beamlineInfo, userSettings
#     createField

def test_setup():
    # just do anything to make it actually create a db
    t=Types(name='nombre', description='desc', base_type='test')
    t.save()

    assert_equal(1, 1)


if __name__ == "__main__":
    import nose
    nose.runmodule(argv=['-s', '--with-doctest'], exit=False)
