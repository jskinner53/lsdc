import beamline_support
import beamline_lib #did this really screw me if I imported b/c of daq_utils import??
from beamline_lib import *
import daq_lib
from daq_lib import *
import daq_utils
import db_lib
#import string
import math
import robot_lib
from PyQt4 import QtGui
from PyQt4 import QtCore
import time
from random import randint
import glob
##import xml.etree.ElementTree as ET
import xmltodict
##from XSDataMXv1 import XSDataResultCharacterisation
from importlib import reload
import start_bs
from start_bs import *
import subprocess

def hi_macro():
  print("hello from macros\n")
  daq_lib.broadcast_output("broadcast hi")


def BS():
  movr(omega,40)

def BS2():
  ascan(omega,0,100,10)

def abortBS():
  RE.abort()
  
def flipLoopShapeCoords(filename): # not used
  xrec_out_file = open(filename,"r")  
  correctedFilename = "loopFaceShape.txt"
  resultLine = xrec_out_file.readline()
  tokens = resultLine.split()
  numpoints = int(tokens[0])
  points = []
  for i in range(1,len(tokens)-1,2):
    point = [tokens[i],tokens[i+1]]
    correctedPoint = [daq_utils.screenPixX-int(tokens[i]),daq_utils.screenPixY-int(tokens[i+1])]
  xrec_out_file.close() 


def autoRasterLoop(currentRequest):
  set_field("xrecRasterFlag",100)        
  sampleID = currentRequest["sample_id"]
  print("auto raster " + str(sampleID))
  loop_center_xrec()
  time.sleep(1) #looks like I really need this sleep, they really improve the appearance 
  runRasterScan(currentRequest,"LoopShape")
  time.sleep(1.5) 
  runRasterScan(currentRequest,"Fine")
  time.sleep(1) 
  runRasterScan(currentRequest,"Line")  
  time.sleep(1) 

def multiCol(currentRequest):
  set_field("xrecRasterFlag",100)      
  sampleID = currentRequest["sample_id"]
  print("multiCol " + str(sampleID))
  loop_center_xrec()
  time.sleep(1) #looks like I really need this sleep, they really improve the appearance 
  runRasterScan(currentRequest,"LoopShape")
#  time.sleep(1) 

def loop_center_xrec():
  global face_on

  daq_lib.abort_flag = 0    

  for i in range(0,360,40):
    if (daq_lib.abort_flag == 1):
      return 0
    mvaDescriptor("omega",i)
    pic_prefix = "findloop_" + str(i)
    time.sleep(1.0) #for video lag. This sucks
    daq_utils.take_crystal_picture(filename=pic_prefix)
  comm_s = "xrec " + os.environ["CONFIGDIR"] + "/xrec_360_40.txt xrec_result.txt"
  print(comm_s)
  os.system(comm_s)
  xrec_out_file = open("xrec_result.txt","r")
  target_angle = 0.0
  radius = 0
  x_centre = 0
  y_centre = 0
  reliability = 0
  for result_line in xrec_out_file.readlines():
    print(result_line)
    tokens = result_line.split()
    tag = tokens[0]
    val = tokens[1]
    if (tag == "TARGET_ANGLE"):
      target_angle = float(val )
    elif (tag == "RADIUS"):
      radius = float(val )
    elif (tag == "Y_CENTRE"):
      y_centre_xrec = float(val )
    elif (tag == "X_CENTRE"):
      x_centre_xrec = float(val )
    elif (tag == "RELIABILITY"):
      reliability = int(val )
    elif (tag == "FACE"):
      face_on = float(tokens[3])
  xrec_out_file.close()
  xrec_check_file = open("Xrec_check.txt","r")  
  check_result =  int(xrec_check_file.read(1))
  print("result = " + str(check_result))
  xrec_check_file.close()
  if (reliability < 70 or check_result == 0): #bail if xrec couldn't align loop
    return 0
  mvaDescriptor("omega",target_angle)
  x_center = daq_utils.lowMagPixX/2
  y_center = daq_utils.lowMagPixY/2
#  set_epics_pv("image_X_center","A",x_center)
#  set_epics_pv("image_Y_center","A",y_center)
  print("center on click " + str(x_center) + " " + str(y_center-radius))
  print("center on click " + str((x_center*2) - y_centre_xrec) + " " + str(x_centre_xrec))
  center_on_click(x_center,y_center-radius,source="macro")
  center_on_click((x_center*2) - y_centre_xrec,x_centre_xrec,source="macro")
#  center_on_click(y_centre_xrec,x_centre_xrec,source="macro")  
  mvaDescriptor("omega",face_on)
  #now try to get the loopshape starting from here
  return 1

def fakeDC(directory,filePrefix,numstart,numimages):
#  return #SHORT CIRCUIT
#  testImgFileList = glob.glob("/home/pxuser/Test-JJ/johnPil6/data/B1GGTApo_9_*.cbf")
  if (numimages > 360):
    return
  testImgFileList = glob.glob("/GPFS/CENTRAL/XF17ID1/skinner/testdata/johnPil6/data/B1GGTApo_9_0*.cbf")
  testImgFileList.sort()
  prefix_long = directory+"/"+filePrefix
  expectedFilenameList = []
  for i in range (numstart,numstart+numimages):
    filename = daq_utils.create_filename(prefix_long,i)
    expectedFilenameList.append(filename)
  for i in range (0,len(expectedFilenameList)):
    comm_s = "ln -sf " + testImgFileList[i] + " " + expectedFilenameList[i]
    print(comm_s)
    os.system(comm_s)



def generateGridMap(rasterRequest):
  reqObj = rasterRequest["request_obj"]
  rasterDef = reqObj["rasterDef"]
  stepsize = float(rasterDef["stepsize"])
  omega = float(rasterDef["omega"])
  rasterStartX = float(rasterDef["x"])
  rasterStartY = float(rasterDef["y"])
  rasterStartZ = float(rasterDef["z"])
  omegaRad = math.radians(omega)
  filePrefix = reqObj["directory"]+"/"+reqObj["file_prefix"]
#  testImgFileList = glob.glob("/GPFS/CENTRAL/XF17ID1/skinner/testdata/Eiger1M/*.cbf")
  testImgFileList = glob.glob("/nfs/skinner/testdata/Eiger1M/*.cbf")  
  testImgCount = 0
  rasterCellMap = {}
  os.system("mkdir -p " + reqObj["directory"])
  for i in range(len(rasterDef["rowDefs"])):
    numsteps = float(rasterDef["rowDefs"][i]["numsteps"])
    if (i%2 == 0): #left to right if even, else right to left - a snake attempt
      startX = rasterDef["rowDefs"][i]["start"]["x"]+(stepsize/2.0) #this is relative to center, so signs are reversed from motor movements.
    else:
      startX = (numsteps*stepsize) + rasterDef["rowDefs"][i]["start"]["x"]-(stepsize/2.0)
    startY = rasterDef["rowDefs"][i]["start"]["y"]+(stepsize/2.0)

    xRelativeMove = startX
    yzRelativeMove = startY*sin(omegaRad)
    yyRelativeMove = startY*cos(omegaRad)


    xMotAbsoluteMove = rasterStartX+xRelativeMove    
    yMotAbsoluteMove = rasterStartY-yyRelativeMove
    zMotAbsoluteMove = rasterStartZ-yzRelativeMove

    numsteps = int(rasterDef["rowDefs"][i]["numsteps"])
    for j in range(numsteps):
      if (i%2 == 0): #left to right if even, else right to left - a snake attempt
        xMotCellAbsoluteMove = xMotAbsoluteMove+(j*stepsize)
      else:
        xMotCellAbsoluteMove = xMotAbsoluteMove-(j*stepsize)

      dataFileName = daq_utils.create_filename(filePrefix+"_"+str(i),j+1)
      comm_s = "ln -sf " + testImgFileList[testImgCount] + " " + dataFileName      
      os.system(comm_s)
      testImgCount+=1
      rasterCellCoords = {"x":xMotCellAbsoluteMove,"y":yMotAbsoluteMove,"z":zMotAbsoluteMove}
      rasterCellMap[dataFileName[:-4]] = rasterCellCoords
####  comm_s = "ssh -q xf17id1-srv1 \"ls -rt " + reqObj["directory"]+"/"+reqObj["file_prefix"]+"*.cbf|/usr/local/crys/dials-installer-dev-316-intel-linux-2.6-x86_64-centos5/build/bin/dials.find_spots_client\""
#  comm_s = "ssh -q cpu-004 \"ls -rt " + reqObj["directory"]+"/"+reqObj["file_prefix"]+"*.cbf|/usr/local/crys/dials-installer-dev-316-intel-linux-2.6-x86_64-centos5/build/bin/dials.find_spots_client\""
###############the following 2 lines are for that strange bug where a remote process doesn't see stuff on a remote filesystem!
  comm_s = "ssh -q cpu-004 'ls -rt " + reqObj["directory"]+"/"+reqObj["file_prefix"]+"*.cbf>>/dev/null'"
  lsOut = os.system(comm_s)
  
  comm_s = "ssh -q cpu-004 'ls -rt " + reqObj["directory"]+"/"+reqObj["file_prefix"]+"*.cbf| /usr/local/crys-local/dials-v1-1-4/build/bin/dials.find_spots_client'"  
#  comm_s = "ssh -q cpu-004 'ls -rt " + reqObj["directory"]+"/"+reqObj["file_prefix"]+"*.cbf|strace /usr/local/crys-local/dials-v1-1-4/build/bin/dials.find_spots_client >dialsClientOut2.txt 2>&1'"  
  print(comm_s)
#  dialsResultObj = xmltodict.parse("<data>\n"+os.popen(comm_s).read()+"</data>\n")
  dialsOut = os.popen(comm_s)
#  dialsOut = subprocess.Popen(comm_s,shell=True)  
  time.sleep(1)
  dialsResultObj = xmltodict.parse("<data>\n"+dialsOut.read()+"</data>\n")  
  print("done parsing dials output")
  print(dialsResultObj)
  if ("parentReqID" in rasterRequest["request_obj"]):
    parentReqID = rasterRequest["request_obj"]["parentReqID"]
  else:
    parentReqID = -1
  rasterResultObj = {"sample_id": rasterRequest["sample_id"],"parentReqID":parentReqID,"rasterCellMap":rasterCellMap,"rasterCellResults":{"type":"dialsRasterResult","resultObj":dialsResultObj}}
#  rasterResult = daq_utils.createResult("rasterResult",rasterResultObj)
  rasterResult = db_lib.addResultforRequest("rasterResult",rasterRequest["request_id"], rasterResultObj)
  return rasterResult


def rasterWait():
  time.sleep(0.2)
  while (beamline_support.getPvValFromDescriptor("RasterActive")):
    time.sleep(0.2)

def vectorWait():
  time.sleep(0.15)
  while (beamline_support.getPvValFromDescriptor("VectorActive")):
    time.sleep(0.05)


def snakeRaster(rasterReqID,grain=""):
  rasterRequest = db_lib.getRequest(rasterReqID)
  reqObj = rasterRequest["request_obj"]
  parentReqID = reqObj["parentReqID"]
  parentReqProtocol = ""
  detDist = 100 # for now, no motor yet
  if (parentReqID != -1):
    parentRequest = db_lib.getRequest(parentReqID)
    parentReqObj = parentRequest["request_obj"]
    parentReqProtocol = parentReqObj["protocol"]
    detDist = parentReqObj["detDist"]    
# 2/17/16 - a few things for integrating dials/spotfinding into this routine
#  filePrefix = reqObj["directory"]+"/"+reqObj["file_prefix"]
  data_directory_name = str(reqObj["directory"])
  os.system("mkdir -p " + data_directory_name)
  os.system("chmod -R 777 " + data_directory_name)  
  filePrefix = str(reqObj["file_prefix"])
  exptimePerCell = reqObj["exposure_time"]
  img_width_per_cell = reqObj["img_width"]
#really should read these two from hardware  
  wave = reqObj["wavelength"]

  
  xbeam = daq_utils.xbeam
  ybeam = daq_utils.ybeam  
  
  rasterDef = reqObj["rasterDef"]
  stepsize = float(rasterDef["stepsize"])
  omega = float(rasterDef["omega"])
  rasterStartX = float(rasterDef["x"]) #these are real sample motor positions
  rasterStartY = float(rasterDef["y"])
  rasterStartZ = float(rasterDef["z"])
  omegaRad = math.radians(omega)
#  current_omega_mod = beamline_lib.get_epics_motor_pos(beamline_support.pvNameSuffix_from_descriptor("omega"))%360.0

# 2/17/16 - a few things for integrating dials/spotfinding into this routine, this is just to fake the data
#  testImgFileList = glob.glob("/nfs/skinner/testdata/Eiger1M/*.cbf")
#  testImgCount = 0
#  for i in xrange(len(rasterDef["rowDefs"])):
#    numsteps = int(rasterDef["rowDefs"][i]["numsteps"])    
#    for j in xrange(numsteps):
#      dataFileName = daq_utils.create_filename(filePrefix+"_"+str(i),j+1)
#      os.system("mkdir -p " + reqObj["directory"])
#      comm_s = "ln -sf " + testImgFileList[testImgCount] + " " + dataFileName
#      os.system(comm_s)
#      testImgCount+=1

  for i in range(len(rasterDef["rowDefs"])):    
    numsteps = int(rasterDef["rowDefs"][i]["numsteps"])
#    startX = rasterDef["rowDefs"][i]["start"]["x"]+(stepsize/2.0)
#    endX = rasterDef["rowDefs"][i]["end"]["x"]-(stepsize/2.0)    

    startX = rasterDef["rowDefs"][i]["start"]["x"]
    endX = rasterDef["rowDefs"][i]["end"]["x"]
    
    startY = rasterDef["rowDefs"][i]["start"]["y"]
    endY = rasterDef["rowDefs"][i]["end"]["y"]

    deltaX = abs(endX-startX)
    deltaY = abs(endY-startY)
    if (deltaX>deltaY): #horizontal raster
      startX = startX + (stepsize/2.0)
      endX = endX - (stepsize/2.0)
      startY = startY + (stepsize/2.0)
      endY = startY
    else: #vertical raster
      startY = startY + (stepsize/2.0)
      endY = endY - (stepsize/2.0)
      startX = startX + (stepsize/2.0)
      endX = startX
      
    xRelativeMove = startX

    yzRelativeMove = startY*sin(omegaRad)
    yyRelativeMove = startY*cos(omegaRad)

    xMotAbsoluteMove = rasterStartX+xRelativeMove #note we convert relative to absolute moves, using the raster center that was saved in x,y,z
    yMotAbsoluteMove = rasterStartY-yyRelativeMove
    zMotAbsoluteMove = rasterStartZ-yzRelativeMove
##      time.sleep(1)#cosmetic
#      yRelativeMove = -((numsteps-1)*stepsize)
    xRelativeMove = endX-startX
    yRelativeMove = endY-startY
##    yRelativeMove = -(endY-startY)    
    
    yyRelativeMove = yRelativeMove*cos(omegaRad)
    yzRelativeMove = yRelativeMove*sin(omegaRad)
      
      
    xEnd = xMotAbsoluteMove + xRelativeMove
    yEnd = yMotAbsoluteMove - yyRelativeMove
    zEnd = zMotAbsoluteMove - yzRelativeMove

    if (i%2 != 0): #this is to scan opposite direction for snaking
      xEndSave = xEnd
      yEndSave = yEnd
      zEndSave = zEnd
      xEnd = xMotAbsoluteMove
      yEnd = yMotAbsoluteMove
      zEnd = zMotAbsoluteMove
      xMotAbsoluteMove = xEndSave
      yMotAbsoluteMove = yEndSave
      zMotAbsoluteMove = zEndSave            
    beamline_support.setPvValFromDescriptor("vectorStartOmega",omega)
    beamline_support.setPvValFromDescriptor("vectorStepOmega",img_width_per_cell)
    beamline_support.setPvValFromDescriptor("vectorStartX",xMotAbsoluteMove)
    beamline_support.setPvValFromDescriptor("vectorStartY",yMotAbsoluteMove)  
    beamline_support.setPvValFromDescriptor("vectorStartZ",zMotAbsoluteMove)  
    beamline_support.setPvValFromDescriptor("vectorEndX",xEnd)
    beamline_support.setPvValFromDescriptor("vectorEndY",yEnd)  
    beamline_support.setPvValFromDescriptor("vectorEndZ",zEnd)  
    beamline_support.setPvValFromDescriptor("vectorframeExptime",exptimePerCell)
    beamline_support.setPvValFromDescriptor("vectorNumFrames",numsteps-1)
    rasterFilePrefix = filePrefix + "_Raster_" + str(i+1)
    if (daq_utils.detector_id == "EIGER-16" and 0):
      detectorArmEiger(numsteps,exptimePerCell,rasterFilePrefix,data_directory_name,wave,xbeam,ybeam,detDist)
    beamline_support.setPvValFromDescriptor("vectorGo",1)
    vectorWait()
##    detector_wait()

# 2/17/16 - a few things for integrating dials/spotfinding into this routine    
#    rasterFilePattern = filePrefix+"_"+str(i)+"*.cbf"

# add the threading dials stuff here, and the thread routine elsewhere.


  rasterResult = generateGridMap(rasterRequest) #I think rasterRequest is entire request, of raster type
  rasterRequest["request_obj"]["rasterDef"]["status"] = 2
  print("parent protocol = " + parentReqProtocol)
  if (parentReqProtocol == "multiCol"):
    multiColThreshold  = parentReqObj["diffCutoff"]     
    gotoMaxRaster(rasterResult,multiColThreshold=multiColThreshold) 
  else:
    if (deltaX>deltaY): #horizontal raster, dont bother vert for now, did not do pos calcs, wait for zebra
      gotoMaxRaster(rasterResult)    
  db_lib.updateRequest(rasterRequest)
  db_lib.updatePriority(rasterRequest["request_id"],-1)  
  set_field("xrecRasterFlag",rasterRequest["request_id"])  



def runRasterScan(currentRequest,rasterType=""): #this actualkl defines and runs
  sampleID = currentRequest["sample_id"]
  if (rasterType=="Fine"):
    set_field("xrecRasterFlag",100)    
    rasterReqID = defineRectRaster(currentRequest,50,50,10) 
    snakeRaster(rasterReqID)
  elif (rasterType=="Line"):  
    set_field("xrecRasterFlag",100)    
    mvrDescriptor("omega",90)
    rasterReqID = defineRectRaster(currentRequest,10,150,10)
#    rasterReqID = defineVectorRaster(currentRequest,10,150,10)     
    snakeRaster(rasterReqID)
    set_field("xrecRasterFlag",100)    
  else:
    rasterReqID = getXrecLoopShape(currentRequest)
    print("snake raster " + str(rasterReqID))
    time.sleep(1) #I think I really need this, not sure why
    snakeRaster(rasterReqID)
#    set_field("xrecRasterFlag",100)    


def gotoMaxRaster(rasterResult,multiColThreshold=-1):
  if (rasterResult["result_obj"]["rasterCellResults"]['resultObj']["data"] == None):
    print("no raster result!!\n")
    return
  ceiling = 0.0
  floor = 100000000.0 #for resolution where small number means high score
  hotFile = ""
  scoreOption = ""
  print("in gotomax")
  print(rasterResult)
  cellResults = rasterResult["result_obj"]["rasterCellResults"]['resultObj']["data"]["response"]  
  rasterMap = rasterResult["result_obj"]["rasterCellMap"]  
  rasterScoreFlag = int(db_lib.beamlineInfo('john','rasterScoreFlag')["index"])
  if (rasterScoreFlag==0):
    scoreOption = "spot_count"
  elif (rasterScoreFlag==1):
    scoreOption = "d_min"
  else:
    scoreOption = "total_intensity"
  for i in range (0,len(cellResults)):
    scoreVal = float(cellResults[i][scoreOption])
    if (multiColThreshold>0):
      if (scoreVal > multiColThreshold):
        hitFile = cellResults[i]["image"]
        hitCoords = rasterMap[hitFile[:-4]]
#        sampID = rasterResult['result_obj']['sample_id']
        parentReqID = rasterResult['result_obj']["parentReqID"]
        addMultiRequestLocation(parentReqID,hitCoords,i)
    if (scoreOption == "d_min"):
      if (scoreVal < floor):
        floor = scoreVal
        hotFile = cellResults[i]["image"]
    else:
      if (scoreVal > ceiling):
        ceiling = scoreVal
        hotFile = cellResults[i]["image"]
  if (hotFile != ""):
    print(ceiling)
    print(floor)
    print(hotFile)
#    rasterMap = rasterResult["result_obj"]["rasterCellMap"]
    hotCoords = rasterMap[hotFile[:-4]] 
    x = hotCoords["x"]
    y = hotCoords["y"]
    z = hotCoords["z"]
    print("goto " + str(x) + " " + str(y) + " " + str(z))
    mvaDescriptor("sampleX",x,"sampleY",y,"sampleZ",z)
  

def addMultiRequestLocation(parentReqID,hitCoords,locIndex): #rough proto of what to pass here for details like how to organize data
  parentRequest = db_lib.getRequest(parentReqID)
  sampleID = parentRequest["sample_id"]

  print (str(sampleID))
  print (hitCoords)
  currentOmega = round(motorPosFromDescriptor("omega"),2)
#  runNum = db_lib.incrementSampleRequestCount(sampleID)
#  dataDirectory = parentRequest['directory']+"_"+str(locIndex)
  dataDirectory = parentRequest["request_obj"]['directory']+"multi_"+str(locIndex)
  runNum = parentRequest["request_obj"]['runNum']
  tempnewStratRequest = daq_utils.createDefaultRequest(sampleID)
  sweepStart = currentOmega - 5.0
  sweepEnd = currentOmega + 5.0
  imgWidth = parentRequest["request_obj"]['img_width']
  exptime = parentRequest["request_obj"]['exposure_time']
  currentDetDist = parentRequest["request_obj"]['detDist']
  
  newReqObj = tempnewStratRequest["request_obj"]
  newReqObj["sweep_start"] = sweepStart
  newReqObj["sweep_end"] = sweepEnd
  newReqObj["img_width"] = imgWidth
  newReqObj["exposure_time"] = exptime
  newReqObj["detDist"] = currentDetDist
  newReqObj["directory"] = dataDirectory  
  newReqObj["pos_x"] = hitCoords['x']
  newReqObj["pos_y"] = hitCoords['y']
  newReqObj["pos_z"] = hitCoords['z']
  newReqObj["fastDP"] = False
  newReqObj["fastEP"] = False
  newReqObj["xia2"] = False
  newReqObj["runNum"] = runNum
  newRequest = db_lib.addRequesttoSample(sampleID,newReqObj["protocol"],newReqObj,priority=6000) # a higher priority
  
    
#these next three differ a little from the gui. the gui uses isChecked, b/c it was too intense to keep hitting the pv, also screen pix vs image pix
def getCurrentFOV(): 
  fov = {"x":0.0,"y":0.0}
  fov["x"] = daq_utils.highMagFOVx
  fov["y"] = daq_utils.highMagFOVy
  return fov


def screenXmicrons2pixels(microns):
  fov = getCurrentFOV()
  fovX = fov["x"]
#  return int(round(microns*(daq_utils.highMagPixX/fovX)))
  return int(round(microns*(daq_utils.screenPixX/fovX)))

def screenYmicrons2pixels(microns):
  fov = getCurrentFOV()
  fovY = fov["y"]
  return int(round(microns*(daq_utils.screenPixY/fovY)))


def screenXPixels2microns(pixels):
  fov = getCurrentFOV()
  fovX = fov["x"]
  return float(pixels)*(fovX/daq_utils.screenPixX)
#  return float(pixels)*(fovX/daq_utils.highMagPixX)

def screenYPixels2microns(pixels):
  fov = getCurrentFOV()
  fovY = fov["y"]
  return float(pixels)*(fovY/daq_utils.screenPixY)
#  return float(pixels)*(fovY/daq_utils.highMagPixY)


def defineRectRaster(currentRequest,raster_w_s,raster_h_s,stepsizeMicrons_s): #maybe point_x and point_y are image center? #everything can come as microns, make this a horz vector scan, note this never deals with pixels.
  
  sampleID = currentRequest["sample_id"]
  raster_h = float(raster_h_s)
  raster_w = float(raster_w_s)
  stepsize = float(stepsizeMicrons_s)
  beamWidth = stepsize
  beamHeight = stepsize
  rasterDef = {"beamWidth":beamWidth,"beamHeight":beamHeight,"status":0,"x":motorPosFromDescriptor("sampleX"),"y":motorPosFromDescriptor("sampleY"),"z":motorPosFromDescriptor("sampleZ"),"omega":motorPosFromDescriptor("omega"),"stepsize":stepsize,"rowDefs":[]} 
  numsteps_h = int(raster_w/stepsize)
  numsteps_v = int(raster_h/stepsize) #the numsteps is decided in code, so is already odd
  point_offset_x = -(numsteps_h*stepsize)/2.0
  point_offset_y = -(numsteps_v*stepsize)/2.0
  if (numsteps_v > numsteps_h): #vertical raster
    for i in range(numsteps_h):
      vectorStartX = point_offset_x+(i*stepsize)
      vectorEndX = vectorStartX
      vectorStartY = point_offset_y
      vectorEndY = vectorStartY + (numsteps_v*stepsize)
      newRowDef = {"start":{"x": vectorStartX,"y":vectorStartY},"end":{"x":vectorEndX,"y":vectorEndY},"numsteps":numsteps_v}
      rasterDef["rowDefs"].append(newRowDef)
  else: #horizontal raster
    for i in range(numsteps_v):
      vectorStartX = point_offset_x
      vectorEndX = vectorStartX + (numsteps_h*stepsize)
      vectorStartY = point_offset_y+(i*stepsize)
      vectorEndY = vectorStartY
      newRowDef = {"start":{"x": vectorStartX,"y":vectorStartY},"end":{"x":vectorEndX,"y":vectorEndY},"numsteps":numsteps_h}
      rasterDef["rowDefs"].append(newRowDef)

  tempnewRasterRequest = daq_utils.createDefaultRequest(sampleID)
  reqObj = tempnewRasterRequest["request_obj"]
  reqObj["protocol"] = "raster"
  reqObj["exposure_time"] = .05
  reqObj["img_width"] = .05    
  reqObj["directory"] = reqObj["directory"]+"/rasterImages/"
  if (numsteps_h == 1): #column raster
    reqObj["file_prefix"] = reqObj["file_prefix"]+"_lineRaster"
    rasterDef["rasterType"] = "column"
  else:
    reqObj["file_prefix"] = reqObj["file_prefix"]+"_rectRaster"
    rasterDef["rasterType"] = "normal"
  reqObj["rasterDef"] = rasterDef #should this be something like self.currentRasterDef?
  reqObj["rasterDef"]["status"] = 1 # this will tell clients that the raster should be displayed.
  runNum = db_lib.incrementSampleRequestCount(sampleID)
  reqObj["runNum"] = runNum
  reqObj["parentReqID"] = currentRequest["request_id"]
  newRasterRequest = db_lib.addRequesttoSample(sampleID,reqObj["protocol"],reqObj,priority=5000)
  set_field("xrecRasterFlag",newRasterRequest["request_id"])  
  time.sleep(1)
  return newRasterRequest["request_id"]


def definePolyRaster(currentRequest,raster_w,raster_h,stepsizeMicrons,point_x,point_y,rasterPoly): #all come in as pixels
  sampleID = currentRequest["sample_id"]
  newRowDef = {}
  beamWidth = stepsizeMicrons
  beamHeight = stepsizeMicrons
  rasterDef = {"rasterType":"normal","beamWidth":beamWidth,"beamHeight":beamHeight,"status":0,"x":motorPosFromDescriptor("sampleX"),"y":motorPosFromDescriptor("sampleY"),"z":motorPosFromDescriptor("sampleZ"),"omega":motorPosFromDescriptor("omega"),"stepsize":stepsizeMicrons,"rowDefs":[]} #just storing step as microns, not using here
  stepsizeXPix = screenXmicrons2pixels(stepsizeMicrons)   #note conversion to pixels
  stepsizeYPix = screenYmicrons2pixels(stepsizeMicrons)   #note conversion to pixels  
  numsteps_h = int(raster_w/stepsizeXPix) #raster_w = width,goes to numsteps horizonatl
  numsteps_v = int(raster_h/stepsizeYPix)
  if (numsteps_h%2 == 0):
    numsteps_h = numsteps_h + 1
  if (numsteps_v%2 == 0):
    numsteps_v = numsteps_v + 1
  point_offset_x = -(numsteps_h*stepsizeXPix)/2
  point_offset_y = -(numsteps_v*stepsizeYPix)/2
  if (numsteps_v > numsteps_h): #vertical raster
    for i in range(numsteps_h):
      rowCellCount = 0
      for j in range(numsteps_v):
        newCellX = point_x+(i*stepsizeXPix)+point_offset_x
        newCellY = point_y+(j*stepsizeYPix)+point_offset_y
        if (rasterPoly.contains(QtCore.QPointF(newCellX+(stepsizeXPix/2.0),newCellY+(stepsizeYPix/2.0)))): #stepping through every cell to see if it's in the bounding box
          if (rowCellCount == 0): #start of a new row
            rowStartX = newCellX
            rowStartY = newCellY
          rowCellCount = rowCellCount+1
      if (rowCellCount != 0): #test for no points in this row of the bounding rect are in the poly?
        vectorStartX = screenXPixels2microns(rowStartX-daq_utils.screenPixCenterX)
        vectorEndX = vectorStartX 
        vectorStartY = screenYPixels2microns(rowStartY-daq_utils.screenPixCenterY)
        vectorEndY = vectorStartY + (rowCellCount*stepsizeMicrons)
        newRowDef = {"start":{"x": vectorStartX,"y":vectorStartY},"end":{"x":vectorEndX,"y":vectorEndY},"numsteps":rowCellCount}
        rasterDef["rowDefs"].append(newRowDef)
  else: #horizontal raster
  
    for i in range(numsteps_v):
      rowCellCount = 0
      for j in range(numsteps_h):
        newCellX = point_x+(j*stepsizeXPix)+point_offset_x
        newCellY = point_y+(i*stepsizeYPix)+point_offset_y
        if (rasterPoly.contains(QtCore.QPointF(newCellX+(stepsizeXPix/2.0),newCellY+(stepsizeYPix/2.0)))):
          if (rowCellCount == 0): #start of a new row
            rowStartX = newCellX
            rowStartY = newCellY
          rowCellCount = rowCellCount+1
      if (rowCellCount != 0): #no points in this row of the bounding rect are in the poly?
        vectorStartX = screenXPixels2microns(rowStartX-daq_utils.screenPixCenterX)
        vectorEndX = vectorStartX + (rowCellCount*stepsizeMicrons)
        vectorStartY = screenYPixels2microns(rowStartY-daq_utils.screenPixCenterY)
        vectorEndY = vectorStartY
        newRowDef = {"start":{"x": vectorStartX,"y":vectorStartY},"end":{"x":vectorEndX,"y":vectorEndY},"numsteps":rowCellCount}
  #      newRowDef = {"start":{"x": screenXPixels2microns(rowStartX-daq_utils.screenPixCenterX),"y":screenYPixels2microns(rowStartY-daq_utils.screenPixCenterY)},"numsteps":rowCellCount}      
        rasterDef["rowDefs"].append(newRowDef)
  tempnewRasterRequest = daq_utils.createDefaultRequest(sampleID)
  reqObj = tempnewRasterRequest["request_obj"]
  reqObj["protocol"] = "raster"
  reqObj["exposure_time"] = .05
  reqObj["img_width"] = .05  
  reqObj["directory"] = reqObj["directory"]+"/rasterImages/"
  reqObj["file_prefix"] = reqObj["file_prefix"]+"_polyRaster"
  reqObj["rasterDef"] = rasterDef #should this be something like self.currentRasterDef?
  reqObj["rasterDef"]["status"] = 1 # this will tell clients that the raster should be displayed.
  runNum = db_lib.incrementSampleRequestCount(sampleID)
  reqObj["runNum"] = runNum
  reqObj["parentReqID"] = currentRequest["request_id"]
  newRasterRequest = db_lib.addRequesttoSample(sampleID,reqObj["protocol"],reqObj,priority=5000)
  set_field("xrecRasterFlag",newRasterRequest["request_id"])  
  return newRasterRequest["request_id"]
#  daq_lib.refreshGuiTree() # not sure


def getXrecLoopShape(currentRequest):
  sampleID = currentRequest["sample_id"]
#  beamline_support.set_any_epics_pv("XF:17IDC-ES:FMX{Cam:07}MJPGZOOM:NDArrayPort","VAL","ROI1") #not the best, but I had timing issues doing it w/o a sleep
  for i in range(4):
    if (daq_lib.abort_flag == 1):
      return 0
    mvaDescriptor("omega",i*30)
    pic_prefix = "findloopshape_" + str(i)
    time.sleep(1.0) # for vid lag, sucks
    daq_utils.take_crystal_picture(filename=pic_prefix,czoom=1)
  comm_s = "xrec30 " + os.environ["CONFIGDIR"] + "/xrec30.txt xrec30_result.txt"
  os.system(comm_s)
  print ("face on = " + str(face_on))
  mvaDescriptor("omega",face_on) #global, yuk.
  os.system("cp /dev/shm/masks2_hull_0.txt loopPoints.txt")
  polyPoints = [] 
  rasterPoly = None     
  filename = "loopPoints.txt"
  xrec_out_file = open(filename,"r")  
  resultLine = xrec_out_file.readline()
  xrec_out_file.close() 
  tokens = resultLine.split()
  numpoints = int(tokens[0])
  for i in range(1,len(tokens)-1,2):
    point = [tokens[i],tokens[i+1]]
    correctedPoint = [daq_utils.screenPixX-int(tokens[i]),daq_utils.screenPixY-int(tokens[i+1])] 
    polyPoint = QtCore.QPointF(float(correctedPoint[0]),float(correctedPoint[1]))
    polyPoints.append(polyPoint)
    newLoopPoint = QtGui.QGraphicsEllipseItem(correctedPoint[0],correctedPoint[1],3,3)      
  rasterPoly = QtGui.QGraphicsPolygonItem(QtGui.QPolygonF(polyPoints))
  polyBoundingRect = rasterPoly.boundingRect()
  raster_w = int(polyBoundingRect.width())
  raster_h = int(polyBoundingRect.height())
  center_x = int(polyBoundingRect.center().x())
  center_y = int(polyBoundingRect.center().y())
  if (currentRequest['request_obj']['protocol'] == "multiCol"):
    stepsizeMicrons = currentRequest['request_obj']['gridStep']
  else:
    stepsizeMicrons = 30.0 #for now.
  rasterReqID = definePolyRaster(currentRequest,raster_w,raster_h,stepsizeMicrons,center_x,center_y,rasterPoly)
  return rasterReqID


def eScan(energyScanRequest):
  sampleID = energyScanRequest["sample_id"]
  reqObj = energyScanRequest["request_obj"]
  print("energy scan for " + str(reqObj['scanEnergy']))
  scan_element = "Se"
  scanID = dscan(omega,-20,20,10,1)
  scanData = db[scanID]
  scanDataTable = get_table(scanData,["omega","cam_7_stats1_total"])
  print(scanDataTable)
  if (reqObj["runChooch"]):
    chooch_prefix = "choochData1"
    choochOutfileName = chooch_prefix+".efs"
    choochInputFileName = "/nfs/skinner/temp/choochData1.raw"
    comm_s = "chooch -e %s -o %s %s" % (scan_element, choochOutfileName,choochInputFileName)
#  comm_s = "chooch -e %s -o %s -p %s %s" % (scan_element,chooch_prefix+".efs",chooch_prefix+".ps",chooch_prefix+".raw")
    print(comm_s)
    choochInputData_x = []
    choochInputData_y = []
    choochInputFile = open(choochInputFileName,"r")
    for outputLine in choochInputFile.readlines():
      tokens = outputLine.split()
      if (len(tokens) == 2): #not a very elegant way to get past the first two lines that I don't need.    
        choochInputData_x.append(float(tokens[0]))
        choochInputData_y.append(float(tokens[1]))
    choochInputFile.close()
    for outputline in os.popen(comm_s).readlines():
      print(outputline)
      tokens = outputline.split()    
      if (len(tokens)>4):
        if (tokens[1] == "peak"):
          peak = float(tokens[3])
          fprime_peak = float(tokens[7])
          f2prime_peak = float(tokens[5])        
        elif (tokens[1] == "infl"):
          infl = float(tokens[3])
          fprime_infl = float(tokens[7])
          f2prime_infl = float(tokens[5])        
        else:
          pass
#  os.system("xmgrace spectrum.spec&")
#  os.system("gv.sh "+chooch_prefix+".ps") #kludged with a shell call to get around gv bug
#  os.system("ln -sf "+chooch_prefix+".ps latest_chooch_plot.ps")
    choochResultObj = {}
    choochResultObj["infl"] = infl
    choochResultObj["peak"] = peak
    choochResultObj["f2prime_infl"] = f2prime_infl
    choochResultObj["fprime_infl"] = fprime_infl
    choochResultObj["f2prime_peak"] = f2prime_peak
    choochResultObj["fprime_peak"] = fprime_peak
    choochResultObj["sample_id"] = sampleID
    choochOutFile = open("/nfs/skinner/temp/choochData1.efs","r")
    chooch_graph_x = []
    chooch_graph_y1 = []
    chooch_graph_y2 = []
    for outLine in choochOutFile.readlines():
      tokens = outLine.split()
      chooch_graph_x.append(float(tokens[0]))
      chooch_graph_y1.append(float(tokens[1]))
      chooch_graph_y2.append(float(tokens[2]))
    choochOutFile.close()
    choochResultObj["choochOutXAxis"] = chooch_graph_x
    choochResultObj["choochOutY1Axis"] = chooch_graph_y1
    choochResultObj["choochOutY2Axis"] = chooch_graph_y2
    choochResultObj["choochInXAxis"] = choochInputData_x
    choochResultObj["choochInYAxis"] = choochInputData_y  
#    plt.plot(chooch_graph_x,chooch_graph_y1)
#    plt.plot(chooch_graph_x,chooch_graph_y2)
#    plt.show()
#    print(choochResultObj)
    choochResult = db_lib.addResultforRequest("choochResult",energyScanRequest["request_id"], choochResultObj)
    choochResultID = choochResult["result_id"]
    set_field("choochResultFlag",choochResultID)


def vectorScan(vecRequest): 
  reqObj = vecRequest["request_obj"]
  sweep_start_angle = reqObj["sweep_start"]
  sweep_end_angle = reqObj["sweep_end"]
  imgWidth = reqObj["img_width"]
  expTime = reqObj["exposure_time"]
  numImages = int((sweep_end_angle - sweep_start_angle) / imgWidth)
#  numSteps = int(numImages/reqObj["vectorParams"]["fpp"]) #not needed anymore?
  x_vec_start=reqObj["vectorParams"]["vecStart"]["x"]
  y_vec_start=reqObj["vectorParams"]["vecStart"]["y"]
  z_vec_start=reqObj["vectorParams"]["vecStart"]["z"]
  x_vec_end=reqObj["vectorParams"]["vecEnd"]["x"]
  y_vec_end=reqObj["vectorParams"]["vecEnd"]["y"]
  z_vec_end=reqObj["vectorParams"]["vecEnd"]["z"]
  beamline_support.setPvValFromDescriptor("vectorStartOmega",sweep_start_angle)
  beamline_support.setPvValFromDescriptor("vectorStepOmega",imgWidth)
  beamline_support.setPvValFromDescriptor("vectorStartX",x_vec_start)
  beamline_support.setPvValFromDescriptor("vectorStartY",y_vec_start)  
  beamline_support.setPvValFromDescriptor("vectorStartZ",z_vec_start)  
  beamline_support.setPvValFromDescriptor("vectorEndX",x_vec_end)
  beamline_support.setPvValFromDescriptor("vectorEndY",y_vec_end)  
  beamline_support.setPvValFromDescriptor("vectorEndZ",z_vec_end)  
  beamline_support.setPvValFromDescriptor("vectorframeExptime",expTime)
  beamline_support.setPvValFromDescriptor("vectorNumFrames",numImages)
  beamline_support.setPvValFromDescriptor("vectorGo",1)
  vectorWait()


def dna_execute_collection3(dna_start,dna_range,dna_number_of_images,dna_exptime,dna_directory,prefix,start_image_number,overlap,dna_run_num,charRequest):
  global collect_and_characterize_success,dna_have_strategy_results,dna_have_index_results,picture_taken
  global dna_strategy_exptime,dna_strategy_start,dna_strategy_range,dna_strategy_end,dna_strat_dist
  global screeningoutputid
  
  characterizationParams = charRequest["request_obj"]["characterizationParams"]
  dna_res = float(characterizationParams["aimed_resolution"])
  print("dna_res = " + str(dna_res))
  dna_filename_list = []
  print("number of images " + str(dna_number_of_images) + " overlap = " + str(overlap) + " dna_start " + str(dna_start) + " dna_range " + str(dna_range) + " prefix " + prefix + " start number " + str(start_image_number) + "\n")
  collect_and_characterize_success = 0
  dna_have_strategy_results = 0
  dna_have_index_results = 0  
  dg2rd = 3.14159265 / 180.0  
  if (daq_utils.detector_id == "ADSC-Q315"):
    det_radius = 157.5
  elif (daq_utils.detector_id == "ADSC-Q210"):
    det_radius = 105.0
  elif (daq_utils.detector_id == "PILATUS-6"):
    det_radius = 212.0
  else: #default Pilatus
    det_radius = 212.0
#####  theta_radians = daq_lib.get_field("theta") * dg2rd
  theta_radians = 0.0
  wave = 12398.5/beamline_lib.get_mono_energy() #for now
  dx = det_radius/(tan(2.0*(asin(wave/(2.0*dna_res)))-theta_radians))
  print("distance = ",dx)
#skinner - could move distance and wave and scan axis here, leave wave alone for now
  print("skinner about to take reference images.")
  for i in range(0,int(dna_number_of_images)):
    print("skinner prefix7 = " + prefix[0:7] +  " " + str(start_image_number) + "\n")
    if (len(prefix)> 8):
      if ((prefix[0:7] == "postref") and (start_image_number == 1)):
        print("skinner postref bail\n")
        time.sleep(float(dna_number_of_images*float(dna_exptime)))        
        break
  #skinner roi - maybe I can measure and use that for dna_start so that first image is face on.
    dna_start = daq_lib.get_field("datum_omega")
    colstart = float(dna_start) + (i*(abs(overlap)+float(dna_range)))
    dna_prefix = "ref-"+prefix
#12/15 not sure why dna_run_num in prefix    dna_prefix = "ref-"+prefix+"_"+str(dna_run_num)
    image_number = start_image_number+i
    dna_prefix_long = dna_directory+"/"+dna_prefix
    filename = daq_utils.create_filename(dna_prefix_long,image_number)
    beamline_lib.mvaDescriptor("omega",float(colstart))
#####    daq_lib.move_axis_absolute(daq_lib.get_field("scan_axis"),colstart)
#####    daq_lib.take_image(colstart,dna_range,dna_exptime,filename,daq_lib.get_field("scan_axis"),0,1)
    daq_utils.take_crystal_picture(reqID=charRequest["request_id"])
######### BECAUSE I FAKE IT    imagesAttempted = collect_detector_seq(dna_range,dna_range,dna_exptime,dna_prefix,dna_directory,image_number) 
    if (i==0):
      commFake = "ln -sf /nfs/skinner/testdata/johnPil6/data/B1GGTApo_9_00001.cbf " + filename
    else:
      commFake = "ln -sf /nfs/skinner/testdata/johnPil6/data/B1GGTApo_9_00181.cbf " + filename
    os.system(commFake)
    print(commFake)
    dna_filename_list.append(filename)
###4/16, don't bother with image server for now    diffImgJpegData = daq_utils.diff2jpeg(filename,reqID=charRequest["request_id"]) #returns a dictionary
#    diffImgJpegData["timestamp"] = time.time()
#    imgRef = db_lib.addFile(diffImgJpegData["data"])
#    diffImgJpegData["data"] = imgRef
#    imgRef = db_lib.addFile(diffImgJpegData["thumbData"])
#    diffImgJpegData["thumbData"] = imgRef
    picture_taken = 1
#                xml_from_file_list(flux,x_beamsize,y_beamsize,max_exptime_per_dc,aimed_completeness,file_list):
  edna_energy_ev = (12.3985/wave) * 1000.0
#####  xbeam_size = beamline_lib.get_motor_pos("slitHum")
#####  ybeam_size = beamline_lib.get_motor_pos("slitVum")
#  if (xbeam_size == 0.0 or ybeam_size == 0.0): #don't know where to get these from yet
  if (1): 
    xbeam_size = .1
    ybeam_size = .16
  else:
    xbeam_size = xbeam_size/1000
    ybeam_size = ybeam_size/1000    
  aimed_completeness = characterizationParams['aimed_completeness']
  aimed_multiplicity = characterizationParams['aimed_multiplicity']
  aimed_resolution = characterizationParams['aimed_resolution']
  aimed_ISig = characterizationParams['aimed_ISig']
  timeout_check = 0;
#####  while(not os.path.exists(dna_filename_list[len(dna_filename_list)-1])): #this waits for edna images
  if (0):
    timeout_check = timeout_check + 1
    time.sleep(1.0)
    if (timeout_check > 10):
      break
#####  flux = 10000000000 * beamline_lib.get_epics_pv("flux","VAL")
  flux = 600000000.0  #for now
  edna_input_filename = dna_directory + "/adsc1_in.xml"
  
  comm_s = "ssh -q xf17id1-srv1 \"" + os.environ["LSDCHOME"] + "/runEdna.py " + dna_directory + " " + dna_prefix + " " + str(aimed_ISig) + " " + str(flux) + " " + str(xbeam_size) + " " + str(ybeam_size) + " " + edna_input_filename + " " + str(charRequest["request_id"]) + "\""
  print(comm_s)
  os.system(comm_s)

  return 1


