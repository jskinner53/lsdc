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
  for i in range (1,len(tokens)-1,2):
    point = [tokens[i],tokens[i+1]]
    correctedPoint = [daq_utils.screenPixX-int(tokens[i]),daq_utils.screenPixY-int(tokens[i+1])]
  xrec_out_file.close() 


def autoRasterLoop():
  loop_center_xrec()
  getXrecLoopShape()
  time.sleep(1) #looks like I really need this sleep
  runRasterScan()
  runRasterScan("Fine")
  runRasterScan("Line")  



def loop_center_xrec():
  global face_on

  daq_lib.abort_flag = 0    
  for i in range(0,360,40):
    if (daq_lib.abort_flag == 1):
      return 0
    mva("Omega",i)
    pic_prefix = "findloop_" + str(i)
#    time.sleep(0.1)
    take_crystal_picture(pic_prefix)
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


def generateGridMap(rasterDef):
#  rasterDef = db_lib.getRasters()[0]
#  print rasterDef
  stepsize = float(rasterDef["stepsize"])
  omega = float(rasterDef["omega"])
  rasterStartX = float(rasterDef["x"])
  rasterStartY = float(rasterDef["y"])
  rasterStartZ = float(rasterDef["z"])
  omegaRad = math.radians(omega)
  grid_map_file = open("raster_map.txt","w+")
  grid_spots_file = open("raster_spots.txt","w+")
  filePrefix = "raster" #for now
  for i in range (0,len(rasterDef["rowDefs"])):
    numsteps = float(rasterDef["rowDefs"][i]["numsteps"])
    if (i%2 == 0): #left to right if even, else right to left - a snake attempt
      startX = rasterDef["rowDefs"][i]["start"]["x"]+(stepsize/2.0) #this is relative to center, so signs are reversed from motor movements.
    else:
      startX = (numsteps*stepsize) + rasterDef["rowDefs"][i]["start"]["x"]-(stepsize/2.0)
    startY = rasterDef["rowDefs"][i]["start"]["y"]+(stepsize/2.0)
    xRelativeMove = startX
    yxRelativeMove = startY*sin(omegaRad)
    yyRelativeMove = startY*cos(omegaRad)
    zMotAbsoluteMove = rasterStartZ-xRelativeMove
    yMotAbsoluteMove = rasterStartY-yyRelativeMove
    xMotAbsoluteMove = yxRelativeMove+rasterStartX
    numsteps = int(rasterDef["rowDefs"][i]["numsteps"])
    for j in range (0,numsteps):
      if (i%2 == 0): #left to right if even, else right to left - a snake attempt
        zMotCellAbsoluteMove = zMotAbsoluteMove-(j*stepsize)
      else:
        zMotCellAbsoluteMove = zMotAbsoluteMove+(j*stepsize)
#      zMotAbsoluteMove = zMotAbsoluteMove-(j*stepsize)
      dataFileName = create_filename(filePrefix+"_"+str(i),j)
      grid_map_file.write("%f %f %f %s\n" % (xMotAbsoluteMove,yMotAbsoluteMove,zMotCellAbsoluteMove,dataFileName))
      grid_spots_file.write("%d %s\n" % (randint(0,900),dataFileName))
  grid_map_file.close()  
  grid_spots_file.close()  


def generateSingleColumnGridMap(rasterDef):
#  rasterDef = db_lib.getRasters()[0]
#  print rasterDef
  stepsize = float(rasterDef["stepsize"])
  omega = float(rasterDef["omega"])
  rasterStartX = float(rasterDef["x"])
  rasterStartY = float(rasterDef["y"])
  rasterStartZ = float(rasterDef["z"])
  omegaRad = math.radians(omega)
  grid_map_file = open("raster_map.txt","w+")
  grid_spots_file = open("raster_spots.txt","w+")
  filePrefix = "columnRaster" #for now
  for i in range (0,len(rasterDef["rowDefs"])):
    numsteps = float(rasterDef["rowDefs"][i]["numsteps"])
    startX = rasterDef["rowDefs"][i]["start"]["x"]+(stepsize/2.0) #this is relative to center, so signs are reversed from motor movements.
    startY = rasterDef["rowDefs"][i]["start"]["y"]+(stepsize/2.0)
    xRelativeMove = startX
    yxRelativeMove = startY*sin(omegaRad)
    yyRelativeMove = startY*cos(omegaRad)
    zMotAbsoluteMove = rasterStartZ-xRelativeMove
    yMotAbsoluteMove = rasterStartY-yyRelativeMove
    xMotAbsoluteMove = yxRelativeMove+rasterStartX
    numsteps = int(rasterDef["rowDefs"][i]["numsteps"])
    for j in range (0,numsteps):
      yxRelativeMove = stepsize*sin(omegaRad)
      yyRelativeMove = -stepsize*cos(omegaRad)
      xMotCellAbsoluteMove = xMotAbsoluteMove+(j*yxRelativeMove)
      yMotCellAbsoluteMove = yMotAbsoluteMove+(j*yyRelativeMove)
#      zMotAbsoluteMove = zMotAbsoluteMove-(j*stepsize)
      dataFileName = create_filename(filePrefix+"_"+str(i),j)
      grid_map_file.write("%f %f %f %s\n" % (xMotCellAbsoluteMove,yMotCellAbsoluteMove,zMotAbsoluteMove,dataFileName))
      grid_spots_file.write("%d %s\n" % (randint(0,900),dataFileName))
  grid_map_file.close()  
  grid_spots_file.close()  



def columnRaster(): #3/10/15 - not used yet, raster would need to be defined for column orientation. Address later if needed.
  rasterDef = db_lib.getRasters()[0]
#  print rasterDef
  stepsize = float(rasterDef["stepsize"])
  omega = float(rasterDef["omega"])
  rasterStartX = float(rasterDef["x"])
  rasterStartY = float(rasterDef["y"])
  rasterStartZ = float(rasterDef["z"])
  omegaRad = math.radians(omega)
  for i in range (0,len(rasterDef["rowDefs"])):
    rowCellCount = 0
    numsteps = int(rasterDef["rowDefs"][i]["numsteps"])
    if (i%2 == 0): #left to right if even, else right to left - a snake attempt
      startY = rasterDef["rowDefs"][i]["start"]["y"]+(stepsize/2.0)
    else:
      startY = (numsteps*stepsize) + rasterDef["rowDefs"][i]["start"]["y"]-(stepsize/2.0)
#    startY = rasterDef["rowDefs"][i]["start"]["y"]+(stepsize/2.0)
    startX = rasterDef["rowDefs"][i]["start"]["x"]+(stepsize/2.0)

    xRelativeMove = startX
    yxRelativeMove = -startY*sin(omegaRad)
    yyRelativeMove = startY*cos(omegaRad)
    zMotAbsoluteMove = rasterStartZ-xRelativeMove
    yMotAbsoluteMove = rasterStartY-yyRelativeMove
    xMotAbsoluteMove = yxRelativeMove+rasterStartX
    mva("X",xMotAbsoluteMove,"Y",yMotAbsoluteMove,"Z",zMotAbsoluteMove)
    if (i%2 == 0): #left to right if even, else right to left - a snake attempt
      yRelativeMove = -((numsteps-1)*stepsize)
    else:
      yRelativeMove = ((numsteps-1)*stepsize)
    yxRelativeMove = -yRelativeMove*sin(omegaRad)
    yyRelativeMove = yRelativeMove*cos(omegaRad)
    print "mvr Y " + str(yyRelativeMove)
    print "mvr X " + str(yxRelativeMove)
    mvr("X",yxRelativeMove,"Y",yyRelativeMove)
#    mvr("X",yxRelativeMove)
  mva("X",rasterStartX,"Y",rasterStartY,"Z",rasterStartZ)
  generateGridMap()
#  gotoMaxRaster("raster_spots.txt","raster_map.txt")
  set_field("xrecRasterFlag",2)  


def singleColumnRaster(): #for the 90-degree step.
  time.sleep(0.2) #maybe need this??
###  time.sleep(2)
  rasterDef = db_lib.getNextRunRaster()
#  print rasterDef
  stepsize = float(rasterDef["stepsize"])
  omega = float(rasterDef["omega"])
  rasterStartX = float(rasterDef["x"])
  rasterStartY = float(rasterDef["y"])
  rasterStartZ = float(rasterDef["z"])
  omegaRad = math.radians(omega)
  numsteps = int(rasterDef["rowDefs"][0]["numsteps"])
  startY = rasterDef["rowDefs"][0]["start"]["y"]+(stepsize/2.0) #- these are the simple relative moves
  startX = rasterDef["rowDefs"][0]["start"]["x"]+(stepsize/2.0)
  xRelativeMove = startX
  yxRelativeMove = startY*sin(omegaRad)
  yyRelativeMove = -startY*cos(omegaRad)
#  print "mvr Y " + str(yyRelativeMove)
#  print "mvr X " + str(yxRelativeMove)

  mvr("X",yxRelativeMove,"Y",yyRelativeMove,"Z",xRelativeMove) #this should get to the start
  time.sleep(1)#cosmetic
  yRelativeMove = -((numsteps-1)*stepsize)
  yxRelativeMove = -yRelativeMove*sin(omegaRad)
  yyRelativeMove = yRelativeMove*cos(omegaRad)
#  print "mvr Y " + str(yyRelativeMove)
#  print "mvr X " + str(yxRelativeMove)
  mvr("X",yxRelativeMove,"Y",yyRelativeMove) #this should be the actual scan

#  mva("X",rasterStartX,"Y",rasterStartY,"Z",rasterStartZ)
  generateSingleColumnGridMap(rasterDef) #this might need to be different depending on scan direction
  gotoMaxRaster("raster_spots.txt","raster_map.txt")
  set_field("xrecRasterFlag",2)  

def snakeRaster(grain=""):
  rasterDef = db_lib.getNextRunRaster()
#  print rasterDef
  stepsize = float(rasterDef["stepsize"])
  omega = float(rasterDef["omega"])
  rasterStartX = float(rasterDef["x"])
  rasterStartY = float(rasterDef["y"])
  rasterStartZ = float(rasterDef["z"])
  omegaRad = math.radians(omega)
  for i in range (0,len(rasterDef["rowDefs"])):
    rowCellCount = 0
    numsteps = float(rasterDef["rowDefs"][i]["numsteps"])
    if (i%2 == 0): #left to right if even, else right to left - a snake attempt
      startX = rasterDef["rowDefs"][i]["start"]["x"]+(stepsize/2.0)
    else:
      startX = (numsteps*stepsize) + rasterDef["rowDefs"][i]["start"]["x"]-(stepsize/2.0)
    startY = rasterDef["rowDefs"][i]["start"]["y"]+(stepsize/2.0)
    xRelativeMove = startX
    yxRelativeMove = startY*sin(omegaRad)
    yyRelativeMove = startY*cos(omegaRad)
    zMotAbsoluteMove = rasterStartZ-xRelativeMove
    yMotAbsoluteMove = rasterStartY-yyRelativeMove
    xMotAbsoluteMove = yxRelativeMove+rasterStartX
#    print str(xMotAbsoluteMove) + " " + str(yMotAbsoluteMove) + " " + str(zMotAbsoluteMove)
    mva("X",xMotAbsoluteMove,"Y",yMotAbsoluteMove,"Z",zMotAbsoluteMove) #why not just do relative move here, b/c the relative move is an offset from center
#    mva("Y",yMotAbsoluteMove)
#    mva("Z",zMotAbsoluteMove)
    if (i%2 == 0): #left to right if even, else right to left - a snake attempt
      xRelativeMove = -((numsteps-1)*stepsize)
    else:
      xRelativeMove = ((numsteps-1)*stepsize)
#    print xRelativeMove
#########    time.sleep(0.2)
    mvr("Z",xRelativeMove)
#    time.sleep(0.3)
###  mva("X",rasterStartX,"Y",rasterStartY,"Z",rasterStartZ)
#  mva("Y",rasterStartY)
#  mva("Z",rasterStartZ)
  generateGridMap(rasterDef)
  gotoMaxRaster("raster_spots.txt","raster_map.txt")
  set_field("xrecRasterFlag",2)  

def runRasterScan(rasterType=""):
  if (rasterType=="Fine"):
    set_field("xrecRasterFlag",100)    
    defineRectRaster(50,50,10)
    snakeRaster()
#    gotoMaxRaster("raster_spots.txt","raster_map.txt")
#    set_field("xrecRasterFlag",2)  
  elif (rasterType=="Line"):  
    set_field("xrecRasterFlag",100)    
    mvr("Omega",90)
    defineColumnRaster(10,150,10)
    singleColumnRaster()
    set_field("xrecRasterFlag",100)    
  else:
    snakeRaster()


def gotoMaxRaster(spotfilename,mapfilename):
  spotfile = open(spotfilename,"r")
  ceiling = 0
  hotFile = ""
  for spotline in spotfile.readlines():
    (spotcount_s,filename) = spotline.split()
    spotcount = int(spotcount_s)
    if (spotcount > ceiling):
      ceiling = spotcount    
      hotFile = filename
  spotfile.close()
  if (ceiling > 0):
    print hotFile
    rasterMapfile = open(mapfilename,"r")
    for mapline in rasterMapfile.readlines():
      (x_s,y_s,z_s,filename) = mapline.split()
      if (filename==hotFile):
        x = float(x_s)
        y = float(y_s)
        z = float(z_s)
        print "goto " + x_s + " " + y_s + " " + z_s
        mva("X",x,"Y",y,"Z",z)
#        mva("Y",y)
#        mva("Z",z)
    rasterMapfile.close()
  
    
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


def defineColumnRaster(raster_w,raster_h_s,stepsizeMicrons_s): #maybe point_x and point_y are image center? #everything can come as microns
  raster_h = float(raster_h_s)
  stepsizeMicrons = float(stepsizeMicrons_s)
  beamWidth = stepsizeMicrons
  beamHeight = stepsizeMicrons
  rasterDef = {"beamWidth":beamWidth,"beamHeight":beamHeight,"status":0,"x":get_epics_motor_pos("X"),"y":get_epics_motor_pos("Y"),"z":get_epics_motor_pos("Z"),"omega":get_epics_motor_pos("Omega"),"stepsize":stepsizeMicrons,"rowDefs":[]} #just storing step as microns, not using here
  stepsize = float(stepsizeMicrons)   #note conversion to pixels
  numsteps_h = 1
  numsteps_v = int(raster_h/stepsize) #the numsteps is decided in code, so is already odd
  point_offset_x = -stepsize/2.0
  point_offset_y = -(numsteps_v*stepsize)/2
  newRowDef = {"start":{"x": point_offset_x,"y":point_offset_y},"numsteps":numsteps_v}
  rasterDef["rowDefs"].append(newRowDef)
##      rasterCoords = {"x":pvGet(self.sampx_pv),"y":pvGet(self.sampy_pv),"z":pvGet(self.sampz_pv)}
#  print rasterDef
  db_lib.addRaster(rasterDef) 
  set_field("xrecRasterFlag",3)


def defineRectRaster(raster_w_s,raster_h_s,stepsizeMicrons_s): #maybe point_x and point_y are image center? #everything can come as microns
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
  for i in range (0,numsteps_v):
    newRowDef = {"start":{"x": point_offset_x,"y":point_offset_y+(i*stepsize)},"numsteps":numsteps_h}
    rasterDef["rowDefs"].append(newRowDef)
##      rasterCoords = {"x":pvGet(self.sampx_pv),"y":pvGet(self.sampy_pv),"z":pvGet(self.sampz_pv)}
#  print rasterDef
  db_lib.addRaster(rasterDef)
  set_field("xrecRasterFlag",1)
  time.sleep(1)


def definePolyRaster(raster_w,raster_h,stepsizeMicrons,point_x,point_y,rasterPoly): #all come in as pixels
  newRowDef = {}
#  print "draw raster " + str(raster_w) + " " + str(raster_h) + " " + str(stepsizeMicrons)
  beamWidth = stepsizeMicrons
  beamHeight = stepsizeMicrons
  rasterDef = {"beamWidth":beamWidth,"beamHeight":beamHeight,"status":0,"x":get_epics_motor_pos("X"),"y":get_epics_motor_pos("Y"),"z":get_epics_motor_pos("Z"),"omega":get_epics_motor_pos("Omega"),"stepsize":stepsizeMicrons,"rowDefs":[]} #just storing step as microns, not using here
  stepsize = screenXmicrons2pixels(stepsizeMicrons)   #note conversion to pixels
  numsteps_h = int(raster_w/stepsize) #raster_w = width,goes to numsteps horizonatl
  numsteps_v = int(raster_h/stepsize)
  if (numsteps_h%2 == 0):
    numsteps_h = numsteps_h + 1
  if (numsteps_v%2 == 0):
    numsteps_v = numsteps_v + 1
  point_offset_x = -(numsteps_h*stepsize)/2
  point_offset_y = -(numsteps_v*stepsize)/2
  for i in range (0,numsteps_v):
    rowCellCount = 0
    for j in range (0,numsteps_h):
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
  db_lib.addRaster(rasterDef)
  set_field("xrecRasterFlag",1)
##      self.drawPolyRaster(self.rasterDef)



def getXrecLoopShape():
  beamline_support.set_any_epics_pv("FAMX-cam1:MJPGZOOM:NDArrayPort","VAL","ROI1") #not the best, but I had timing issues doing it w/o a sleep
  for i in range(0,4):
    if (daq_lib.abort_flag == 1):
      return 0
    mvr("Omega",i*30)
    pic_prefix = "findloopshape_" + str(i)
#    time.sleep(0.1)
    take_crystal_picture(pic_prefix,1)
  comm_s = "xrec30 xrec30.txt xrec30_result.txt"
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
  for i in range (1,len(tokens)-1,2):
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
  definePolyRaster(raster_w,raster_h,stepsizeMicrons,center_x,center_y,rasterPoly)


def vectorScan(numPoints_s): #bogus for now until we figure out what we want
  numPoints = int(numPoints_s)
  for i in range (0,numPoints+1):
    vector_move(float(i)*(100.0/float(numPoints))/100.0)
#    time.sleep(.1)


