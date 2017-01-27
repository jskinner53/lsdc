import beamline_support
import beamline_lib #did this really screw me if I imported b/c of daq_utils import??
from beamline_lib import *
import daq_lib
from daq_lib import *
import daq_utils
import db_lib
import det_lib
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
import super_state_machine
import _thread
import parseSheet
import attenCalc

global dialsResultDict, rasterRowResultsList, processedRasterRowCount

dialsResultDict = {}
rasterRowResultsList = []


def hi_macro():
  print("hello from macros\n")
  daq_lib.broadcast_output("broadcast hi")


def BS():
  movr(omega,40)

def BS2():
  ascan(omega,0,100,10)

def abortBS():
  if (RE.state != "idle"):
    try:
      RE.abort()
    except super_state_machine.errors.TransitionError:
      print("caught BS")

def changeImageCenterLowMag(x,y,czoom):
  zoom = int(czoom)
  zoomMinXRBV = beamline_support.getPvValFromDescriptor("lowMagZoomMinXRBV")
  zoomMinYRBV = beamline_support.getPvValFromDescriptor("lowMagZoomMinYRBV")
  minXRBV = beamline_support.getPvValFromDescriptor("lowMagMinXRBV")
  minYRBV = beamline_support.getPvValFromDescriptor("lowMagMinYRBV")
  
  sizeXRBV = beamline_support.getPvValFromDescriptor("lowMagZoomSizeXRBV")
  sizeYRBV = beamline_support.getPvValFromDescriptor("lowMagZoomSizeYRBV")
  sizeXRBV = 640.0
  sizeYRBV = 512.0
  roiSizeXRBV = beamline_support.getPvValFromDescriptor("lowMagROISizeXRBV")
  roiSizeYRBV = beamline_support.getPvValFromDescriptor("lowMagROISizeYRBV")  
  roiSizeZoomXRBV = beamline_support.getPvValFromDescriptor("lowMagZoomROISizeXRBV")
  roiSizeZoomYRBV = beamline_support.getPvValFromDescriptor("lowMagZoomROISizeYRBV")
  inputSizeZoomXRBV = beamline_support.getPvValFromDescriptor("lowMagZoomMaxSizeXRBV")
  inputSizeZoomYRBV = beamline_support.getPvValFromDescriptor("lowMagZoomMaxSizeYRBV")      
  inputSizeXRBV = beamline_support.getPvValFromDescriptor("lowMagMaxSizeXRBV")
  inputSizeYRBV = beamline_support.getPvValFromDescriptor("lowMagMaxSizeYRBV")      
  x_click = float(x)
  y_click = float(y)
  binningFactor = 2.0  
  if (zoom):
    xclickFullFOV = x_click + zoomMinXRBV
    yclickFullFOV = y_click + zoomMinYRBV
  else:
    binningFactor = 2.0
    xclickFullFOV = (x_click * binningFactor) + minXRBV
    yclickFullFOV = (y_click * binningFactor) + minYRBV    
  new_minXZoom = xclickFullFOV-(sizeXRBV/2.0)
  new_minYZoom = yclickFullFOV-(sizeYRBV/2.0)
  new_minX = new_minXZoom - (sizeXRBV/2.0)
  new_minY = new_minYZoom - (sizeYRBV/2.0)
#  if (new_minXZoom < 0):
#    return
#    new_minXZoom = 0
#  if (new_minYZoom < 0):
#    return    
#    new_minYZoom = 0
#  if (new_minXZoom+roiSizeZoomXRBV>inputSizeZoomXRBV):
#    return
#  if (new_minYZoom+roiSizeZoomYRBV>inputSizeZoomYRBV):
#    return
  noZoomCenterX = sizeXRBV/2.0
  noZoomCenterY = sizeYRBV/2.0  
#  if (daq_utils.detector_id != "EIGER-16"): #sloppy short circuit until fix up amx
#  if (1): #sloppy short circuit until fix up amx    
#    return
  if (new_minX < 0):
    print("1")
    new_minX = 0
    noZoomCenterX = (new_minXZoom+(sizeXRBV/2.0))/binningFactor
  if (new_minY < 0):
    print("2")    
    new_minY = 0    
    noZoomCenterY = (new_minYZoom+(sizeYRBV/2.0))/binningFactor
  if (new_minX+roiSizeXRBV>inputSizeXRBV):
    print("3")    
    new_minX = inputSizeXRBV-roiSizeXRBV    
    noZoomCenterX = ((new_minXZoom+(sizeXRBV/2.0)) - new_minX)/binningFactor
  if (new_minY+roiSizeYRBV>inputSizeYRBV):
    print("4")    
    new_minY = inputSizeYRBV-roiSizeYRBV
    noZoomCenterY = ((new_minYZoom+(sizeYRBV/2.0)) - new_minY)/binningFactor    
#    noZoomCenterY = (new_minYZoom+(sizeYRBV/2.0))/binningFactor
  if (new_minXZoom+roiSizeZoomXRBV>inputSizeZoomXRBV):
    new_minXZoom = inputSizeZoomXRBV-roiSizeZoomXRBV
  if (new_minXZoom < 0):
    new_minXZoom = 0
  beamline_support.setPvValFromDescriptor("lowMagZoomMinX",new_minXZoom)    
  if (new_minYZoom+roiSizeZoomYRBV>inputSizeZoomYRBV):
    new_minYZoom = inputSizeZoomYRBV-roiSizeZoomYRBV
  if (new_minYZoom < 0):
    new_minYZoom = 0
  beamline_support.setPvValFromDescriptor("lowMagZoomMinY",new_minYZoom)        
  beamline_support.setPvValFromDescriptor("lowMagMinX",new_minX)
  beamline_support.setPvValFromDescriptor("lowMagMinY",new_minY)    
  beamline_support.setPvValFromDescriptor("lowMagCursorX",noZoomCenterX)
  beamline_support.setPvValFromDescriptor("lowMagCursorY",noZoomCenterY)  
      

def changeImageCenterHighMag(x,y,czoom):
  zoom = int(czoom)
  zoomMinXRBV = beamline_support.getPvValFromDescriptor("highMagZoomMinXRBV")
  zoomMinYRBV = beamline_support.getPvValFromDescriptor("highMagZoomMinYRBV")
  minXRBV = beamline_support.getPvValFromDescriptor("highMagMinXRBV")
  minYRBV = beamline_support.getPvValFromDescriptor("highMagMinYRBV")
  
  sizeXRBV = beamline_support.getPvValFromDescriptor("highMagZoomSizeXRBV")
  sizeYRBV = beamline_support.getPvValFromDescriptor("highMagZoomSizeYRBV")
  sizeXRBV = 640.0
  sizeYRBV = 512.0
  roiSizeXRBV = beamline_support.getPvValFromDescriptor("highMagROISizeXRBV")
  roiSizeYRBV = beamline_support.getPvValFromDescriptor("highMagROISizeYRBV")  
  roiSizeZoomXRBV = beamline_support.getPvValFromDescriptor("highMagZoomROISizeXRBV")
  roiSizeZoomYRBV = beamline_support.getPvValFromDescriptor("highMagZoomROISizeYRBV")
  inputSizeZoomXRBV = beamline_support.getPvValFromDescriptor("highMagZoomMaxSizeXRBV")
  inputSizeZoomYRBV = beamline_support.getPvValFromDescriptor("highMagZoomMaxSizeYRBV")      
  inputSizeXRBV = beamline_support.getPvValFromDescriptor("highMagMaxSizeXRBV")
  inputSizeYRBV = beamline_support.getPvValFromDescriptor("highMagMaxSizeYRBV")      
  x_click = float(x)
  y_click = float(y)
  binningFactor = 2.0  
  if (zoom):
    xclickFullFOV = x_click + zoomMinXRBV
    yclickFullFOV = y_click + zoomMinYRBV
  else:
    binningFactor = 2.0
    xclickFullFOV = (x_click * binningFactor) + minXRBV
    yclickFullFOV = (y_click * binningFactor) + minYRBV    
  new_minXZoom = xclickFullFOV-(sizeXRBV/2.0)
  new_minYZoom = yclickFullFOV-(sizeYRBV/2.0)
  new_minX = new_minXZoom - (sizeXRBV/2.0)
  new_minY = new_minYZoom - (sizeYRBV/2.0)
#  if (new_minXZoom < 0 or new_minYZoom < 0):
#    return  
#  if (new_minXZoom+roiSizeZoomXRBV>inputSizeZoomXRBV):
#    return
#  if (new_minYZoom+roiSizeZoomYRBV>inputSizeZoomYRBV):
#    return
  noZoomCenterX = sizeXRBV/2.0
  noZoomCenterY = sizeYRBV/2.0  
#  if (daq_utils.detector_id != "EIGER-16"): #sloppy short circuit until fix up amx
#  if (1): #sloppy short circuit until fix up amx    
#    return
  if (new_minX < 0):
    print("1")
    new_minX = 0
    noZoomCenterX = (new_minXZoom+(sizeXRBV/2.0))/binningFactor
  if (new_minY < 0):
    print("2")    
    new_minY = 0    
    noZoomCenterY = (new_minYZoom+(sizeYRBV/2.0))/binningFactor
  if (new_minX+roiSizeXRBV>inputSizeXRBV):
    print("3")    
    new_minX = inputSizeXRBV-roiSizeXRBV    
    noZoomCenterX = ((new_minXZoom+(sizeXRBV/2.0)) - new_minX)/binningFactor
  if (new_minY+roiSizeYRBV>inputSizeYRBV):
    print("4")    
    new_minY = inputSizeYRBV-roiSizeYRBV
    noZoomCenterY = ((new_minYZoom+(sizeYRBV/2.0)) - new_minY)/binningFactor    
#    noZoomCenterY = (new_minYZoom+(sizeYRBV/2.0))/binningFactor

  if (new_minXZoom+roiSizeZoomXRBV>inputSizeZoomXRBV):
    new_minXZoom = inputSizeZoomXRBV-roiSizeZoomXRBV
  if (new_minXZoom < 0):
    new_minXZoom = 0
  if (new_minYZoom+roiSizeZoomYRBV>inputSizeZoomYRBV):
    new_minYZoom = inputSizeZoomYRBV-roiSizeZoomYRBV
  if (new_minYZoom < 0):
    new_minYZoom = 0
  beamline_support.setPvValFromDescriptor("highMagZoomMinX",new_minXZoom)
  beamline_support.setPvValFromDescriptor("highMagZoomMinY",new_minYZoom)
  beamline_support.setPvValFromDescriptor("highMagMinX",new_minX)
  beamline_support.setPvValFromDescriptor("highMagMinY",new_minY)    
  beamline_support.setPvValFromDescriptor("highMagCursorX",noZoomCenterX)
  beamline_support.setPvValFromDescriptor("highMagCursorY",noZoomCenterY)
  

  
  
def changeImageCenterLowMagObsolete(x,y):
#  if (daq_utils.detector_id != "EIGER-16"): #sloppy short circuit until fix up amx
#  if (1): #sloppy short circuit until fix up amx    
#    return
  minXRBV = beamline_support.getPvValFromDescriptor("lowMagMinXRBV")
  minYRBV = beamline_support.getPvValFromDescriptor("lowMagMinYRBV")
  sizeXRBV = beamline_support.getPvValFromDescriptor("lowMagSizeXRBV")
  sizeYRBV = beamline_support.getPvValFromDescriptor("lowMagSizeYRBV")
  sizeXRBV = 640.0
  sizeYRBV = 512.0
  roiSizeXRBV = beamline_support.getPvValFromDescriptor("lowMagROISizeXRBV")
  roiSizeYRBV = beamline_support.getPvValFromDescriptor("lowMagROISizeYRBV")  
  roiSizeZoomXRBV = beamline_support.getPvValFromDescriptor("lowMagZoomROISizeXRBV")
  roiSizeZoomYRBV = beamline_support.getPvValFromDescriptor("lowMagZoomROISizeYRBV")
  inputSizeZoomXRBV = beamline_support.getPvValFromDescriptor("lowMagZoomMaxSizeXRBV")
  inputSizeZoomYRBV = beamline_support.getPvValFromDescriptor("lowMagZoomMaxSizeYRBV")      
  inputSizeXRBV = beamline_support.getPvValFromDescriptor("lowMagMaxSizeXRBV")
  inputSizeYRBV = beamline_support.getPvValFromDescriptor("lowMagMaxSizeYRBV")      
  
  x_click = float(x)
  y_click = float(y)  
  new_minX = minXRBV + (2.0*(x_click-(sizeXRBV/2.0)))
  new_minY = minYRBV + (2.0*(y_click-(sizeYRBV/2.0)))
  new_minXZoom = new_minX + (sizeXRBV/2.0)
  new_minYZoom = new_minY + (sizeYRBV/2.0)    
  if (new_minX < 0 or new_minY < 0):
    return
  if (new_minXZoom+roiSizeZoomXRBV>inputSizeZoomXRBV):
    return
  if (new_minYZoom+roiSizeZoomYRBV>inputSizeZoomYRBV):
    return
  if (new_minX+roiSizeXRBV>inputSizeXRBV):
    return
  if (new_minY+roiSizeYRBV>inputSizeYRBV):
    return
  beamline_support.setPvValFromDescriptor("lowMagMinX",new_minX)
  beamline_support.setPvValFromDescriptor("lowMagMinY",new_minY)    
  beamline_support.setPvValFromDescriptor("lowMagZoomMinX",new_minXZoom)
  beamline_support.setPvValFromDescriptor("lowMagZoomMinY",new_minYZoom)    


def changeImageCenterHighMagZoomObsolete(x,y):
  minXRBV = beamline_support.getPvValFromDescriptor("highMagZoomMinXRBV")
  minYRBV = beamline_support.getPvValFromDescriptor("highMagZoomMinYRBV")
  sizeXRBV = beamline_support.getPvValFromDescriptor("highMagZoomSizeXRBV")
  sizeYRBV = beamline_support.getPvValFromDescriptor("highMagZoomSizeYRBV")
  sizeXRBV = 640.0
  sizeYRBV = 512.0    
  x_click = float(x)
  y_click = float(y)  
  new_minX = minXRBV + (x_click-(sizeXRBV/2.0))
  new_minY = minYRBV + (y_click-(sizeYRBV/2.0))
#  new_minX_nozoom = new_minX - (sizeXRBV/2.0)
#  new_minY_nozoom = new_minY - (sizeYRBV/2.0)  
  beamline_support.setPvValFromDescriptor("highMagZoomMinX",new_minX)
  beamline_support.setPvValFromDescriptor("highMagZoomMinY",new_minY)
#  if (daq_utils.detector_id != "EIGER-16"): #sloppy short circuit until fix up amx
#    return  
#  beamline_support.setPvValFromDescriptor("highMagMinX",new_minX_nozoom)
#  beamline_support.setPvValFromDescriptor("highMagMinY",new_minY_nozoom)    

def changeImageCenterLowMagZoomObsolete(x,y):
  minXRBV = beamline_support.getPvValFromDescriptor("lowMagZoomMinXRBV")
  minYRBV = beamline_support.getPvValFromDescriptor("lowMagZoomMinYRBV")
  sizeXRBV = beamline_support.getPvValFromDescriptor("lowMagZoomSizeXRBV")
  sizeYRBV = beamline_support.getPvValFromDescriptor("lowMagZoomSizeYRBV")
  sizeXRBV = 640.0
  sizeYRBV = 512.0
  roiSizeXRBV = beamline_support.getPvValFromDescriptor("lowMagROISizeXRBV")
  roiSizeYRBV = beamline_support.getPvValFromDescriptor("lowMagROISizeYRBV")  
  roiSizeZoomXRBV = beamline_support.getPvValFromDescriptor("lowMagZoomROISizeXRBV")
  roiSizeZoomYRBV = beamline_support.getPvValFromDescriptor("lowMagZoomROISizeYRBV")
  inputSizeZoomXRBV = beamline_support.getPvValFromDescriptor("lowMagZoomMaxSizeXRBV")
  inputSizeZoomYRBV = beamline_support.getPvValFromDescriptor("lowMagZoomMaxSizeYRBV")      
  inputSizeXRBV = beamline_support.getPvValFromDescriptor("lowMagMaxSizeXRBV")
  inputSizeYRBV = beamline_support.getPvValFromDescriptor("lowMagMaxSizeYRBV")      
  x_click = float(x)
  y_click = float(y)  
  new_minXZoom = minXRBV + (x_click-(sizeXRBV/2.0))
  new_minYZoom = minYRBV + (y_click-(sizeYRBV/2.0))
  new_minX = new_minXZoom - (sizeXRBV/2.0)
  new_minY = new_minYZoom - (sizeYRBV/2.0)
  if (new_minXZoom < 0 or new_minYZoom < 0):
    return  
  if (new_minXZoom+roiSizeZoomXRBV>inputSizeZoomXRBV):
    return
  if (new_minYZoom+roiSizeZoomYRBV>inputSizeZoomYRBV):
    return
  beamline_support.setPvValFromDescriptor("lowMagZoomMinX",new_minXZoom)
  beamline_support.setPvValFromDescriptor("lowMagZoomMinY",new_minYZoom)
  noZoomCenterX = sizeXRBV/2.0
  noZoomCenterY = sizeYRBV/2.0  
#  if (daq_utils.detector_id != "EIGER-16"): #sloppy short circuit until fix up amx
#  if (1): #sloppy short circuit until fix up amx    
#    return
  binningFactor = 2.0
  if (new_minX < 0):
    print("1")
    new_minX = 0
    noZoomCenterX = (new_minXZoom+(sizeXRBV/2.0))/binningFactor
  if (new_minY < 0):
    print("2")    
    new_minY = 0    
    noZoomCenterY = (new_minYZoom+(sizeYRBV/2.0))/binningFactor
  if (new_minX+roiSizeXRBV>inputSizeXRBV):
    print("3")    
    new_minX = inputSizeXRBV-roiSizeXRBV    
    noZoomCenterX = ((new_minXZoom+(sizeXRBV/2.0)) - new_minX)/binningFactor
  if (new_minY+roiSizeYRBV>inputSizeYRBV):
    print("4")    
    new_minY = inputSizeYRBV-roiSizeYRBV
    noZoomCenterY = ((new_minYZoom+(sizeYRBV/2.0)) - new_minY)/binningFactor    
#    noZoomCenterY = (new_minYZoom+(sizeYRBV/2.0))/binningFactor
  beamline_support.setPvValFromDescriptor("lowMagMinX",new_minX)
  beamline_support.setPvValFromDescriptor("lowMagMinY",new_minY)    
  beamline_support.setPvValFromDescriptor("lowMagCursorX",noZoomCenterX)
  beamline_support.setPvValFromDescriptor("lowMagCursorY",noZoomCenterY)  

  
  

def autoRasterLoop(currentRequest):
  return 1 #short circuit for commissioning
  set_field("xrecRasterFlag","100")        
  sampleID = currentRequest["sample"]
  print("auto raster " + str(sampleID))
  status = loop_center_xrec()
  if (status == -99): #abort, never hit this
    db_lib.updatePriority(currentRequest["uid"],5000)
    return 0    
  if not (status):
    return 0
  time.sleep(1) #looks like I really need this sleep, they really improve the appearance 
  runRasterScan(currentRequest,"LoopShape")
  time.sleep(1.5) 
  runRasterScan(currentRequest,"Fine")
  time.sleep(1) 
  runRasterScan(currentRequest,"Line")  
  time.sleep(1)
  return 1

def multiCol(currentRequest):
  set_field("xrecRasterFlag","100")      
  sampleID = currentRequest["sample"]
  print("multiCol " + str(sampleID))
  status = loop_center_xrec()
  if not (status):
    return 0  
  time.sleep(1) #looks like I really need this sleep, they really improve the appearance 
  runRasterScan(currentRequest,"LoopShape")
#  time.sleep(1) 

def loop_center_xrec():
  global face_on

  daq_lib.abort_flag = 0    

  for i in range(0,360,40):
    if (daq_lib.abort_flag == 1):
      print("caught abort in loop center")
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
  x_center = daq_utils.highMagPixX/2
  y_center = daq_utils.highMagPixY/2
#  x_center = daq_utils.lowMagPixX/2
#  y_center = daq_utils.lowMagPixY/2
  
#  set_epics_pv("image_X_center","A",x_center)
#  set_epics_pv("image_Y_center","A",y_center)
  print("center on click " + str(x_center) + " " + str(y_center-radius))
  print("center on click " + str((x_center*2) - y_centre_xrec) + " " + str(x_centre_xrec))
  fovx = daq_utils.highMagFOVx
  fovy = daq_utils.highMagFOVy
#  fovx = daq_utils.lowMagFOVx
#  fovy = daq_utils.lowMagFOVy
  
  center_on_click(x_center,y_center-radius,fovx,fovy,source="macro")
  center_on_click((x_center*2) - y_centre_xrec,x_centre_xrec,fovx,fovy,source="macro")
#  center_on_click(y_centre_xrec,x_centre_xrec,source="macro")  
  mvaDescriptor("omega",face_on)
  #now try to get the loopshape starting from here
  return 1

def fakeDC(directory,filePrefix,numstart,numimages):
  if (numimages > 900):
    return
  testImgFileList = glob.glob("/GPFS/CENTRAL/XF17ID1/skinner/eiger16M/cbf/*.cbf")    
#  testImgFileList = glob.glob("/GPFS/CENTRAL/XF17ID1/skinner/testdata/johnPil6/data/B1GGTApo_9_0*.cbf")  
  testImgFileList.sort()
  prefix_long = directory+"/"+filePrefix
  expectedFilenameList = []
  for i in range (numstart,numstart+numimages):
    filename = daq_utils.create_filename(prefix_long,i)
    expectedFilenameList.append(filename)
  for i in range (0,len(expectedFilenameList)):
    comm_s = "ln -sf " + testImgFileList[i] + " " + expectedFilenameList[i]
#    print(comm_s)
    os.system(comm_s)



def generateGridMap(rasterRequest):
  global dialsResultDict,rasterRowResultsList

  reqObj = rasterRequest["request_obj"]
  rasterDef = reqObj["rasterDef"]
  stepsize = float(rasterDef["stepsize"])
  omega = float(rasterDef["omega"])
  rasterStartX = float(rasterDef["x"])
  rasterStartY = float(rasterDef["y"])
  rasterStartZ = float(rasterDef["z"])
  omegaRad = math.radians(omega)
  filePrefix = reqObj["directory"]+"/"+reqObj["file_prefix"]
  testImgFileList = glob.glob("/GPFS/CENTRAL/XF17ID1/skinner/eiger16M/cbf/*.cbf")  
#  testImgFileList = glob.glob("/GPFS/CENTRAL/XF17ID1/skinner/testdata/Eiger1M/*.cbf")
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
      if (daq_utils.detector_id == "EIGER-16"):
        dataFileName = "%s_%06d.cbf" % (reqObj["directory"]+"/cbf/"+reqObj["file_prefix"]+"_Raster_"+str(i),j+1)
      else:
        dataFileName = daq_utils.create_filename(filePrefix+"_Raster_"+str(i),j+1)

 ##     comm_s = "ln -sf " + testImgFileList[testImgCount] + " " + dataFileName      
##      os.system(comm_s)
      testImgCount+=1
      rasterCellCoords = {"x":xMotCellAbsoluteMove,"y":yMotAbsoluteMove,"z":zMotAbsoluteMove}
      rasterCellMap[dataFileName[:-4]] = rasterCellCoords
#commented out all of the processing, as this should have been done by the thread
  if ("parentReqID" in rasterRequest["request_obj"]):
    parentReqID = rasterRequest["request_obj"]["parentReqID"]
  else:
    parentReqID = -1
  print("RASTER CELL RESULTS")
#  print(rasterCellMap)
  dialsResultLocalList = []
  for i in range (0,len(rasterRowResultsList)):
    for j in range (0,len(rasterRowResultsList[i])):
      try:
        dialsResultLocalList.append(rasterRowResultsList[i][j])
      except KeyError: #this is to deal with single cell row. Instead of getting back a list of one row, I get back just the row from Dials.
        dialsResultLocalList.append(rasterRowResultsList[i])
        break
###############
  print(dialsResultLocalList)

  rasterResultObj = {"sample_id": rasterRequest["sample"],"parentReqID":parentReqID,"rasterCellMap":rasterCellMap,"rasterCellResults":{"type":"dialsRasterResult","resultObj":dialsResultLocalList}}
  rasterResultID = db_lib.addResultforRequest("rasterResult",rasterRequest["uid"], owner=daq_utils.owner,result_obj=rasterResultObj)
  rasterResult = db_lib.getResult(rasterResultID)
  return rasterResult


def setVectorDelay(delayVal):
  beamline_support.setPvValFromDescriptor("vectorDelay",float(delayVal))

def getVectorDelay():
  return beamline_support.getPvValFromDescriptor("vectorDelay")

def rasterWait():
  time.sleep(0.2)
  while (beamline_support.getPvValFromDescriptor("RasterActive")):
    time.sleep(0.2)

def vectorWait():
  time.sleep(0.15)
  while (beamline_support.getPvValFromDescriptor("VectorActive")):
    time.sleep(0.05)


def runDialsThread(directory,prefix,rowIndex,rowCellCount,seqNum):
  global rasterRowResultsList,processedRasterRowCount

  if (daq_utils.detector_id == "EIGER-16"):
    if (rowIndex%2 == 0):
#      node = "cpu-010"
      node = "cpu-009"      
    else:
      node = "cpu-010"
  else:
    if (rowIndex%2 == 0):
      node = "cpu-004"
    else:
      node = "cpu-005"
  if (seqNum>-1): #eiger
    cbfDir = directory+"/cbf"
    comm_s = "mkdir -p " + cbfDir
    os.system(comm_s)
    hdfSampleDataPattern = directory+"/"+prefix+"_" 
    hdfRowFilepattern = hdfSampleDataPattern + str(rowIndex) + "_" + str(int(float(seqNum))) + "_master.h5"
    CBF_conversion_pattern = cbfDir + "/" + prefix+"_" + str(rowIndex)+"_"  
    comm_s = "eiger2cbf-linux " + hdfRowFilepattern
    if (rowCellCount==1): #account for bug in converter
      comm_s = "ssh -q " + node + " \"/usr/local/crys-local/bin/eiger2cbf-linux " + hdfRowFilepattern  + " 1 " + CBF_conversion_pattern + "000001.cbf\""    
    else:
      comm_s = "ssh -q " + node + " \"/usr/local/crys-local/bin/eiger2cbf-linux " + hdfRowFilepattern  + " 1:" + str(rowCellCount) + " " + CBF_conversion_pattern + "\""
    print(comm_s)
    os.system(comm_s)
    CBFpattern = CBF_conversion_pattern + "*.cbf"
  else:
    CBFpattern = directory + "/" + prefix+"_" + str(rowIndex) + "_" + "*.cbf"
  comm_s = "ssh -q " + node + " \"ls -rt " + CBFpattern + ">>/dev/null\""
  lsOut = os.system(comm_s)
  comm_s = "ssh -q " + node + " \"ls -rt " + CBFpattern + "|/usr/local/crys-local/dials-v1-2-0/build/bin/dials.find_spots_client\""
###  comm_s = "ls -rt " + CBFpattern + "|/usr/local/crys-local/dials/build/bin/dials.find_spots_client"  
####  comm_s = "ssh -q cpu-004 \"ls -rt " + prefix + "|/usr/local/crys-local/dials-v1-1-4/build/bin/dials.find_spots_client\""  
  print(comm_s)
  retry = 3
  while(1):
    resultString = "<data>\n"+os.popen(comm_s).read()+"</data>\n"
    localDialsResultDict = xmltodict.parse(resultString)
    if (localDialsResultDict["data"] == None and retry>0):
      print("ERROR \n" + resultString + " retry = " + str(retry))
      retry = retry - 1
    else:
      break
  rasterRowResultsList[rowIndex] = localDialsResultDict["data"]["response"]
#  print("\n")
#  print(rasterRowResultsList[rowIndex])
#  print("\n")
  processedRasterRowCount+=1



def snakeRaster(rasterReqID,grain=""):
  global dialsResultDict,rasterRowResultsList,processedRasterRowCount
  
  rasterRequest = db_lib.getRequestByID(rasterReqID)
  reqObj = rasterRequest["request_obj"]
  parentReqID = reqObj["parentReqID"]
  parentReqProtocol = ""
  
  if (parentReqID != -1):
    parentRequest = db_lib.getRequestByID(parentReqID)
    parentReqObj = parentRequest["request_obj"]
    parentReqProtocol = parentReqObj["protocol"]
    detDist = parentReqObj["detDist"]    
# 2/17/16 - a few things for integrating dials/spotfinding into this routine
#  filePrefix = reqObj["directory"]+"/"+reqObj["file_prefix"]
  data_directory_name = str(reqObj["directory"])
  os.system("mkdir -p " + data_directory_name)
  os.system("chmod -R 777 " + data_directory_name)  
  filePrefix = str(reqObj["file_prefix"])
  file_number_start = reqObj["file_number_start"]  
  dataFilePrefix = reqObj["directory"]+"/"+reqObj["file_prefix"]  
  exptimePerCell = reqObj["exposure_time"]
  img_width_per_cell = reqObj["img_width"]
#really should read these two from hardware  
  wave = reqObj["wavelength"]
  xbeam = beamline_support.getPvValFromDescriptor("beamCenterX")
  ybeam = beamline_support.getPvValFromDescriptor("beamCenterY")
  rasterDef = reqObj["rasterDef"]
  stepsize = float(rasterDef["stepsize"])
  omega = float(rasterDef["omega"])
  rasterStartX = float(rasterDef["x"]) #these are real sample motor positions
  rasterStartY = float(rasterDef["y"])
  rasterStartZ = float(rasterDef["z"])
  omegaRad = math.radians(omega)
#  current_omega_mod = beamline_lib.get_epics_motor_pos(beamline_support.pvNameSuffix_from_descriptor("omega"))%360.0

# 2/17/16 - a few things for integrating dials/spotfinding into this routine, this is just to fake the data
##  testImgFileList = glob.glob("/GPFS/CENTRAL/XF17ID1/skinner/eiger16M/cbf/*.cbf")
##  testImgCount = 0
##  for i in range(0,len(rasterDef["rowDefs"])):
##    numsteps = int(rasterDef["rowDefs"][i]["numsteps"])    
  rowCount = len(rasterDef["rowDefs"])
  rasterRowResultsList = [{} for i in range(0,rowCount)]    
  processedRasterRowCount = 0
  
  for i in range(len(rasterDef["rowDefs"])):
    if (daq_lib.abort_flag == 1):
      return 0
    numsteps = int(rasterDef["rowDefs"][i]["numsteps"])
#6/16  a few things for integrating dials/spotfinding into this routine, this is just to fake the data 
##    for j in range(0,numsteps):
##      rasterFilePrefix = dataFilePrefix + "_Raster_"
##n      dataFileName = daq_utils.create_filename(rasterFilePrefix+str(i),j+1)
##      os.system("mkdir -p " + reqObj["directory"])
##      comm_s = "ln -sf " + testImgFileList[testImgCount] + " " + dataFileName
##      os.system(comm_s)
##      testImgCount+=1
    
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
    print("x rel move = " + str(xRelativeMove))
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
    mvaDescriptor("omega",omega)
    beamline_support.setPvValFromDescriptor("vectorStepOmega",img_width_per_cell)
    beamline_support.setPvValFromDescriptor("vectorStartX",xMotAbsoluteMove)
    beamline_support.setPvValFromDescriptor("vectorStartY",yMotAbsoluteMove)  
    beamline_support.setPvValFromDescriptor("vectorStartZ",zMotAbsoluteMove)
    mvaDescriptor("sampleX",xMotAbsoluteMove,"sampleY",yMotAbsoluteMove,"sampleZ",zMotAbsoluteMove)
    beamline_support.setPvValFromDescriptor("vectorEndX",xEnd)
    beamline_support.setPvValFromDescriptor("vectorEndY",yEnd)  
    beamline_support.setPvValFromDescriptor("vectorEndZ",zEnd)  
    beamline_support.setPvValFromDescriptor("vectorframeExptime",exptimePerCell)
    beamline_support.setPvValFromDescriptor("vectorNumFrames",numsteps)
#    beamline_support.setPvValFromDescriptor("vectorNumFrames",numsteps-1)    
    rasterFilePrefix = dataFilePrefix + "_Raster_" + str(i)
    detectorArm(omega,img_width_per_cell,numsteps,exptimePerCell,rasterFilePrefix,data_directory_name,file_number_start)
    beamline_support.setPvValFromDescriptor("vectorGo",1)
#    if (1):
    if (daq_utils.detector_id == "EIGER-16"):      
      if (det_lib.detector_is_manual_trigger()):
#        print("vector delay")
        time.sleep(getVectorDelay())
        det_lib.detector_trigger()
    vectorWait()
    detector_wait()
#    time.sleep(1)    
# add the threading dials stuff here, and the thread routine elsewhere.
    if (daq_utils.detector_id == "EIGER-16"):
#      seqNum = beamline_support.get_any_epics_pv("XF:17IDC-ES:FMX{Det:Eig16M}cam1:SequenceId","VAL")
      seqNum = int(det_lib.detector_get_seqnum())
    else:
      seqNum = -1
    print("running dials thread")
    _thread.start_new_thread(runDialsThread,(data_directory_name,filePrefix+"_Raster",i,numsteps,seqNum))
    print("thread running")
  rasterTimeout = 60
  timerCount = 0
  while (1):
    timerCount +=1
    if (timerCount>rasterTimeout):
      break
    time.sleep(1)
    print(processedRasterRowCount)
    if (processedRasterRowCount == rowCount):
      break

  rasterResult = generateGridMap(rasterRequest) #I think rasterRequest is entire request, of raster type
  rasterRequest["request_obj"]["rasterDef"]["status"] = 2
  protocol = reqObj["protocol"]
  print("protocol = " + protocol)
  if (protocol == "multiCol" or parentReqProtocol == "multiCol"):
    if (parentReqProtocol == "multiCol"):    
      multiColThreshold  = parentReqObj["diffCutoff"]
    else:
      multiColThreshold  = reqObj["diffCutoff"]         
    gotoMaxRaster(rasterResult,multiColThreshold=multiColThreshold) 
  else:
    if (deltaX>deltaY): #horizontal raster, dont bother vert for now, did not do pos calcs, wait for zebra
      gotoMaxRaster(rasterResult)
#  print(rasterRequest)
  rasterRequestID = rasterRequest["uid"]
  db_lib.updateRequest(rasterRequest)
#  print("after update")
#  print(rasterRequest)
  
  db_lib.updatePriority(rasterRequestID,-1)  
  set_field("xrecRasterFlag",rasterRequest["uid"])
  return 1



def runRasterScan(currentRequest,rasterType=""): #this actually defines and runs
  sampleID = currentRequest["sample"]
  if (rasterType=="Fine"):
    set_field("xrecRasterFlag","100")    
    rasterReqID = defineRectRaster(currentRequest,50,50,10) 
    snakeRaster(rasterReqID)
  elif (rasterType=="Line"):  
    set_field("xrecRasterFlag","100")    
    mvrDescriptor("omega",90)
    rasterReqID = defineRectRaster(currentRequest,10,150,10)
#    rasterReqID = defineVectorRaster(currentRequest,10,150,10)     
    snakeRaster(rasterReqID)
    set_field("xrecRasterFlag","100")    
  else:
    rasterReqID = getXrecLoopShape(currentRequest)
    print("snake raster " + str(rasterReqID))
    time.sleep(1) #I think I really need this, not sure why
    snakeRaster(rasterReqID)
#    set_field("xrecRasterFlag",100)    


def gotoMaxRaster(rasterResult,multiColThreshold=-1):
#  print("raster result = ")
#  print(rasterResult)
  if (rasterResult["result_obj"]["rasterCellResults"]['resultObj'] == None):
#  if (rasterResult["result_obj"]["rasterCellResults"]['resultObj']["data"] == None):    
    print("no raster result!!\n")
    return
  ceiling = 0.0
  floor = 100000000.0 #for resolution where small number means high score
  hotFile = ""
  scoreOption = ""
  print("in gotomax")
#  print(rasterResult)
  cellResults = rasterResult["result_obj"]["rasterCellResults"]['resultObj']
#  cellResults = rasterResult["result_obj"]["rasterCellResults"]['resultObj']["data"]["response"]    
  rasterMap = rasterResult["result_obj"]["rasterCellMap"]  
  rasterScoreFlag = int(db_lib.beamlineInfo(daq_utils.beamline,'rasterScoreFlag')["index"])
  if (rasterScoreFlag==0):
    scoreOption = "spot_count"
  elif (rasterScoreFlag==1):
    scoreOption = "d_min"
  else:
    scoreOption = "total_intensity"
  for i in range (0,len(cellResults)):
#    print(cellResults[i])
#    print("\n")
    try:
      scoreVal = float(cellResults[i][scoreOption])
    except TypeError:
#      continue
      scoreVal = 0.0
    if (multiColThreshold>-1):
      print("doing multicol")
      if (scoreVal >= multiColThreshold):
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
  parentRequest = db_lib.getRequestByID(parentReqID)
  sampleID = parentRequest["sample"]

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
#careful here, I'm hardcoding the view I think we'll use for definePolyRaster
def getCurrentFOV(): 
  fov = {"x":0.0,"y":0.0}
#  fov["x"] = daq_utils.lowMagFOVx/3.0
#  fov["y"] = daq_utils.lowMagFOVy/3.0

  fov["x"] = daq_utils.highMagFOVx
  fov["y"] = daq_utils.highMagFOVy
  
  return fov


def screenXmicrons2pixels(microns):
  fov = getCurrentFOV()
  fovX = fov["x"]
  return int(round(microns*(daq_utils.highMagPixX/fovX)))

def screenYmicrons2pixels(microns):
  fov = getCurrentFOV()
  fovY = fov["y"]
  return int(round(microns*(daq_utils.highMagPixY/fovY)))  


def screenXPixels2microns(pixels):
  fov = getCurrentFOV()
  fovX = fov["x"]
  return float(pixels)*(fovX/daq_utils.highMagPixX)

def screenYPixels2microns(pixels):
  fov = getCurrentFOV()
  fovY = fov["y"]
  return float(pixels)*(fovY/daq_utils.highMagPixY)


def defineRectRaster(currentRequest,raster_w_s,raster_h_s,stepsizeMicrons_s): #maybe point_x and point_y are image center? #everything can come as microns, make this a horz vector scan, note this never deals with pixels.
  
  sampleID = currentRequest["sample"]
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
  reqObj["parentReqID"] = currentRequest["uid"]
  newRasterRequest = db_lib.addRequesttoSample(sampleID,reqObj["protocol"],reqObj,priority=5000)
  set_field("xrecRasterFlag",newRasterRequest["uid"])  
  time.sleep(1)
  return newRasterRequest["uid"]


def definePolyRaster(currentRequest,raster_w,raster_h,stepsizeMicrons,point_x,point_y,rasterPoly): #all come in as pixels
  sampleID = currentRequest["sample"]
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
  if (numsteps_v > numsteps_h): #vertical raster, other than single column, I don't think we have loopshapes that hit this vert raster code
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
#        vectorEndY = vectorStartY + (rowCellCount*stepsizeMicrons)
        vectorEndY = vectorStartY + screenYPixels2microns(rowCellCount*stepsizeYPix)    #looks better
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
        vectorEndX = vectorStartX + screenXPixels2microns(rowCellCount*stepsizeXPix) #this looks better, see gui and notes comments
#        vectorEndX = vectorStartX + (rowCellCount*stepsizeMicrons) 
        vectorStartY = screenYPixels2microns(rowStartY-daq_utils.screenPixCenterY)
        vectorEndY = vectorStartY
        newRowDef = {"start":{"x": vectorStartX,"y":vectorStartY},"end":{"x":vectorEndX,"y":vectorEndY},"numsteps":rowCellCount}
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
  reqObj["parentReqID"] = currentRequest["uid"]
  newRasterRequest = db_lib.addRequesttoSample(sampleID,reqObj["protocol"],reqObj,priority=5000)
  set_field("xrecRasterFlag",newRasterRequest["uid"])  
  return newRasterRequest["uid"]
#  daq_lib.refreshGuiTree() # not sure


def getXrecLoopShape(currentRequest):
  sampleID = currentRequest["sample"]
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
  plt.clf()
  sampleID = energyScanRequest["sample"]
  reqObj = energyScanRequest["request_obj"]
  exptime = reqObj['exposure_time']
  targetEnergy = reqObj['scanEnergy'] *1000.0
  print("energy scan for " + str(targetEnergy))
  scan_element = "Se"
  mvaDescriptor("energy",targetEnergy)
  open_shutter()
  scanID = RE(relative_scan([mercury],vdcm.e,-20,20,41),[LivePlot("mercury_mca_rois_roi0_count")])
#  scanID = RE(relative_scan([mercury],vdcm.e,-40,40,80),[LivePlot("mercury_mca_rois_roi0_count")])  
#  scanID = RE(relative_scan([mercury],vdcm.e,-60,60,40))  
  close_shutter()
  scanData = db[scanID[0]]
  for ev in get_events(scanData):
    if ('mercury_mca_spectrum' in ev['data']):
      print(ev['seq_num'], ev['data']['mercury_mca_spectrum'].sum())
      
  scanDataTable = get_table(scanData)
#these next lines only make sense for the mca
  specFile = open("spectrumData.txt","w+")
  #mercury.mca.rois.roi0.count.value
##  for i in range (0,len(scanDataTable.mercury_mca_spectrum.values)):
##    for j in range (0,len(scanDataTable.mercury_mca_spectrum.values[i])):
#  specFile.write("From LSDC\n")
  specFile.write(str(len(scanDataTable.mercury_mca_rois_roi0_count)) + "\n")
  for i in range (0,len(scanDataTable.mercury_mca_rois_roi0_count)):
    specFile.write(str(scanDataTable.vdcm_e[i+1]) + " " + str(scanDataTable.mercury_mca_rois_roi0_count[i+1]))
    specFile.write("\n")
  specFile.close()
#  scanDataTable = get_table(scanData,["omega","cam_7_stats1_total"])  
  eScanResultObj = {}
  eScanResultObj["databrokerID"] = scanID
  eScanResultObj["sample_id"] = sampleID  
  eScanResultID = db_lib.addResultforRequest("eScanResult",energyScanRequest["uid"], daq_utils.owner,result_obj=eScanResultObj)
  eScanResult = db_lib.getResult(eScanResultID)
  print(scanDataTable)
  if (reqObj["runChooch"]):
    chooch_prefix = "choochData1"
    choochOutfileName = chooch_prefix+".efs"
    choochInputFileName = "spectrumData.txt"
#    choochInputFileName = "/nfs/skinner/temp/choochData1.raw"    
    comm_s = "chooch -e %s -o %s %s" % (scan_element, choochOutfileName,choochInputFileName)
#  comm_s = "chooch -e %s -o %s -p %s %s" % (scan_element,chooch_prefix+".efs",chooch_prefix+".ps",chooch_prefix+".raw")
    print(comm_s)
    choochInputData_x = []
    choochInputData_y = []
    infl = 0
    peak = 0
    f2prime_infl = 0
    fprime_infl = 0
    f2prime_peak = 0
    fprime_peak = 0
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
    choochResultID = db_lib.addResultforRequest("choochResult",energyScanRequest["uid"], daq_utils.owner,result_obj=choochResultObj)
    choochResult = db_lib.getResult(choochResultID)
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
  det_radius = db_lib.getBeamlineConfigParam(beamline,"detRadius")  
#  if (daq_utils.detector_id == "ADSC-Q315"):
#    det_radius = 157.5
#  elif (daq_utils.detector_id == "ADSC-Q210"):
#    det_radius = 105.0
#  elif (daq_utils.detector_id == "PILATUS-6"):
#    det_radius = 212.0
#  else: #default Pilatus
#    det_radius = 212.0
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
#    dna_start = motorPosFromDescriptor("omega")    
#    dna_start = daq_lib.get_field("datum_omega")    
    colstart = float(dna_start) + (i*(abs(overlap)+float(dna_range)))
    dna_prefix = "ref-"+prefix
#12/15 not sure why dna_run_num in prefix    dna_prefix = "ref-"+prefix+"_"+str(dna_run_num)
    image_number = start_image_number+i
    dna_prefix_long = dna_directory+"/"+dna_prefix
    filename = daq_utils.create_filename(dna_prefix_long,image_number)
    beamline_lib.mvaDescriptor("omega",float(colstart))
#####    daq_lib.move_axis_absolute(daq_lib.get_field("scan_axis"),colstart)
#####    daq_lib.take_image(colstart,dna_range,dna_exptime,filename,daq_lib.get_field("scan_axis"),0,1)
    daq_utils.take_crystal_picture(reqID=charRequest["uid"])
    charRequest["request_obj"]["sweep_start"] = colstart
    imagesAttempted = collect_detector_seq(dna_range,dna_range,dna_exptime,dna_prefix,dna_directory,image_number,charRequest) 
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
  while(not os.path.exists(dna_filename_list[len(dna_filename_list)-1])): #this waits for edna images
    timeout_check = timeout_check + 1
    time.sleep(1.0)
    if (timeout_check > 10):
      break
  flux = beamline_support.getPvValFromDescriptor("flux")
#  flux = 600000000.0  #for now
  edna_input_filename = dna_directory + "/adsc1_in.xml"
  
  comm_s = "ssh -q xf17id1-srv1 \"source /nfs/skinner/wrappers/ednaWrap;" + os.environ["LSDCHOME"] + "/runEdna.py " + dna_directory + " " + dna_prefix + " " + str(aimed_ISig) + " " + str(flux) + " " + str(xbeam_size) + " " + str(ybeam_size) + " " + edna_input_filename + " " + str(charRequest["uid"]) + "\""
  print(comm_s)
  os.system(comm_s)

  return 1


def setAttens(transmission): #where transmission = 0.0-1.0
  attenValList = []
  attenValList = attenCalc.RIfoils(beamline_lib.get_mono_energy(),transmission)
# attenValList = [0,1,0,1,0,1,0,1,0,1,0,1]
  for i in range (0,len(attenValList)):
    pvVal = attenValList[i]
    pvKeyName = "Atten%02d-%d" % (i+1,pvVal)    
    beamline_support.setPvValFromDescriptor(pvKeyName,1)
    print (pvKeyName)

def importSpreadsheet(fname):
  parseSheet.importSpreadsheet(fname,daq_utils.owner)

