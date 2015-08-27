import time
import string
#import beamline_support
import os
from math import *
import metadatastore.commands as mdsc
import db_lib
from db_lib import *

#global det_radius
#det_radius = 0
global beamline
beamline = "john"
global searchParams
searchParams = {"config_params.beamline_id":beamline}



def init_environment():
  global beamline,detector_id,mono_mot_code,has_beamline,has_xtalview,xtal_url,xtal_url_small,xtalview_user,xtalview_pass,det_type,has_dna,beamstop_x_pvname,beamstop_y_pvname,camera_offset,det_radius,lowMagFOVx,lowMagFOVy,highMagFOVx,highMagFOVy,lowMagPixX,lowMagPixY,highMagPixX,highMagPixY,screenPixX,screenPixY,screenPixCenterX,screenPixCenterY,screenProtocol,screenPhist,screenPhiend,screenWidth,screenDist,screenExptime,screenWave,screenReso,gonioPvPrefix,searchParams,screenEnergy,detectorOffline,imgsrv_host,imgsrv_port

#  var_list["state"] = "Idle"


  configIter= mdsc.find_beamline_configs(**searchParams)
  beamlineConfig = configIter.next()["config_params"]

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
  if os.environ.has_key(varname):
    has_xtalview = int(os.environ[varname])
  varname = "DETECTOR_OFFLINE"
  if os.environ.has_key(varname):
    detectorOffline = int(os.environ[varname])



#def broadcast_output(s):
#  time.sleep(0.01)
#  if (string.find(s,'|') == -1):
#    print s
#  beamline_support.pvPut(message_string_pv,s)

def setBeamlineConfigParams(paramDict):
  configIter= mdsc.find_beamline_configs(**searchParams)
  beamlineConfig = configIter.next()["config_params"]
  configIter= mdsc.find_beamline_configs(**searchParams)
  beamlineConfig = configIter.next()["config_params"]
  for paramName in paramDict.keys():
    beamlineConfig[paramName] = paramDict[paramName]
  mdsc.insert_beamline_config(beamlineConfig, time.time())

#def setBeamlineConfigParam(paramName,val):
#  configIter= mdsc.find_beamline_configs(**searchParams)
#  beamlineConfig = configIter.next()["config_params"]
#  beamlineConfig[paramName] = val
#  mdsc.insert_beamline_config(beamlineConfig, time.time())

def getBeamlineConfigParam(paramName):
  configIter= mdsc.find_beamline_configs(**searchParams)
  beamlineConfig = configIter.next()["config_params"]
  return beamlineConfig[paramName] 

def getAllBeamlineConfigParams():
  configIter= mdsc.find_beamline_configs(**searchParams)
  beamlineConfig = configIter.next()["config_params"]
#  for key in beamlineConfig.keys():
#     print key + " " + str(beamlineConfig[key])
  return beamlineConfig


def getCurrentFOVx(camera,zoom): #cam 0 = lowMag, 
  if (camera==0):
    return daq_utils.lowMagFOVx
  else:
    if (zoom==0):
      return daq_utils.highMagFOVx          
    else:
      return daq_utils.highMagFOVx/2          

def getCurrentFOVy(camera,zoom): #cam 0 = lowMag, 
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
    configIter= mdsc.find_beamline_configs(**searchParams)
    beamlineConfig = configIter.next()["config_params"]
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
    sampleName = str(getSampleNamebyID(sample_id))
    basePath = os.getcwd()
    request = {
               "sample_id": sample_id,
               "sweep_start": screenPhist,  "sweep_end": screenPhiend,
               "img_width": screenWidth,
               "exposure_time": screenExptime,
               "priority": 0,
               "protocol": "standard",
               "basePath": basePath,
               "file_prefix": sampleName,
               "directory": basePath+"/projID/"+sampleName+"/1/",
               "file_number_start": 1,
               "energy":screenEnergy,
               "wavelength": energy2wave(screenEnergy),
               "resolution": screenReso,
               "slit_height": screenbeamHeight,  "slit_width": screenbeamWidth,
               "attenuation": screenTransmissionPercent,
               "pos_x": 0,  "pos_y": 0,  "pos_z": 0,  "pos_type": 'A',
               "gridW": 0,  "gridH": 0,  "gridStep": 30}

    return request

def createResult(typeName,resultObj):
  result = {}
  result["type"] = typeName
  result["timestamp"] = time.time()
  result["resultObj"] = resultObj
  return result

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
