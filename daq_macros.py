import beamline_support
import beamline_lib #did this really screw me if I imported b/c of daq_utils import??
from beamline_lib import *
import daq_lib
from daq_lib import *
import daq_utils
import db_lib
import string
import math
import robot_lib
from PyQt4 import QtGui
from PyQt4 import QtCore
import time
from random import randint
import glob
import xml.etree.ElementTree as ET
import xmltodict
from XSDataMXv1 import XSDataResultCharacterisation

def hi_macro():
  print "hello from macros\n"
  daq_lib.broadcast_output("broadcast hi")

    
def flipLoopShapeCoords(filename): # not used
  xrec_out_file = open(filename,"r")  
  correctedFilename = "loopFaceShape.txt"
  resultLine = xrec_out_file.readline()
  tokens = string.split(resultLine)
  numpoints = int(tokens[0])
  points = []
  for i in xrange(1,len(tokens)-1,2):
    point = [tokens[i],tokens[i+1]]
    correctedPoint = [daq_utils.screenPixX-int(tokens[i]),daq_utils.screenPixY-int(tokens[i+1])]
  xrec_out_file.close() 


def autoRasterLoop(sampleID):
  print "auto raster " + str(sampleID)
  loop_center_xrec()
#  getXrecLoopShape(sampleID)
  time.sleep(1) #looks like I really need this sleep, they really improve the appearance 
  runRasterScan(sampleID,"LoopShape")
  time.sleep(1.5) 
  runRasterScan(sampleID,"Fine")
  time.sleep(1) 
  runRasterScan(sampleID,"Line")  
  time.sleep(1) 



def loop_center_xrec():
  global face_on

  daq_lib.abort_flag = 0    

  for i in xrange(0,360,40):
    if (daq_lib.abort_flag == 1):
      return 0
    mva("Omega",i)
    pic_prefix = "findloop_" + str(i)
#    time.sleep(0.1)
    take_crystal_picture(filename=pic_prefix)
  comm_s = "xrec " + os.environ["CONFIGDIR"] + "/xrec_360_40.txt xrec_result.txt"
  print comm_s
  os.system(comm_s)
  xrec_out_file = open("xrec_result.txt","r")
  target_angle = 0.0
  radius = 0
  x_centre = 0
  y_centre = 0
  reliability = 0
  for result_line in xrec_out_file.readlines():
    print result_line
    tokens = split(result_line)
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
  print "result = " + str(check_result)
  xrec_check_file.close()
  if (reliability < 70 or check_result == 0): #bail if xrec couldn't align loop
    return 0
  mva("Omega",target_angle)
  x_center = daq_utils.lowMagPixX/2
  y_center = daq_utils.lowMagPixY/2
#  set_epics_pv("image_X_center","A",x_center)
#  set_epics_pv("image_Y_center","A",y_center)
  print "center on click " + str(x_center) + " " + str(y_center-radius)
  print "center on click " + str((x_center*2) - y_centre_xrec) + " " + str(x_centre_xrec)
  center_on_click(x_center,y_center-radius,source="macro")
  center_on_click((x_center*2) - y_centre_xrec,x_centre_xrec,source="macro")
#cheating here, not accounting for scaling. Diameter=2*Radius cancelled out by halved image.  
#  daq_lib.set_field("grid_w",int(radius))
#  daq_lib.set_field("grid_h",int(radius))
  mva("Omega",face_on)
  #now try to get the loopshape starting from here
  return 1

def fakeDC(directory,filePrefix,numstart,numimages):
  testImgFileList = glob.glob("/home/pxuser/Test-JJ/johnPil6/data/B1GGTApo_9_*.cbf")
  testImgFileList.sort()
  prefix_long = directory+"/"+filePrefix
  expectedFilenameList = []
  for i in range (numstart,numstart+numimages):
    filename = create_filename(prefix_long,i)
    expectedFilenameList.append(filename)
  for i in range (0,len(expectedFilenameList)):
    comm_s = "ln -sf " + testImgFileList[i] + " " + expectedFilenameList[i]
    print comm_s
    os.system(comm_s)


def generateGridMap(rasterRequest):
#  rasterDef = db_lib.getRasters()[0]
#  print rasterDef
  reqObj = rasterRequest["request_obj"]
  rasterDef = reqObj["rasterDef"]
  stepsize = float(rasterDef["stepsize"])
  omega = float(rasterDef["omega"])
  rasterStartX = float(rasterDef["x"])
  rasterStartY = float(rasterDef["y"])
  rasterStartZ = float(rasterDef["z"])
  omegaRad = math.radians(omega)
#  filePrefix = "raster" #for now
  filePrefix = reqObj["directory"]+"/"+reqObj["file_prefix"]
  testImgFileList = glob.glob("/home/pxuser/Test-JJ/DataSets/Eiger1M-Tryps-cbf/*.cbf")
  testImgCount = 0
  rasterCellMap = {}
  for i in xrange(len(rasterDef["rowDefs"])):
    numsteps = float(rasterDef["rowDefs"][i]["numsteps"])
    if (i%2 == 0): #left to right if even, else right to left - a snake attempt
      startX = rasterDef["rowDefs"][i]["start"]["x"]+(stepsize/2.0) #this is relative to center, so signs are reversed from motor movements.
    else:
      startX = (numsteps*stepsize) + rasterDef["rowDefs"][i]["start"]["x"]-(stepsize/2.0)
    startY = rasterDef["rowDefs"][i]["start"]["y"]+(stepsize/2.0)
    xRelativeMove = startX
    yyRelativeMove = startY*sin(omegaRad)
    yxRelativeMove = startY*cos(omegaRad)
#old    yxRelativeMove = startY*sin(omegaRad)
#    yyRelativeMove = startY*cos(omegaRad)

    zMotAbsoluteMove = rasterStartZ-xRelativeMove

#old    yMotAbsoluteMove = rasterStartY-yyRelativeMove
#    xMotAbsoluteMove = yxRelativeMove+rasterStartX

    yMotAbsoluteMove = rasterStartY+yyRelativeMove
    xMotAbsoluteMove = rasterStartX-yxRelativeMove

    numsteps = int(rasterDef["rowDefs"][i]["numsteps"])
    for j in xrange(numsteps):
      if (i%2 == 0): #left to right if even, else right to left - a snake attempt
        zMotCellAbsoluteMove = zMotAbsoluteMove-(j*stepsize)
      else:
        zMotCellAbsoluteMove = zMotAbsoluteMove+(j*stepsize)
#      zMotAbsoluteMove = zMotAbsoluteMove-(j*stepsize)
      dataFileName = create_filename(filePrefix+"_"+str(i),j+1)
      os.system("mkdir -p " + reqObj["directory"])
      comm_s = "ln -sf " + testImgFileList[testImgCount] + " " + dataFileName
      os.system(comm_s)
      testImgCount+=1
      rasterCellCoords = {"x":xMotAbsoluteMove,"y":yMotAbsoluteMove,"z":zMotCellAbsoluteMove}
      rasterCellMap[dataFileName] = rasterCellCoords
  comm_s = "ls -rt " + reqObj["directory"]+"/"+reqObj["file_prefix"]+"*.cbf|dials.find_spots_client"
  print comm_s
  dialsResultObj = xmltodict.parse("<data>\n"+os.popen(comm_s).read()+"</data>\n")
  print "done parsing dials output"
  rasterResultObj = {"rasterCellMap":rasterCellMap,"rasterCellResults":{"type":"dialsRasterResult","resultObj":dialsResultObj}}
#  rasterResult = daq_utils.createResult("rasterResult",rasterResultObj)
  db_lib.addResultforRequest("rasterResult",rasterRequest["request_id"], rasterResultObj)
  return rasterResult


def snakeRaster(rasterReqID,grain=""):
  rasterRequest = db_lib.getRequest(rasterReqID)
  reqObj = rasterRequest["request_obj"]
  rasterDef = reqObj["rasterDef"]
  stepsize = float(rasterDef["stepsize"])
  omega = float(rasterDef["omega"])
  rasterStartX = float(rasterDef["x"])
  rasterStartY = float(rasterDef["y"])
  rasterStartZ = float(rasterDef["z"])
  omegaRad = math.radians(omega)
  if (rasterDef["rasterType"] == "normal"):
    for i in xrange(len(rasterDef["rowDefs"])):
      rowCellCount = 0
      numsteps = float(rasterDef["rowDefs"][i]["numsteps"])
      if (i%2 == 0): #left to right if even, else right to left - a snake attempt
        startX = rasterDef["rowDefs"][i]["start"]["x"]+(stepsize/2.0)
      else:
        startX = (numsteps*stepsize) + rasterDef["rowDefs"][i]["start"]["x"]-(stepsize/2.0)
      startY = rasterDef["rowDefs"][i]["start"]["y"]+(stepsize/2.0)
      xRelativeMove = startX
      yyRelativeMove = startY*sin(omegaRad)
      yxRelativeMove = startY*cos(omegaRad)
      zMotAbsoluteMove = rasterStartZ-xRelativeMove
      yMotAbsoluteMove = rasterStartY+yyRelativeMove
      xMotAbsoluteMove = rasterStartX-yxRelativeMove
      mva("X",xMotAbsoluteMove,"Y",yMotAbsoluteMove,"Z",zMotAbsoluteMove) #why not just do relative move here, b/c the relative move is an offset from center
      if (i%2 == 0): #left to right if even, else right to left - a snake attempt
        xRelativeMove = -((numsteps-1)*stepsize)
      else:
        xRelativeMove = ((numsteps-1)*stepsize)
      mvr("Z",xRelativeMove) #I guess this is where I need to arm and collect., see collect_pixel_array_detector_seq_for_grid in cbass
  else: #column raster for 90-degree 
    numsteps = int(rasterDef["rowDefs"][0]["numsteps"])
    startY = rasterDef["rowDefs"][0]["start"]["y"]+(stepsize/2.0) #- these are the simple relative moves
    startX = rasterDef["rowDefs"][0]["start"]["x"]+(stepsize/2.0)
    xRelativeMove = startX
    yyRelativeMove = -startY*sin(omegaRad)
    yxRelativeMove = startY*cos(omegaRad)
    mvr("X",yxRelativeMove,"Y",yyRelativeMove,"Z",xRelativeMove) #this should get to the start
    time.sleep(1)#cosmetic
    yRelativeMove = -((numsteps-1)*stepsize)
    yyRelativeMove = yRelativeMove*sin(omegaRad)
    yxRelativeMove = -yRelativeMove*cos(omegaRad)
    mvr("X",yxRelativeMove,"Y",yyRelativeMove) #this should be the actual scan
  rasterResult = generateGridMap(rasterRequest)
  rasterRequest["request_obj"]["rasterDef"]["status"] = 2
  gotoMaxRaster(rasterResult)
  db_lib.updateRequest(rasterRequest)
  set_field("xrecRasterFlag",rasterRequest["request_id"])  


def runRasterScan(sampleID,rasterType=""): #this actualkl defines and runs
  if (rasterType=="Fine"):
    set_field("xrecRasterFlag",100)    
    rasterReqID = defineRectRaster(sampleID,50,50,10) 
    snakeRaster(rasterReqID)
#    gotoMaxRaster("raster_spots.txt","raster_map.txt")
#    set_field("xrecRasterFlag",2)  
  elif (rasterType=="Line"):  
    set_field("xrecRasterFlag",100)    
    mvr("Omega",90)
#    rasterReqID = defineColumnRaster(sampleID,10,150,10)
#    singleColumnRaster(rasterReqID)
    rasterReqID = defineRectRaster(sampleID,10,150,10) 
    snakeRaster(rasterReqID)
    set_field("xrecRasterFlag",100)    
  else:
    rasterReqID = getXrecLoopShape(sampleID)
    print "snake raster " + str(rasterReqID)
    time.sleep(1) #I think I really need this, not sure why
    snakeRaster(rasterReqID)
#    set_field("xrecRasterFlag",100)    


def gotoMaxRaster(rasterResult):
  ceiling = 0
  hotFile = ""
  cellResults = rasterResult["resultObj"]["rasterCellResults"]['resultObj']["data"]["response"]
##  print cellResults
  for i in range (0,len(cellResults)):
    spotcount = cellResults[i]["spot_count"]
    if (spotcount > ceiling):
      ceiling = spotcount    
      hotFile = cellResults[i]["image"]
  if (ceiling > 0):
    print ceiling
    print hotFile
    rasterMap = rasterResult["resultObj"]["rasterCellMap"]
##    print rasterMap
    hotCoords = rasterMap[hotFile]
    x = hotCoords["x"]
    y = hotCoords["y"]
    z = hotCoords["z"]
    print "goto " + str(x) + " " + str(y) + " " + str(z)
    mva("X",x,"Y",y,"Z",z)
  
    
#these next three differ a little from the gui. the gui uses isChecked, b/c it was too intense to keep hitting the pv, also screen pix vs image pix
def getCurrentFOV(): 
  fov = {"x":0.0,"y":0.0}
  fov["x"] = daq_utils.highMagFOVx/2.0
  fov["y"] = daq_utils.highMagFOVy/2.0
  return fov


def screenXmicrons2pixels(microns):
  fov = getCurrentFOV()
  fovX = fov["x"]
#  return int(round(microns*(daq_utils.highMagPixX/fovX)))
  return int(round(microns*(daq_utils.screenPixX/fovX)))


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


def defineRectRaster(sampleID,raster_w_s,raster_h_s,stepsizeMicrons_s): #maybe point_x and point_y are image center? #everything can come as microns
  raster_h = float(raster_h_s)
  raster_w = float(raster_w_s)
  stepsize = float(stepsizeMicrons_s)
  beamWidth = stepsize
  beamHeight = stepsize
  rasterDef = {"beamWidth":beamWidth,"beamHeight":beamHeight,"status":0,"x":get_epics_motor_pos("X"),"y":get_epics_motor_pos("Y"),"z":get_epics_motor_pos("Z"),"omega":get_epics_motor_pos("Omega"),"stepsize":stepsize,"rowDefs":[]} 
  numsteps_h = int(raster_w/stepsize)
  numsteps_v = int(raster_h/stepsize) #the numsteps is decided in code, so is already odd
  point_offset_x = -(numsteps_h*stepsize)/2.0
  point_offset_y = -(numsteps_v*stepsize)/2.0
  for i in xrange(numsteps_v):
    newRowDef = {"start":{"x": point_offset_x,"y":point_offset_y+(i*stepsize)},"numsteps":numsteps_h}
    rasterDef["rowDefs"].append(newRowDef)
##      rasterCoords = {"x":pvGet(self.sampx_pv),"y":pvGet(self.sampy_pv),"z":pvGet(self.sampz_pv)}
#  print rasterDef
  tempnewRasterRequest = daq_utils.createDefaultRequest(sampleID)
  reqObj = tempnewRasterRequest["request_obj"]
  reqObj["protocol"] = "raster"
  reqObj["directory"] = os.getcwd()+"/rasterImages/"
  if (numsteps_h == 1): #column raster
    reqObj["file_prefix"] = reqObj["file_prefix"]+"_lineRaster"
    rasterDef["rasterType"] = "column"
  else:
    reqObj["file_prefix"] = reqObj["file_prefix"]+"_rectRaster"
    rasterDef["rasterType"] = "normal"
  reqObj["rasterDef"] = rasterDef #should this be something like self.currentRasterDef?
  reqObj["rasterDef"]["status"] = 1 # this will tell clients that the raster should be displayed.
  reqObj["priority"] = 5000
  newRasterRequest = db_lib.addRequesttoSample(sampleID,reqObj["protocol"],reqObj)
  set_field("xrecRasterFlag",newRasterRequest["request_id"])  
#  db_lib.addRaster(rasterDef)
#  set_field("xrecRasterFlag",1)
  time.sleep(1)
  return newRasterRequest["request_id"]


def definePolyRaster(sampleID,raster_w,raster_h,stepsizeMicrons,point_x,point_y,rasterPoly): #all come in as pixels
  newRowDef = {}
#  print "draw raster " + str(raster_w) + " " + str(raster_h) + " " + str(stepsizeMicrons)
  beamWidth = stepsizeMicrons
  beamHeight = stepsizeMicrons
  rasterDef = {"rasterType":"normal","beamWidth":beamWidth,"beamHeight":beamHeight,"status":0,"x":get_epics_motor_pos("X"),"y":get_epics_motor_pos("Y"),"z":get_epics_motor_pos("Z"),"omega":get_epics_motor_pos("Omega"),"stepsize":stepsizeMicrons,"rowDefs":[]} #just storing step as microns, not using here
  stepsize = screenXmicrons2pixels(stepsizeMicrons)   #note conversion to pixels
  numsteps_h = int(raster_w/stepsize) #raster_w = width,goes to numsteps horizonatl
  numsteps_v = int(raster_h/stepsize)
  if (numsteps_h%2 == 0):
    numsteps_h = numsteps_h + 1
  if (numsteps_v%2 == 0):
    numsteps_v = numsteps_v + 1
  point_offset_x = -(numsteps_h*stepsize)/2
  point_offset_y = -(numsteps_v*stepsize)/2
  for i in xrange(numsteps_v):
    rowCellCount = 0
    for j in xrange(numsteps_h):
      newCellX = point_x+(j*stepsize)+point_offset_x
      newCellY = point_y+(i*stepsize)+point_offset_y
      if (rasterPoly.contains(QtCore.QPointF(newCellX+(stepsize/2.0),newCellY+(stepsize/2.0)))):
        if (rowCellCount == 0): #start of a new row
          rowStartX = newCellX
          rowStartY = newCellY
        rowCellCount = rowCellCount+1
    if (rowCellCount != 0): #no points in this row of the bounding rect are in the poly?
      newRowDef = {"start":{"x": screenXPixels2microns(rowStartX-daq_utils.screenPixCenterX),"y":screenYPixels2microns(rowStartY-daq_utils.screenPixCenterY)},"numsteps":rowCellCount}
#      newRowDef = {"start":{"x": screenXPixels2microns(rowStartX-daq_utils.highMagPixX/2.0),"y":screenYPixels2microns(rowStartY-daq_utils.highMagPixY/2.0)},"numsteps":rowCellCount}
      rasterDef["rowDefs"].append(newRowDef)
##      rasterCoords = {"x":pvGet(self.sampx_pv),"y":pvGet(self.sampy_pv),"z":pvGet(self.sampz_pv)}
#  print rasterDef
  tempnewRasterRequest = daq_utils.createDefaultRequest(sampleID)
  reqObj = tempnewRasterRequest["request_obj"]
  reqObj["protocol"] = "raster"
  reqObj["directory"] = os.getcwd()+"/rasterImages/"
  reqObj["file_prefix"] = reqObj["file_prefix"]+"_polyRaster"
  reqObj["rasterDef"] = rasterDef #should this be something like self.currentRasterDef?
  reqObj["rasterDef"]["status"] = 1 # this will tell clients that the raster should be displayed.
  reqObj["priority"] = 5000
  newRasterRequest = db_lib.addRequesttoSample(sampleID,reqObj["protocol"],reqObj)
  set_field("xrecRasterFlag",newRasterRequest["request_id"])  
  return newRasterRequest["request_id"]
#  daq_lib.refreshGuiTree() # not sure




def getXrecLoopShape(sampleID):
  beamline_support.set_any_epics_pv("FAMX-cam1:MJPGZOOM:NDArrayPort","VAL","ROI1") #not the best, but I had timing issues doing it w/o a sleep
  for i in xrange(4):
    if (daq_lib.abort_flag == 1):
      return 0
    mvr("Omega",i*30)
    pic_prefix = "findloopshape_" + str(i)
#    time.sleep(0.1)
    take_crystal_picture(filename=pic_prefix,czoom=1)
  comm_s = "xrec30 " + os.environ["CONFIGDIR"] + "/xrec30.txt xrec30_result.txt"
  os.system(comm_s)
#  xrec_out_file = open("xrec30_result.txt","r")
  mva("Omega",face_on)
  os.system("cp /dev/shm/masks2_hull_0.txt loopPoints.txt")

  polyPoints = [] 
  rasterPoly = None     
  filename = "loopPoints.txt"
  xrec_out_file = open(filename,"r")  
  resultLine = xrec_out_file.readline()
  xrec_out_file.close() 
  tokens = string.split(resultLine)
  numpoints = int(tokens[0])
  for i in xrange(1,len(tokens)-1,2):
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
  stepsizeMicrons = 30.0 #for now.
  rasterReqID = definePolyRaster(sampleID,raster_w,raster_h,stepsizeMicrons,center_x,center_y,rasterPoly)
  return rasterReqID

def vectorScan(vecRequest): #bogus for now until we figure out what we want
  print vecRequest
  sweep_start_angle = vecRequest["sweep_start"]
  sweep_end_angle = vecRequest["sweep_end"]
  imgWidth = vecRequest["img_width"]
  numImages = int((sweep_end_angle - sweep_start_angle) / imgWidth)
  numSteps = int(numImages/vecRequest["vectorParams"]["fpp"])
  print "numsteps " + str(numSteps)
  for i in xrange(numSteps+1):
    vector_move(float(i)*(100.0/float(numSteps))/100.0,vecRequest)
#    time.sleep(.1)


def dna_execute_collection3(dna_start,dna_range,dna_number_of_images,dna_exptime,dna_directory,prefix,start_image_number,overlap,dna_run_num,charRequest):
  global collect_and_characterize_success,dna_have_strategy_results,dna_have_index_results,picture_taken
  global dna_strategy_exptime,dna_strategy_start,dna_strategy_range,dna_strategy_end,dna_strat_dist
  global screeningoutputid
  
  characterizationParams = charRequest["characterizationParams"]
  dna_res = float(characterizationParams["aimed_resolution"])
  print "dna_res = " + str(dna_res)
  dna_filename_list = []
  print "number of images " + str(dna_number_of_images) + " overlap = " + str(overlap) + " dna_start " + str(dna_start) + " dna_range " + str(dna_range) + " prefix " + prefix + " start number " + str(start_image_number) + "\n"
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
  print "distance = ",dx
#skinner - could move distance and wave and scan axis here, leave wave alone for now
  print "skinner about to take reference images."
  for i in range(0,int(dna_number_of_images)):
    print "skinner prefix7 = " + prefix[0:7] + " startnum + " + str(start_image_number) + "\n"
    if (len(prefix)> 8):
      if ((prefix[0:7] == "postref") and (start_image_number == 1)):
        print "skinner postref bail\n"
        time.sleep(float(dna_number_of_images*float(dna_exptime)))        
        break
  #skinner roi - maybe I can measure and use that for dna_start so that first image is face on.
    dna_start = daq_lib.get_field("datum_omega")
    colstart = float(dna_start) + (i*(abs(overlap)+float(dna_range)))
#    colstart = colstart + daq_lib.var_list["datum_omega"]    
#    daq_lib.move_axis_absolute(daq_lib.var_list["scan_axis"],colstart)
#    daq_lib.move_axis_absolute("dist",dx)
    dna_prefix = "ref-"+prefix+"_"+str(dna_run_num)
    image_number = start_image_number+i
    dna_prefix_long = dna_directory+"/"+dna_prefix
    filename = daq_lib.create_filename(dna_prefix_long,image_number)
#####    if (daq_lib.need_auto_align_xtal_pic == 1):
    if (0):
      daq_lib.need_auto_align_xtal_pic = 0
      camera_offset = float(os.environ["CAMERA_OFFSET"])
      beamline_lib.mvr("Omega",float(camera_offset))
#####      daq_lib.move_axis_relative("omega",camera_offset)
#####      daq_lib.take_crystal_picture_with_boxes(daq_lib.html_data_directory_name + "/xtal_align_" + str(daq_lib.sweep_seq_id))
#####      daq_lib.move_axis_relative("omega",0-camera_offset)
      beamline_lib.mvr("Omega",float(0-camera_offset))
#####    if (daq_lib.need_auto_align_xtal_pic == 2 and daq_lib.has_xtalview):
    if (0):
      daq_lib.need_auto_align_xtal_pic = 0
#####      daq_lib.take_crystal_picture_with_boxes(daq_lib.html_data_directory_name + "/xtal_postalign_" + str(daq_lib.sweep_seq_id))
      postalign_jpg = "xtal_postalign_" + str(daq_lib.sweep_seq_id)
#      postalign_jpg_th = "xtal_postalign_th_" + str(daq_lib.sweep_seq_id)    
    beamline_lib.mva("Omega",float(colstart))
#####    daq_lib.move_axis_absolute(daq_lib.get_field("scan_axis"),colstart)
#####    daq_lib.take_image(colstart,dna_range,dna_exptime,filename,daq_lib.get_field("scan_axis"),0,1)
    daq_lib.take_crystal_picture(reqID=charRequest["request_id"])
    imagesAttempted = collect_detector_seq(dna_range,dna_range,dna_exptime,dna_prefix,dna_directory,1) #should be a single image
    dna_filename_list.append(filename)
    diffImgJpegData = diff2jpeg(filename,reqID=charRequest["request_id"]) #returns a dictionary
#    diffImgJpegData["timestamp"] = time.time()
#    imgRef = db_lib.addFile(diffImgJpegData["data"])
#    diffImgJpegData["data"] = imgRef
#    imgRef = db_lib.addFile(diffImgJpegData["thumbData"])
#    diffImgJpegData["thumbData"] = imgRef
#    print diffImgJpegData
    
#####    daq_lib.take_crystal_picture_with_boxes(daq_lib.html_data_directory_name + "/xtal_" + str(daq_lib.sweep_seq_id) + "_" + str(i))
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
  print "generating edna input\n"
#  edna_input_filename = edna_input_xml.xml_from_file_list(edna_energy_ev,xbeam_size,ybeam_size,1000000,aimed_completness,aimed_ISig,aimed_multiplicity,aimed_resolution,dna_filename_list)
#####  flux = 10000000000 * beamline_lib.get_epics_pv("flux","VAL")
  flux = 600000000.0  #for now
  edna_input_filename = dna_directory + "/adsc1_in.xml"
  edna_input_xml_command = "/h/data/backed-up/pxsys/skinner/edna_header_code/makeAnEDNAXML-bnl.sh 1232 %s %s none %f %f 4000 0.01 0.01 0 xh1223_2_ %f %f %f > %s" % (dna_directory,dna_prefix,3,aimed_ISig,flux,xbeam_size,ybeam_size,edna_input_filename)
#####  edna_input_xml_command = "ssh swill \"/h/data/backed-up/pxsys/skinner/edna_header_code/makeAnEDNAXML-bnl.sh 1232 %s %s none %f %f 4000 0.01 0.01 0 xh1223_2_ %f %f %f\" > %s" % (daq_lib.data_directory_name,dna_prefix,3,aimed_ISig,flux,xbeam_size,ybeam_size,edna_input_filename)
  print edna_input_xml_command
  comm_sss = "echo " + edna_input_xml_command + "> edna_comm.txt"
  os.system(comm_sss)
  os.system(edna_input_xml_command)

  print "done generating edna input\n"
#  command_string = "cd %s; /usr/local/crys/edna-mx/mxv1/bin/edna-mxv1-characterisation.py --verbose --data %s" % (dna_directory,edna_input_filename)
  command_string = "/usr/local/crys/edna-mx/mxv1/bin/edna-mxv1-characterisation.py --verbose --data %s" % (edna_input_filename)
#  command_string = "/usr/local/crys/edna-mx/mxv1/bin/edna-mxv1-characterisation.py --verbose --data /img11/data1/pxuser/staff/skinner/edna_run/adsc1_in.xml"
#old  command_string = "$EDNA_HOME/mxv1/bin/edna-mxv1-characterisation --data " + edna_input_filename
  print command_string
#  for i in range (0,len(dna_filename_list)):
#    command_string = command_string + " " + dna_filename_list[i]
  broadcast_output("\nProcessing with EDNA. Please stand by.\n")
  if ( os.path.exists( "edna.log" ) ) :
    os.remove( "edna.log" )
  if ( os.path.exists( "edna.err" ) ) :
    os.remove( "edna.err" )
  edna_execution_status = os.system( "%s > edna.log 2> edna.err" % command_string)
#####  fEdnaLogFile = open(daq_lib.get_misc_dir_name() + "/edna.log", "r" )
  fEdnaLogFile = open("./edna.log", "r" )
  ednaLogLines = fEdnaLogFile.readlines()
  fEdnaLogFile.close()
  for outline in ednaLogLines: 
 # for outline in os.popen(command_string,'r',0).readlines():
####skinner6/11 seg faults?    broadcast_output(outline)    
    if (string.find(outline,"EdnaDir")!= -1):
      (param,dirname) = string.split(outline,'=')
      strXMLFileName = dirname[0:len(dirname)-1]+"/ControlInterfacev1_2/Characterisation/ControlCharacterisationv1_3_dataOutput.xml"
#####      strXMLFileName = dirname[0:len(dirname)-1]+"/ControlInterfacev1_2/Characterisation/ControlCharacterisationv1_1_dataOutput.xml"
    if (string.find(outline,"characterisation successful!")!= -1):
      collect_and_characterize_success = 1
  if (not collect_and_characterize_success):
    dna_comment =  "Indexing Failure"
#####    pxdb_lib.update_sweep(2,daq_lib.sweep_seq_id,dna_comment)  
    return 0
  xsDataCharacterisation = XSDataResultCharacterisation.parseFile( strXMLFileName )
  xsDataIndexingResult = xsDataCharacterisation.getIndexingResult()
  xsDataIndexingSolutionSelected = xsDataIndexingResult.getSelectedSolution()
  xsDataStatisticsIndexing = xsDataIndexingSolutionSelected.getStatistics()
  numSpotsFound  = xsDataStatisticsIndexing.getSpotsTotal().getValue()
  numSpotsUsed  = xsDataStatisticsIndexing.getSpotsUsed().getValue()
  numSpotsRejected = numSpotsFound-numSpotsUsed
  beamShiftX = xsDataStatisticsIndexing.getBeamPositionShiftX().getValue()
  beamShiftY = xsDataStatisticsIndexing.getBeamPositionShiftY().getValue()
  spotDeviationR = xsDataStatisticsIndexing.getSpotDeviationPositional().getValue()
  try:
    spotDeviationTheta = xsDataStatisticsIndexing.getSpotDeviationAngular().getValue()
  except AttributeError:
    spotDeviationTheta = 0.0
  diffractionRings = 0 #for now, don't see this in xml except message string        
  reflections_used = 0 #for now
  reflections_used_in_indexing = 0 #for now
  rejectedReflections = 0 #for now
  xsDataOrientation = xsDataIndexingSolutionSelected.getOrientation()
  xsDataMatrixA = xsDataOrientation.getMatrixA()
  rawOrientationMatrix_a_x = xsDataMatrixA.getM11()
  rawOrientationMatrix_a_y = xsDataMatrixA.getM12()
  rawOrientationMatrix_a_z = xsDataMatrixA.getM13()
  rawOrientationMatrix_b_x = xsDataMatrixA.getM21()
  rawOrientationMatrix_b_y = xsDataMatrixA.getM22()
  rawOrientationMatrix_b_z = xsDataMatrixA.getM23()
  rawOrientationMatrix_c_x = xsDataMatrixA.getM31()
  rawOrientationMatrix_c_y = xsDataMatrixA.getM32()
  rawOrientationMatrix_c_z = xsDataMatrixA.getM33()
  xsDataCrystal = xsDataIndexingSolutionSelected.getCrystal()
  xsDataCell = xsDataCrystal.getCell()
  unitCell_alpha = xsDataCell.getAngle_alpha().getValue()
  unitCell_beta = xsDataCell.getAngle_beta().getValue()
  unitCell_gamma = xsDataCell.getAngle_gamma().getValue()
  unitCell_a = xsDataCell.getLength_a().getValue()
  unitCell_b = xsDataCell.getLength_b().getValue()
  unitCell_c = xsDataCell.getLength_c().getValue()
  mosaicity = xsDataCrystal.getMosaicity().getValue()
  xsSpaceGroup = xsDataCrystal.getSpaceGroup()
  spacegroup_name = xsSpaceGroup.getName().getValue()
  pointGroup = spacegroup_name #for now
  bravaisLattice = pointGroup #for now
  statusDescription = "ok" #for now
  try:
    spacegroup_number = xsSpaceGroup.getITNumber().getValue()
  except AttributeError:
    spacegroup_number = 0
  xsStrategyResult = xsDataCharacterisation.getStrategyResult()
  resolutionObtained = -999
  if (xsStrategyResult != None):
    dna_have_strategy_results = 1
    xsCollectionPlan = xsStrategyResult.getCollectionPlan()
    xsStrategySummary = xsCollectionPlan[0].getStrategySummary()
    resolutionObtained = xsStrategySummary.getRankingResolution().getValue()
    xsCollectionStrategy = xsCollectionPlan[0].getCollectionStrategy()
    xsSubWedge = xsCollectionStrategy.getSubWedge()
    for i in range (0,len(xsSubWedge)):
      xsExperimentalCondition = xsSubWedge[i].getExperimentalCondition()
      xsGoniostat = xsExperimentalCondition.getGoniostat()
      xsDetector = xsExperimentalCondition.getDetector()
      xsBeam = xsExperimentalCondition.getBeam()
      dna_strategy_start = xsGoniostat.getRotationAxisStart().getValue()
      dna_strategy_start = dna_strategy_start-(dna_strategy_start%.1)
      dna_strategy_range = xsGoniostat.getOscillationWidth().getValue()
      dna_strategy_range = dna_strategy_range-(dna_strategy_range%.1)
      dna_strategy_end = xsGoniostat.getRotationAxisEnd().getValue()
      dna_strategy_end = (dna_strategy_end-(dna_strategy_end%.1)) + dna_strategy_range
      dna_strat_dist = xsDetector.getDistance().getValue()
      dna_strat_dist = dna_strat_dist-(dna_strat_dist%1)
      dna_strategy_exptime = xsBeam.getExposureTime().getValue()
#wtf?      dna_strategy_exptime = dna_strategy_exptime-(dna_strategy_exptime%.2)
  program = "edna-1.0" # for now
#####  screeningoutputid = pxdb_lib.insert_dna_index_results(daq_lib.sweep_seq_id,daq_lib.get_field("xtal_id"),program,statusDescription,rejectedReflections,resolutionObtained,spotDeviationR,spotDeviationTheta,beamShiftX,beamShiftY,numSpotsFound,numSpotsUsed,numSpotsRejected,mosaicity,diffractionRings,spacegroup_name,pointGroup,bravaisLattice,rawOrientationMatrix_a_x,rawOrientationMatrix_a_y,rawOrientationMatrix_a_z,rawOrientationMatrix_b_x,rawOrientationMatrix_b_y,rawOrientationMatrix_b_z,rawOrientationMatrix_c_x,rawOrientationMatrix_c_y,rawOrientationMatrix_c_z,unitCell_a,unitCell_b,unitCell_c,unitCell_alpha,unitCell_beta,unitCell_gamma)
  dna_comment =  "spacegroup = " + str(spacegroup_name) + " mosaicity = " + str(mosaicity) + " resolutionHigh = " + str(resolutionObtained) + " cell_a = " + str(unitCell_a) + " cell_b = " + str(unitCell_b) + " cell_c = " + str(unitCell_c) + " cell_alpha = " + str(unitCell_alpha) + " cell_beta = " + str(unitCell_beta) + " cell_gamma = " + str(unitCell_gamma) + " status = " + str(statusDescription)
#####  print "\n\n skinner " + dna_comment + "\n" +str(daq_lib.sweep_seq_id) + "\n"
  print "\n\n skinner " + dna_comment + "\n" 
#####  pxdb_lib.update_sweep(2,daq_lib.sweep_seq_id,dna_comment)
  if (dna_have_strategy_results):
#####    pxdb_lib.insert_to_screening_strategy_table(screeningoutputid,dna_strategy_start,dna_strategy_end,dna_strategy_range,dna_strategy_exptime,resolutionObtained,program)
    dna_strat_comment = "\ndna Strategy results: Start=" + str(dna_strategy_start) + " End=" + str(dna_strategy_end) + " Width=" + str(dna_strategy_range) + " Time=" + str(dna_strategy_exptime) + " Dist=" + str(dna_strat_dist)
#    characterizationResult = {}
    characterizationResultObj = {}
#    characterizationResult["type"] = "characterizationStrategy"
 #   characterizationResult["timestamp"] = time.time()
    characterizationResultObj = {"strategy":{"start":dna_strategy_start,"end":dna_strategy_end,"width":dna_strategy_range,"exptime":dna_strategy_exptime,"detDist":dna_strat_dist}}
#    characterizationResult["resultObj"] = characterizationResultObj
    db_lib.addResultforRequest("characterizationStrategy",charRequest["request_id"], characterizationResultObj)
#####    pxdb_lib.update_sweep(2,daq_lib.sweep_seq_id,dna_strat_comment)
    xsStrategyStatistics = xsCollectionPlan[0].getStatistics()
    xsStrategyResolutionBins = xsStrategyStatistics.getResolutionBin()
    now = time.time()
#  edna_isig_plot_filename = dirname[0:len(dirname)-1] + "/edna_isig_res_" + str(now) + ".txt"
    edna_isig_plot_filename = dirname[0:len(dirname)-1] + "/edna_isig_res.txt"
    isig_plot_file = open(edna_isig_plot_filename,"w")
    for i in range (0,len(xsStrategyResolutionBins)-1):
      i_over_sigma_bin = xsStrategyResolutionBins[i].getIOverSigma().getValue()
      maxResolution_bin = xsStrategyResolutionBins[i].getMaxResolution().getValue()
      print  str(maxResolution_bin) + " " + str(i_over_sigma_bin)
      isig_plot_file.write(str(maxResolution_bin) + " " + str(i_over_sigma_bin)+"\n")
    isig_plot_file.close()
#####    comm_s = "isig_res_plot.pl -i " + edna_isig_plot_filename + " -o " + daq_lib.html_data_directory_name + "/edna_isig_res_plot" + str(int(now))
#####    os.system(comm_s)
#####  broadcast_output(dna_comment)
  if (dna_have_strategy_results):
    broadcast_output(dna_strat_comment)  
  
  return 1


def addFileToDB(filename):
  fd = open(filename)
  fID = db_lib.addFile(fd.read())
  print "you stored fileID " + str(fID)
  return fID
