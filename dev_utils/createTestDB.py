#!/usr/bin/python

import time
import os

import sys
sys.path.append('/h/cowan/projects')  # until we get this packaged+installed

import lsdc.db_lib  # makes db connection
from lsdc.db_lib import *

def createTestDB():
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
    request_type = 'test_request'
    request_id = createRequest({'request_type': request_type, 'test_request_param': 'bare request 1'},
                           as_mongo_obj=True)
    
    # bare results
    result_type = 'test_result'
    createResult({'result_type': result_type,
                  'request_id': request_id,
                  'test_result_value': 'bare result 1'})
    
    # in requestList on sample
    request_id = addRequesttoSample(sampID,
                             {'request_type': request_type,
                              'test_request_param': 'test param 1'},
                             as_mongo_obj=True)
    
    # in resultsList on sample
    addResultforRequest({'request_id': request_id,
                         'result_type': result_type,
                         'test_result_val': 'test val 1'})


if __name__ == '__main__':
    createTestDB()
