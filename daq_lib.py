import sys
import os
import time
import string
import math
import daq_macros
from math import *
#from string import *
from gon_lib import *
from det_lib import *
import robot_lib
import daq_utils
import beamline_lib
import beamline_support
import db_lib
import stateModule

var_list = {'beam_check_flag':0,'overwrite_check_flag':1,'omega':0.00,'kappa':0.00,'phi':0.00,'theta':0.00,'distance':10.00,'rot_dist0':300.0,'inc0':1.00,'exptime0':5.00,'file_prefix0':'lowercase','numstart0':0,'col_start0':0.00,'col_end0':1.00,'scan_axis':'omega','wavelength0':1.1,'datum_omega':0.00,'datum_kappa':0.00,'datum_phi':0.00,'size_mode':0,'spcgrp':1,'state':"Idle",'state_percent':0,'datafilename':'none','active_sweep':-1,'html_logging':1,'take_xtal_pics':0,'px_id':'none','xtal_id':'none','current_pinpos':0,'sweep_count':0,'group_name':'none','mono_energy_target':1.1,'mono_wave_target':1.1,'energy_inflection':12398.5,'energy_peak':12398.5,'wave_inflection':1.0,'wave_peak':1.0,'energy_fall':12398.5,'wave_fall':1.0,'beamline_merit':0,'fprime_peak':0.0,'f2prime_peak':0.0,'fprime_infl':0.0,'f2prime_infl':0.0,'program_state':"Program Ready",'filter':0,'edna_aimed_completeness':0.99,'edna_aimed_ISig':2.0,'edna_aimed_multiplicity':'auto','edna_aimed_resolution':'auto','mono_energy_current':1.1,'mono_energy_scan_step':1,'mono_wave_current':1.1,'mono_scan_points':21,'mounted_pin':int(db_lib.beamlineInfo('john', 'mountedSample')["sampleID"]),'pause_button_state':'Pause','grid_w':210,'grid_h':150,'grid_i':10,'grid_on':0,'vector_on':0,'vector_fpp':1,'vector_step':0.0,'vector_translation':0.0,'xia2_on':0,'grid_exptime':0.2,'grid_imwidth':0.2,'choochResultFlag':0,'xrecRasterFlag':0}


global x_vec_start, y_vec_start, z_vec_start, x_vec_end, y_vec_end, z_vec_end, x_vec, y_vec, z_vec
global var_channel_list
global message_string_pv
global gui_popup_message_string_pv
global data_directory_name
var_channel_list = {}


global abort_flag
abort_flag = 0

def init_var_channels():
  global var_channel_list

  for varname in list(var_list.keys()):
    var_channel_list[varname] = beamline_support.pvCreate(daq_utils.beamlineComm + varname)
    beamline_support.pvPut(var_channel_list[varname],var_list[varname])


def gui_message(message_string): 
  beamline_support.pvPut(gui_popup_message_string_pv,message_string)

def destroy_gui_message():
  beamline_support.pvPut(gui_popup_message_string_pv,"killMessage")


def monitored_sleep(sleep_time):   #this sleeps while checking for aborts every second, good for stills
  global abort_flag                #and allowing for aborts from beamdump recovery sleeps.
  
  now = time.time()
  start_time = now
  while ((now-start_time)<float(sleep_time)):
    time.sleep(1.0)
    now = time.time()
    if abort_flag:
      abort_flag = 0
      break

def set_field(param,val):
  var_list[param] = val
  beamline_support.pvPut(var_channel_list[param],val)


def get_field(param):
#  return pvGet(var_channel_list[param])
  return var_list[param]
    

def set_group_name(group_name):
  set_field("group_name",group_name)

def set_distance_value(distance):
  set_field("distance",atof(distance))
  
def set_xbeam(xbeam):
  daq_utils.setBeamlineConfigParams({"xbeam":float(xbeam)})
  daq_utils.xbeam = float(xbeam)  

def set_ybeam(ybeam):
  daq_utils.setBeamlineConfigParams({"ybeam":float(ybeam)})
  daq_utils.xbeam = float(ybeam)  

def set_beamcenter(xbeam,ybeam):
  set_xbeam(xbeam)
  set_ybeam(ybeam)

def set_space_group(spcgrp):
  set_field("spcgrp",spcgrp)


def beam_monitor_on():
  set_field("beam_check_flag",1)

def beam_monitor_off():
  set_field("beam_check_flag",0)

def overwrite_check_on():
  global allow_overwrite
  
  set_field("overwrite_check_flag",1)
  allow_overwrite = 0

def overwrite_check_off():
  global allow_overwrite  

  set_field("overwrite_check_flag",0)
  allow_overwrite = 1
  
def beam_check_on():
  return get_field("beam_check_flag")


def check_beam():
  return 1

def check_pause():
  global pause_flag

  while (pause_flag==1):
    time.sleep(1.0)

def pause_data_collection():
  global pause_flag

  pause_flag = 1
  set_field("pause_button_state","Continue")
  
def continue_data_collection():
  global pause_flag

  pause_flag = 0
  set_field("pause_button_state","Pause")  


def abort_data_collection():
  global datafile_name,abort_flag,image_started

#  logit("logfile.txt","message","User aborted")
#  if (daq_utils.has_beamline):  
  if (1):   #for now
    beamline_lib.bl_stop_motors() ##this already sets abort flag to 1
  abort_flag = 1
  gon_stop()
  detector_stop()
  close_shutter()


def open_shutter():
  lib_open_shutter()
  set_field("state","Expose")

def close_shutter():
  lib_close_shutter()
  set_field("state","Idle")
  
def open_shutter2():
  lib_open_shutter2()

def close_shutter2():
  lib_close_shutter2()
  
def init_diffractometer():
  lib_init_diffractometer()

def close_diffractometer():
  lib_close_diffractometer()

def home():
  lib_home()

def home_omega():
  lib_home_omega()


def px_id(id):
  set_field("px_id",id)
  if (pxdb_lib.is_mailin(id)):
    print("is mailin")
    if (archive_active == 1 and archive == ""):
      try:
        default_archive_location = os.environ["DEFAULT_ARCHIVE_LOCATION"]
        set_archive(default_archive_location)
      except KeyError:
        pass
  else:
    print("is not mailin")


def xtal_id(id):
  set_field("xtal_id",id)


def set_relative_zero(omega,kappa,phi):
  set_field("datum_omega",omega)
  set_field("datum_kappa",kappa)
  set_field("datum_phi",phi)

def relative_zero_to_cp():
  set_field("datum_omega",get_field("omega"))
  set_field("datum_kappa",get_field("kappa"))
  set_field("datum_phi",get_field("phi"))


def refreshGuiTree():
  beamline_support.set_any_epics_pv(daq_utils.beamlineComm+"live_q_change_flag","VAL",1)

def broadcast_output(s):
  time.sleep(0.01)
  if (s.find('|') == -1):
    print(s)
  beamline_support.pvPut(message_string_pv,s)


def runChooch():
  broadcast_output("running chooch")
  time.sleep(4)
  set_field("choochResultFlag",1)


def mountSample(sampID):
  mountedSampleDict = db_lib.beamlineInfo('john', 'mountedSample')
  currentMountedSampleID = mountedSampleDict["sampleID"]
  if (currentMountedSampleID != 99): #then unmount what's there
    if (sampID!=currentMountedSampleID):
      puckPos = mountedSampleDict["puckPos"]
      pinPos = mountedSampleDict["pinPos"]
      robot_lib.unmountRobotSample(puckPos,pinPos,currentMountedSampleID)
      set_field("mounted_pin",sampID)
      (puckPos,pinPos,puckID) = db_lib.getCoordsfromSampleID(sampID)
      robot_lib.mountRobotSample(puckPos,pinPos,sampID)
    else: #desired sample is mounted, nothing to do
      return 1
  else: #nothing mounted
    (puckPos,pinPos,puckID) = db_lib.getCoordsfromSampleID(sampID)
    robot_lib.mountRobotSample(puckPos,pinPos,sampID)
  db_lib.beamlineInfo('john', 'mountedSample', info_dict={'puckPos':puckPos,'pinPos':pinPos,'sampleID':sampID})



def unmountSample():
  mountedSampleDict = db_lib.beamlineInfo('john', 'mountedSample')
  currentMountedSampleID = mountedSampleDict["sampleID"]
  puckPos = mountedSampleDict["puckPos"]
  pinPos = mountedSampleDict["pinPos"]
  robot_lib.unmountRobotSample(puckPos,pinPos,currentMountedSampleID)
  set_field("mounted_pin",-99)
  db_lib.beamlineInfo('john', 'mountedSample', info_dict={'puckPos':0,'pinPos':0,'sampleID':-99})


def runDCQueue(): #maybe don't run rasters from here???
  global abort_flag

  print("running queue in daq server")
  while (1):
    if (abort_flag):
      abort_flag =  0 #careful about when to reset this
      return
    currentRequest = db_lib.popNextRequest()
    if (currentRequest == {}):
      break
    sampleID = currentRequest["sample_id"]
    if (get_field("mounted_pin") != sampleID):
      mountSample(sampleID)
    db_lib.updatePriority(currentRequest["request_id"],99999)
    refreshGuiTree() #just tells the GUI to repopulate the tree from the DB
    if (stateModule.gotoState("SampleAlignment")):
      colStatus = collectData(currentRequest)
    else:
      print("State violation DC")
      break


def stopDCQueue():
  print("stopping queue in daq server")
  abort_data_collection()

def logMxRequestParams(currentRequest):
  resultObj = {"requestObj":currentRequest["request_obj"]}
  db_lib.addResultforRequest("mxExpParams",currentRequest["request_id"],resultObj)  
  db_lib.beamlineInfo('john', 'currentSampleID', info_dict={'sampleID':currentRequest["sample_id"]})
  db_lib.beamlineInfo('john', 'currentRequestID', info_dict={'requestID':currentRequest["request_id"]})

def collectData(currentRequest):
  global data_directory_name

  logMxRequestParams(currentRequest)
  reqObj = currentRequest["request_obj"]
  data_directory_name = str(reqObj["directory"])
  if not (os.path.isdir(data_directory_name)):
    comm_s = "mkdir -p " + data_directory_name
    os.system(comm_s)
  print(reqObj["protocol"])
  prot = str(reqObj["protocol"])
  if (prot == "raster"):
    daq_macros.snakeRaster(currentRequest["request_id"])
  elif (prot == "vector"):
    daq_macros.vectorScan(currentRequest)
  elif (prot == "multiCol"):
    daq_macros.multiCol(currentRequest)
  else: #standard, screening, or edna - these may require autoalign, checking first
    if (reqObj["pos_x"] != 0):
      beamline_lib.mvaDescriptor("sampleX",reqObj["pos_x"])
      beamline_lib.mvaDescriptor("sampleY",reqObj["pos_y"])
      beamline_lib.mvaDescriptor("sampleZ",reqObj["pos_z"])
    else:
      print("autoRaster")
      daq_macros.autoRasterLoop(currentRequest)    
    exposure_period = reqObj["exposure_time"]
    wavelength = reqObj["wavelength"]
    resolution = reqObj["resolution"]
    slit_height = reqObj["slit_height"]
    slit_width = reqObj["slit_width"]
    attenuation = reqObj["attenuation"]
    img_width = reqObj["img_width"]
    file_prefix = str(reqObj["file_prefix"])
    if (not stateModule.gotoState("DataCollection")):
      print("State violation")
      return
    if (reqObj["protocol"] == "screen"):
      screenImages = 2
      screenRange = 90
      range_degrees = img_width
      for i in range (0,screenImages):
        sweep_start = reqObj["sweep_start"]+(i*screenRange)
        sweep_end = reqObj["sweep_end"]+(i*screenRange)
        file_prefix = str(reqObj["file_prefix"]+"_"+str(i*screenRange))
        data_directory_name = str(reqObj["directory"]) # for now
        file_number_start = reqObj["file_number_start"]
        beamline_lib.mvaDescriptor("omega",sweep_start)
        imagesAttempted = collect_detector_seq(range_degrees,img_width,exposure_period,file_prefix,data_directory_name,file_number_start)
    elif (reqObj["protocol"] == "characterize" or reqObj["protocol"] == "ednaCol"):
      characterizationParams = reqObj["characterizationParams"]
      index_success = daq_macros.dna_execute_collection3(0.0,img_width,2,exposure_period,data_directory_name+"/",file_prefix,1,-89.0,1,currentRequest)
      if (index_success):
        resultsList = db_lib.getResultsforRequest(currentRequest["request_id"]) # because for testing I keep running the same request. Probably not in usual use.
        results = resultsList[len(resultsList)-1]
        strategyResults = results["result_obj"]["strategy"]
        stratStart = strategyResults["start"]
        stratEnd = strategyResults["end"]
        stratWidth = strategyResults["width"]
        stratExptime = strategyResults["exptime"]
        stratDetDist = strategyResults["detDist"]
        sampleID = currentRequest["sample_id"]
        tempnewStratRequest = daq_utils.createDefaultRequest(sampleID)
        newReqObj = tempnewStratRequest["request_obj"]
        newReqObj["sweep_start"] = stratStart
        newReqObj["sweep_end"] = stratEnd
        newReqObj["img_width"] = stratWidth
        newReqObj["exposure_time"] = stratExptime
        newReqObj["detDist"] = stratDetDist
        newReqObj["directory"] = data_directory_name
        newReqObj["pos_x"] = beamline_lib.motorPosFromDescriptor("sampleX")
        newReqObj["pos_y"] = beamline_lib.motorPosFromDescriptor("sampleY")
        newReqObj["pos_z"] = beamline_lib.motorPosFromDescriptor("sampleZ")
        newReqObj["fastDP"] = reqObj["fastDP"] # this is where you might want a "new from old" request to carry over stuff like this.
        newReqObj["fastEP"] = reqObj["fastEP"]
        newReqObj["xia2"] = reqObj["xia2"]
        runNum = db_lib.incrementSampleRequestCount(sampleID)
        reqObj["runNum"] = runNum
        newStratRequest = db_lib.addRequesttoSample(sampleID,newReqObj["protocol"],newReqObj,priority=0)
        if (reqObj["protocol"] == "ednaCol"):
          db_lib.updatePriority(currentRequest["request_id"],-1)
          refreshGuiTree()
          collectData(newStratRequest)
          return

    else: #standard
      sweep_start = reqObj["sweep_start"]
      sweep_end = reqObj["sweep_end"]
      file_prefix = str(reqObj["file_prefix"])
      file_number_start = reqObj["file_number_start"]
      range_degrees = abs(sweep_end-sweep_start)
      beamline_lib.mvaDescriptor("omega",sweep_start)
      imagesAttempted = collect_detector_seq(range_degrees,img_width,exposure_period,file_prefix,data_directory_name,file_number_start)
      if (reqObj["fastDP"]):
        if (reqObj["fastEP"]):
          fastEPFlag = 1
        else:
          fastEPFlag = 0
        comm_s = os.environ["CBHOME"] + "/runFastDP.py " + data_directory_name + " " + file_prefix + " " + str(file_number_start) + " " + str(int(round(range_degrees/img_width))) + " " + str(currentRequest["request_id"]) + " " + str(fastEPFlag) + "&"
        print(comm_s)
        os.system(comm_s)
      if (reqObj["xia2"]):
        comm_s = os.environ["CBHOME"] + "/runXia2.py " + data_directory_name + " " + file_prefix + " " + str(file_number_start) + " " + str(int(round(range_degrees/img_width))) + " " + str(currentRequest["request_id"]) + "&"
        os.system(comm_s)
  
  db_lib.updatePriority(currentRequest["request_id"],-1)
  refreshGuiTree()

    

def collect_detector_seq(range_degrees,image_width,exposure_period,fileprefix,data_directory_name,file_number,z_target=0): #works for pilatus
  global image_started,allow_overwrite,abort_flag


  print("data directory = " + data_directory_name)
  test_filename = "%s_%05d.cbf" % (fileprefix,int(file_number))
#  if (os.path.exists(test_filename) and allow_overwrite == 0):
#    gui_message("You are about to overwrite " + test_filename + " If this is OK, push Continue, else Abort.&")
#    pause_data_collection()
#    check_pause()
#    time.sleep(1.0)
#    destroy_gui_message()
#    if (abort_flag):
#      print "collect sequence aborted"
#      return 0
#    else:
#      allow_overwrite = 1
  number_of_images = round(range_degrees/image_width)
  range_seconds = number_of_images*exposure_period
  exposure_time = exposure_period - .0024
  file_prefix_minus_directory = str(fileprefix)
  try:
    file_prefix_minus_directory = file_prefix_minus_directory[file_prefix_minus_directory.rindex("/")+1:len(file_prefix_minus_directory)]
  except ValueError: 
    pass
  print("collect pilatus %f degrees for %f seconds %d images exposure_period = %f exposure_time = %f" % (range_degrees,range_seconds,number_of_images,exposure_period,exposure_time))
  detector_set_period(exposure_period)
  detector_set_exposure_time(exposure_time)
  detector_set_numimages(number_of_images)
  detector_set_filepath(data_directory_name)
  detector_set_fileprefix(file_prefix_minus_directory)
  detector_set_filenumber(file_number)
  detector_set_fileheader(get_field(get_field("scan_axis")),get_field("inc0"),get_field("distance"),12398.5/beamline_lib.get_mono_energy(),get_field("theta"),get_field("exptime0"),daq_utils.xbeam,daq_utils.ybeam,get_field("scan_axis"),get_field("omega"),get_field("kappa"),get_field("phi"))
  print("collect pilatus %f degrees for %f seconds %d images exposure_period = %f exposure_time = %f" % (range_degrees,range_seconds,number_of_images,exposure_period,exposure_time))
  detector_start()
  image_started = range_seconds
  time.sleep(1.0) #4/15 - why so long?
#  time.sleep(0.3)  
  set_field("state","Expose")
##########  set_epics_pv_nowait("xtz","VAL",z_target)   #this is for grid!!!!!!!!
  gon_osc(get_field("scan_axis"),0.0,range_degrees,range_seconds) #0.0 is the angle start that's not used
  image_started = 0        
  set_field("state","Idle")        
###  detector_wait()
  daq_macros.fakeDC(data_directory_name,file_prefix_minus_directory,int(file_number),int(number_of_images))  
  return number_of_images



def center_on_click(x,y,maglevel=0,source="screen",jog=0): #maglevel=0 means lowmag, high fov, #1 = himag with digizoom option, 
  #source=screen = from screen click, otherwise from macro with full pixel dimensions
  if (source == "screen"):
    beamline_support.setPvValFromDescriptor("image_X_scalePix",daq_utils.screenPixX) #these are video dimensions in the gui
    beamline_support.setPvValFromDescriptor("image_Y_scalePix",daq_utils.screenPixY)
    beamline_support.setPvValFromDescriptor("image_X_centerPix",daq_utils.screenPixX/2)
    beamline_support.setPvValFromDescriptor("image_Y_centerPix",daq_utils.screenPixY/2)    
  else:
    if (int(maglevel)==0):
      beamline_support.setPvValFromDescriptor("image_X_scalePix",daq_utils.lowMagPixX)
      beamline_support.setPvValFromDescriptor("image_Y_scalePix",daq_utils.lowMagPixY)
      beamline_support.setPvValFromDescriptor("image_X_centerPix",daq_utils.lowMagPixX/2)
      beamline_support.setPvValFromDescriptor("image_Y_centerPix",daq_utils.lowMagPixY/2)
    else:
      beamline_support.setPvValFromDescriptor("image_X_scalePix",daq_utils.highMagPixX)
      beamline_support.setPvValFromDescriptor("image_Y_scalePix",daq_utils.highMagPixY)
      beamline_support.setPvValFromDescriptor("image_X_centerPix",daq_utils.highMagPixX/2)
      beamline_support.setPvValFromDescriptor("image_Y_centerPix",daq_utils.highMagPixY/2)

  if (int(maglevel)==0):
    beamline_support.setPvValFromDescriptor("image_X_scaleMM",daq_utils.lowMagFOVx)
    beamline_support.setPvValFromDescriptor("image_Y_scaleMM",daq_utils.lowMagFOVy)
  else:
    if (1):
#    if (beamline_support.get_any_epics_pv("XF:17IDC-ES:FMX{Cam:07}MJPGZOOM:NDArrayPort","VAL") == "ROI2"):      
      beamline_support.setPvValFromDescriptor("image_X_scaleMM",daq_utils.highMagFOVx)
      beamline_support.setPvValFromDescriptor("image_Y_scaleMM",daq_utils.highMagFOVy)
    else:
      beamline_support.setPvValFromDescriptor("image_X_scaleMM",daq_utils.highMagFOVx/2.0)
      beamline_support.setPvValFromDescriptor("image_Y_scaleMM",daq_utils.highMagFOVy/2.0)
#  omega_mod = beamline_lib.get_epics_motor_pos(beamline_support.pvNameSuffix_from_descriptor("omega"))%360.0
  omega_mod = beamline_lib.motorPosFromDescriptor("omega")%360.0
#  omega_mod = beamline_lib.get_epics_motor_pos("Omega")%360.0  
#  daq_utils.broadcast_output("\ncenter on x = %s, y = %s, omega = %f, phi = %f\n" % (x,y,omega_mod,0))
  lib_gon_center_xtal(x,y,omega_mod,0)
  if (jog):
    beamline_lib.mvrDescriptor("omega",float(jog))



def set_vector_startObsolete():
  global x_vec_start, y_vec_start, z_vec_start
  x_vec_start = beamline_lib.get_epics_motor_pos("X")
  y_vec_start = beamline_lib.get_epics_motor_pos("Y")
  z_vec_start = beamline_lib.get_epics_motor_pos("Z")

def set_vector_endObsolete():
  global x_vec_end, y_vec_end, z_vec_end, x_vec, y_vec, z_vec, x_vec_start, y_vec_start, z_vec_start
  x_vec_end = beamline_lib.get_epics_motor_pos("X")
  y_vec_end = beamline_lib.get_epics_motor_pos("Y")
  z_vec_end = beamline_lib.get_epics_motor_pos("Z")
  x_vec = x_vec_end - x_vec_start
  y_vec = y_vec_end - y_vec_start
  z_vec = z_vec_end - z_vec_start
  trans_total = sqrt(x_vec**2 + y_vec**2 + z_vec**2)
  set_field("vector_translation",trans_total)  
  print("translation total =  " + str(trans_total))

  
def set_vector_fppObsolete(fpp,numframes): #not used 7/22/15
  global x_vec, y_vec, z_vec

  set_field("vector_fpp",int(fpp))
  trans_total = 1000.0* sqrt(x_vec**2 + y_vec**2 + z_vec**2)
#  print "translation total =  " + str(trans_total)
  vec_step_microns = trans_total/(float(numframes)/float(fpp))
  print("trans step in microns = " + str(vec_step_microns))
  set_field("vector_step",vec_step_microns)


def vector_moveOBSOLETE(t_s,vecRequest): #I think t_s is a fraction of the total vector, so "1" would do the whole thing
  global x_vec_end, y_vec_end, z_vec_end, x_vec, y_vec, z_vec, x_vec_start, y_vec_start, z_vec_start

#  print "vec t = " + str(t_s)
  t = float(t_s)
  reqObj = vecRequest["request_obj"]
  trans_total = reqObj["vectorParams"]["trans_total"]
  trans_done = trans_total*t
  percent_done = t*100.0
  vec_s = "translation total = %f, translation done = %f, translation percent done = %f\n" % (trans_total,trans_done,percent_done)
  print(vec_s)
#  daq_utils.broadcast_output(vec_s)
  x_vec_start=reqObj["vectorParams"]["vecStart"]["x"]
  y_vec_start=reqObj["vectorParams"]["vecStart"]["y"]
  z_vec_start=reqObj["vectorParams"]["vecStart"]["z"]
  x_vec = reqObj["vectorParams"]["x_vec"]
  y_vec = reqObj["vectorParams"]["y_vec"]
  z_vec = reqObj["vectorParams"]["z_vec"]
  new_x = x_vec_start + (x_vec*t)
  new_y = y_vec_start + (y_vec*t)
  new_z = z_vec_start + (z_vec*t)
  beamline_lib.mvaDescriptor("sampleX",new_x,"sampleY",new_y,"sampleZ",new_z)
#  mva("Y",new_y)
#  mva("Z",new_z)


