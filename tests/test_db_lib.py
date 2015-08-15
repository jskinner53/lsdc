from __future__ import print_function

import sys
import time as ttime

from nose.tools import assert_equal, assert_raises, raises

import bson

from lsdc.dev_utils.testing import (dbtest_setup, dbtest_teardown)
from lsdc.db_lib import *
from lsdc.odm_templates import *


# setup db fixtures

def teardown_module():
    print('in teardown', file=sys.stderr)
    dbtest_teardown(collections)  # can pass drop_db=False to keep db for debugging

def setup_module():
    print('in setup', file=sys.stderr)

    # this runs createTestDB()!
    # All the test below assume a fresh test db from createTestDB()
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
#     getCoordsfromSampleID, getSampleIDfromCoords
#     popNextRequest, getRequest, updateRequest, deleteRequest
#     deleteSample, removePuckFromDewar, emptyLiveQueue
#     getSortedPriorityList, getOrderedRequestList
#     beamlineInfo, userSettings
#     createField

def test_setup():
    # just do anything to make it actually create a db
    t=Types(name='nombre', description='desc', parent_type='test')
    t.save()

    assert_equal(1, 1)

def test_find_container():

    expected_types = {'containerName': unicode,
                     '_id': bson.ObjectId,
                     'item_list': list,
                     'container_id': int,
                     'container_type': bson.dbref.DBRef}

    expected_set = set(expected_types.keys())

    for cont in find_container():
        try:
            assert(set(cont.keys()).union(set(['item_list'])) == expected_set)
        except AssertionError:
            raise AssertionError('unexpected container field: {0}\n{1}'.format(cont.keys(), expected_set))

        for key in expected_types:
            try:
                assert(isinstance(cont[key], expected_types[key]))
            except KeyError:
                if key != 'item_list':  # some containers don't have a fixed size item list
                    raise KeyError('key error on field: {0}'.format(key))
            except AssertionError:
                raise AssertionError('expected container[{0}] as {1}, not {2}'.format(key, expected_types[key], cont[key].__class__))


if __name__ == "__main__":
    import nose
    nose.runmodule(argv=['-s', '--with-doctest'], exit=False)
