#!/usr/bin/python

import time

import sys
sys.path.append('/h/cowan/projects')  # until we get this packaged+installed
import lsdc.db_lib  # makes db connection
from lsdc.db_lib import *


# fields

# types
base_types = [{'name': 'sample', 'description': '', 'base_type': 'base'},
              {'name': 'container', 'description': '', 'base_type': 'base'},
              {'name': 'request', 'description': '', 'base_type': 'base'},
              {'name': 'result', 'description': '', 'base_type': 'base'}]  # 'location'?

for t in  base_types:
    print 'name: {0}'.format(t['name'])
    createType(t['name'], t['description'], t['base_type'])


types = [{'name': 'puck', 'description': '', 'base_type': 'container'},
         {'name': 'pin', 'description': '', 'base_type': 'sample'},
         {'name': 'dewar', 'description': '', 'base_type': 'container'},
         {'name': 'test_request', 'description': '', 'base_type': 'request'},
         {'name': 'test_result', 'description': '', 'base_type': 'result'}]

for t in types:
    print 'name: {0}, base_type {1}'.format(t['name'], t['base_type'])
    createType(t['name'], t['description'], t['base_type'])


# containers
for i in range(3)+[6]:  # discontinuity for testing
    containerName = 'Puck_{0}'.format(i)
    createContainer(containerName, 'puck', 16)

for i in range(4):  # discontinuity for testing
    containerName = 'dewar_{0}'.format(i)
    createContainer(containerName, 'std_shipping_dewar', 5)


# named containers
primary_dewar_name = 'primaryDewar'

createContainer(primary_dewar_name, 'dewar', 24) 

for i in range(4)+[6]:  # discontinuity for testing
    containerName = 'Puck_'.format(i)
    insertIntoContainer(primary_dewar_name, i, getContainerIDbyName(containerName))


# samples
for i in range(3)+[6]:  # discontinuity for testing
    containerName = 'Puck_{0}'.format(i)
    for j in range(4)+[6]:
        sampleName = 'samp_{0}_{1}'.format(i, j)

        try:
            sampID = createSample(sampleName)
        except NotUniqueError:
            raise NotUniqueError('{0}'.format(sampleName))

        if not insertIntoContainer(containerName, j, sampID):
            print 'name {0}, pos {1}, sampid {2}'.format(containerName, j, sampID)


# bare requests
reqt_obj = type_from_name('test_request', as_mongo_obj=True)
req_id = createRequest({'request_type': reqt_obj, 'test_request_param': 'bare request 1'},
                       as_mongo_obj=True)

# bare results
rest_obj = type_from_name('test_result', as_mongo_obj=True)
createResult({'result_type': rest_obj, 'request_id': req_id, 'test_result_value': 'bare result 1'})

# in requestList on sample
req = addRequesttoSample(sampID,
                         {'request_type': reqt_obj,
                          'test_request_param': 'test param 1'},
                         as_mongo_obj=True)

# in resultsList on sample
addResultforRequest({'request_id': req,
                     'result_type': rest_obj,
                     'test_result_val': 'test val 1'})


