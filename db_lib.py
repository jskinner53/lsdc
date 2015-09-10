#!/usr/bin/python
from __future__ import print_function
#from __future__ import (absolute_import, print_function)

import sys
import os
import socket

import bson
import six

import mongoengine 
from  mongoengine import NotUniqueError

# I would prefer if these were relative imports :(
from odm_templates import (Sample, Container, Request, Result,
                           GenericFile, Types, Field)

from odm_templates import (BeamlineInfo, UserSettings)   # for bl info and user settings



### !!!!  all the XXXByName()'s also need to take a group_id since Sample/Container/Etc names
### !!!!  are only unique per group.


def db_disconnect(collections, alias=None):
    """
    collections = list of document types from odm_templates
    """

    mongoengine.connection.disconnect(alias)

    for collection in collections:
        collection._collection = None


def db_connect():
    """
    recommended idiom:
    (mongo_conn, db_name, db_host) = db_connect()
    """

    # horrible tmp cludges instead of config :(
    # try to guess the db to use based on hostname and stuff
    
    # defaults
    db_host = '127.0.0.1'
    db_name = 'tmp_mongo_junk_from_db_lib'
    
    host = socket.gethostname()
    
    client = os.getenv('SSH_CLIENT')  # 1st check for ssh env for commandline dev work
    if not client:
        client = os.getenv('REMOTE_ADDR')  # next check web client
    else:
        client = client.split()[0]
    
    # set in test routines for disposable fixture dbs
    db_env_suffix = os.getenv('DB_LIB_SUFFIX')
    if db_env_suffix:
        db_suffix = db_env_suffix
    else:
        db_suffix = "_mongo"
    
    if host == 'fluke.nsls2.bnl.gov' or host == 'fluke' or client == '130.199.219.42':
        db_host = 'lsbr-dev'
        db_name = 'john{0}'.format(db_suffix)
    
    elif host == 'lsbr-dev.nsls2.bnl.gov' or host == 'lsbr-dev':
        if not client:  # django site
            db_name = 'matt_tmp{0}'.format(db_suffix)
            db_host = '127.0.0.1'
    
        elif client == '130.199.219.44':
            db_name = 'matt_tmp{0}'.format(db_suffix)
    
    # env vars override guesses
    db_env_name = os.getenv('DB_LIB_NAME')
    if db_env_name:
        db_name = db_env_name
    db_env_host = os.getenv('DB_LIB_HOST')
    if db_env_host:
        db_host = db_env_host
    
    
    print("---- connecting with:  mongoengine.connect({0}, host={1}) ----".format(db_name, db_host), file=sys.stderr)
    return (mongoengine.connect(db_name, host=db_host), db_name, db_host)



# connect on import for now... :(  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
(mongo_conn, db_name, db_host) = db_connect()


# should be in config :(
primaryDewarName = 'primaryDewar'


# temp stuff for web stuff

# django doesn't seem to understand generators(?), so we need to return lists here.
def find_container():
    ret_list = []

    headers = ['container_name', 'container_type', 'capacity', 'contents']

    #return [c.to_mongo() for c in Container.objects()]
    for cont in Container.objects():
        c = cont.to_mongo()
    #    cont.pop('_id')
    #    cont.pop(

        c['container_type'] = cont.container_type.name
        try:
            c['capacity'] = cont.item_list.__len__()
        except AttributeError:
            c['capacity'] = 'variable'  # indeterminate or variable capacity

        ret_list.append(c)

    return (headers, ret_list)


def find_sample():
    ret_list = []
    headers = ['sample_name', 'sample_type']

    #return [s.to_mongo() for s in Sample.objects()]
    for samp in Sample.objects():
        s = samp.to_mongo()
        s['sample_type'] = samp.sample_type.name

        ret_list.append(s)
    return (headers, ret_list)


def find_request():
    ret_list = []
    headers = ['request_name', 'request_type']

    #return [r.to_mongo() for r in Request.objects()]
    for req in Request.objects():
        r = req.to_mongo()
        r['request_type'] = req.request_type.name

        ret_list.append(r)
    return (headers, ret_list)


def find_result():
    return [r.to_mongo() for r in Result.objects()]


def find_sample_request():
    req_list = []

    for samp in Sample.objects():
        for req in samp.requestList:
            req_list.append(req.to_mongo())
            
    return req_list


def type_from_name(name, as_mongo_obj=False):
    """
    Given a type name ('standard_pin', 'shipping_dewar'), return the
    name of it's base type ('sample', 'container').
    """

    if isinstance(name, str):
        name = unicode(name)

    try:
        if as_mongo_obj:
            return Types.objects(__raw__={'name': name})[0]
        return Types.objects(__raw__={'name': name})[0].parent_type
    except IndexError:
        return None


def find_base_type(obj_type):
    """
    recurse throught the type heirarchy to find the base type
    """

#    print('{0}'.format(obj_type, file=sys.stderr))

    parent = type_from_name(obj_type)
    if not parent:
              return None
    if parent == 'base':
            return obj_type

    else:
        return find_base_type(parent)


def constructor_from_name(name):
    """
    create a constructor for the right type of object using find_base_type
    so we can save items from a spreadsheet by figuring out what they are
    """



def _try0_dict_key(query_set, obj_type_str, search_key_str, search_key_val,
                   def_retval, dict_key):
    """
    Try to get the specified key from the first ([0]th) item from a QuerySet.
    Return a default return value if there are no entries in the QuerySet.
    """

    try:
        return query_set.only(dict_key)[0].to_mongo()[dict_key]

    except IndexError:
        #raise ValueError('failed to find {obj} with {attr}={val} and attr "{dk}"'.format(
        #        obj=obj_type_str, attr=search_key_str, val=search_key_val, dk=dict_key))
        return def_retval

    except KeyError:
        raise ValueError('found {obj} with {attr}={val} but no attr "{dk}"'.format(
                obj=obj_type_str, attr=search_key_str, val=search_key_val, dk=dict_key))


def _try0_maybe_mongo(query_set, obj_type_str, search_key_str, search_key_val,
                   def_retval, as_mongo_obj=False):
    """
    Try to get the the first ([0]th) item from a QuerySet,
    converted to a dictionary by default, as the raw mongo object if specified.
    Return a default return value if there are no entries in the QuerySet.
    """

    if as_mongo_obj:
        try:
            return query_set[0]
        except IndexError:
            #raise ValueError('failed to find {obj} with {attr}={val}'.format(
            #        obj=obj_type_str, attr=search_key_str, val=search_key_val))
            return def_retval

    try:
        return query_set[0].to_mongo()

    except IndexError:
        #raise ValueError('failed to find {obj} with {attr}={val}'.format(
        #        obj=obj_type_str, attr=search_key_str, val=search_key_val))
        return def_retval

    # hrm... .first returns the first or None, slower
    # [0] returns the first or raises IndexError, fastest
    # .get() returns the only or raises DoesNotExist or MultipleObjectsReturned, slowest
    

def createContainer(container_name, container_type, **kwargs):
    """
    container_name:  string, name for the new container, required
    container_type:  required, either:
                     - string, name for existing type in Types collection, or
                     - mongo type object for existing type in Types collection
    kwargs:          passed to constructor
    """

    kwargs['containerName'] = container_name

    if isinstance(container_type, unicode) or isinstance(container_type, str):
        kwargs['container_type'] = type_from_name(container_type, as_mongo_obj=True)
    else:
        kwargs['container_type'] = container_type  # this seems weird?

    print('container_type t({0}) v({1})'.format(type(container_type), container_type), file=sys.stderr)

    #try:
    #    kwargs['container_type'] = Types.objects(__raw__={'name': type_name})[0]
    #except IndexError:
    #    raise ValueError('no container type found matching "{0}"'.format(type_name))

    try:
        kwargs['item_list'] = [None] * kwargs['container_type'].capacity
        print("capacity = {0}: {1}".format(kwargs['container_type'].capacity, kwargs['item_list']))
    except AttributeError:
        # not all containers have a fixed capacity, eg. shipping dewar.
        # depends on what subcontainers are used...
        print("no capacity")

#    kwargs['item_list'] = []

    c = Container(**kwargs)
    c.save()

    return c.container_id


def createSample(sample_name, sample_type, **kwargs):
    """
    sample_name:  string, name for the new sample, required
    sample_type:  required, either:
                  - string, name for existing type in Types collection, or
                  - mongo type object for existing type in Types collection
    kwargs:       passed to constructor
    """
    kwargs['sampleName'] = sample_name
    kwargs['requestList'] = []
    kwargs['resultList'] = []

    # initialize request count to zero
    if not kwargs.has_key('request_count'):
        kwargs['request_count'] = 0

    if isinstance(sample_type, unicode) or isinstance(sample_type, str):
        kwargs['sample_type'] = type_from_name(sample_type, as_mongo_obj=True)

#    try:
#        kwargs['sample_type'] = Types.objects(__raw__={'name': type_name})[0]
#    except IndexError:
#        raise ValueError('no sample type found matching "{0}"'.format(type_name))

    s = Sample(**kwargs)
    s.save()

    return s.sample_id


def incrementSampleRequestCount(sample_id):
    """
    increment the 'request_count' attribute of the specified sample by 1
    """
    
    # potential for race here?
    s = Sample.objects(__raw__={'sample_id': sample_id})[0]
    s.update(inc__request_count=1)
    s.reload()
    return s.request_count


def getSampleRequestCount(sample_id):
    """
    get the 'request_count' attribute of the specified sample
    """
    
    s = Sample.objects(__raw__={'sample_id': sample_id})
    return _try0_dict_key(s, 'sample', 'sample_id', sample_id, None, 
                           dict_key='request_count')


def getRequestsBySampleID(sample_id):
    """
    return a list of request dictionaries for the given sample_id
    """
    s = getSampleByID(sample_id, as_mongo_obj=True)
    return [r.to_mongo() for r in s.requestList]


def getSampleByID(sample_id, as_mongo_obj=False):
    """
    sample_id:  required, integer
    """

    s = Sample.objects(__raw__={'sample_id': sample_id})
    return _try0_maybe_mongo(s, 'sample', 'sample_id', sample_id, None,
                             as_mongo_obj=as_mongo_obj)


#def getSampleByRef(sample_ref, as_mongo_obj=False):
#    """
#    sample_ref:  required, bson.DBRef
#    """
#
#    s = Sample.objects(__raw__={'_id': sample_ref.id})
#    return _try0_maybe_mongo(s, 'sample', 'sample _id', sample_ref.id, None,
#                             as_mongo_obj=as_mongo_obj)


# should fetch only the needed field(s)! :(

def getSampleIDbyName(sample_name):
    s = Sample.objects(__raw__={'sampleName': sample_name})
    return _try0_dict_key(s, 'sample', 'sampleName', sample_name, -99, 
                           dict_key='sample_id')


def getSampleNamebyID(sample_id):
    """
    sample_id:  required, integer
    """
    s = Sample.objects(__raw__={'sample_id': sample_id})
    return _try0_dict_key(s, 'sample', 'sample_id', sample_id, -99,
                          dict_key='sampleName')


#def getSampleNamebyRef(sample_ref):
#    """
#    sample_ref:  required, bson.DBRef
#    """
#    s = Sample.objects(__raw__={'_id': sample_ref.id})
#    return _try0_dict_key(s, 'sample', 'sample _id', sample_ref, -99,
#                          dict_key='sampleName')


def getContainerIDbyName(container_name):
    c = Container.objects(__raw__={'containerName': container_name})
    return _try0_dict_key(c, 'container', 'containerName', container_name,
                           -99, dict_key='container_id')


def getContainerNameByID(container_id):
    """
    container_id:  required, integer
    """
    c = Container.objects(__raw__={'container_id': container_id})
    return _try0_dict_key(c, 'container', 'container_id', container_id, '',
                           dict_key='containerName')


def createResult(result_type, request_id, result_obj=None, timestamp=None,
                 as_mongo_obj=False, **kwargs):
    """
    result_type:  string, Type object, or dbref, required
    request_id:   int, Request object, or dbref, required
    """

    if not isinstance(result_type, Result) and not isinstance(result_type, bson.DBRef):
        result_type = type_from_name(result_type, as_mongo_obj=True)

    if not isinstance(request_id, Request) and not isinstance(request_id, bson.DBRef):
        request_id = getRequest(request_id, as_mongo_obj=True)
        
    kwargs['result_type'] = result_type
    kwargs['request_id'] = request_id
    kwargs['timestamp'] = timestamp
    kwargs['result_obj'] = result_obj

    r = Result(**kwargs)
    r.save()

    if as_mongo_obj:
        return r
    return r.to_mongo()


def getResult(result_id, as_mongo_obj=False):
    """
    result_id:  required, int or bson.DBRef
    """

    if isinstance(result_id, bson.DBRef):
        result = Request.objects(__raw__={'_id': result_id.id})
        return _try0_maybe_mongo(result, 'result', 'result _id', result_id.id, None,
                                 as_mongo_obj=as_mongo_obj)

    else:
        result_id = int(result_id)  # do we need this cast?
        
        r = Result.objects(__raw__={'result_id': result_id})
        return _try0_maybe_mongo(result, 'result', 'result_id', result_id, None,
                                 as_mongo_obj=as_mongo_obj)


def deleteResult(result_id, get_result=False):
    """
    Takes a result_id, deletes, and optionally returns the matching result or None.
    When should we ever be doing this?

    result_id:  required, int
    """
    result_id = int(result_id)

    # delete it from any samples first
    sample_qs = Sample.objects(__raw__={'resultList.result_id': result_id})
    sample = _try0_maybe_mongo(sample_qs, 'result', 'result_id', result_id, None,
                                 as_mongo_obj=True)

    for res in sample.resultList:
        if res.result_id == result_id:
            tmp = res
            sample.resultList.remove(res)
            sample.save()

    # then directly in Results
    r = getResult(result_id, as_mongo_obj=True)
    r.delete()


def getResultsforRequest(request_id):
    """
    Takes an integer request_id  and returns a list of matching results or [].
    """
    reslist = []

    # convert int ('request_id') to ObjectID ('_id')
    if isinstance(request_id, int):
        request_id = Request.objects(__raw__={'request_id': request_id}).only('id')[0].id
    for result in Result.objects(request_id=request_id):
        reslist.append(result.to_mongo())

    return reslist


def getResultsforSample(sample_id):
    """
    Takes a sample_id and returns it's resultsList or [].
    """

    sample = Sample.objects(__raw__={'sample_id': sample_id}
                            ).only('resultList')
    return [r.to_mongo() for r in 
            _try0_maybe_mongo(sample, 'sample', 'sample_id', sample_id, None,
                             as_mongo_obj=True).resultList]


def addResultforRequest(result_type, request_id, result_obj=None, timestamp=None,
                        as_mongo_obj=False, **kwargs):

    """
    like createResult, but also adds it to the resultList of result['sample_id']
    """
    r = createResult(result_type, request_id, result_obj=result_obj, timestamp=timestamp,
                     as_mongo_obj=True, **kwargs)

    request = r.request_id

    #sample_qs = Sample.objects(__raw__={'requestList.request_id': request_id})
    #sample = _try0_maybe_mongo(sample_qs, 'request', 'request_id', request_id, None,
    #                           as_mongo_obj=True)

    try:
        sample = Sample.objects(requestList__in=[request])[0]
    except IndexError:
        return None
    
    sample.resultList.append(r)
    sample.save()

    return r.to_mongo()


def addFile(data=None, filename=None):
    """
    Put the file data into the GenericFile collection,
    return the _id for use as an id or ReferenceField.

    If a filename kwarg is given, read data from the file.
    If a data kwarg is given or data is the 1st arg, store the data.
    If both or neither is given, raise an error.
    """

    if filename is not None:
        if data is not None:
            raise ValueError('both filename and data kwargs given.  can only use one.')
        else:
            with open(filename, 'r') as file:  # do we need 'b' for binary?
                data = file.read()  # is this blocking?  might not always get everything at once?!

    elif data is None:
        raise ValueError('neither filename or data kwargs given.  need one.')

    f = GenericFile(data=data)
    f.save()
    f.reload()  # to fetch generated id
    return f.id  # is this supposed to be 'id' or '_id'?
#    return f._id  # is this supposed to be 'id' or '_id'?


def getFile(_id):
    """
    Retrieve the data from the GenericFile collection
    for the given _id.

    Returns the data in Binary.  If you know it's a txt file and want a string,
    convert with str()

    Maybe this will be automatically deref'd most of the time?
    Only if they're mongoengine ReferenceFields...
    """

    f = GenericFile.objects(__raw__={'_id': _id})  # yes it's '_id' here but just 'id' below, gofigure
    return _try0_dict_key(f, 'file', 'id', _id, None,
                           dict_key='data')

def createRequest(request_type, request_obj=None, timestamp=None, as_mongo_obj=False, **kwargs):
    """
    request_type:  required, name (string) of request type, dbref to it's db entry, or a Type object
    request_obj:  optional, stored as is, could be a dict of collection parameters, or whatever
    timestamp:  datetime.datetime.now() if not provided
    priority:  optional, integer priority level

    anything else (priority, sample_id) can either be embedded in the
    request_object or passed in as keyword args to get saved at the
    top level.
    """
    if isinstance(request_type, unicode) or isinstance(request_type, str):
        request_type = type_from_name(request_type, as_mongo_obj=True)
        print('rt:[{0}]'.format(request_type))
#    elif not isinstance(request_type, Request):
#        raise ValueError('wrong type {0}'.format(request_type.__class__))

    kwargs['request_type'] = request_type
    kwargs['timestamp'] = timestamp
    kwargs['request_obj'] = request_obj

    r = Request(**kwargs)
    r.save()

    if as_mongo_obj:
        return r
    return r.to_mongo()


def addRequesttoSample(sample_id, request_type, request_obj=None, timestamp=None,
                       as_mongo_obj=False, **kwargs):
    """
    sample_id:  required, integer sample id
    request_type:  required, name (string) of request type, dbref to it's db entry, or a Type object
    request_obj:  optional, stored as is, could be a dict of collection parameters, or whatever
    timestamp:  datetime.datetime.now() if not provided

    anything else (priority, sample_id) can either be embedded in the
    request_object or passed in as keyword args to get saved at the
    top level.
    """

    kwargs['sample_id'] = sample_id
    r = createRequest(request_type, request_obj=request_obj, timestamp=timestamp,
                      as_mongo_obj=True, **kwargs)

    s = getSampleByID(sample_id, as_mongo_obj=True)
    #s.save(push__requestList=r)
    s.requestList.append(r)
    s.save()
    if as_mongo_obj:
            return r
    return r.to_mongo()


def insertIntoContainer(container_name, position, itemID):
    c = getContainerByName(container_name, as_mongo_obj=True)
    if c is not None:
        c.item_list[position - 1] = itemID  # most people don't zero index things
        c.save()
        return True
    else:
        print("bad container name")
        return False


def _ret_list(objects, as_mongo_obj=False):
    """helper function to get a list of objects as either dicts or mongo objects"""

    if as_mongo_obj:
        return list(objects)
    else:
        return [obj.to_mongo() for obj in objects]


def getContainers(as_mongo_obj=False): 
    """get *all* containers""" 

    c = Container.objects()
    return _ret_list(c, as_mongo_obj=as_mongo_obj)


def getContainersByType(type_name, group_name, as_mongo_obj=False): 

    if isinstance(type_name, unicode) or isinstance(type_name, str):
        type_obj = type_from_name(type_name, as_mongo_obj=True)
    else:
        type_obj = type_name

    # go one level deaper for now?  maybe we should have another field to search on
    # "class" or something?  :(
    container_types = Types.objects(__raw__={'$or': [{'name': type_name},
                                                     {'parent_type': type_name}]})

    #c = Container.objects(container_type=type_obj)
    #c = Container.objects(__raw__={'container_type': {'$in': container_types}})
    c = Container.objects(container_type__in=container_types)
    return _ret_list(c, as_mongo_obj=as_mongo_obj)


def getAllPucks(as_mongo_obj=False):
    # find all the types desended from 'puck'?
    # and then we could do this?
    return getContainersByType("puck", "", as_mongo_obj=as_mongo_obj)
    


def getPrimaryDewar(as_mongo_obj=False):
    """
    returns the mongo object for a container with a name matching
    the global variable 'primaryDewarName'
    """

    return getContainerByName(primaryDewarName, as_mongo_obj=as_mongo_obj)


def getContainerByName(container_name, as_mongo_obj=False): 
    c = Container.objects(__raw__={'containerName': container_name})
    return _try0_maybe_mongo(c, 'container', 'containerName', container_name,
                           None, as_mongo_obj=as_mongo_obj)


def getContainerByID(container_id, as_mongo_obj=False): 
    c = Container.objects(__raw__={'container_id': container_id})
    return _try0_maybe_mongo(c, 'container', 'container_id', container_id,
                           None, as_mongo_obj=as_mongo_obj)


#stuff I forgot - alignment type?, what about some sort of s.sample lock?,


def getQueueFast():
    requests = Request.objects(sample_id__exists=True)

#    return [request.to_mongo() for request in requests]
    # generator seems slightly faster even when wrapped by list()
    for request in requests:
        yield request.to_mongo()


def getQueue():
    """
    returns a list of request dicts for all the samples in the container
    named by the global variable 'primaryDewarName'
    """
    
    # seems like this would be alot simpler if it weren't for the Nones?

    ret_list = []

    # try to only retrieve what we need...
    # Use .first() instead of [0] here because when the query returns nothing,
    # .first() returns None while [0] generates an IndexError
    # Nah... [0] is faster and catch Exception...
    try:
        items = Container.objects(__raw__={'containerName': primaryDewarName}).only('item_list')[0].item_list
    except IndexError, AttributeError:
        raise ValueError('could not find container: "{0}"!'.format(primaryDewarName))
    
    items = set(items)
    items.discard(None)  # skip empty positions

    sample_list = []
    for samp in Container.objects(container_id__in=items).only('item_list'):
        sil = set(samp.item_list)
        sil.discard(None)
        sample_list += sil

    for request in Request.objects(sample_id__in=sample_list):
        yield request.to_mongo()

#    
##    for item_id in items.item_list:
##        if item_id is not None:
#    for item_id in items:
#            try:
#                puck_items = Container.objects(__raw__={'container_id': item_id}).only('item_list')[0].item_list
#            except IndexError, AttributeError:
#                raise ValueError('could not find container id: "{0}"!'.format(item_id))
#
#            puck_items = set(puck_items)
#            puck_items.discard(None)  # skip empty positions
#            
##            for sample_id in puck.item_list:
##                if sample_id is not None:
#            for sample_id in puck_items:
#                    #print("sample ID = " + str(sample_id))
#                    # If we don't request sample_id it gets set to the next id in the sequence!?
#                    # maybe that doesn't matter if we don't use or return it?
#                    try:
#                        sampleObj = Sample.objects(__raw__={'sample_id': sample_id}).only('requestList','sample_id')[0]
#                    except IndexError:
#                        raise ValueError('could not find sample id: "{0}"!'.format(sample_id))
#
#                    try:
#                        for request in sampleObj.requestList:
#                            try:
#                                # testing shows generator version is the same speed?
#                                #yield request.to_mongo()
#                                ret_list.append(request.to_mongo())
#                            except AttributeError:
#                                pass
#                    except TypeError:
#                        print(sampleObj.to_mongo())
#
#   return ret_list


def getDewarPosfromSampleID(sample_id):

    """
    returns the container_id and position in that container for a sample with the given id
    in one of the containers in the container named by the global variable 'primaryDewarName'
    """
    try:
        cont = Container.objects(__raw__={'containerName': primaryDewarName}).only('item_list')[0]
    except IndexError:
        return None

    for puck_id in cont.item_list:
        if puck_id is not None:
            try:
                puck = Container.objects(__raw__={'container_id': puck_id}).only('item_list')[0]
            except IndexError:
                continue

            for j,samp_id in enumerate(puck.item_list):
                if samp_id == sample_id and samp_id is not None:
                    containerID = puck_id
                    position = j + 1  # most people don't zero index things
                    return (containerID, position)    


#def getCoordsfromSampleID(sample_id):
#    """
#    returns the container position within the dewar and position in
#    that container for a sample with the given id in one of the
#    containers in the container named by the global variable
#    'primaryDewarName'
#    """
#    try:
#        cont = Container.objects(__raw__={'containerName': primaryDewarName}).only('item_list')[0]
#    except IndexError:
#        return None
#
#    for i,puck_id in enumerate(cont.item_list):
#        if puck_id is not None:
#            puck = getContainerByID(puck_id)
#            sampleList = puck["item_list"]
#
#            for j,samp_id in enumerate(sampleList):
#                if samp_id == sample_id and samp_id is not None:
#                    return (i, j, puck_id)

# In [133]: %timeit dl.getCoordsfromSampleID(24006)
# 10 loops, best of 3: 26.8 ms per loop
# 
# In [134]: %timeit dl.getOrderedRequestList()
# 1 loops, best of 3: 1.06 s per loop
# 
# In [135]: dl.getCoordsfromSampleID(24006)
# Out[135]: (17, 13, 11585)

def getCoordsfromSampleID(sample_id):
    """
    returns the container position within the dewar and position in
    that container for a sample with the given id in one of the
    containers in the container named by the global variable
    'primaryDewarName'
    """
    try:
        primary_dewar_item_list = Container.objects(__raw__={'containerName': primaryDewarName}).only('item_list')[0].item_list
    except IndexError, AttributeError:
        return None

    # eliminate empty item_list slots
    pdil_set = set(primary_dewar_item_list)
    pdil_set.discard(None)
    
    # find container in the primary_dewar_item_list (pdil) which has the sample
    c = Container.objects(container_id__in=pdil_set, item_list__all=[sample_id])[0]

    # get the index of the found container in the primary dewar
    i = primary_dewar_item_list.index(c.container_id)

    # get the index of the sample in the found container item_list
    j = c.item_list.index(sample_id)

    # get the container_id of the found container
    puck_id = c.container_id

    return (i, j, puck_id)

# In [116]: %timeit dl.getCoordsfromSampleID(24006)
# 100 loops, best of 3: 3.16 ms per loop
# 
# In [117]: %timeit dl.getOrderedRequestList()
# 1 loops, best of 3: 1.06 s per loop
# 
# In [118]: dl.getCoordsfromSampleID(24006)
# Out[118]: (17, 13, 11585)


def getSampleIDfromCoords(puck_num, position):
    """
    given a container position within the dewar and position in
    that container, returns the id for a sample in one of the
    containers in the container named by the global variable
    'primaryDewarName'
    """
    try:
        cont = Container.objects(__raw__={'containerName': primaryDewarName}).only('item_list')[0]
    except IndexError:
        return None

    puck_id = cont.item_list[puck_num]
    puck = getContainerByID(puck_id)
            
    sample_id = puck["item_list"][position - 1]  # most people don't zero index things
    return sample_id


def popNextRequest():
    # is this more 'getNextRequest'? where's the 'pop'?
    orderedRequests = getOrderedRequestList()
    try:
        if (orderedRequests[0]["priority"] != 99999):
            if orderedRequests[0]["priority"] > 0:
                return orderedRequests[0]
            else: #99999 priority means it's running, try next
                if orderedRequests[1]["priority"] > 0:
                    return orderedRequests[1]
    except IndexError:
        pass

    return {}


def getRequest(reqID, as_mongo_obj=False):  # need to get this from searching the dewar I guess
    reqID = int(reqID)
    """
    request_id:  required, integer id
    """
    r = Request.objects(__raw__={'request_id': reqID})
    return _try0_maybe_mongo(r, 'request', 'request_id', reqID, None,
                             as_mongo_obj=as_mongo_obj)


# this is really "update_sample" because the request is stored with the sample.

def updateRequest(request_dict):
    """
    This is not recommended once results are recorded for a request!
    Using a new request instead would keep the apparent history
    complete and intuitive.  Although it won't hurt anything if you've
    also recorded the request params used inside the results and query
    against that, making requests basically ephemerally useful objects.
    """

    if not Request.objects(__raw__={'request_id': request_dict['request_id']}).update(
        set__request_obj=request_dict['request_obj']):
        
        addRequesttoSample(**request_dict)


def deleteRequest(reqObj):
    """
    reqObj should be a dictionary with a 'request_id' field
    and optionally a 'sample_id' field.

    If the request to be deleted is the last entry in a sample's
    requestList, the list attribute is removed entirely, not just set
    to an empty list!

    The request_id attribute for any results which references the deleted request
    are also entirely removed, not just set to None!

    This seems to be the way wither mongo, pymongo, or mongoengine works :(
    """

    r_id = reqObj['request_id']

    # delete it from any sample first
    try:
        sample = getSampleByID(reqObj['sample_id'], as_mongo_obj=True)
    
        # maybe there's a slicker way to get the req with a query and remove it?
        for req in sample.requestList:
            if req.request_id == r_id:
                print("found the request to delete")
                sample.requestList.remove(req)
                sample.save()
                break

    except KeyError:
        pass  # not all requests are linked to samples

    # then any results that refer to it
    req = Request.objects(__raw__={'request_id': r_id}).only('id')[0].id
    for res in Result.objects(request_id=req):
        res.request_id = None
        res.save()

    # then finally directly in Requests
    r = getRequest(r_id, as_mongo_obj=True)
    if r:
        r.delete()


def deleteSample(sampleObj):
    s = getSampleByID(sampleObj["sample_id"], as_mongo_obj=True)
    s.delete()


def removePuckFromDewar(dewarPos):
    dewar = getPrimaryDewar(as_mongo_obj=True)
    dewar.item_list[dewarPos] = None
    dewar.save()


def updatePriority(request_id, priority):
    r = getRequest(request_id, as_mongo_obj=True)
    r.priority = priority
    r.save()


def emptyLiveQueue(): #a convenience to say nothing is ready to be run
    for request in getQueue():
        updatePriority(request['request_id'], priority)


def getPriorityMap():
    """
    returns a dictionary with priorities as keys and lists of requests
    having those priorities as values
    """

    priority_map = {}

    for request in getQueue():
        try:
            priority_map[request['priority']].append(request)

        except KeyError:
            priority_map[request['priority']] = [request]

    return priority_map
    

def getOrderedRequestList():
#def getOrderedRequests():
    """
    returns a generator of requests sorted by priority
    """

    orderedRequestsList = []

    priority_map = getPriorityMap()

    for priority in sorted(six.iterkeys(priority_map), reverse=True):
        orderedRequestsList += priority_map[priority]
        #for request in priority_map[priority]:
        #    yield request

    return orderedRequestsList


def beamlineInfo(beamline_id, info_name, info_dict=None):
    """
    to write info:  beamlineInfo('x25', 'det', info_dict={'vendor':'adsc','model':'q315r'})
    to fetch info:  info = beamlineInfo('x25', 'det')
    """

    # if it exists it's a query or update
    try:
        bli = BeamlineInfo.objects(__raw__={'beamline_id': beamline_id,
                                            'info_name': info_name})[0]

        if info_dict is None:  # this is a query
            return bli.info

        # else it's an update
        bli.update(set__info=info_dict)

    # else it's a create
    except IndexError:
        BeamlineInfo(beamline_id=beamline_id, info_name=info_name, info=info_dict).save()


def userSettings(user_id, settings_name, settings_dict=None):
    """
    to write settings:  userSettings('matt', 'numbers', info_dict={'phone':'123','fax':'456'})
    to fetch settings:  settings = userSettings('matt', 'numbers')
    """

    # if it exists it's a query or update
    try:
        uset = UserSettings.objects(__raw__={'user_id': user_id,
                                             'settings_name': settings_name})[0]

        if settings_dict is None:  # this is a query
            return uset.settings

        # else it's an update
        uset.update(set__settings=settings_dict)

    # else it's a create
    except IndexError:
        UserSettings(user_id=user_id, settings_name=settings_name, settings=settings_dict).save()


def createField(name, description, bson_type, default_value=None,
                validation_routine_name=None, **kwargs):
    """
    all params are strings except default_value, which might or might not be a string
    depending on the type
    """

    f = Field(name=name, description=description, bson_type=bson_type,
              default_value=default_value, validation_routine_name=validation_routine_name,
              **kwargs)
    f.save()


def createType(name, desc, parent_type, field_list=None, **kwargs):
    """
    name must be a unique string
    parent_type must be either, 'base', or an existing type_name
    field_list is a list of Field objects.
    """

    t = Types(name=name, description=desc, parent_type=parent_type, **kwargs)
    t.save()


