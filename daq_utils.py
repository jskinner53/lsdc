import time
import string
#import beamline_support
import os
from math import *
import metadatastore.commands as mdsc


#global det_radius
#det_radius = 0
global beamline
beamline = "john"
global searchParams
searchParams = {"config_params.beamline_id":beamline}

def init_environment():
  global beamline,detector_id,mono_mot_code,has_beamline,has_xtalview,xtal_url,xtal_url_small,xtalview_user,xtalview_pass,det_type,has_dna,beamstop_x_pvname,beamstop_y_pvname,camera_offset,det_radius,lowMagFOVx,lowMagFOVy,highMagFOVx,highMagFOVy,lowMagPixX,lowMagPixY,highMagPixX,highMagPixY,screenPixX,screenPixY,screenPixCenterX,screenPixCenterY,screenProtocol,screenPhist,screenPhiend,screenWidth,screenDist,screenExptime,screenWave,screenReso,gonioPvPrefix,searchParams,screenEnergy

#  var_list["state"] = "Idle"


  configIter= mdsc.find_beamline_configs(**searchParams)
  beamlineConfig = configIter.next()["config_params"]

  lowMagFOVx = beamlineConfig["lowMagFOVx"]
  lowMagFOVy = beamlineConfig["lowMagFOVy"]
  highMagFOVx = beamlineConfig["highMagFOVx"] #digizoom will be this/2
  highMagFOVy = beamlineConfig["highMagFOVy"]
  lowMagPixX = beamlineConfig["lowMagPixX"] #for automated images
  lowMagPixY = beamlineConfig["lowMagPixY"]
  highMagPixX = beamlineConfig["highMagPixX"] #for automated images
  highMagPixY = beamlineConfig["highMagPixY"]
  screenPixX = beamlineConfig["screenPixX"]
  screenPixY = beamlineConfig["screenPixY"]
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
  has_dna = beamlineConfig["has_edna"]
  has_beamline = beamlineConfig["has_beamline"]
  has_xtalview = beamlineConfig["has_xtalview"]
  camera_offset = beamlineConfig["camera_offset"]
  if (has_xtalview):
    xtal_url_small = beamlineConfig["xtal_url_small"]
    xtal_url = beamlineConfig["xtal_url"]
  mono_mot_code = beamlineConfig["mono_mot_code"]
  screenProtocol = beamlineConfig["screen_default_protocol"]
  screenPhist = beamlineConfig["screen_default_phist"]
  screenPhiend = beamlineConfig["screen_default_phi_end"]
  screenWidth = beamlineConfig["screen_default_width"]
  screenDist =  beamlineConfig["screen_default_dist"]
  screenExptime = beamlineConfig["screen_default_time"]
  screenReso = beamlineConfig["screen_default_reso"]
  screenWave = beamlineConfig["screen_default_wave"]
  screenEnergy = beamlineConfig["screen_default_energy"]
  screenbeamWidth = beamlineConfig["screen_default_beamWidth"]
  screenbeamHeight = beamlineConfig["screen_default_beamHeight"]
  screenTransmissionPercent = beamlineConfig["screen_transmission_percent"]
  beamstop_x_pvname = beamlineConfig["beamstop_x_pvname"]
  beamstop_y_pvname = beamlineConfig["beamstop_y_pvname"]

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

  dg2rd = 3.14159265 / 180.0
  theta_radians = float(theta) * dg2rd
#  det_radius = float(diameter)/2
  dx = det_radius/(tan(2*(asin(float(wave)/(2*reso)))-theta_radians))
  return float("%.2f" % dx)


def energy2wave(e):
  return float("%.2f" % (12.3985/e))

def wave2energy(w):
  return float("%.2f" % (12.3985/w))

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
