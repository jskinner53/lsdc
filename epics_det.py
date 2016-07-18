import os
import sys
import time
from string import *
#import EpicsCA
#from EpicsCA import PV
import beamline_support
from beamline_support import *

global det_pv_list
global channel_list
global det_type,det_id

det_type = ""
channel_list = {}
det_pv_list = {}

axis_list = ['omega','phi']

def read_db():
  global beamline_designation,motor_list
  
  try:
    dbfilename = os.environ["DET_PV_LIST"]
  except KeyError:
    print("det_pv_list not defined. Please set the environment variable det_pv_list to the name of the detector pv list file and try again.")
    sys.exit()
  if (os.path.exists(dbfilename) == 0):
    error_msg = "\ndet_pv_list: %s does not exist.\n Program exiting." % dbfilename
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
        det_pv_info = line.split()
        det_pv_list[det_pv_info[0]] = (beamline_designation + ':' + det_pv_info[1])
        i = i+1


def det_init_pvs():
  global channel_list

  for keyname in list(det_pv_list.keys()):
    channel_list[keyname] = pvCreate(det_pv_list[keyname])

#  EpicsCA.connect_all()

def det_set_autoinc_filenum(flag):
  set_det_pv('filenum_auto_increment',int(flag))


def det_set_file_template(image_type):
  if (image_type == "cbf"):
    template = "%s%s_%5.5d." + image_type
  else: #adsc img
    template = "%s/%s_%03d." + image_type    
  set_det_pv('data_file_template_val',template)


def det_channels_init():
  global offline,det_type,det_id
  try:
    varname = "DETECTOR_OFFLINE"
    offline = int(os.environ[varname])
    varname = "DET_TYPE" 
    det_type = os.environ[varname]
    varname = "DETECTOR_ID" 
    det_id = os.environ[varname]
    if (not offline):
      read_db()
      det_init_pvs()
      if (det_id == "PILATUS-6"):
        set_det_pv('det_trigger_mode',0)        #internal for devel
#        set_det_pv('det_trigger_mode',2)        
        det_set_autoinc_filenum(1) 
        det_set_file_template("cbf")
      elif (det_id == "EIGER-16"):
        pass #leave alone for now
      else:
        set_det_pv('det_trigger_mode',1)        
        set_det_pv('filenum_auto_inc_flag',0)
        det_set_file_template("img")        
  except KeyError:
    print("No ENV VAR %s\n" % varname)
      

def set_det_pv(pvcode,val):
#####  print offline
  if (offline):
    return
  pvPut(channel_list[pvcode],val)


#def set_det_pv_nowait(pvcode,val):
#  channel_list[pvcode].put(val)
#  EpicsCA.pend_event()    


def get_det_pv(pvcode):
  return_val =  pvGet(channel_list[pvcode])
  return return_val


def det_setheader(phist,phiinc,dist,wave,theta,exptime,xbeam,ybeam,rot_ax,omega,kappa,phi):

  #maybe phist not used, it picks it from axis
  set_det_pv("det_distance",dist)
  set_det_pv("x_beam",xbeam)
  set_det_pv("y_beam",ybeam)
  set_det_pv("img_width",phiinc)
  set_det_pv("start_angle",phist)  
  if (det_id=="PILATUS-6"):
    set_det_pv("wave",wave)
    set_det_pv("twotheta",theta)
    set_det_pv("kappa",kappa)
    set_det_pv("phi",phi)

#  if (det_type != "pixel_array"):
#    set_det_pv("exptime",exptime)  
#    set_det_pv("axis",rot_ax)
#    set_det_pv("omega",omega)    
#  else:

    
def det_set_fileprefix(prefix):
  if (det_id=="PILATUS-6"):
    set_det_pv("data_filename_val",prefix)
  elif (det_id=="EIGER-16"):
    set_det_pv("data_filename_val",prefix+"_$id")    

def det_set_filepath(filepath):
  set_det_pv("data_filepath_val",filepath)
#  set_det_pv("data_filepath_val",filepath+"\0")    
  
def det_set_filetemplate(filetemplate):
  set_det_pv("data_file_template_val",filetemplate)  

def det_set_filenum_auto_inc_flag(flag):
  set_det_pv("filenum_auto_inc_flag",flag)    

def det_set_filenum(filenum):
  set_det_pv("file_number",filenum)  

def det_set_numimages(numimages):
  set_det_pv("numimages",numimages)  

def det_set_numexposures(numexposures):
  if (det_type == "pixel_array"):
    set_det_pv("numexposures",numexposures)  

def det_take_image():
  set_det_pv("acquire",1)

def det_set_exptime(exptime): #exposure_time = exposure_period - .0024 for nsls1 pil6
  set_det_pv("exptime",exptime)

def det_set_image_period(period):
  set_det_pv("image_period",period)

def det_start():
  if (offline):
    return
  if (det_type == "pixel_array"):
    set_det_pv("start",1)
    return
  else:
    set_det_pv("acquire",1) #I don't know why everytime
#  print "IN START after acquire set"
  while (1):
    if (get_det_pv("det_state") == "Error"): #6=error
      os.system("killall -KILL tkmessage")
      os.system("tkmessage Detector error. Restart CBASS to recover.&")
      os.system("kill_detector")
      while (1):
        time.sleep(1.0)
    expose_ok = get_det_pv("expose_ok")
#    print "after get expose ok = " + str(expose_ok)
    if (expose_ok == "Yes"): #0=no,1=yes,2=error
      set_det_pv("det_control",1) #start
#      print "after start"          
      break
    elif (expose_ok == "Error"): #0=no,1=yes,2=error
      os.system("killall -KILL tkmessage")
      os.system("tkmessage Detector error. Restart CBASS to recover.&")
      os.system("kill_detector")
      while (1):
        time.sleep(1.0)
    else:
      time.sleep(0.05)
  
def det_wait():
  if (offline):
    return  
  if (det_type == "pixel_array"):
    time.sleep(0.5)      
    while (get_det_pv("det_state") != 0):
#      print(get_det_pv("det_state"))
#    while (get_det_pv("det_state") == "Acquire"):      
      time.sleep(.5)

def det_waitArmed(): #not even sure what this means.
  if (offline):
    return  
  if (det_type == "pixel_array"):
    print("armed = " + str(get_det_pv("armed_state")))
    time.sleep(0.5)      
    while (get_det_pv("armed_state") == 0):
#      print(get_det_pv("armed_state"))
      time.sleep(.01)
      
def det_stop():
  if (offline):
    return  
  if (det_type == "pixel_array"):
    set_det_pv("start",0)
    return
  set_det_pv("det_control",0) #stop
#  print "after stop"            
  while (1):
    if (get_det_pv("det_state") == "Error"): #6=error
      os.system("killall -KILL tkmessage")
      os.system("tkmessage Detector error. Restart CBASS to recover.&")
      os.system("kill_detector")
      while (1):
        time.sleep(1.0)
    stop_ok = get_det_pv("det_control_RBV")
#    print "after get control rbv"              
    if (stop_ok == "OK"): #0=stop,1=start,2=ok,3=again
      break
    elif (stop_ok == "Again"): #0=stop,1=start,2=ok,3=again
      os.system("killall -KILL tkmessage")
      os.system("tkmessage Detector error. Restart CBASS to recover.&")
      os.system("kill_detector")
      while (1):
        time.sleep(1.0)
    else:
      time.sleep(0.05)
  

def det_set_trigger_mode(mode): #0=internal, 1=external - cbass uses 1
  set_det_pv("det_trigger_mode",mode)

  
def det_set_bin(binval):
  set_det_pv("bin_x",binval)
  set_det_pv("bin_y",binval)  
