import time
import string
import beamline_support
import os
from math import *

global message_string_pv

#global det_radius
#det_radius = 0


def init_environment():
  global beamline,detector_id,mono_mot_code,tablex_mot_code,tabley_mot_code,has_beamline,has_db,has_xtalview,xtal_url,xtal_bmp_url,xtal_url_small,xtalview_user,xtalview_pass,det_type,epics_type,ringfile,has_dna,beamstop_x_pvname,beamstop_y_pvname,camera_offset,det_radius,lowMagFOVx,lowMagFOVy,highMagFOVx,highMagFOVy,lowMagPixX,lowMagPixY,highMagPixX,highMagPixY,screenPixX,screenPixY,screenPixCenterX,screenPixCenterY,screenProtocol,screenPhist,screenPhiend,screenWidth,screenDist,screenExptime,screenWave,screenReso,gonioPvPrefix

#  var_list["state"] = "Idle"
  lowMagFOVx = 1739.0
  lowMagFOVy = 1370.0
  highMagFOVx = 1739.0 #digizoom will be this/2
  highMagFOVy = 1370.0
  lowMagPixX = 1292.0 #for automated images
  lowMagPixY = 964.0
  highMagPixX = 1292.0 #for automated images
  highMagPixY = 964.0
  screenPixX = 646.0
  screenPixY = 482.0
  screenPixCenterX = screenPixX/2.0
  screenPixCenterY = screenPixY/2.0
  gonioPvPrefix = "XF:AMXFMX{MC-Goni}"
  
  try:
    varname = "BEAMLINE_ID" 
    beamline = os.environ[varname]
    varname = "DETECTOR_ID" 
    detector_id = os.environ[varname]
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
    varname = "EPICS_TYPE" 
    epics_type = os.environ[varname]
    varname = "RINGFILE" 
    ringfile = os.environ[varname]
    varname = "DET_TYPE" 
    det_type = os.environ[varname]
    varname = "HAS_DNA"
    has_dna = int(os.environ[varname])
    varname = "HAS_BEAMLINE"
    has_beamline = int(os.environ[varname])
    varname = "HAS_XTALVIEW"
    has_xtalview = int(os.environ[varname])
    varname = "CAMERA_OFFSET"
    camera_offset = float(os.environ[varname])
    if (has_xtalview):
      varname = "XTAL_URL_SMALL"
      xtal_url_small = os.environ[varname]
      varname = "XTAL_URL"
      xtal_url = os.environ[varname]
      varname = "XTAL_BMP_URL"
      xtal_bmp_url = os.environ[varname]
      varname = "XTALVIEW_HAS_PASSWORD"
      xtalview_has_password = int(os.environ[varname])
      if (xtalview_has_password):
        varname = "XTALVIEW_USER"
        xtalview_user = os.environ[varname]
        varname = "XTALVIEW_PASS"
        xtalview_pass = os.environ[varname]
      else:
        xtalview_user = 'None'
        xtalview_pass = 'None'        
    varname = "HAS_DB"
    has_db = int(os.environ[varname])
    varname = "MONO_MOTOR_CODE"
    mono_mot_code = os.environ[varname]
    varname = "TABLEX_MOTOR_CODE"
    tablex_mot_code = os.environ[varname]
    varname = "TABLEY_MOTOR_CODE"
    tabley_mot_code = os.environ[varname]    
    varname = "SCREEN_DEFAULT_PROTOCOL"
    screenProtocol = os.environ[varname]    
    varname = "SCREEN_DEFAULT_PHIST"
    screenPhist = float(os.environ[varname])
    varname = "SCREEN_DEFAULT_PHI_END"
    screenPhiend = float(os.environ[varname])
    varname = "SCREEN_DEFAULT_WIDTH"
    screenWidth = float(os.environ[varname])
    varname = "SCREEN_DEFAULT_DIST"
    screenDist = float(os.environ[varname])
    varname = "SCREEN_DEFAULT_TIME"
    screenExptime = float(os.environ[varname])
    varname = "SCREEN_DEFAULT_RESO"
    screenReso = float(os.environ[varname])
    varname = "SCREEN_DEFAULT_WAVE"
    screenWave = float(os.environ[varname])
  except KeyError:
    print "No ENV VAR %s\n" % varname
  try:        
    varname = "BEAMSTOP_X_PVNAME"
    beamstop_x_pvname = os.environ[varname]
  except KeyError:
    pass
  try:        
    varname = "BEAMSTOP_Y_PVNAME"
    beamstop_y_pvname = os.environ[varname]
  except KeyError:
    pass



def broadcast_output(s):
  time.sleep(0.01)
  if (string.find(s,'|') == -1):
    print s
  beamline_support.pvPut(message_string_pv,s)


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
