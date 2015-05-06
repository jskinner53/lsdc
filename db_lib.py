#!/usr/bin/python
import pickle
import time
import uuid
import functools
import mongoengine as mongo

from odm_templates import (Sample, Container, Raster)



### !!!!  all the XXXByName()'s also need to take a group_id since Sample/Container/Etc names
### !!!!  are only unique per group.


mongo_conn = mongo.connect('matt_tmp_mongo')


def createContainer(container_name, type_name, capacity):

    container_id = uuid.uuid1()

    containerObj = {"container_id": container_id,
                    "containerName": container_name,
                    "type_name": type_name,
                    "item_list": []}

    # the item list is a list of id's, whether they be other
    # containers or samples. This is because samples and pucks can move.
    for i in xrange(capacity):
        containerObj["item_list"].append(None)

    c = Container(**containerObj)
    c.save()


def getRasters(): 
    #ret_list = []
    #rasterFile = open( "raster.db", "r" )
    #try:
    #    while (1):
    #        retQ = pickle.load(rasterFile)
    #        ret_list.append(retQ)
    #except EOFError:
    #    rasterFile.close()
    #return ret_list

    return [r.to_mongo() for r in Raster.objects()]


def addRaster(rasterDefObj):
    #rasterList = getRasters()
    #rasterList.append(rasterDefObj)
    #pickleFile = open( "raster.db", "w+" )
    #for i in range (0, len(rasterList)):
    #    pickle.dump(rasterList[i], pickleFile)
    #pickleFile.close()

    r = Raster(**rasterDefObj)
    r.save()


def clearRasters():
    #pickleFile = open( "raster.db", "w+" )    
    #pickleFile.close()

    Raster.drop_collection()


def getNextRunRaster(updateFlag=1):
    rasterList = getRasters()
    if (len(rasterList) == 0):
        return None
    for i in xrange(len(rasterList)):
        if (rasterList[i]["status"] == 0):
            retRaster = rasterList[i]
            if (updateFlag==1):
                rasterList[i]["status"] = 1
                break
            else:
#                print "drawing " 
#                print retRaster
                return retRaster
    #pickleFile = open( "raster.db", "w+" )
    for i in xrange(len(rasterList)):
        #pickle.dump(rasterList[i], pickleFile)
        rasterList[i].save()
    #pickleFile.close()
    return retRaster


def getNextDisplayRaster():
    rasterList = getRasters()
    if (len(rasterList) == 0):
        return None
    #pickleFile = open( "raster.db", "w+" )
    for i in range (0, len(rasterList)):
        if (rasterList[i]["status"] == 1):
            retRaster = (i, rasterList[i])
            rasterList[i]["status"] = 2
            break
    for i in range (0, len(rasterList)):
        #pickle.dump(rasterList[i], pickleFile)
        rasterList[i].save()      
    #pickleFile.close()
    return retRaster



def createSample(sampleName):

    sample_id = uuid.uuid1()

    sampleObj = {"sample_id":  sample_id, "sampleName": sampleName, "requestList": []}

    #sampleFile = open( "sample.db", "a+" )
    #pickle.dump(sampleObj, sampleFile)
    #sampleFile.close()

    s = Sample(**sampleObj)
    s.save()

    return sampleObj["sample_id"]


def getSampleByID(sample_id, as_mongo_obj=False):
    #pickleFile = open( "sample.db", "r" )
    #try:
    #    while (1):
    #        retQ = pickle.load(pickleFile)
    #        if (retQ["sample_id"] == sample_id):
    #            pickleFile.close()
    #            return retQ
    #except EOFError:
    #    pickleFile.close()

    s = Sample.objects(sample_id=sample_id)
    if s.count() == 1:
        if as_mongo_obj:
            return s.first()
        else:
            return s.first().to_mongo()

    elif s.count() > 1:
        raise ValueError('got more than one sample when searching for sample id ({0})!?'.format(sample_id))

    return None


def getSampleIDbyName(sample_name, as_mongo_obj=False):
    #pickleFile = open( "sample.db", "r" )
    #try:
    #    while (1):
    #        retQ = pickle.load(pickleFile)
    #        if (retQ["sampleName"] == sample_name):
    #            pickleFile.close()
    #            return retQ["sample_id"]
    #except EOFError:
    #    pickleFile.close()
    #return -99

    s = Sample.objects(sampleName=sample_name)
    if s.count() == 1:
        return s.first().to_mongo()['sample_id']
    elif s.count() > 1:
        raise ValueError('got more than one sample when searching for sample name ({0})!?'.format(sample_name))

    return -99


def getSampleNamebyID(sample_id):
    #pickleFile = open( "sample.db", "r" )
    #try:
    #    while (1):
    #        retQ = pickle.load(pickleFile)
    #        if (retQ["sample_id"] == sample_id):
    #            pickleFile.close()
    #            return retQ["sampleName"]
    #except EOFError:
    #    pickleFile.close()
    #return -99

    s = Sample.objects(sample_id=sample_id)
    if s.count() == 1:
        return s.first().to_mongo()['sampleName']
    elif s.count() > 1:
        raise ValueError('got more than one sample when searching for sample id ({0})!?'.format(sample_id))

    return -99


def getContainerIDbyName(container_name):
    #pickleFile = open( "container.db", "r" )
    #try:
    #    while (1):
    #        retQ = pickle.load(pickleFile)
    #        if (retQ["containerName"] == container_name):
    #            pickleFile.close()
    #            return retQ["container_id"]
    #except EOFError:
    #    pickleFile.close()
    #return -99

    c = Container.objects(container_name=container_name)
    if c.count() == 1:
        return c.first().to_mongo()['ContainerName']
    elif c.count() > 1:
        raise ValueError('got more than one container when searching for container name ({0})!?'.format(container_name))

    return -99


def getContainerNameByID(container_id):
    #pickleFile = open( "container.db", "r" )
    #try:
    #    while (1):
    #        retQ = pickle.load(pickleFile)
    #        if (retQ["container_id"] == container_id):
    #            pickleFile.close()
    #            return retQ["containerName"]
    #except EOFError:
    #    pickleFile.close()
    #return ""

    c = Container.objects(container_id=container_id)
    if c.count() == 1:
        return c.first().to_mongo()['ContainerName']
    elif c.count() > 1:
        raise ValueError('got more than one container when searching for container name ({0})!?'.format(container_id))

    return ""


def addRequesttoSample(sample_id, request):
    #pickleFile = open( "sample.db", "a+" )
    #sampList = []
    #try:
    #    while (1):
    #        retQ = pickle.load(pickleFile)
    #        if (retQ["sample_id"] == sample_id):
    #            retQ["requestList"].append(request)
    #        sampList.append(retQ)
    #except EOFError:
    #    pickleFile.close()
    #pickleFile = open( "sample.db", "w+" )
    #for i in range (0, len(sampList)):
    #    pickle.dump(sampList[i], pickleFile)
    #pickleFile.close()
  
    s = getSampleByID(sample_id, as_mongo_obj=True)
    s.modify(push__requestList=request)


def createDefaultRequest(sample_id):
    request = {
               "request_id": int(time.time()),
               "sample_id" : sample_id,
               "sweep_start":0.0,  "sweep_end":0.1,
               "img_width":.1,
               "exposure_time":.1,
               "priority":0,
               "protocol":"standard",
               "directory":"/",  "file_prefix":getSampleNamebyID(sample_id)+"_data",
               "file_number_start":1,
               "wavelength":1.1,
               "resolution":3.0,
               "slit_height":30.0,  "slit_width":30.0,
               "attenuation":0,
               "pos_x":0,  "pos_y":0,  "pos_z":0,  "pos_type":'A',
               "gridW":0,  "gridH":0,  "gridStep":10}

    return request
####    addRequesttoSample(sample_id, request)


def insertIntoContainer(container_name, position, itemID):
    #origQ = getContainers()
    #found = 0
    #for i in range (0, len(origQ)):
    #    if (origQ[i]["containerName"] == container_name):
    #        origQ[i]["item_list"][position] = itemID
    #        found = 1
    #        break
    #if (found):
    #    containerFile = open( "container.db", 
    #"w+" )
    #    for i in range (0, len(origQ)):
    #        pickle.dump(origQ[i], containerFile)
    #    containerFile.close()
    #else:
    #    print "bad container name"

    c = getContainerByName(container_name, as_mongo_obj=True)
    if c is not None:
        c.item_list[position] = itemID
        c.save()
    else:
        print "bad container name"


def getContainers(as_mongo_obj=False): 
    #ret_list = []
    #containerFile = open( "container.db", "r" )
    #try:
    #    while (1):
    #        retQ = pickle.load(containerFile)
    #        ret_list.append(retQ)
    #except EOFError:
    #    containerFile.close()
    #return ret_list

    c = Container.objects()

    if as_mongo_obj:
        return list(c)
    else:
        return [c.to_mongo() for c in c]


def getContainersByType(type_name, group_name, as_mongo_obj=False): 
    #ret_list = []
    #containerFile = open( "container.db", "r" )
    #try:
    #    while (1):
    #        retQ = pickle.load(containerFile)
    #        if (retQ["type_name"] == type_name):
    #            ret_list.append(retQ)
    #except EOFError:
    #    containerFile.close()
    #return ret_list

    c = Container.objects(type_name=type_name)

    if as_mongo_obj:
        return list(c)
    else:
        return [c.to_mongo() for c in c]


def getAllPucks(as_mongo_obj=False):
    return getContainersByType("puck", "", as_mongo_obj=as_mongo_obj)


def getPrimaryDewar(as_mongo_obj=False):
#    return getContainersByType("dewar", "")[0]
    return getContainerByName("primaryDewar2", as_mongo_obj=as_mongo_obj)


def getContainerByName(container_name, as_mongo_obj=False): 
    #containerFile = open( "container.db", "r" )
    #try:
    #    while (1):
    #        retQ = pickle.load(containerFile)
    #        if (retQ["containerName"] == container_name):
    #            containerFile.close()
    #            return retQ
    #except EOFError:
    #    containerFile.close()
    #return None

    c = Container.objects(containerName=container_name)

    if c.count() == 1:
        if as_mongo_obj:
            return c.first()
        else:
            return c.first().to_mongo()

    elif c.count() > 1:
        raise ValueError('got more than one container when searching for container name ({0})!?'.format(container_name))

    return None


def getContainerByID(container_id, as_mongo_obj=False): 
    #containerFile = open( "container.db", "r" )
    #try:
    #    while (1):
    #        retQ = pickle.load(containerFile)
    #        if (retQ["container_id"] == container_id):
    #            containerFile.close()
    #            return retQ
    #except EOFError:
    #    containerFile.close()
    #return None

    c = Container.objects(container_id=container_id)

    if c.count() == 1:
        if as_mongo_obj:
            return c.first()
        else:
            return c.first().to_mongo()

    elif c.count() > 1:
        raise ValueError('got more than one container when searching for'
                         'container id ({0})!?'.format(container_id))

    return None


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
    sampleObj = getSampleByID(sample_id)
    sampleObj["requestList"].append(colobj)

    s = getSampleByID(sample_id, as_mongo_obj=True)
    s.modify(push__requestList=colobj)

#,vec_x_start,vec_y_start,vec_z_start,vec_x_end,vec_y_end,vec_z_end,vec_numframes,vec_fpp
#vec_fpp means frames per point, vec_numframes is the total. Not sure if this is the best way.

#pinpos, sweep_start, numimages, sweep_inc, exposure_time, protocol, file_prefix, file_number_start, wavelength, resolution, xtal_id,    slit_height, slit_width, attenuation,priority



def getQueue():
    ret_list = []
    dewar = getContainerByName("primaryDewar2")
    for i in range (0,len(dewar["item_list"])): #these are pucks
        if (dewar["item_list"][i] != None):
            puck_id = dewar["item_list"][i]
            if (puck_id != None): 
                puck = getContainerByID(puck_id)
                sampleList = puck["item_list"]
                for j in range (0,len(sampleList)):
                    if (sampleList[j] != None):
#                        print "sample ID = " + str(sampleList[j])
                        sampleObj = getSampleByID(sampleList[j])
                        if (sampleObj == None): #not sure how it gets here, I think it's a server update
                            print "sample ID = " + str(sampleList[j])
                        else:
                            sampleReqList = sampleObj["requestList"]
                            for k in range (0,len(sampleReqList)):
                                if (sampleReqList[k] != None):
                                    ret_list.append(sampleReqList[k])
    return ret_list




def getDewarPosfromSampleID(sample_id):
    dewar = getContainerByName("primaryDewar2")
    for i in range (0,len(dewar["item_list"])): #these are pucks
        if (dewar["item_list"][i] != None):
            puck_id = dewar["item_list"][i]
            if (puck_id != None): 
                puck = getContainerByID(puck_id)
                sampleList = puck["item_list"]
                for j in range (0,len(sampleList)):
                    if (sampleList[j] != None):
                        if (sampleList[j] == sample_id):
                            containerID = puck_id
                            position = j
                            return (containerID,position)    



def getAbsoluteDewarPosfromSampleID(sample_id):
    dewar = getContainerByName("primaryDewar2")
    dewarCapacity = len(dewar["item_list"])
    for i in range (0,dewarCapacity): #these are pucks
        if (dewar["item_list"][i] != None):
            puck_id = dewar["item_list"][i]
            if (puck_id != None): 
                puck = getContainerByID(puck_id)
                sampleList = puck["item_list"]
                puckCapacity = len(sampleList) #puck
                for j in range (0,puckCapacity):
                    if (sampleList[j] != None):
                        if (sampleList[j] == sample_id):
                            absPosition = (i*puckCapacity) + j
                            return absPosition



def popNextRequest():
    orderedRequests = getOrderedRequestList()
    if (orderedRequests[0]["priority"] > 0):
        return orderedRequests[0]
    else:
        return {}




def getRequest(reqID): #need to get this from searching the dewar I guess
    reqList = getQueue()
    for i in range (0,len(reqList)):
        req = reqList[i]
        if (req["request_id"] == int(reqID)):
            return req
    return None



def getAllSamples():
    #pickleFile = open( "sample.db", "r" )
    #retList = []
    #try:
    #    while (1):
    #        retQ = pickle.load(pickleFile)
    #        retList.append(retQ)
    #except EOFError:
    #    pickleFile.close()
    #return retList

    return [s.to_mongo() for s in Sample.objects()]
    
    
#really need to generalize these update routines 


def updateSample(sampleObj):
    #sampleList = getAllSamples()
    #for i in range (0,len(sampleList)):
    #    if (sampleList[i]["sample_id"] == sampleObj["sample_id"]):
    #        sampleList[i] = sampleObj
    #        break
    #pickleFile = open( "sample.db", "w+" )
    #for i in range (0,len(sampleList)):
    #    pickle.dump(sampleList[i],pickleFile)
    #pickleFile.close()

    s = Sample(sampleObj)
    s.save()
    

def updateContainer(containerObj):
    #containerList = getContainers()
    #for i in range (0,len(containerList)):
    #    if (containerList[i]["container_id"] == containerObj["container_id"]):
    #        containerList[i] = containerObj
    #        break
    #pickleFile = open( "container.db", "w+" )
    #for i in range (0,len(containerList)):
    #    pickle.dump(containerList[i],pickleFile)
    #pickleFile.close()

    c = Container(containerObj)
    c.save()
    
    

#this is really "update_sample" because the request is stored with the sample.

def updateRequest(reqObj):
    found = 0
    sample = getSampleByID(reqObj["sample_id"])
    reqList = sample["requestList"]
    for i in range (0,len(reqList)):
        if (reqList[i] != None):
            if (reqObj["request_id"] == reqList[i]["request_id"]):
                sample["requestList"][i] = reqObj
                found = 1
                break
    if (found):
        updateSample(sample)    
    else:
        addRequesttoSample(reqObj["sample_id"],reqObj)



def deleteRequest(reqObj):
    origQ = getQueue()
    found = 0
    for i in range (0,len(origQ)):
        if (origQ[i]["request_id"] == reqObj["request_id"]):
            print "found the request to delete 1"
            s = getSampleByID(reqObj["sample_id"])
            for i in range (0,len(s["requestList"])):
                if (s["requestList"][i] != None):
                    if (s["requestList"][i]["request_id"] == reqObj["request_id"]):
                        print "trying to delete request"
                        s["requestList"][i] = None
                        updateSample(s)


def deleteSample(samplObj):
    #retList = []
    #pickleFile = open( "sample.db", "a+" )
    #try:
    #    while (1):
    #        retQ = pickle.load(pickleFile)
    #        if (retQ["sample_id"] != samplObj["sample_id"]):
    #            retList.append(retQ)
    #except EOFError:
    #    pickleFile.close()
    #pickleFile = open( "sample.db", "w+" )
    #for i in range (0,len(retList)):
    #    pickle.dump(retList[i],pickleFile)
    #pickleFile.close()

    s = getSampleByID(sampleObj["sample_id"], as_mongo_obj=True)
    s.delete()



def removePuckFromDewar(dewarPos):
    dewar = getPrimaryDewar()
    dewar["item_list"][dewarPos] = None
    updateContainer(dewar)

    

def emptyLiveQueue(): #a convenience to say nothing is ready to be run
    q = getQueue()
    for i in range (0,len(q)):
        q[i]["priority"] = 0
        updateRequest(q[i])



def getSortedPriorityList(): # mayb an intermediate to return a list of all priorities.
    pList = []
    requestsList = getQueue()
    for i in range (0,len(requestsList)):
        if (requestsList[i]["priority"] not in pList):
            pList.append(requestsList[i]["priority"])
    return sorted(pList,reverse=True)



def getOrderedRequestList():
    orderedRequestsList = []
    priorityList = getSortedPriorityList() #just sorts priorities
    requestsList = getQueue() #this is everything in the dewar
#    dewarDict = getDewar()
    for i in range (0,len(priorityList)):
        for j in range (0,len(requestsList)):
            if (requestsList[j]["priority"] == priorityList[i]):
                orderedRequestsList.append(requestsList[j])
    return orderedRequestsList


                    



            





