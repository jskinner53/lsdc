#!/usr/bin/python
from __future__ import (absolute_import, print_function)

import sys
import os
import socket

import mongoengine 
from  mongoengine import NotUniqueError


from .odm_templates import (Sample, Container, Raster, Request, Result,
                           GenericFile, Types, Field)
from .odm_templates import (BeamlineInfo, UserSettings)   # for bl info and user settings



### !!!!  all the XXXByName()'s also need to take a group_id since Sample/Container/Etc names
### !!!!  are only unique per group.


def db_disconnect(collections, alias=None):
    """stolen from metadatastore
    """

    mongoengine.connection.disconnect(alias)

    for collection in collections:
        collection._collection = None


def db_connect():
    """
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


# connect on import for now... :(
(mongo_conn, db_name, db_host) = db_connect()

primaryDewarName = 'primaryDewar2'


# temp stuff for web stuff

# django doesn't seem to understand generators(?), so we need to return lists here.
def find_container():
    return [c.to_mongo() for c in Container.objects()]
    #for cont in Container.objects():
    #    cont = cont.to_mongo()
    #    cont.pop('_id')
    #    cont.pop(

def find_sample():
    return [s.to_mongo() for s in Sample.objects()]

def find_request():
    return [r.to_mongo() for r in Request.objects()]

def find_result():
    return [r.to_mongo() for r in Result.objects()]

def find_sample_request():
    req_list = []

    for samp in Sample.objects():
        for req in samp.requestList:
            req_list.append(req.to_mongo())
            
    return req_list


def createContainer(container_name, type_name, **kwargs):

    kwargs['containerName'] = container_name

    try:
        kwargs['container_type'] = Types.objects(__raw__={'name': type_name})[0]
    except IndexError:
        raise ValueError('no container type found matching "{0}"'.format(type_name))

    try:
        kwargs['item_list'] = [None] * kwargs['container_type'].capacity
    except AttributeError:
        pass  # not all containers have a fixed capacity, eg. shipping dewar.
              # depends on what subcontainers are used...

    c = Container(**kwargs)
    c.save()

    return c.container_id


def getRasters(as_mongo_obj=False):
    if as_mongo_obj:
        return Raster.objects()

    return [r.to_mongo() for r in Raster.objects()]


def addRaster(rasterDefObj):
    r = Raster(**rasterDefObj)
    r.save()

    return r.raster_id


def clearRasters():
    Raster.drop_collection()


def getNextRunRaster(updateFlag=1):
    try:
        rast = Raster.objects(status=0)[0]
    except IndexError:
        return None

    retRaster = rast.to_mongo()
    if updateFlag == 1:
        rast.status = 1
        rast.save()
#    else:
#        print("drawing ") 
#        print(retRaster)

    return retRaster


def getNextDisplayRaster():
    # if getRasters() returns [] retRaster=? !
    # should it be initialized to None as in previous func?

    # Would it be better to skip the loop entirely by using .first(), and check for None?
    # What is 'i' doing?  if we were 'break'ing, we should only ever have one
    # iteration and i would *always* be 0?
#    for i,rast in enumerate(Raster.objects(status=1)):
#        retRaster = (i, rast.to_mongo())
#        rast.status = 2
#        rast.save()
#        #break  # shouldn't need this anymore?
#    return retRaster
    try:
        rast = Raster.objects(__raw__={'status': 1})[0]
    except IndexError:
        return None

    retRaster = (0, rast.to_mongo())
    rast.status = 2
    rast.save()
    return retRaster
    



def createSample(sample_name, type_name, **kwargs):
    kwargs['sampleName'] = sample_name
    kwargs['requestList'] = []
    kwargs['resultList'] = []

    try:
        kwargs['sample_type'] = Types.objects(__raw__={'name': type_name})[0]
    except IndexError:
        raise ValueError('no sample type found matching "{0}"'.format(type_name))

    s = Sample(**kwargs)
    s.save()

    return s.sample_id


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
    

def getSampleByID(sample_id, as_mongo_obj=False):
    s = Sample.objects(__raw__={'sample_id': sample_id})
    return _try0_maybe_mongo(s, 'sample', 'sample_id', sample_id, None,
                           as_mongo_obj=as_mongo_obj)


# should fetch only the needed field(s)! :(

def getSampleIDbyName(sample_name):
    s = Sample.objects(__raw__={'sampleName': sample_name})
    return _try0_dict_key(s, 'sample', 'sampleName', sample_name, -99, 
                           dict_key='sample_id')


def getSampleNamebyID(sample_id):
    s = Sample.objects(__raw__={'sample_id': sample_id})
    return _try0_dict_key(s, 'sample', 'sample_id', sample_id, -99,
                           dict_key='sampleName')


def getContainerIDbyName(container_name):
    c = Container.objects(__raw__={'containerName': container_name})
    return _try0_dict_key(c, 'container', 'containerName', container_name,
                           -99, dict_key='container_id')


def getContainerNameByID(container_id):
    c = Container.objects(__raw__={'container_id': container_id})
    return _try0_dict_key(c, 'container', 'container_id', container_id, '',
                           dict_key='containerName')


def createResult(result_type, request_id, result_obj=None, timestamp=None,
                 as_mongo_obj=False, **kwargs):

    if isinstance(result_type, str):
        result_type = type_from_name(result_type, as_mongo_obj=True)

    if not isinstance(request_id, Request):
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
    Takes a result_id and returns the matching result or None.
    """
    result_id = int(result_id)

    r = Result.objects(__raw__={'result_id': result_id})
    return _try0_maybe_mongo(result, 'result', 'result_id', result_id, None,
                             as_mongo_obj=as_mongo_obj)


def deleteResult(result_id, get_result=False):
    """
    Takes a result_id, deletes, and optionally returns the matching result or None.
    When should we ever be doing this?
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
    Takes an integer request_id or request obj and returns a list of matching results or [].

    This is not a completely intuitive relationship
    """
    reslist = []

    if not isinstance(request_id, Request):
        request_id = getRequest(result['request_id'], as_mongo_obj=True)

    for result in Results.objects(request_id=request_id):
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
    return f.id


def getFile(id):
    """
    Retrieve the data from the GenericFile collection
    for the given _id.

    Returns the data in Binary.  If you know it's a txt file and want a string,
    convert with str()

    Maybe this will be automatically deref'd most of the time?
    Only if they're mongoengine ReferenceFields...
    """

    f = GenericFile.objects(__raw__={'_id': id})  # yes it's '_id' here but just 'id' below, gofigure
    return _try0_dict_key(f, 'file', 'id', id, None,
                           dict_key='data')

def createRequest(request_type, request_obj=None, timestamp=None, as_mongo_obj=False, **kwargs):
    """
    request_type:  required, name (string) of request type, dbref to it's db entry, or a Type object
    request_obj:  optional, stored as is, could be a dict of collection parameters, or whatever
    timestamp:  datetime.datetime.now() if not provided

    anything else (priority, sample_id) can either be embedded in the
    request_object or passed in as keyword args to get saved at the
    top level.
    """
    if isinstance(request_type, str):
        request_type = type_from_name(request_type, as_mongo_obj=True)
        print('rt:[{0}]'.format(request_type))
    elif not isinstance(request_type, Request):
        raise ValueError('wrong type {0}'.format(request_type.__class__))

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
    r = createRequest(request_type, request_obj=request_obj, timestamp=timestamp,
                      as_mongo_obj=True, **kwargs)

    s = getSampleByID(sample_id, as_mongo_obj=True)
    #s.save(push__requestList=r)
    s.requestList.append(r)
    s.save()
    if as_mongo_obj:
            return r
    return r.to_mongo()


def createDefaultRequest(sample_id):
    """
    Doesn't really create a request, just returns a dictionary
    with the default parameters that can be passed to addRequesttoSample().
    """
    request = {
               "sample_id": sample_id,
               "sweep_start": 0.0,  "sweep_end": 0.1,
               "img_width": .1,
               "exposure_time": .1,
               "priority": 0,
               "protocol": "standard",
               "directory": "/",
               "file_prefix": str(getSampleNamebyID(sample_id)),
               "file_number_start": 1,
               "wavelength": 1.1,
               "resolution": 3.0,
               "slit_height": 30.0,  "slit_width": 30.0,
               "attenuation": 0,
               "pos_x": 0,  "pos_y": 0,  "pos_z": 0,  "pos_type": 'A',
               "gridW": 0,  "gridH": 0,  "gridStep": 30}

    return request


def insertIntoContainer(container_name, position, itemID):
    c = getContainerByName(container_name, as_mongo_obj=True)
    if c is not None:
        c.item_list[position] = itemID
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
    c = Container.objects(__raw__={'type_name': type_name})
    return _ret_list(c, as_mongo_obj=as_mongo_obj)


def getAllPucks(as_mongo_obj=False):
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


def insertCollectionRequest(sample_id, sweep_start, sweep_end, img_width, exposure_time,
                            priority, protocol, directory, file_prefix, file_number_start,
                            wavelength, resolution, slit_height, slit_width, attenuation,
                            pos_x, pos_y, pos_z, pos_type, gridW, gridH, gridStep):
    """adds a request to a sample"""

    colobj = {"request_id": int(time.time()), "sample_id": sample_id,
              "sweep_start": sweep_start, "sweep_end": sweep_end, "img_width": img_width,
              "exposure_time": exposure_time, "priority": priority, "protocol": protocol,
              "directory": directory, "file_prefix": file_prefix,
              "file_number_start": file_number_start, "wavelength": wavelength,
              "resolution": resolution, "slit_height": slit_height, "slit_width": slit_width,
              "attenuation": attenuation, "pos_x": pos_x, "pos_y": pos_y, "pos_z": pos_z,
              "pos_type": pos_type, "gridW": gridW, "gridH": gridH, "gridStep": gridStep}

    ######### need to insert this into the request List for the sample
    s = getSampleByID(sample_id, as_mongo_obj=True)
    s.modify(push__requestList=colobj)

#,vec_x_start,vec_y_start,vec_z_start,vec_x_end,vec_y_end,vec_z_end,vec_numframes,vec_fpp
#vec_fpp means frames per point, vec_numframes is the total. Not sure if this is the best way.

#pinpos, sweep_start, numimages, sweep_inc, exposure_time, protocol, file_prefix, file_number_start, wavelength, resolution, xtal_id,    slit_height, slit_width, attenuation,priority


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
        items = Container.objects(__raw__={'containerName': primaryDewarName}).only('item_list')[0]
    except IndexError:
        raise ValueError('could not find container: "{0}"!'.format(primaryDewarName))

    for item_id in items.item_list:
        if item_id is not None:
            try:
                puck = Container.objects(__raw__={'container_id': item_id}).only('item_list')[0]
            except IndexError:
                raise ValueError('could not find container id: "{0}"!'.format(item_id))

            for sample_id in puck.item_list:
                if sample_id is not None:
                    #print("sample ID = " + str(sample_id))
                    # If we don't request sample_id it gets set to the next id in the sequence!?
                    # maybe that doesn't matter if we don't use or return it?
                    try:
                        sampleObj = Sample.objects(__raw__={'sample_id': sample_id}).only('requestList','sample_id')[0]
                    except IndexError:
                        raise ValueError('could not find sample id: "{0}"!'.format(sample_id))

#                    # stick this in try/except too....
#                    if sampleObj.requestList is None:
#                        print(sampleObj.to_mongo())
#                    else:
#                        for request in sampleObj.requestList:
#                            if request is not None:
#                                #yield request.to_mongo()
#                                ret_list.append(request.to_mongo())

                    try:
                        for request in sampleObj.requestList:
                            try:
                                # testing shows generator version is the same speed?
                                #yield request.to_mongo()
                                ret_list.append(request.to_mongo())
                            except AttributeError:
                                pass
                    except TypeError:
                        print(sampleObj.to_mongo())

    return ret_list


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
                    position = j
                    return (containerID, position)    


def getCoordsfromSampleID(sample_id):
    """
    returns the container position within the dewar and position in
    that container for a sample with the given id in one of the
    containers in the container named by the global variable
    'primaryDewarName'
    """
    try:
        cont = Container.objects(__raw__={'containerName': primaryDewarName}).only('item_list')[0]
    except IndexError:
        return None

    for i,puck_id in enumerate(cont.item_list):
        if puck_id is not None:
            puck = getContainerByID(puck_id)
            sampleList = puck["item_list"]

            for j,samp_id in enumerate(sampleList):
                if samp_id == sample_id and samp_id is not None:
                    return (i, j,puck_id)


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
            
    sample_id = puck["item_list"][position]
    return sample_id


def popNextRequest():
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
    r_id = int(reqID)

    ## It's faster to get the mongo obj and only .to_mongo() convert the 
    ## desired request then the opposite.
    ## Maybe with mongov9 a query can return only a specific list entry?
    #sample = Sample.objects(__raw__={'requestList.request_id': reqID}).only('requestList')
    #req_list = _try0_maybe_mongo(sample, 'request', 'request_id', reqID, None,
    #                           as_mongo_obj=True).requestList
    #
    #for req in req_list:
    #    if req.request_id == r_id:
    #        if as_mongo_obj:
    #            return req
    #        return req.to_mongo()
    #return None

    r = Request.objects(__raw__={'request_id': req_id})
    return _try0_maybe_mongo(result, 'request', 'request_id', request_id, None,
                             as_mongo_obj=as_mongo_obj)


# this is really "update_sample" because the request is stored with the sample.

def _updateRequest(reqObj):
    """
    This is not recommended once results are recorded for a request!
    Using a new request instead would keep the apparent history
    complete and intuitive.  Although it won't hurt anything if you've
    also recorded the request params used inside the results and query
    against that, making requests basically ephemerally useful objects.

    Further, this only updates:  priority, timestamp, and request_obj

    Argh! this is so stupid!
    Even if mongoengine queryset.update(upsert=True) took whole documents,
    it doesn't initialize new objects like the regular constructors :(
    ... doesn't handle sequencefields (eg all the sequential int [type]_id fields)).
    Looks like the only way to replace an entire document is by falling back to pymongo.
    Could we concoct some scheme where we only do inserts, adding some 'active' field
    flagging the old version as inactive and deleting all inactive documents, but how can
    that be less error prone than a single call that does what we need?

    solution?  cop out and embed the dict we need to update in a single field
    """
    
    

    addRequesttoSample(reqObj["sample_id"], reqObj)


def deleteRequest(reqObj):
    sample = getSampleByID(reqObj['sample_id'], as_mongo_obj=True)
    r_id = reqObj['request_id']

    # delete it from any sample first
    # maybe there's a slicker way to get the req with a query and remove it?
    for req in sample.requestList:
        if req.request_id == r_id:
            print("found the request to delete")
            sample.requestList.remove(req)
            sample.save()
            break

    # then directly in Requests
    r = getRequest(r_id, as_mongo_obj=True)
    r.delete()


def deleteSample(sampleObj):
    s = getSampleByID(sampleObj["sample_id"], as_mongo_obj=True)
    s.delete()


def removePuckFromDewar(dewarPos):
    dewar = getPrimaryDewar(as_mongo_obj=True)
    dewar.item_list[dewarPos] = None
    dewar.save()
    

def emptyLiveQueue(): #a convenience to say nothing is ready to be run
    for request in getQueue():
        request["priority"] = 0
        updateRequest(request)


def getSortedPriorityList(with_requests=False): # mayb an intermediate to return a list of all priorities.
    """
    returns a sorted list of the priority levels found on requests in the database.
    optionally also returns the list of requests, since it had to get them.
    """
    pList = []
    requests = getQueue()

    for request in requests:
        if request["priority"] not in pList:
            pList.append(request["priority"])

    if with_requests:
        return sorted(pList, reverse=True), requests
    return sorted(pList, reverse=True)


def getOrderedRequestList():
    """
    returns the request list sorted by priority
    """
    orderedRequestsList = []

    (priorities, requests) = getSortedPriorityList(with_requests=True)

    for priority in priorities:  # just sorts priorities 
        for request in requests:
            if request["priority"] == priority:
                orderedRequestsList.append(request)

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

def type_from_name(name, as_mongo_obj=False):
    """
    Given a type name ('standard_pin', 'shipping_dewar'), return the
    name of it's base type ('sample', 'container').
    """
    try:
        if as_mongo_obj:
            return Types.objects(__raw__={'name': name})[0]
        return Types.objects(__raw__={'name': name})[0].parent_type
    except IndexError:
        return None


