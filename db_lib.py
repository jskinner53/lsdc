#!/usr/bin/python
import time
import uuid
import functools
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

if host == 'fluke.nsls2.bnl.gov':
    db_host = 'lsbr-dev'
    if not client:
        db_name = 'john_mongo'

elif host == 'gisele':
    if not client:
        db_name = 'matt_tmp_mongo'

if client:
    client = client.split()[0]

    if client == '130.199.219.44':
        db_name = 'matt_tmp_mongo'

    elif client == '130.199.219.42':
        db_name = 'john_mongo'


#print "---- [{0},{1}] mongo.connect({2}, host={3}) ----".format(host, client, db_name, db_host)
mongo_conn = mongo.connect(db_name, host=db_host)



def createContainer(container_name, type_name, capacity):
    containerObj = {"containerName": container_name,
                    "type_name": type_name,
                    "item_list": []}

    # the item list is a list of id's, whether they be other
    # containers or samples. This is because samples and pucks can move.
    for i in xrange(capacity):
        containerObj["item_list"].append(None)

    c = Container(**containerObj)
    c.save()

    return c.container_id


def getRasters(as_mongo_obj=False):
    if as_mongo_obj:
        return oRaster.objects()

    return [r.to_mongo() for r in Raster.objects()]


def addRaster(rasterDefObj):
    r = Raster(**rasterDefObj)
    r.save()

    return r.raster_id


def clearRasters():
    Raster.drop_collection()


def getNextRunRaster(updateFlag=1):
#    rasterList = getRasters()
#    if (len(rasterList) == 0):
#        return None
#    for i in xrange(len(rasterList)):
#        if (rasterList[i]["status"] == 0):
#            retRaster = rasterList[i]
#            if (updateFlag==1):
#                rasterList[i]["status"] = 1
#                break
#            else:
##                print "drawing " 
##                print retRaster
#                return retRaster
#    #pickleFile = open( "raster.db", "w+" )
#    for i in xrange(len(rasterList)):
#        #pickle.dump(rasterList[i], pickleFile)
#        rasterList[i].save()
#    #pickleFile.close()
#    return retRaster

    retRaster = None

    for rast in getRasters(as_mongo_obj=True):
        if rast.status == 0:
            retRaster = rast
            if updateFlag == 1:
                rast.status = 1
                rast.save()
                break
    return retRaster


def getNextDisplayRaster():
#    rasterList = getRasters()
#    if (len(rasterList) == 0):
#        return None
#    #pickleFile = open( "raster.db", "w+" )
#    for i in range (0, len(rasterList)):
#        if (rasterList[i]["status"] == 1):
#            retRaster = (i, rasterList[i])
#            rasterList[i]["status"] = 2
#            break
#    for i in range (0, len(rasterList)):
#        #pickle.dump(rasterList[i], pickleFile)
#        rasterList[i].save()      
#    #pickleFile.close()
#    return retRaster

    # if getRasters() returns [] retRaster=? !
    # should it be initialized to None as in previous func?
    for i,rast in enumerate(getRasters(as_mongo_obj=True)):
        if rast.status == 1:
            retRaster = (i, rast)
            rast.status = 2
            rast.save()
            break
    return retRaster


def createSample(sampleName):
    sampleObj = {"sampleName": sampleName, "requestList": []}

    s = Sample(**sampleObj)
    s.save()

    return s.sample_id


def _check_only_one(query_set, obj_type_str, search_key_str, search_key_val,
                   def_retval, as_mongo_obj=False, dict_key=None):

    if query_set.count() == 1:
        if as_mongo_obj:
            return query_set.first()
        else:
            if dict_key is not None:
                # could eliminate this 'to_mongo' conversion if move
                # this out to calling func which can access mongo_obj.dict_key?
                # or even better fetch only the needed fields in the query
                return query_set.first().to_mongo()[dict_key]
            return query_set.first().to_mongo()

    elif query_set.count() > 1:
        raise ValueError('got more than one {2} when searching'
                         ' for {1} ({0})!?'.format(search_key_val, search_key_str,
                                                   obj_type_str))

    return def_retval
    

def getSampleByID(sample_id, as_mongo_obj=False):
    s = Sample.objects(sample_id=sample_id)
    return _check_only_one(s, 'sample', 'sample_id', sample_id, None,
                           as_mongo_obj=as_mongo_obj)


# should fetch only the needed field(s)! :(

def getSampleIDbyName(sample_name):
    s = Sample.objects(sampleName=sample_name)
    return _check_only_one(s, 'sample', 'sampleName', sample_name, -99, 
                           dict_key='sample_id')


def getSampleNamebyID(sample_id):
    s = Sample.objects(sample_id=sample_id)
    return _check_only_one(s, 'sample', 'sample_id', sample_id, -99,
                           dict_key='sampleName')


def getContainerIDbyName(container_name):
    c = Container.objects(containerName=container_name)
    return _check_only_one(c, 'container', 'containerName', container_name,
                           -99, dict_key='container_id')


def getContainerNameByID(container_id):
    c = Container.objects(container_id=container_id)
    return _check_only_one(c, 'container', 'container_id', container_id, '',
                           dict_key='containerName')


def addRequesttoSample(sample_id, request):
    r = Request(**request)

    s = getSampleByID(sample_id, as_mongo_obj=True)
    #s.save(push__requestList=r)
    s.requestList.append(r)
    s.save()


def createDefaultRequest(sample_id):
    request = {
               "sample_id" : sample_id,
               "sweep_start":0.0,  "sweep_end":0.1,
               "img_width":.1,
               "exposure_time":.1,
               "priority":0,
               "protocol":"standard",
               "directory":"/",
               "file_prefix":getSampleNamebyID(sample_id)+"_data",
               "file_number_start":1,
               "wavelength":1.1,
               "resolution":3.0,
               "slit_height":30.0,  "slit_width":30.0,
               "attenuation":0,
               "pos_x":0,  "pos_y":0,  "pos_z":0,  "pos_type":'A',
               "gridW":0,  "gridH":0,  "gridStep":10}

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
    _ret_list(c, as_mongo_obj=as_mongo_obj)


def getContainersByType(type_name, group_name, as_mongo_obj=False): 
    c = Container.objects(type_name=type_name)
    _ret_list(c, as_mongo_obj=as_mongo_obj)


def getAllPucks(as_mongo_obj=False):
    return getContainersByType("puck", "", as_mongo_obj=as_mongo_obj)


def getPrimaryDewar(as_mongo_obj=False):
    return getContainerByName("primaryDewar2", as_mongo_obj=as_mongo_obj)


def getContainerByName(container_name, as_mongo_obj=False): 
    c = Container.objects(containerName=container_name)
    return _check_only_one(c, 'container', 'containerName', container_name,
                           None, as_mongo_obj=as_mongo_obj)


def getContainerByID(container_id, as_mongo_obj=False): 
    c = Container.objects(container_id=container_id)
    return _check_only_one(c, 'container', 'container_id', container_id,
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
#    ret_list = []
#    dewar = getContainerByName("primaryDewar2")
#    for i in range (0,len(dewar["item_list"])): #these are pucks
#        if (dewar["item_list"][i] != None):
#            puck_id = dewar["item_list"][i]
#            if (puck_id != None): 
#                puck = getContainerByID(puck_id)
#                sampleList = puck["item_list"]
#                for j in range (0,len(sampleList)):
#                    if (sampleList[j] != None):
##                        print "sample ID = " + str(sampleList[j])
#                        sampleObj = getSampleByID(sampleList[j])
#                        if (sampleObj == None): #not sure how it gets here, I think it's a server update
#                            print "sample ID = " + str(sampleList[j])
#                        else:
#                            sampleReqList = sampleObj["requestList"]
#                            for k in range (0,len(sampleReqList)):
#                                if (sampleReqList[k] != None):
#                                    ret_list.append(sampleReqList[k])
#    return ret_list

    # seems like this would be alot simpler if it weren't for the Nones?

    ret_list = []
    items = getContainerByName("primaryDewar2")["item_list"]  #these are pucks
    for item_id in items:
        if item_id is not None:
            puck = getContainerByID(item_id)
            for sample_id in puck["item_list"]:
                if sample_id is not None:
#                    print "sample ID = " + str(sample_id)
                    sampleObj = getSampleByID(sample_id)
                    if sampleObj is None:  #not sure how it gets here, I think it's a server update
                        print "sample ID = " + str(sample_id)
                    else:
                        for request in sampleObj["requestList"]:
                            if request is not None:
                                ret_list.append(request)
    return ret_list


def getDewarPosfromSampleID(sample_id):
#    dewar = getContainerByName("primaryDewar2")
#    for i in xrange(len(dewar["item_list"])): #these are pucks
#        if (dewar["item_list"][i] != None):
#            puck_id = dewar["item_list"][i]
#            if (puck_id != None): 
#                puck = getContainerByID(puck_id)
#                sampleList = puck["item_list"]
#                for j in xrange(len(sampleList)):
#                    if (sampleList[j] != None):
#                        if (sampleList[j] == sample_id):
#                            containerID = puck_id
#                            position = j
#                            return (containerID,position)    

    for puck_id in getContainerByName("primaryDewar2")["item_list"]:
        if puck_id is not None:
            for j,samp_id in enumerate(getContainerByID(puck_id)["item_list"]):
                if samp_id is not None and samp_id == sample_id:
                    containerID = puck_id
                    position = j
                    return (containerID, position)    


def getAbsoluteDewarPosfromSampleID(sample_id):
#    dewar = getContainerByName("primaryDewar2")
#    dewarCapacity = len(dewar["item_list"])
#    for i in xrange(dewarCapacity): #these are pucks
#        if (dewar["item_list"][i] != None):
#            puck_id = dewar["item_list"][i]
#            if (puck_id != None): 
#                puck = getContainerByID(puck_id)
#                sampleList = puck["item_list"]
#                puckCapacity = len(sampleList) #puck
#                for j in xrange(puckCapacity):
#                    if (sampleList[j] != None):
#                        if (sampleList[j] == sample_id):
#                            absPosition = (i*puckCapacity) + j
#                            return absPosition

    for i,puck_id in enumerate(getContainerByName("primaryDewar2")["item_list"]):
        if puck_id is not None:
            puck = getContainerByID(puck_id)
            sampleList = puck["item_list"]
            puckCapacity = len(sampleList)  # would be more efficient to have a capacity field

            for j,samp_id in enumerate(sampleList):
                if samp_id is not None and samp_id == sample_id:
                    absPosition = (i*puckCapacity) + j
                    return absPosition


def popNextRequest():
    orderedRequests = getOrderedRequestList()
    if orderedRequests[0]["priority"] > 0:
        return orderedRequests[0]
    else:
        return {}


def getRequest(reqID):  # need to get this from searching the dewar I guess
    r_id = int(reqID)
    for req in getQueue():
        if req["request_id"] == r_id:
            return req
    return None


def getAllSamples():
    return [s.to_mongo() for s in Sample.objects()]
    
    
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
    

#this is really "update_sample" because the request is stored with the sample.

def updateRequest(reqObj):
    sample = getSampleByID(reqObj["sample_id"], as_mongo_obj=True)

    for req in sample.requestList:
        if req is not None:
            try:
                if reqObj["request_id"] == req.request_id:
                    updated_req = Request(**reqObj)
                    updated_req.request_id = req.request_id
    
                    #sample.requestList.remove(req)
                    #sample.requestList.append(updated_req)
                    #sample.save()
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


def getSortedPriorityList(): # mayb an intermediate to return a list of all priorities.
    pList = []

    for request in getQueue():
        if request["priority"] not in pList:
            pList.append(request["priority"])

    return sorted(pList, reverse=True)


def getOrderedRequestList():
    orderedRequestsList = []
    requestsList = getQueue()  # this is everything in the dewar

    for priority in getSortedPriorityList():  # just sorts priorities 
        for request in requestsList:
            if request["priority"] == priority:
                orderedRequestsList.append(request)

    return orderedRequestsList
