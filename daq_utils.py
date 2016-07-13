import time
#import string
import os
from math import *
import requests

import functools


import xmltodict

#import metadatastore.commands as mdsc

#import beamline_support
import db_lib
# need to change refs to daq_utils.[these_funcs] to db_lib.[these_funcs] and then nuke this line
from db_lib import (setBeamlineConfigParams, getBeamlineConfigParam, getAllBeamlineConfigParams)

#global det_radius
#det_radius = 0
global beamline
beamline = "john"
global beamlineComm #this is the comm_ioc
beamlineComm = "XF:17IDC-ES:FMX{Comm}"
global searchParams
global motor_dict,counter_dict,scan_list,soft_motor_list
motor_dict = {}
counter_dict = {}
scan_list = []
soft_motor_list = []
global screenYCenterPixelsLowMagOffset
screenYCenterPixelsLowMagOffset = 58


#searchParams = {"config_params.beamline_id":beamline}
searchParams = {'info_name': 'config_params', 'beamline_id': beamline}


# needed for moving beamlineconfig stuff to db_lib while retaining the existing signatures
setBeamlineConfigParams = functools.partial(setBeamlineConfigParams, searchParams=searchParams)
getBeamlineConfigParam = functools.partial(getBeamlineConfigParam, searchParams=searchParams)
getAllBeamlineConfigParams = functools.partial(getAllBeamlineConfigParams, searchParams=searchParams)



def init_environment():
  global beamline,detector_id,mono_mot_code,has_beamline,has_xtalview,xtal_url,xtal_url_small,xtalview_user,xtalview_pass,det_type,has_dna,beamstop_x_pvname,beamstop_y_pvname,camera_offset,det_radius,lowMagFOVx,lowMagFOVy,highMagFOVx,highMagFOVy,lowMagPixX,lowMagPixY,highMagPixX,highMagPixY,screenPixX,screenPixY,screenPixCenterX,screenPixCenterY,screenProtocol,screenPhist,screenPhiend,screenWidth,screenDist,screenExptime,screenWave,screenReso,gonioPvPrefix,searchParams,screenEnergy,detectorOffline,imgsrv_host,imgsrv_port,xbeam,ybeam

#  var_list["state"] = "Idle"


# beamlineConfig = db_lib.getAllBeamlineConfigParams(**searchParams)
  beamlineConfig = getAllBeamlineConfigParams()
  xbeam = float(beamlineConfig["xbeam"])
  ybeam = float(beamlineConfig["ybeam"])  
  lowMagFOVx = float(beamlineConfig["lowMagFOVx"])
  lowMagFOVy = float(beamlineConfig["lowMagFOVy"])
  highMagFOVx = float(beamlineConfig["highMagFOVx"]) #digizoom will be this/2
  highMagFOVy = float(beamlineConfig["highMagFOVy"])
  lowMagPixX = float(beamlineConfig["lowMagPixX"]) #for automated images
  lowMagPixY = float(beamlineConfig["lowMagPixY"])
  highMagPixX = float(beamlineConfig["highMagPixX"]) #for automated images
  highMagPixY = float(beamlineConfig["highMagPixY"])
  screenPixX = float(beamlineConfig["screenPixX"])
  screenPixY = float(beamlineConfig["screenPixY"])
  screenPixCenterX = screenPixX/2.0
  screenPixCenterY = screenPixY/2.0
  gonioPvPrefix = beamlineConfig["gonioPvPrefix"]
  detector_id = beamlineConfig["detector_id"]
  if (detector_id == "ADSC-Q315"):
    det_radius = 157.5
  elif (detector_id == "ADSC-Q210"):
    det_radius = 105.0
  elif (detector_id == "PILATUS-6"):
    det_radius = 212.0
  elif (detector_id == "ADSC-Q4"):
    det_radius = 94.0
  else: #default q4
    det_radius = 94.0 
  det_type = beamlineConfig["detector_type"]
  imgsrv_port = beamlineConfig["imgsrv_port"]
  imgsrv_host = beamlineConfig["imgsrv_host"]
  has_dna = int(beamlineConfig["has_edna"])
  has_beamline = int(beamlineConfig["has_beamline"])
  detectorOffline = int(beamlineConfig["detector_offline"])
  has_xtalview = int(beamlineConfig["has_xtalview"])
  camera_offset = float(beamlineConfig["camera_offset"])
  if (has_xtalview):
    xtal_url_small = beamlineConfig["xtal_url_small"]
    xtal_url = beamlineConfig["xtal_url"]
  mono_mot_code = beamlineConfig["mono_mot_code"]
  screenProtocol = beamlineConfig["screen_default_protocol"]
  screenPhist = float(beamlineConfig["screen_default_phist"])
  screenPhiend = float(beamlineConfig["screen_default_phi_end"])
  screenWidth = float(beamlineConfig["screen_default_width"])
  screenDist =  float(beamlineConfig["screen_default_dist"])
  screenExptime = float(beamlineConfig["screen_default_time"])
  screenReso = float(beamlineConfig["screen_default_reso"])
  screenWave = float(beamlineConfig["screen_default_wave"])
  screenEnergy = float(beamlineConfig["screen_default_energy"])
  screenbeamWidth = float(beamlineConfig["screen_default_beamWidth"])
  screenbeamHeight = float(beamlineConfig["screen_default_beamHeight"])
  screenTransmissionPercent = float(beamlineConfig["screen_transmission_percent"])
  beamstop_x_pvname = beamlineConfig["beamstop_x_pvname"]
  beamstop_y_pvname = beamlineConfig["beamstop_y_pvname"]

  varname = "HAS_XTALVIEW"
  if varname in os.environ:
    has_xtalview = int(os.environ[varname])
  varname = "DETECTOR_OFFLINE"
  if varname in os.environ:
    detectorOffline = int(os.environ[varname])



#def broadcast_output(s):
#  time.sleep(0.01)
#  if (string.find(s,'|') == -1):
#    print s
#  beamline_support.pvPut(message_string_pv,s)


# beamlineconfig stuff moved to db_lib


def ObsoletegetCurrentFOVx(camera,zoom): #cam 0 = lowMag, 
  if (camera==0):
    return daq_utils.lowMagFOVx
  else:
    if (zoom==0):
      return daq_utils.highMagFOVx          
    else:
      return daq_utils.highMagFOVx/2          

def ObsoletegetCurrentFOVy(camera,zoom): #cam 0 = lowMag, 
  if (camera==0):
    return daq_utils.lowMagFOVy
  else:
    if (zoom==0):
      return daq_utils.highMagFOVy
    else:
      return daq_utils.highMagFOVy/2          


def calc_reso(det_radius,distance,wave,theta):

  dg2rd = 3.14159265 / 180.0
#  det_radius = float(diameter)/2
  theta_radians = float(theta) * dg2rd
  theta_t = (theta_radians + atan(det_radius/float(distance)))/2
  dmin_t = float(wave)/(2*(sin(theta_t)))
  return float("%.2f" % dmin_t)


def distance_from_reso(det_radius,reso,wave,theta):

  try:
    dg2rd = 3.14159265 / 180.0
    theta_radians = float(theta) * dg2rd
#  det_radius = float(diameter)/2
    dx = det_radius/(tan(2*(asin(float(wave)/(2*reso)))-theta_radians))
    return float("%.2f" % dx)
  except ValueError:  
    return 500.0 #a safe value for now


def energy2wave(e):
  return float("%.2f" % (12.3985/e))

def wave2energy(w):
  return float("%.2f" % (12.3985/w))

def createDefaultRequest(sample_id):
    """
    Doesn't really create a request, just returns a dictionary
    with the default parameters that can be passed to addRequesttoSample().
    """
#   beamlineConfig = db_lib.getAllBeamlineConfigParams(**searchParams)
    beamlineConfig = getAllBeamlineConfigParams()

    screenPhist = float(beamlineConfig["screen_default_phist"])
    screenPhiend = float(beamlineConfig["screen_default_phi_end"])
    screenWidth = float(beamlineConfig["screen_default_width"])
    screenDist =  float(beamlineConfig["screen_default_dist"])
    screenExptime = float(beamlineConfig["screen_default_time"])
    screenReso = float(beamlineConfig["screen_default_reso"])
    screenWave = float(beamlineConfig["screen_default_wave"])
    screenEnergy = float(beamlineConfig["screen_default_energy"])
    screenbeamWidth = float(beamlineConfig["screen_default_beamWidth"])
    screenbeamHeight = float(beamlineConfig["screen_default_beamHeight"])
    screenTransmissionPercent = float(beamlineConfig["screen_transmission_percent"])
    sampleName = str(db_lib.getSampleNamebyID(sample_id))
    basePath = os.getcwd()
    runNum = db_lib.getSampleRequestCount(sample_id)
    request = {"sample_id": sample_id}
    requestObj = {
               "sample_id": sample_id,
               "sweep_start": screenPhist,  "sweep_end": screenPhiend,
               "img_width": screenWidth,
               "exposure_time": screenExptime,
               "protocol": "standard",
               "parentReqID": -1,
               "basePath": basePath,
               "file_prefix": sampleName,
               "directory": basePath+"/projID/"+sampleName+"/" + str(runNum) + "/",
               "file_number_start": 1,
               "energy":screenEnergy,
               "wavelength": energy2wave(screenEnergy),
               "resolution": screenReso,
               "slit_height": screenbeamHeight,  "slit_width": screenbeamWidth,
               "attenuation": screenTransmissionPercent,
               "pos_x": 0,  "pos_y": 0,  "pos_z": 0,  "pos_type": 'A', "gridStep": 30}
    request["request_obj"] = requestObj

    return request

def createResult(typeName,resultObj):
  result = {}
  result["type"] = typeName
  result["timestamp"] = time.time()
  result["resultObj"] = resultObj
  return result


def runDials(imgPath,reqID=None):
  comm_s = "dials.find_spots_client " + imgPath
  print(comm_s)
  dialsResultObj = xmltodict.parse("<data>\n"+os.popen(comm_s).read()+"</data>\n")
  print("done parsing dials output")
  print(dialsResultObj)
  currentRequestID = db_lib.beamlineInfo(beamline, 'currentRequestID')["requestID"]
  dialsResult = db_lib.addResultforRequest("dials",currentRequestID, dialsResultObj)



def take_crystal_picture(filename=None,czoom=0,reqID=None,omega=-999):
  zoom = int(czoom)
  if not (has_xtalview):
    return
  if (1):
    if (zoom==0):
      r=requests.get(xtal_url)
    else:
      r=requests.get(xtal_url_small)
  else: #password, need to change to requests module if we need this
    comm_s = "curl -u %s:%s -o %s.jpg -s %s" % (xtalview_user,xtalview_pass,filename,xtal_url)
  data = r.content
  if (filename != None):
    fd = open(filename+".jpg","wb+")
    fd.write(data)
    fd.close()
  if (reqID != None):
    xtalpicJpegDataResult = {}
    imgRef = db_lib.addFile(data)
    xtalpicJpegDataResult["data"] = imgRef
    xtalpicJpegDataResult["omegaPos"] = omega 
    db_lib.addResultforRequest("xtalpicJpeg",reqID,xtalpicJpegDataResult)


def diff2jpegLYNX(diffimageName,JPEGfilename=None,reqID=None):
  imageJpegData = {}
  imageJpegHeader = {}
  imageJpegData["dataFilePath"]=diffimageName
  img_url = "http://"+imgsrv_host+":"+imgsrv_port+"/getImage\?fileName="+ diffimageName+"\&sizeX=500\&sizeY=500\&gray=100\&zoom=1.0\&percentX=0.5\&percentY=0.5\&userName=me\&sessionId=E"
#  comm_s = "lynx -source %s >%s" % (img_url,JPEGfilename) 
  comm_s = "lynx -source %s" % (img_url) 
  print(comm_s)
  data = os.popen(comm_s).read()
  imageJpegData["data"] = data
#  os.system(comm_s)
  img_url = "http://"+imgsrv_host+":"+imgsrv_port+"/getThumbnail\?fileName="+ diffimageName+"\&sizeX=500\&sizeY=500\&gray=100\&zoom=1.0\&percentX=0.5\&percentY=0.5\&userName=me\&sessionId=E"
  comm_s = "lynx -source %s" % (img_url) 
  thumbData = os.popen(comm_s).read()
  imageJpegData["thumbData"] = thumbData
#  comm_s = "lynx -source %s >%s" % (img_url,"thumb_"+JPEGfilename) 
  print(comm_s)
#  os.system(comm_s)
  img_url = "http://"+imgsrv_host+":"+imgsrv_port+"/getHeader\?fileName="+ diffimageName+"\&userName=me\&sessionId=E"
  comm_s = "lynx -source " + img_url
  for outputline in os.popen(comm_s).readlines():    
    print(outputline)
    tokens = outputline.split()      
    if (tokens[0] == "OSC_START"):
      print("Omega start = " + tokens[1])
      imageJpegHeader["oscStart"] = float(tokens[1])
    elif (tokens[0] == "OSC_RANGE"):
      print("Omega range = " + tokens[1]) 
      imageJpegHeader["oscRange"] = float(tokens[1])
    elif (tokens[0] == "EXPOSURE"):
      print("Exposure Time = " + tokens[2])
      imageJpegHeader["exptime"] = float(tokens[2])
    elif (tokens[0] == "DISTANCE"):
      print("Distance = " + str(float(tokens[1])/1000.0))
      imageJpegHeader["detDist"] = float(tokens[1])
    elif (tokens[0] == "WAVELENGTH"):
      print("Wavelength = " + tokens[1]) 
      imageJpegHeader["wave"] = float(tokens[1])
  if (reqID != None):
    resultObj = {}
    imgRef = db_lib.addFile(data)
    resultObj["data"] = imgRef
    imgRef = db_lib.addFile(thumbData)
    resultObj["thumbData"] = imgRef
    resultObj["dataFilePath"] = diffimageName
    resultObj["header"] = imageJpegHeader
    db_lib.addResultforRequest("diffImageJpeg",reqID,resultObj)
  return imageJpegData


def diff2jpeg(diffimageName,JPEGfilename=None,reqID=None):
  imageJpegData = {}
  imageJpegHeader = {}
  imageJpegData["dataFilePath"]=diffimageName
  payload = {"fileName":diffimageName,"sizeX":500,"sizeY":500,"gray":100,"percentX":0.5,"percentY":0.5,"userName":"me","sessionId":"E","zoom":1.0}
  img_url = "http://"+imgsrv_host+":"+imgsrv_port+"/getImage" 
  r = requests.get(img_url,params=payload)
  data = r.content
  imageJpegData["data"] = data
  img_url = "http://"+imgsrv_host+":"+imgsrv_port+"/getThumbnail"
  r = requests.get(img_url,params=payload)
  thumbData = r.content
  imageJpegData["thumbData"] = thumbData
  payload = {"fileName":diffimageName,"userName":"me","sessionId":"E"}
  img_url = "http://"+imgsrv_host+":"+imgsrv_port+"/getHeader"
  r = requests.get(img_url,params=payload)
  imageJpegData["header"] = r
  headerData = r.text
  lines = headerData.split("\n")
  for i in range (0,len(lines)):
    line = lines[i]
    print(line)
    tokens = line.split()
    if (len(tokens) > 1):
      if (tokens[0] == "OSC_START"):
        print("Omega start = " + tokens[1])
        imageJpegHeader["oscStart"] = float(tokens[1])
      elif (tokens[0] == "OSC_RANGE"):
        print("Omega range = " + tokens[1]) 
        imageJpegHeader["oscRange"] = float(tokens[1])
      elif (tokens[0] == "EXPOSURE"):
        print("Exposure Time = " + tokens[2])
        imageJpegHeader["exptime"] = float(tokens[2])
      elif (tokens[0] == "DISTANCE"):
        print("Distance = " + str(float(tokens[1])/1000.0))
        imageJpegHeader["detDist"] = float(tokens[1])
      elif (tokens[0] == "WAVELENGTH"):
        print("Wavelength = " + tokens[1]) 
        imageJpegHeader["wave"] = float(tokens[1])
  imageJpegData["header"] = imageJpegHeader
  if (reqID != None): #this means I'll dump into mongo as a result
    resultObj = {}
    imgRef = db_lib.addFile(data)
    resultObj["data"] = imgRef
    imgRef = db_lib.addFile(thumbData)
    resultObj["thumbData"] = imgRef
    resultObj["dataFilePath"] = diffimageName
    resultObj["header"] = imageJpegHeader
    db_lib.addResultforRequest("diffImageJpeg",reqID,resultObj)
  return imageJpegData

def create_filename(prefix,number):
  tmp_filename = "%s_%06d.cbf" % (prefix,int(number))
  if (prefix[0] != "/"):
    cwd = os.getcwd()
    filename = "%s/%s" % (cwd,tmp_filename)
  else:
    filename = tmp_filename
  return filename


def readPVDesc():
  global motor_dict,soft_motor_list,scan_list,counter_dict
  
  envname = "EPICS_BEAMLINE_INFO"
  try:
    dbfilename = os.environ[envname]
  except KeyError:
    print(envname + " not defined. Defaulting to epx.db.")
    dbfilename = "epx.db"
  if (os.path.exists(dbfilename) == 0):
    error_msg = "EPICS BEAMLINE INFO %s does not exist.\n Program exiting." % dbfilename
    print(error_msg)
    sys.exit()
  else:
    dbfile = open(dbfilename,'r')
    line = dbfile.readline()
    line = dbfile.readline()
    beamline_designation = line[:-1]
    line = dbfile.readline()
    i = 0
    while(1):
      line = dbfile.readline()
      if (line == ""):
        break
      else:
        line = line[:-1]
        if (line == "#virtual motors"):
          break
        else:
          motor_inf = line.split()
          motor_dict[motor_inf[1]] = beamline_designation +  motor_inf[0]
    while(1):
      line = dbfile.readline()
      if (line == ""):
        break
      else:
        line = line[:-1]
        if (line == "#scanned motors"):
          break
        else:
          motor_inf = line.split()
          soft_motor_list.append(beamline_designation + motor_inf[0])
          motor_dict[motor_inf[1]] = beamline_designation + motor_inf[0]          
    while(1):
      line = dbfile.readline()
      if (line == ""):
        break
      else:
        line = line[:-1]
        if (line == "#counters"):
          break
        else:
          scan_list.append(beamline_designation + line + "scanParms")
    line = dbfile.readline()
    counter_inf = line.split()    
    counter_dict[counter_inf[1]] = beamline_designation + counter_inf[0]    




#def calc_reso_edge(distance,wave,theta):
#  if (distance < 1.0):
#    distance = 1.0
#  theta_radians = float(theta) * dg2rd
#  theta_t = (theta_radians + atan(det_radius/float(distance)))/2
#  dmin_t = float(wave)/(2*(sin(theta_t)))
#  return dmin_t


#def distance_from_reso(reso,wave,theta):
#  theta_radians = float(theta) * dg2rd
#  dx = det_radius/(tan(2*(asin(float(wave)/(2*reso)))-theta_radians))
#  return dx

#def move_det_to_reso(reso):
#  new_distance = distance_from_reso(reso,12398.5/get_mono_energy(),0)
#  move_axis_absolute("dist",new_distance)
