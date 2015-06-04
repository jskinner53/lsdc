#!/usr/bin/python
import time
import uuid
import functools
import itertools
import os
import socket
import mongoengine as mongo

from odm_templates import (Sample, Container, Raster, Request)



### !!!!  all the XXXByName()'s also need to take a group_id since Sample/Container/Etc names
### !!!!  are only unique per group.



# tmp cludges instead of config :(

# defaults
db_host = '127.0.0.1'
db_name = 'tmp_mongo_junk_from_db_lib'

host = socket.gethostname()
client = os.getenv('SSH_CLIENT')

if host == 'fluke.nsls2.bnl.gov' or host == 'fluke':
    db_host = 'lsbr-dev'
    #if not client:
    db_name = 'john_mongo'

elif host == 'gisele.nsls2.bnl.gov' or host == 'gisele':
    if not client:
        db_name = 'matt_tmp_mongo'

if client:
    client = client.split()[0]

    if client == '130.199.219.44':
        db_name = 'matt_tmp_mongo'

    elif client == '130.199.219.42':
        db_name = 'john_mongo'


#print "---- [{0},{1}] mongo.connect({2}, host={3}) ----".format(host, client, db_name, db_host)
print "---- connecting with:  mongo.connect({0}, host={1}) ----".format(db_name, db_host)
mongo_conn = mongo.connect(db_name, host=db_host)


primaryDewarName = 'primaryDewar2'


def createContainer(container_name, type_name, capacity):
    containerObj = {"containerName": container_name,
                    "type_name": type_name,
                    "item_list": [None] * capacity}

    c = Container(**containerObj)
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
#        print "drawing " 
#        print retRaster

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
        rast = Raster.objects(status=1)[0]
    except IndexError:
        return None

    retRaster = (0, rast.to_mongo())
    rast.status = 2
    rast.save()
    return retRaster
    



def createSample(sampleName):
    sampleObj = {"sampleName": sampleName, "requestList": []}

    s = Sample(**sampleObj)
    s.save()

    return s.sample_id


def _try0_dict_key(query_set, obj_type_str, search_key_str, search_key_val,
                   def_retval, dict_key):
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
    s = Sample.objects(sample_id=sample_id)
    return _try0_maybe_mongo(s, 'sample', 'sample_id', sample_id, None,
                           as_mongo_obj=as_mongo_obj)


# should fetch only the needed field(s)! :(

def getSampleIDbyName(sample_name):
    s = Sample.objects(sampleName=sample_name)
    return _try0_dict_key(s, 'sample', 'sampleName', sample_name, -99, 
                           dict_key='sample_id')


def getSampleNamebyID(sample_id):
    s = Sample.objects(sample_id=sample_id)
    return _try0_dict_key(s, 'sample', 'sample_id', sample_id, -99,
                           dict_key='sampleName')


def getContainerIDbyName(container_name):
    c = Container.objects(containerName=container_name)
    return _try0_dict_key(c, 'container', 'containerName', container_name,
                           -99, dict_key='container_id')


def getContainerNameByID(container_id):
    c = Container.objects(container_id=container_id)
    return _try0_dict_key(c, 'container', 'container_id', container_id, '',
                           dict_key='containerName')


def addRequesttoSample(sample_id, request):
    r = Request(**request)

    s = getSampleByID(sample_id, as_mongo_obj=True)
    #s.save(push__requestList=r)
    s.requestList.append(r)
    s.save()
    return r.to_mongo()


def createDefaultRequest(sample_id):
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
    else:
        print "bad container name"


def _ret_list(objects, as_mongo_obj=False):
    if as_mongo_obj:
        return list(objects)
    else:
        return [obj.to_mongo() for obj in objects]


def getContainers(as_mongo_obj=False): 
    c = Container.objects()
    return _ret_list(c, as_mongo_obj=as_mongo_obj)


def getContainersByType(type_name, group_name, as_mongo_obj=False): 
    c = Container.objects(type_name=type_name)
    return _ret_list(c, as_mongo_obj=as_mongo_obj)


def getAllPucks(as_mongo_obj=False):
    return getContainersByType("puck", "", as_mongo_obj=as_mongo_obj)


def getPrimaryDewar(as_mongo_obj=False):
    return getContainerByName(primaryDewarName, as_mongo_obj=as_mongo_obj)


def getContainerByName(container_name, as_mongo_obj=False): 
    c = Container.objects(containerName=container_name)
    return _try0_maybe_mongo(c, 'container', 'containerName', container_name,
                           None, as_mongo_obj=as_mongo_obj)


def getContainerByID(container_id, as_mongo_obj=False): 
    c = Container.objects(container_id=container_id)
    return _try0_maybe_mongo(c, 'container', 'container_id', container_id,
                           None, as_mongo_obj=as_mongo_obj)


#stuff I forgot - alignment type?, what about some sort of s.sample lock?,


def insertCollectionRequest(sample_id, sweep_start, sweep_end, img_width, exposure_time,
                            priority, protocol, directory, file_prefix, file_number_start,
                            wavelength, resolution, slit_height, slit_width, attenuation,
                            pos_x, pos_y, pos_z, pos_type, gridW, gridH, gridStep):

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
    # seems like this would be alot simpler if it weren't for the Nones?

    ret_list = []

    # try to only retrieve what we need...
    # Use .first() instead of [0] here because when the query returns nothing,
    # .first() returns None while [0] generates an IndexError
    # Nah... [0] is faster and catch Exception...
    try:
        items = Container.objects(containerName=primaryDewarName).only('item_list')[0]
    except IndexError:
        raise ValueError('could not find container: "{0}"!'.format(primaryDewarName))

    for item_id in items.item_list:
        if item_id is not None:
            try:
                puck = Container.objects(container_id=item_id).only('item_list')[0]
            except IndexError:
                raise ValueError('could not find container id: "{0}"!'.format(item_id))

            for sample_id in puck.item_list:
                if sample_id is not None:
                    #print "sample ID = " + str(sample_id)
                    # If we don't request sample_id it gets set to the next id in the sequence!?
                    # maybe that doesn't matter if we don't use or return it?
                    try:
                        sampleObj = Sample.objects(sample_id=sample_id).only('requestList','sample_id')[0]
                    except IndexError:
                        raise ValueError('could not find sample id: "{0}"!'.format(sample_id))

#                    # stick this in try/except too....
#                    if sampleObj.requestList is None:
#                        print sampleObj.to_mongo()
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
                        print sampleObj.to_mongo()

    return ret_list


def getDewarPosfromSampleID(sample_id):
    try:
        cont = Container.objects(containerName=primaryDewarName).only('item_list')[0]
    except IndexError:
        return None

    for puck_id in cont.item_list:
        if puck_id is not None:
            try:
                puck = Container.objects(container_id=puck_id).only('item_list')[0]
            except IndexError:
                continue

            for j,samp_id in enumerate(puck.item_list):
                if samp_id == sample_id and samp_id is not None:
                    containerID = puck_id
                    position = j
                    return (containerID, position)    


def getAbsoluteDewarPosfromSampleID(sample_id):
    try:
        cont = Container.objects(containerName=primaryDewarName).only('item_list')[0]
    except IndexError:
        return None

    for i,puck_id in enumerate(cont.item_list):
        if puck_id is not None:
            puck = getContainerByID(puck_id)
            sampleList = puck["item_list"]
            puckCapacity = len(sampleList)  # would be more efficient to have a capacity field

            for j,samp_id in enumerate(sampleList):
                if samp_id == sample_id and samp_id is not None:
                    absPosition = (i*puckCapacity) + j
                    return absPosition


def getCoordsfromSampleID(sample_id):
    try:
        cont = Container.objects(containerName=primaryDewarName).only('item_list')[0]
    except IndexError:
        return None

    for i,puck_id in enumerate(cont.item_list):
        if puck_id is not None:
            puck = getContainerByID(puck_id)
            sampleList = puck["item_list"]

            for j,samp_id in enumerate(sampleList):
                if samp_id == sample_id and samp_id is not None:
                    return (i, j)


def getSampleIDfromAbsoluteDewarPos(abs_pos):
    # try/except is faster than checking for an empty list before 
    # indexing into it!
    try:
        pd = Container.objects(containerName=primaryDewarName).only('item_list')[0]
    except IndexError:
        raise IndexError('Failed to find container named: "{0}"'.format(primaryDewarName))

    # get puck capacity from the 1st puck we find
    # This is wonky, need to totally rethink the idea of absolute position.
    for i,puck_id in enumerate(pd.item_list):
        if puck_id is not None:
            #puck = getContainerByID(puck_id)
            try:
                puck = Container.objects(container_id=puck_id).only('item_list')[0]
            except IndexError:
                raise IndexError('Failed to find container_id: "{0}"'.format(puck_id))

            puck_capacity = len(puck.item_list)
            break

    # get puck# and position from absolute position
    (puck_num, position) = divmod(abs_pos, puck_capacity)

    # use puck# and position to get the sample_id
    puck_id = pd.item_list[puck_num]
    try:
        puck = Container.objects(container_id=puck_id).only('item_list')[0]
    except IndexError:
        if puck_id is None:
            raise ValueError('no puck in position {0} in primary dewar!'.format(puck_num))
        raise IndexError('Failed to get puck id {0}.'.format(puck_id))

    return puck.item_list[position]


def popNextRequest():
    orderedRequests = getOrderedRequestList()
    if orderedRequests != [] and orderedRequests[0]["priority"] > 0:
        return orderedRequests[0]
    else:
        return {}


def getRequest(reqID):  # need to get this from searching the dewar I guess
    r_id = int(reqID)

    # It's faster to get the mongo obj and only .to_mongo() convert the 
    # desired request then the opposite.
    # Maybe with mongov9 a query can return only a specific list entry?
    sample = Sample.objects(requestList__request_id=reqID).only('requestList')
    req_list = _try0_maybe_mongo(sample, 'request', 'request_id', reqID, None,
                               as_mongo_obj=True).requestList
    
    for req in req_list:
        if req.request_id == r_id:
            return req.to_mongo()
    return None


# getAllSamples and update{Sample,Container} aren't used at the moment...
    
#def getAllSamples():
#    return [s.to_mongo() for s in Sample.objects()]


#def updateSample(sampleObj):
#    samp_id = sampleObj['sample_id']
#
#    updated_samp = Sample(**sampleObj)
#    updated_samp.sample_id = samp_id
#    Sample.objects(sample_id=samp_id).update(updated_samp)
    

#def updateContainer(containerObj):
#    cont_id = containerObj['container_id']
#
#    updated_cont = Container(**containerObj)
#    updated_cont.container_id = cont_id
#    Container.objects(container_id=cont_id).update(updated_cont)
    

# this is really "update_sample" because the request is stored with the sample.

def updateRequest(reqObj):
    sample = getSampleByID(reqObj["sample_id"], as_mongo_obj=True)

    for req in sample.requestList:
        #if req is not None:  # when would it ever be None?
        try:
            req_id = req.request_id
        except AttributeError:
            continue

        try:
            if reqObj["request_id"] == req.request_id:
                updated_req = Request(**reqObj)
                updated_req.request_id = req.request_id
    
                Sample.objects(requestList__request_id=req.request_id
                               ).update(set__requestList__S=updated_req)
                return
        except KeyError:
            pass

    addRequesttoSample(reqObj["sample_id"], reqObj)


def deleteRequest(reqObj):
    sample = getSampleByID(reqObj['sample_id'], as_mongo_obj=True)
    r_id = reqObj['request_id']

    # maybe there's a slicker way to get the req with a query and remove it?
    for req in sample.requestList:
        if req.request_id == r_id:
            print "found the request to delete"
            sample.requestList.remove(req)
            sample.save()
            break


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
    pList = []
    requests = getQueue()

    for request in requests:
        if request["priority"] not in pList:
            pList.append(request["priority"])

    if with_requests:
        return sorted(pList, reverse=True), requests
    return sorted(pList, reverse=True)


def getOrderedRequestList():
    orderedRequestsList = []

    (priorities, requests) = getSortedPriorityList(with_requests=True)

    for priority in priorities:  # just sorts priorities 
        for request in requests:
            if request["priority"] == priority:
                orderedRequestsList.append(request)

    return orderedRequestsList
