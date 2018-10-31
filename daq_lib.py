import sys
import os
import grp
import getpass
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
import ispybLib

var_list = {'beam_check_flag':0,'overwrite_check_flag':1,'omega':0.00,'kappa':0.00,'phi':0.00,'theta':0.00,'distance':10.00,'rot_dist0':300.0,'inc0':1.00,'exptime0':5.00,'file_prefix0':'lowercase','numstart0':0,'col_start0':0.00,'col_end0':1.00,'scan_axis':'omega','wavelength0':1.1,'datum_omega':0.00,'datum_kappa':0.00,'datum_phi':0.00,'size_mode':0,'spcgrp':1,'state':"Idle",'state_percent':0,'datafilename':'none','active_sweep':-1,'html_logging':1,'take_xtal_pics':0,'px_id':'none','xtal_id':'none','current_pinpos':0,'sweep_count':0,'group_name':'none','mono_energy_target':1.1,'mono_wave_target':1.1,'energy_inflection':12398.5,'energy_peak':12398.5,'wave_inflection':1.0,'wave_peak':1.0,'energy_fall':12398.5,'wave_fall':1.0,'beamline_merit':0,'fprime_peak':0.0,'f2prime_peak':0.0,'fprime_infl':0.0,'f2prime_infl':0.0,'program_state':"Program Ready",'filter':0,'edna_aimed_completeness':0.99,'edna_aimed_ISig':2.0,'edna_aimed_multiplicity':'auto','edna_aimed_resolution':'auto','mono_energy_current':1.1,'mono_energy_scan_step':1,'mono_wave_current':1.1,'mono_scan_points':21,'mounted_pin':(db_lib.beamlineInfo(daq_utils.beamline, 'mountedSample')["sampleID"]),'pause_button_state':'Pause','vector_on':0,'vector_fpp':1,'vector_step':0.0,'vector_translation':0.0,'xia2_on':0,'grid_exptime':0.2,'grid_imwidth':0.2,'choochResultFlag':"0",'xrecRasterFlag':"0"}


global x_vec_start, y_vec_start, z_vec_start, x_vec_end, y_vec_end, z_vec_end, x_vec, y_vec, z_vec
global var_channel_list
global message_string_pv
global gui_popup_message_string_pv
global data_directory_name
global currentIspybDCID

global fastDPNodeCount
fastDPNodeCount = 4
global fastDPNodeCounter
fastDPNodeCounter = 0



global mountCounter
mountCounter = 0

var_channel_list = {}


global abort_flag
abort_flag = 0

def init_var_channels():
  global var_channel_list

  for varname in list(var_list.keys()):
#    print(varname)
    var_channel_list[varname] = beamline_support.pvCreate(daq_utils.beamlineComm + varname)
    beamline_support.pvPut(var_channel_list[varname],var_list[varname])


def gui_message(message_string): 
  beamline_support.pvPut(gui_popup_message_string_pv,message_string)

def destroy_gui_message():
  beamline_support.pvPut(gui_popup_message_string_pv,"killMessage")


def monitored_sleepObsolete(sleep_time):   #this sleeps while checking for aborts every second, good for stills
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
  
def set_xbeam(xbeam): #detector center for image header, in pixels
  beamline_support.setPvValFromDescriptor("beamCenterX",float(xbeam))

def set_ybeam(ybeam):
  beamline_support.setPvValFromDescriptor("beamCenterY",float(ybeam))  


def set_beamcenter(xbeam,ybeam): #detector center for image header, in pixels
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


def abort_data_collection(flag):
  global datafile_name,abort_flag,image_started

  if (flag==2): #stop queue after current collection
    abort_flag = 2
    return
#  logit("logfile.txt","message","User aborted")
#  if (daq_utils.has_beamline):  
  if (0):   #for now, just try to stop zebra and detector
    beamline_lib.bl_stop_motors() ##this already sets abort flag to 1
  gui_message("Aborting. This may take a minute or more.")  
  while not (beamline_support.getPvValFromDescriptor("VectorActive")): #only stop if actually collecting
    time.sleep(0.1)
  destroy_gui_message()    
  abort_flag = 1
  time.sleep(1.0)
  gon_stop() #this calls osc abort
#  daq_macros.zebraDaqPrep()
  beamline_support.setPvValFromDescriptor("zebraDisarm",1)
  time.sleep(2)
  detector_stop()
####  daq_macros.abortBS() #one less thing to hang
#  close_shutter() #was hanging on a shutter problem, and Bruno should handle this.


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


def runChoochObsolete():
  broadcast_output("running chooch")
  time.sleep(4)
  set_field("choochResultFlag",1)

def getRobotConfigNoStringObsolete():
  
  if (beamline_support.getPvValFromDescriptor("robotGovConfig") == 1):
    return "Robot"
  else:
    return "Human"

def getRobotConfig():
  return beamline_support.getPvValFromDescriptor("robotGovConfig",as_string=True)


def setRobotGovState(stateString):
  if (getRobotConfig() == "Robot"):
    beamline_support.setPvValFromDescriptor("robotGovGo",stateString)
  else:
    beamline_support.setPvValFromDescriptor("humanGovGo",stateString)

def toggleLowMagCameraSettings(stateCode):

  if (stateCode == "DA"):
    lowMagExpTime = db_lib.getBeamlineConfigParam(daq_utils.beamline,"lowMagExptimeDA")    
    beamline_support.setPvValFromDescriptor("lowMagGain",25)
    beamline_support.setPvValFromDescriptor("lowMagAcquireTime",lowMagExpTime)
  else:
    lowMagExpTime = db_lib.getBeamlineConfigParam(daq_utils.beamline,"lowMagExptime")    
    beamline_support.setPvValFromDescriptor("lowMagGain",1)                        
    beamline_support.setPvValFromDescriptor("lowMagAcquireTime",lowMagExpTime)                    

    

def waitGovRobotSE():
  waitGovNoSleep()    
  robotGovState = (beamline_support.getPvValFromDescriptor("robotSeActive") or beamline_support.getPvValFromDescriptor("humanSeActive"))
  print("robot gov state = " + str(robotGovState))
  if (robotGovState != 0):
    toggleLowMagCameraSettings("SE")
    return 1
  else:
    print("Governor did not reach SE")
    gui_message("Governor did not reach SE.")    
    return 0

def setGovRobotSE():
  setRobotGovState("SE")
  waitGov()    
  robotGovState = (beamline_support.getPvValFromDescriptor("robotSeActive") or beamline_support.getPvValFromDescriptor("humanSeActive"))
  print("robot gov state = " + str(robotGovState))
  if (robotGovState != 0):
    return 1
  else:
    print("Governor did not reach SE")
    gui_message("Governor did not reach SE.")        
    return 0

def setGovRobotXF():
  setRobotGovState("XF")
  waitGov()    
  robotGovState = (beamline_support.getPvValFromDescriptor("robotXfActive") or beamline_support.getPvValFromDescriptor("humanXfActive"))
  print("robot gov state = " + str(robotGovState))
  if (robotGovState != 0):
    return 1
  else:
    print("Governor did not reach XF")
    gui_message("Governor did not reach XF.")        
    return 0

def govBusy():
  return (beamline_support.getPvValFromDescriptor("robotGovStatus") == 1 or beamline_support.getPvValFromDescriptor("humanGovStatus") == 1)

def setGovRobotSA():
  print("setGovRobotSA")  
  setRobotGovState("SA")
  waitGov()  
  robotGovState = (beamline_support.getPvValFromDescriptor("robotSaActive") or beamline_support.getPvValFromDescriptor("humanSaActive"))
  print("robot gov state = " + str(robotGovState))
  if (robotGovState != 0):
    toggleLowMagCameraSettings("SA")    
    return 1
  else:
    print("Governor did not reach SA")
    gui_message("Governor did not reach SA.")        
    return 0

def setGovRobotDA():
  setRobotGovState("DA")
  waitGov()
  robotGovState = (beamline_support.getPvValFromDescriptor("robotDaActive") or beamline_support.getPvValFromDescriptor("humanDaActive"))
  print("robot gov state = " + str(robotGovState))
  if (robotGovState != 0):
    toggleLowMagCameraSettings("DA")    
    return 1
  else:
    print("Governor did not reach DA")
    gui_message("Governor did not reach DA.")        
    return 0
  
def waitGov():
  govTimeout = 120  
  startTime = time.time()
  time.sleep(1.5)  
  while (1):
    robotGovStatus = govBusy()
    print("robot gov status = " + str(robotGovStatus))    
    if (robotGovStatus != 1): #enum 1 = busy
      break
    if (time.time()-startTime > govTimeout):
      print("Governor Timeout!")
      gui_message("Governor Timeout!")          
      return 0
    time.sleep(0.1)        
  time.sleep(1.0)    

def waitGovNoSleep():
  govTimeout = 120  
  startTime = time.time()
  while (1):
    time.sleep(.05)
    robotGovStatus = govBusy()
    print("robot gov status = " + str(robotGovStatus))    
    if (robotGovStatus != 1): #enum 1 = busy
      break
    if (time.time()-startTime > govTimeout):
      print("Governor Timeout!")
      gui_message("Governor Timeout!")                
      return 0
  
  
def mountSample(sampID):
  global mountCounter

  warmUpNeeded = 0
  if (db_lib.getBeamlineConfigParam(daq_utils.beamline,"queueCollect") == 1):
    mountCounter+=1
    if (mountCounter > db_lib.getBeamlineConfigParam(daq_utils.beamline,"robotWarmupInterval")):
      warmUpNeeded = 1
  mountedSampleDict = db_lib.beamlineInfo(daq_utils.beamline, 'mountedSample')
  currentMountedSampleID = mountedSampleDict["sampleID"]
  if (currentMountedSampleID != ""): #then unmount what's there
    if (sampID!=currentMountedSampleID):
      puckPos = mountedSampleDict["puckPos"]
      pinPos = mountedSampleDict["pinPos"]
      if (robot_lib.unmountRobotSample(puckPos,pinPos,currentMountedSampleID)):
        db_lib.deleteCompletedRequestsforSample(currentMountedSampleID)
        set_field("mounted_pin","")        
        db_lib.beamlineInfo(daq_utils.beamline, 'mountedSample', info_dict={'puckPos':0,'pinPos':0,'sampleID':""})        
        (puckPos,pinPos,puckID) = db_lib.getCoordsfromSampleID(daq_utils.beamline,sampID)
        if (warmUpNeeded):
          gui_message("Warming gripper. Please stand by.")
          mountCounter = 0
        mountStat = robot_lib.mountRobotSample(puckPos,pinPos,sampID,init=0,warmup=warmUpNeeded)
        if (warmUpNeeded):
          destroy_gui_message()
        if (mountStat == 1):
          set_field("mounted_pin",sampID)
        elif(mountStat == 2):
          return 2
        else:
          return 0
      else:
        return 0
    else: #desired sample is mounted, nothing to do
      return 1
  else: #nothing mounted
    (puckPos,pinPos,puckID) = db_lib.getCoordsfromSampleID(daq_utils.beamline,sampID)
    mountStat = robot_lib.mountRobotSample(puckPos,pinPos,sampID,init=1)
    if (mountStat == 1):
      set_field("mounted_pin",sampID)
    elif(mountStat == 2):
      return 2
    else:
      return 0
  db_lib.beamlineInfo(daq_utils.beamline, 'mountedSample', info_dict={'puckPos':puckPos,'pinPos':pinPos,'sampleID':sampID})
  return 1


def clearMountedSample():
  set_field("mounted_pin","")
  db_lib.beamlineInfo(daq_utils.beamline, 'mountedSample', info_dict={'puckPos':0,'pinPos':0,'sampleID':""})
  

def unmountSample():
  global mountCounter

  mountCounter = 0
  mountedSampleDict = db_lib.beamlineInfo(daq_utils.beamline, 'mountedSample')
  currentMountedSampleID = mountedSampleDict["sampleID"]
  if (currentMountedSampleID != ""):
    puckPos = mountedSampleDict["puckPos"]
    pinPos = mountedSampleDict["pinPos"]
    if (robot_lib.unmountRobotSample(puckPos,pinPos,currentMountedSampleID)):
      db_lib.deleteCompletedRequestsforSample(currentMountedSampleID)      
      robot_lib.finish()
      set_field("mounted_pin","")
      db_lib.beamlineInfo(daq_utils.beamline, 'mountedSample', info_dict={'puckPos':0,'pinPos':0,'sampleID':""})
      return 1
    else:
      return 0

def unmountCold():
  mountedSampleDict = db_lib.beamlineInfo(daq_utils.beamline, 'mountedSample')
  currentMountedSampleID = mountedSampleDict["sampleID"]
  if (currentMountedSampleID != ""):
    puckPos = mountedSampleDict["puckPos"]
    pinPos = mountedSampleDict["pinPos"]
    if (robot_lib.unmountRobotSample(puckPos,pinPos,currentMountedSampleID)):
      db_lib.deleteCompletedRequestsforSample(currentMountedSampleID)      
#      robot_lib.finish()
      robot_lib.parkGripper()
      set_field("mounted_pin","")
      db_lib.beamlineInfo(daq_utils.beamline, 'mountedSample', info_dict={'puckPos':0,'pinPos':0,'sampleID':""})
      beamline_support.setPvValFromDescriptor("robotGovActive",1)
      return 1
    else:
      return 0

    

def runDCQueue(): #maybe don't run rasters from here???
  global abort_flag

  autoMounted = 0 #this means the mount was performed from a runQueue, as opposed to a manual mount button push
  print("running queue in daq server")
  while (1):
    if (abort_flag):
      abort_flag =  0 #careful about when to reset this
      return
    currentRequest = db_lib.popNextRequest(daq_utils.beamline)
    if (currentRequest == {}):
      break
    if (1):
      reqObj = currentRequest["request_obj"]
      beamline_support.setPvValFromDescriptor("govRobotDetDist",reqObj["detDist"])
      beamline_support.setPvValFromDescriptor("govHumanDetDist",reqObj["detDist"])
      if (reqObj["detDist"] > 200.0):
        beamline_support.setPvValFromDescriptor("govRobotDetDistOut",reqObj["detDist"])
        beamline_support.setPvValFromDescriptor("govHumanDetDistOut",reqObj["detDist"])          
    sampleID = currentRequest["sample"]
    if (get_field("mounted_pin") != sampleID):
      mountStat = mountSample(sampleID)
      if (mountStat == 1):
        autoMounted = 1
      elif(mountStat == 2):
        db_lib.updatePriority(currentRequest["uid"],-1)
        refreshGuiTree()        
        continue
      else:
## do this???        db_lib.updatePriority(currentRequest["uid"],99999)        
        return 0
    db_lib.updatePriority(currentRequest["uid"],99999)
    refreshGuiTree() #just tells the GUI to repopulate the tree from the DB
    colStatus = collectData(currentRequest)
    if (autoMounted and db_lib.queueDone(daq_utils.beamline)):
      unmountSample()

    

def stopDCQueue(flag):
  print("stopping queue in daq server " + str(flag))
  abort_data_collection(int(flag))



def logMxRequestParams(currentRequest):
  global currentIspybDCID
  reqObj = currentRequest["request_obj"]
  transmissionReadback = beamline_support.getPvValFromDescriptor("transmissionRBV")
  flux = beamline_support.getPvValFromDescriptor("flux")
  resultObj = {"requestObj":reqObj,"transmissionReadback":transmissionReadback,"flux":flux}  
  resultID = db_lib.addResultforRequest("mxExpParams",currentRequest["uid"],owner=daq_utils.owner,result_obj=resultObj,proposalID=daq_utils.getProposalID(),beamline=daq_utils.beamline)
  newResult = db_lib.getResult(resultID)
  db_lib.beamlineInfo(daq_utils.beamline, 'currentSampleID', info_dict={'sampleID':currentRequest["sample"]})
  db_lib.beamlineInfo(daq_utils.beamline, 'currentRequestID', info_dict={'requestID':currentRequest["uid"]})
  logfile = open("dataColLog.txt","a+")
  try:
    logfile.write("\n\ntimestamp: " + time.ctime(currentRequest["time"])+"\n")
  except KeyError:    
    print("caught key error in logging")
    print(currentRequest)
  logfile.write("protocol: " + reqObj["protocol"] +"\n")  
  logfile.write("data prefix: " + reqObj["file_prefix"] +"\n")
  logfile.write("flux: " + str(flux) +"\n")
  logfile.write("transimission percent: " + str(transmissionReadback) +"\n")
  logfile.write("total current (BCU): " + str(beamline_support.getPvValFromDescriptor("totalCurrentBCU")) +"\n")    
  logfile.write("omega start: " + str(reqObj["sweep_start"]) +"\n")
  logfile.write("omega end: " + str(reqObj["sweep_end"]) +"\n")
  logfile.write("image width: " + str(reqObj["img_width"]) +"\n")
  logfile.write("exposure time per image (s): " + str(reqObj["exposure_time"]) +"\n")
  logfile.write("detector distance: " + str(reqObj["detDist"]) +"\n")
  logfile.write("wavelength: " + str(reqObj["wavelength"]) +"\n")
  logfile.close()
  visitName = daq_utils.getVisitName()
  try: #I'm worried about unforseen ispyb db errors
    currentIspybDCID = ispybLib.insertResult(newResult,"mxExpParams",currentRequest,visitName)
  except:
    currentIspybDCID = 999999
    print("ispyb error")



def collectData(currentRequest):
  global data_directory_name,currentIspybDCID,fastDPNodeCount,fastDPNodeCounter

#  print(currentRequest)
#  print("pretending to collect")
#  time.sleep(5)
#  db_lib.updatePriority(currentRequest["uid"],-1)
#  refreshGuiTree()
#  return 1 #SHORT CIRCUIT
  logMe = 1
  reqObj = currentRequest["request_obj"]
  data_directory_name = str(reqObj["directory"])
  exposure_period = reqObj["exposure_time"]
  wavelength = reqObj["wavelength"]
  resolution = reqObj["resolution"]
  slit_height = reqObj["slit_height"]
  slit_width = reqObj["slit_width"]
  attenuation = reqObj["attenuation"]
  img_width = reqObj["img_width"]
  file_prefix = str(reqObj["file_prefix"])
  print(reqObj["protocol"])
  prot = str(reqObj["protocol"])
  sweep_start = reqObj["sweep_start"]
  sweep_end = reqObj["sweep_end"]
  range_degrees = abs(sweep_end-sweep_start)  
  sweep_start = reqObj["sweep_start"]%360.0
  file_number_start = reqObj["file_number_start"]
  basePath = reqObj["basePath"]
#  jpegDirectory = "jpegs" + data_directory_name[data_directory_name.find(basePath)+len(basePath):len(data_directory_name)]
  visitName = daq_utils.getVisitName()
  jpegDirectory = visitName + "/jpegs/" + data_directory_name[data_directory_name.find(visitName)+len(visitName):len(data_directory_name)]  

    
  status = 1
  if not (os.path.isdir(data_directory_name)):
    comm_s = "mkdir -p " + data_directory_name
    os.system(comm_s)
    comm_s = "chmod 777 " + data_directory_name
    os.system(comm_s)
    comm_s = "mkdir -p " + jpegDirectory
    os.system(comm_s)
    comm_s = "chmod 777 " + jpegDirectory
    os.system(comm_s)
  if (prot == "raster"):
    status = daq_macros.snakeRaster(currentRequest["uid"])
  elif (prot == "stepRaster"):
    status = daq_macros.snakeStepRaster(currentRequest["uid"])    
  elif (prot == "vector" or prot == "stepVector"):
    if (reqObj["centeringOption"] != "Interactive"):
      logMe = 0
      daq_macros.autoVector(currentRequest)
    else:
      imagesAttempted = collect_detector_seq_hw(sweep_start,range_degrees,img_width,exposure_period,file_prefix,data_directory_name,file_number_start,currentRequest)
  elif (prot == "multiCol"):
#    daq_macros.multiCol(currentRequest)
    daq_macros.snakeRaster(currentRequest["uid"])    
  elif (prot == "multiColQ"):
    daq_macros.multiCol(currentRequest)
#    daq_macros.snakeRaster(currentRequest["uid"])    
  elif (prot == "eScan"):
    daq_macros.eScan(currentRequest)
  else: #standard, screening, or edna - these may require autoalign, checking first
    if (reqObj["pos_x"] != -999):
      beamline_lib.mvaDescriptor("sampleX",reqObj["pos_x"])
      beamline_lib.mvaDescriptor("sampleY",reqObj["pos_y"])
      beamline_lib.mvaDescriptor("sampleZ",reqObj["pos_z"])
    elif (reqObj["centeringOption"] == "Interactive"): #robotic, pause and let user center
      pause_data_collection()
      check_pause()
    else:
      print("autoRaster")
      if not (daq_macros.autoRasterLoop(currentRequest)):
        print("could not center sample")
        db_lib.updatePriority(currentRequest["uid"],-1)
        refreshGuiTree()
        return 0
#    if (not stateModule.gotoState("DataCollection")):      
#      print("State violation")
#      db_lib.updatePriority(currentRequest["uid"],-1)
#      refreshGuiTree()
#      return 0
    if (reqObj["protocol"] == "screen"):
      screenImages = 2
      screenRange = 90
      range_degrees = img_width
      for i in range (0,screenImages):
        sweep_start = reqObj["sweep_start"]+(i*screenRange)
        sweep_end = sweep_start+screenRange
#        sweep_end = reqObj["sweep_end"]+(i*screenRange)        
        file_prefix = str(reqObj["file_prefix"]+"_"+str(i*screenRange))
        data_directory_name = str(reqObj["directory"]) # for now
        file_number_start = reqObj["file_number_start"]
        beamline_lib.mvaDescriptor("omega",sweep_start)
        if (1):
#        if (beamline_support.getPvValFromDescriptor("gonDaqHwTrig")):                  
          imagesAttempted = collect_detector_seq_hw(sweep_start,range_degrees,img_width,exposure_period,file_prefix,data_directory_name,file_number_start,currentRequest)
        else:
          imagesAttempted = collect_detector_seq(sweep_start,range_degrees,img_width,exposure_period,file_prefix,data_directory_name,file_number_start,currentRequest)
        seqNum = int(detector_get_seqnum())         
        cbfComm = db_lib.getBeamlineConfigParam(daq_utils.beamline,"cbfComm")
        cbfDir = data_directory_name+"/cbf"
        comm_s = "mkdir -p " + cbfDir
        os.system(comm_s)
        hdfSampleDataPattern = data_directory_name+"/"+file_prefix+"_" 
        hdfRowFilepattern = hdfSampleDataPattern + str(int(float(seqNum))) + "_master.h5"
        CBF_conversion_pattern = cbfDir + "/" + file_prefix+"_" + str(int(sweep_start))+".cbf"  
        comm_s = "eiger2cbf-linux " + hdfRowFilepattern
        startIndex=1
        endIndex = 1
        node = db_lib.getBeamlineConfigParam(daq_utils.beamline,"spotNode1")        
        comm_s = "ssh -q " + node + " \"sleep 6;" + cbfComm + " " + hdfRowFilepattern  + " " + str(startIndex) + ":" + str(endIndex) + " " + CBF_conversion_pattern + "\"&" 
        print(comm_s)
        os.system(comm_s)
          
    elif (reqObj["protocol"] == "characterize" or reqObj["protocol"] == "ednaCol"):
      characterizationParams = reqObj["characterizationParams"]
      index_success = daq_macros.dna_execute_collection3(0.0,img_width,2,exposure_period,data_directory_name+"/",file_prefix,1,-89.0,1,currentRequest)
#      if (0):
      if (index_success):        
        resultsList = db_lib.getResultsforRequest(currentRequest["uid"]) # because for testing I keep running the same request. Probably not in usual use.
        results = resultsList[-2]
        strategyResults = results["result_obj"]["strategy"]
        stratStart = strategyResults["start"]
        stratEnd = strategyResults["end"]
        stratWidth = strategyResults["width"]
        stratExptime = strategyResults["exptime"]
        stratDetDist = strategyResults["detDist"]
        sampleID = currentRequest["sample"]
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
        newReqObj["dimple"] = reqObj["dimple"]                
        newReqObj["xia2"] = reqObj["xia2"]
        runNum = db_lib.incrementSampleRequestCount(sampleID)
        reqObj["runNum"] = runNum
        newStratRequest = db_lib.addRequesttoSample(sampleID,newReqObj["protocol"],daq_utils.owner,newReqObj,priority=0,proposalID=daq_utils.getProposalID())
        if (reqObj["protocol"] == "ednaCol"):
          db_lib.updatePriority(currentRequest["uid"],-1)
          refreshGuiTree()
          collectData(newStratRequest)
          return 1
    else: #standard
      beamline_lib.mvaDescriptor("omega",sweep_start)
      if (1):
#      if (beamline_support.getPvValFromDescriptor("gonDaqHwTrig")):              
        imagesAttempted = collect_detector_seq_hw(sweep_start,range_degrees,img_width,exposure_period,file_prefix,data_directory_name,file_number_start,currentRequest)
      else:
        imagesAttempted = collect_detector_seq(sweep_start,range_degrees,img_width,exposure_period,file_prefix,data_directory_name,file_number_start,currentRequest)
  try:
    if (logMe):
      logMxRequestParams(currentRequest)
  except TypeError:
    print("caught type error in logging")
  if (prot == "vector" or prot == "standard"):
    seqNum = int(detector_get_seqnum())
    comm_s = os.environ["LSDCHOME"] + "/runSpotFinder4syncW.py " + data_directory_name + " " + file_prefix + " " + str(currentRequest["uid"]) + " " + str(seqNum) + " " + str(currentIspybDCID)+ "&"
    print(comm_s)
    os.system(comm_s)    
    if (reqObj["fastDP"]):
      if (reqObj["fastEP"]):
        fastEPFlag = 1
      else:
        fastEPFlag = 0
      if (reqObj["dimple"]):
        dimpleFlag = 1
      else:
        dimpleFlag = 0        
#      node = db_lib.getBeamlineConfigParam(daq_utils.beamline,"fastDPNode")
      nodeName = "fastDPNode" + str((fastDPNodeCounter%fastDPNodeCount)+1)
      fastDPNodeCounter+=1
      node = db_lib.getBeamlineConfigParam(daq_utils.beamline,nodeName)      
      dimpleNode = db_lib.getBeamlineConfigParam(daq_utils.beamline,"dimpleNode")      
      if (daq_utils.detector_id == "EIGER-16"):
        seqNum = int(detector_get_seqnum())
#        seqNum = beamline_support.get_any_epics_pv("XF:17IDC-ES:FMX{Det:Eig16M}cam1:SequenceId","VAL")        
        comm_s = os.environ["LSDCHOME"] + "/runFastDPH5.py " + data_directory_name + " " + file_prefix + " " + str(seqNum) + " " + str(int(round(range_degrees/img_width))) + " " + str(currentRequest["uid"]) + " " + str(fastEPFlag) + " " + node + " " + str(dimpleFlag) + " " + dimpleNode + " " + str(currentIspybDCID)+ "&"
      else:
        comm_s = os.environ["LSDCHOME"] + "/runFastDP.py " + data_directory_name + " " + file_prefix + " " + str(file_number_start) + " " + str(int(round(range_degrees/img_width))) + " " + str(currentRequest["uid"]) + " " + str(fastEPFlag) + " " + node + " " + str(dimpleFlag) + " " + dimpleNode + "&"
      print(comm_s)
      os.system(comm_s)
    if (reqObj["xia2"]):
      comm_s = "ssh -q xf17id1-srv1 \"" + os.environ["LSDCHOME"] + "/runXia2.py " + data_directory_name + " " + file_prefix + " " + str(file_number_start) + " " + str(int(round(range_degrees/img_width))) + " " + str(currentRequest["uid"]) + "\"&"
#      comm_s = os.environ["CBHOME"] + "/runXia2.py " + data_directory_name + " " + file_prefix + " " + str(file_number_start) + " " + str(int(round(range_degrees/img_width))) + " " + str(currentRequest["request_id"]) + "&"        
      os.system(comm_s)
  
  db_lib.updatePriority(currentRequest["uid"],-1)
  refreshGuiTree()
  
  return status

    

def collect_detector_seq_hw(sweep_start,range_degrees,image_width,exposure_period,fileprefix,data_directory_name,file_number,currentRequest,z_target=0): #works for pilatus
  global image_started,allow_overwrite,abort_flag

  print("data directory = " + data_directory_name)
  reqObj = currentRequest["request_obj"]
  protocol = str(reqObj["protocol"])
  if (0):
#  if (daq_utils.beamline == "amx"):                
    beamline_lib.mvaDescriptor("energy",reqObj["energy"])  
  sweep_start = sweep_start%360.0
  if (protocol == "vector" or protocol == "stepVector"):
    beamline_lib.mvaDescriptor("omega",sweep_start)    
  number_of_images = round(range_degrees/image_width)
  range_seconds = number_of_images*exposure_period
  if (daq_utils.detector_id == "EIGER-16"):  
    exposure_time = exposure_period - .00001
  else:
    exposure_time = exposure_period - .0024  
  angleStart = sweep_start
#  angleStart = beamline_lib.motorPosFromDescriptor("omega")  
###  if (angleStart>360.0):
###    angleStart = angleStart%360.0 #note, nsls2 angle start now used, just get current position for now
  file_prefix_minus_directory = str(fileprefix)
  try:
    file_prefix_minus_directory = file_prefix_minus_directory[file_prefix_minus_directory.rindex("/")+1:len(file_prefix_minus_directory)]
  except ValueError: 
    pass
  print("collect %f degrees for %f seconds %d images exposure_period = %f exposure_time = %f" % (range_degrees,range_seconds,number_of_images,exposure_period,exposure_time))
  if (protocol == "standard" or protocol == "characterize" or protocol == "ednaCol" or protocol == "screen"):
    daq_macros.vectorSync()
    daq_macros.zebraDaq(angleStart,range_degrees,image_width,exposure_period,file_prefix_minus_directory,data_directory_name,file_number,3)
#    daq_macros.zebraDaq(angleStart,range_degrees,image_width,exposure_period,file_prefix_minus_directory,data_directory_name,file_number,3,protocol=protocol)  #?protocol?
  elif (protocol == "vector"):
    daq_macros.vectorZebraScan(currentRequest)  
  elif (protocol == "stepVector"):
    daq_macros.vectorZebraStepScan(currentRequest)
  else:
    pass
  return 


def detectorArm(angle_start,image_width,number_of_images,exposure_period,fileprefix,data_directory_name,file_number): #will need some environ info to diff eiger/pilatus
  global image_started,allow_overwrite,abort_flag

  detector_save_files()
  detector_set_username(getpass.getuser())
  detector_set_groupname(grp.getgrgid(os.getgid())[0])
  detector_set_fileperms(420)
  print("data directory = " + data_directory_name)

  file_prefix_minus_directory = str(fileprefix)
  try:
    file_prefix_minus_directory = file_prefix_minus_directory[file_prefix_minus_directory.rindex("/")+1:len(file_prefix_minus_directory)]
  except ValueError: 
    pass
  detector_set_exposure_time(exposure_period)  
  detector_set_period(exposure_period) #apparently this takes care of itself for deadtime
  detector_set_numimages(number_of_images)
  detector_set_filepath(data_directory_name)
  detector_set_fileprefix(file_prefix_minus_directory)
  detector_set_filenumber(file_number)
  detector_set_fileheader(angle_start,image_width,beamline_lib.motorPosFromDescriptor("detectorDist"),beamline_lib.motorPosFromDescriptor("wavelength"),0.0,exposure_period,beamline_support.getPvValFromDescriptor("beamCenterX"),beamline_support.getPvValFromDescriptor("beamCenterY"),"omega",angle_start,0.0,0.0) #only a few for eiger
  
#  print "collect eiger %f degrees for %f seconds %d images exposure_period = %f exposure_time = %f" % (range_degrees,range_seconds,number_of_images,exposure_period,exposure_time)
  detector_start() #but you need wired or manual trigger
  startArm = time.time()
  detector_waitArmed() #don't worry about this while we're not doing hardware triggers., not quite sure what it means
  endArm = time.time()
  armTime = endArm-startArm
  print("\narm time = " + str(armTime) +"\n")
#  image_started = range_seconds
#  time.sleep(1.0) #4/15 - why so long?
#  time.sleep(0.3)  
#  set_field("state","Expose")
#  gon_osc(get_field("scan_axis"),0.0,range_degrees,range_seconds) #0.0 is the angle start that's not used
#  image_started = 0        
#  detector_wait()
#  set_field("state","Idle")          
###  daq_macros.fakeDC(data_directory_name,file_prefix_minus_directory,int(file_number),int(number_of_images))  
#  return number_of_images
  return

def checkC2C_X(x,fovx): # this is to make sure the user doesn't make too much of an x-move in C2C
  scalePixX = beamline_support.getPvValFromDescriptor("image_X_scalePix")
  centerPixX = beamline_support.getPvValFromDescriptor("image_Y_centerPix")
  xpos = beamline_lib.motorPosFromDescriptor("sampleX")
  target = xpos + ((x-centerPixX) * (fovx/scalePixX))
  print(target)
#  xlimLow = 11400.0
#  xlimHi = 14400.0
  xlimLow = beamline_support.getPvValFromDescriptor("robotXMountPos") + beamline_support.getPvValFromDescriptor("robotXMountLowLim")
  xlimHi = beamline_support.getPvValFromDescriptor("robotXMountPos") + beamline_support.getPvValFromDescriptor("robotXMountHiLim")
#  print(xlimHi)
  if (target<xlimLow or target>xlimHi):
    gui_message("Click to Center out of bounds on X move. Please mount next sample.")
    return 0
  return 1
  

def center_on_click(x,y,fovx,fovy,source="screen",maglevel=0,jog=0): #maglevel=0 means lowmag, high fov, #1 = himag with digizoom option, 
  #source=screen = from screen click, otherwise from macro with full pixel dimensions
  if (db_lib.getBeamlineConfigParam(daq_utils.beamline,'robot_online')): #so that we don't move things when robot moving?
    robotGovState = (beamline_support.getPvValFromDescriptor("robotSaActive") or beamline_support.getPvValFromDescriptor("humanSaActive"))
    if (not robotGovState):
      return
#    if (daq_utils.beamline == "amx"):
    if (1):      
      if not (checkC2C_X(x,fovx)):
        return
  if (source == "screen"):
    waitGovNoSleep()
    beamline_support.setPvValFromDescriptor("image_X_scalePix",daq_utils.screenPixX) #these are video dimensions in the gui
    beamline_support.setPvValFromDescriptor("image_Y_scalePix",daq_utils.screenPixY)
    beamline_support.setPvValFromDescriptor("image_X_centerPix",daq_utils.screenPixX/2)
    beamline_support.setPvValFromDescriptor("image_Y_centerPix",daq_utils.screenPixY/2)
    beamline_support.setPvValFromDescriptor("image_X_scaleMM",float(fovx))
    beamline_support.setPvValFromDescriptor("image_Y_scaleMM",float(fovy))
    
  else:
    if (int(maglevel)==0): #I think hardcoded to not use maglevel anymore, replaced with more flexible fov
      beamline_support.setPvValFromDescriptor("image_X_scalePix",daq_utils.lowMagPixX)
      beamline_support.setPvValFromDescriptor("image_Y_scalePix",daq_utils.lowMagPixY)
      beamline_support.setPvValFromDescriptor("image_X_centerPix",daq_utils.lowMagPixX/2)
      beamline_support.setPvValFromDescriptor("image_Y_centerPix",daq_utils.lowMagPixY/2)
      beamline_support.setPvValFromDescriptor("image_X_scaleMM",float(fovx))
      beamline_support.setPvValFromDescriptor("image_Y_scaleMM",float(fovy))
      
    else:
      beamline_support.setPvValFromDescriptor("image_X_scalePix",daq_utils.lowMagPixX)
      beamline_support.setPvValFromDescriptor("image_Y_scalePix",daq_utils.lowMagPixY)
      beamline_support.setPvValFromDescriptor("image_X_centerPix",daq_utils.highMagPixX/2)
      beamline_support.setPvValFromDescriptor("image_Y_centerPix",daq_utils.highMagPixY/2)
      beamline_support.setPvValFromDescriptor("image_X_scaleMM",float(fovx))
      beamline_support.setPvValFromDescriptor("image_Y_scaleMM",float(fovy))

  omega_mod = beamline_lib.motorPosFromDescriptor("omega")%360.0
#  daq_utils.broadcast_output("\ncenter on x = %s, y = %s, omega = %f, phi = %f\n" % (x,y,omega_mod,0))
#  xcheck = checkC2C_X(x,fovx)
#  if (xcheck):
  lib_gon_center_xtal(x,y,omega_mod,0)
  if (jog):
    beamline_lib.mvrDescriptor("omega",float(jog))


def setProposalID(proposalID):
  daq_utils.setProposalID(proposalID)

def getProposalID():
  return daq_utils.getProposalID()


