import sys
import os
import time
import string
import math
import daq_macros
from math import *
from string import *
from gon_lib import *
from det_lib import *
import robot_lib
import daq_utils
import beamline_lib
import beamline_support
import db_lib
import requests

var_list = {'beam_check_flag':0,'overwrite_check_flag':1,'omega':0.00,'kappa':0.00,'phi':0.00,'theta':0.00,'distance':10.00,'rot_dist0':300.0,'inc0':1.00,'exptime0':5.00,'file_prefix0':'lowercase','numstart0':0,'col_start0':0.00,'col_end0':1.00,'scan_axis':'omega','wavelength0':1.1,'datum_omega':0.00,'datum_kappa':0.00,'datum_phi':0.00,'xbeam':157.00,'ybeam':157.00,'size_mode':0,'spcgrp':1,'state':"Idle",'state_percent':0,'datafilename':'none','active_sweep':-1,'html_logging':1,'take_xtal_pics':0,'px_id':'none','xtal_id':'none','current_pinpos':0,'sweep_count':0,'group_name':'none','mono_energy_target':1.1,'mono_wave_target':1.1,'energy_inflection':12398.5,'energy_peak':12398.5,'wave_inflection':1.0,'wave_peak':1.0,'energy_fall':12398.5,'wave_fall':1.0,'beamline_merit':0,'fprime_peak':0.0,'f2prime_peak':0.0,'fprime_infl':0.0,'f2prime_infl':0.0,'program_state':"Program Ready",'filter':0,'edna_aimed_completeness':0.99,'edna_aimed_ISig':2.0,'edna_aimed_multiplicity':'auto','edna_aimed_resolution':'auto','mono_energy_current':1.1,'mono_energy_scan_step':1,'mono_wave_current':1.1,'mono_scan_points':21,'mounted_pin':0,'pause_button_state':'Pause','grid_w':210,'grid_h':150,'grid_i':10,'grid_on':0,'vector_on':0,'vector_fpp':1,'vector_step':0.0,'vector_translation':0.0,'xia2_on':0,'grid_exptime':0.2,'grid_imwidth':0.2,'choochResultFlag':0,'xrecRasterFlag':0}


global x_vec_start, y_vec_start, z_vec_start, x_vec_end, y_vec_end, z_vec_end, x_vec, y_vec, z_vec
global var_channel_list
global message_string_pv
global data_directory_name
var_channel_list = {}


global abort_flag
abort_flag = 0

def init_var_channels():
  global var_channel_list

  for varname in var_list.keys():
    var_channel_list[varname] = beamline_support.pvCreate(daq_utils.beamline + "_comm:" + varname)
    beamline_support.pvPut(var_channel_list[varname],var_list[varname])


def gui_message(message_string): #for now, later in python
    command_string = "tkmessage %s\n" % message_string
    os.system(command_string)


def destroy_gui_message():
  os.system("killall -KILL tkmessage")


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
  set_field("xbeam",atof(xbeam))

def set_ybeam(ybeam):
  set_field("ybeam",atof(ybeam))

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
    print "is mailin"
    if (archive_active == 1 and archive == ""):
      try:
        default_archive_location = os.environ["DEFAULT_ARCHIVE_LOCATION"]
        set_archive(default_archive_location)
      except KeyError:
        pass
  else:
    print "is not mailin"


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

def create_filename(prefix,number):
  tmp_filename = "%s_%05d.cbf" % (prefix,int(number))
  if (prefix[0] != "/"):
    cwd = os.getcwd()
    filename = "%s/%s" % (cwd,tmp_filename)
  else:
    filename = tmp_filename
  return filename


def refreshGuiTree():
  beamline_support.set_any_epics_pv(daq_utils.beamline+"_comm:live_q_change_flag","VAL",1)

def broadcast_output(s):
  time.sleep(0.01)
  if (string.find(s,'|') == -1):
    print s
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

  print "running queue in daq server"
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
    colStatus = collectData(currentRequest)


def stopDCQueue():
  print "stopping queue in daq server"
  abort_data_collection()


def collectData(currentRequest):
  global data_directory_name

  reqObj = currentRequest["request_obj"]
  data_directory_name = str(reqObj["directory"])
  if not (os.path.isdir(data_directory_name)):
    comm_s = "mkdir -p " + data_directory_name
    os.system(comm_s)
  print reqObj["protocol"]
  prot = str(reqObj["protocol"])
  if (prot == "raster"):
    daq_macros.snakeRaster(currentRequest["request_id"])
#    return
  elif (prot == "vector"):
    daq_macros.vectorScan(currentRequest)
#    return
  else: #standard, screening, or edna - these may require autoalign, checking first
    if (reqObj["pos_x"] != 0):
      beamline_lib.mva("X",reqObj["pos_x"])
      beamline_lib.mva("Y",reqObj["pos_y"])
      beamline_lib.mva("Z",reqObj["pos_z"])
    else:
      print "autoRaster"
      daq_macros.autoRasterLoop(currentRequest["sample_id"])    
    exposure_period = reqObj["exposure_time"]
    wavelength = reqObj["wavelength"]
    resolution = reqObj["resolution"]
    slit_height = reqObj["slit_height"]
    slit_width = reqObj["slit_width"]
    attenuation = reqObj["attenuation"]
    img_width = reqObj["img_width"]
    file_prefix = str(reqObj["file_prefix"])
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
        beamline_lib.mva("Omega",sweep_start)
        imagesAttempted = collect_detector_seq(range_degrees,img_width,exposure_period,file_prefix,data_directory_name,file_number_start)
    elif (reqObj["protocol"] == "characterize"):
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
        runNum = db_lib.incrementSampleRequestCount(sampleID)
        reqObj["runNum"] = runNum
        newStratRequest = db_lib.addRequesttoSample(sampleID,newReqObj["protocol"],newReqObj,priority=0)

    else: #standard
      sweep_start = reqObj["sweep_start"]
      sweep_end = reqObj["sweep_end"]
      file_prefix = str(reqObj["file_prefix"])
      file_number_start = reqObj["file_number_start"]
      range_degrees = abs(sweep_end-sweep_start)
      beamline_lib.mva("Omega",sweep_start)
      imagesAttempted = collect_detector_seq(range_degrees,img_width,exposure_period,file_prefix,data_directory_name,file_number_start)
      if (reqObj["fastDP"]):
        if (reqObj["fastEP"]):
          fastEPFlag = 1
        else:
          fastEPFlag = 0
        comm_s = os.environ["CBHOME"] + "/runFastDP.py " + data_directory_name + " " + file_prefix + " " + str(file_number_start) + " " + str(int(round(range_degrees/img_width))) + " " + str(currentRequest["request_id"]) + " " + str(fastEPFlag) + "&"
        print comm_s
        os.system(comm_s)
      if (reqObj["xia2"]):
        comm_s = os.environ["CBHOME"] + "/runXia2.py " + data_directory_name + " " + file_prefix + " " + str(file_number_start) + " " + str(int(round(range_degrees/img_width))) + " " + str(currentRequest["request_id"]) + "&"
        os.system(comm_s)
  
  db_lib.updatePriority(currentRequest["request_id"],-1)
  refreshGuiTree()

    

def collect_detector_seq(range_degrees,image_width,exposure_period,fileprefix,data_directory_name,file_number,z_target=0): #works for pilatus
  global image_started,allow_overwrite,abort_flag


  print "data directory = " + data_directory_name
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
  print "collect pilatus %f degrees for %f seconds %d images exposure_period = %f exposure_time = %f" % (range_degrees,range_seconds,number_of_images,exposure_period,exposure_time)
  detector_set_period(exposure_period)
  detector_set_exposure_time(exposure_time)
  detector_set_numimages(number_of_images)
  detector_set_filepath(data_directory_name)
  detector_set_fileprefix(file_prefix_minus_directory)
  detector_set_filenumber(file_number)
  detector_set_fileheader(get_field(get_field("scan_axis")),get_field("inc0"),get_field("distance"),12398.5/beamline_lib.get_mono_energy(),get_field("theta"),get_field("exptime0"),get_field("xbeam"),get_field("ybeam"),get_field("scan_axis"),get_field("omega"),get_field("kappa"),get_field("phi"))
  print "collect pilatus %f degrees for %f seconds %d images exposure_period = %f exposure_time = %f" % (range_degrees,range_seconds,number_of_images,exposure_period,exposure_time)
  detector_start()
  image_started = range_seconds
  time.sleep(1.0) #4/15 - why so long?
#  time.sleep(0.3)  
  set_field("state","Expose")
##########  set_epics_pv_nowait("xtz","VAL",z_target)   #this is for grid!!!!!!!!
  gon_osc(get_field("scan_axis"),0.0,range_degrees,range_seconds) #0.0 is the angle start that's not used
  image_started = 0        
  set_field("state","Idle")        
  detector_wait()
  daq_macros.fakeDC(data_directory_name,file_prefix_minus_directory,int(file_number),int(number_of_images))  
  return number_of_images



def center_on_click(x,y,maglevel=0,source="screen",jog=0): #maglevel=0 means lowmag, high fov, #1 = himag with digizoom option, 
  #source=screen = from screen click, otherwise from macro with full pixel dimensions
  if (source == "screen"):
    beamline_support.set_any_epics_pv(daq_utils.gonioPvPrefix+"image_X_scale","B",daq_utils.screenPixX) #these are video dimensions in the gui
    beamline_support.set_any_epics_pv(daq_utils.gonioPvPrefix+"image_Y_scale","B",daq_utils.screenPixY)
    beamline_support.set_any_epics_pv(daq_utils.gonioPvPrefix+"image_X_center","A",daq_utils.screenPixX/2)
    beamline_support.set_any_epics_pv(daq_utils.gonioPvPrefix+"image_Y_center","A",daq_utils.screenPixY/2)
  else:
    if (int(maglevel)==0):
      beamline_support.set_any_epics_pv(daq_utils.gonioPvPrefix+"image_X_scale","B",daq_utils.lowMagPixX)
      beamline_support.set_any_epics_pv(daq_utils.gonioPvPrefix+"image_Y_scale","B",daq_utils.lowMagPixY)
      beamline_support.set_any_epics_pv(daq_utils.gonioPvPrefix+"image_X_center","A",daq_utils.lowMagPixX/2)
      beamline_support.set_any_epics_pv(daq_utils.gonioPvPrefix+"image_Y_center","A",daq_utils.lowMagPixY/2)
    else:
      beamline_support.set_any_epics_pv(daq_utils.gonioPvPrefix+"image_X_scale","B",daq_utils.highMagPixX)
      beamline_support.set_any_epics_pv(daq_utils.gonioPvPrefix+"image_Y_scale","B",daq_utils.highMagPixY)
      beamline_support.set_any_epics_pv(daq_utils.gonioPvPrefix+"image_X_center","A",daq_utils.highMagPixX/2)
      beamline_support.set_any_epics_pv(daq_utils.gonioPvPrefix+"image_Y_center","A",daq_utils.highMagPixY/2)

  if (int(maglevel)==0):
    beamline_support.set_any_epics_pv(daq_utils.gonioPvPrefix+"image_X_scale","C",daq_utils.lowMagFOVx)
    beamline_support.set_any_epics_pv(daq_utils.gonioPvPrefix+"image_Y_scale","C",daq_utils.lowMagFOVy)
  else:
    if (beamline_support.get_any_epics_pv("FAMX-cam1:MJPGZOOM:NDArrayPort","VAL") == "ROI2"):
      beamline_support.set_any_epics_pv(daq_utils.gonioPvPrefix+"image_X_scale","C",daq_utils.highMagFOVx)
      beamline_support.set_any_epics_pv(daq_utils.gonioPvPrefix+"image_Y_scale","C",daq_utils.highMagFOVy)
    else:
      beamline_support.set_any_epics_pv(daq_utils.gonioPvPrefix+"image_X_scale","C",daq_utils.highMagFOVx/2.0)
      beamline_support.set_any_epics_pv(daq_utils.gonioPvPrefix+"image_Y_scale","C",daq_utils.highMagFOVy/2.0)
  omega_mod = beamline_lib.get_epics_motor_pos("Omega")%360.0
#  daq_utils.broadcast_output("\ncenter on x = %s, y = %s, omega = %f, phi = %f\n" % (x,y,omega_mod,0))
  lib_gon_center_xtal(x,y,omega_mod,0)
  if (jog):
    beamline_lib.mvr("Omega",float(jog))


def take_crystal_pictureCURL(filename,czoom=0):
  zoom = int(czoom)
  if not (daq_utils.has_xtalview):
    return
#  if (daq_utils.xtalview_user == "None"):
  if (1):
    if (zoom==0):
      comm_s = "curl -o %s.jpg -s %s" % (filename,daq_utils.xtal_url)
    else:
#      beamline_support.set_any_epics_pv("FAMX-cam1:MJPGZOOM:NDArrayPort","VAL","ROI1")
      comm_s = "curl -o %s.jpg -s %s" % (filename,daq_utils.xtal_url_small)
  else:
    comm_s = "curl -u %s:%s -o %s.jpg -s %s" % (daq_utils.xtalview_user,daq_utils.xtalview_pass,filename,daq_utils.xtal_url)
  os.system(comm_s)


def take_crystal_picture(filename=None,czoom=0,reqID=None):
  zoom = int(czoom)
  if not (daq_utils.has_xtalview):
    return
  if (1):
    if (zoom==0):
      r=requests.get(daq_utils.xtal_url)
    else:
      r=requests.get(daq_utils.xtal_url_small)
  else: #password, need to change to requests module if we need this
    comm_s = "curl -u %s:%s -o %s.jpg -s %s" % (daq_utils.xtalview_user,daq_utils.xtalview_pass,filename,daq_utils.xtal_url)
  data = r.content
  if (filename != None):
    fd = open(filename+".jpg","w+")
    fd.write(data)
    fd.close()
  if (reqID != None):
    xtalpicJpegDataResult = {}
    imgRef = db_lib.addFile(data)
    xtalpicJpegDataResult["data"] = imgRef
    db_lib.addResultforRequest("xtalpicJpeg",reqID,xtalpicJpegDataResult)


def diff2jpegLYNX(diffimageName,JPEGfilename=None,reqID=None):
  imageJpegData = {}
  imageJpegHeader = {}
  imageJpegData["dataFilePath"]=diffimageName
  img_url = "http://"+daq_utils.imgsrv_host+":"+daq_utils.imgsrv_port+"/getImage\?fileName="+ diffimageName+"\&sizeX=500\&sizeY=500\&gray=100\&zoom=1.0\&percentX=0.5\&percentY=0.5\&userName=me\&sessionId=E"
#  comm_s = "lynx -source %s >%s" % (img_url,JPEGfilename) 
  comm_s = "lynx -source %s" % (img_url) 
  print comm_s
  data = os.popen(comm_s).read()
  imageJpegData["data"] = data
#  os.system(comm_s)
  img_url = "http://"+daq_utils.imgsrv_host+":"+daq_utils.imgsrv_port+"/getThumbnail\?fileName="+ diffimageName+"\&sizeX=500\&sizeY=500\&gray=100\&zoom=1.0\&percentX=0.5\&percentY=0.5\&userName=me\&sessionId=E"
  comm_s = "lynx -source %s" % (img_url) 
  thumbData = os.popen(comm_s).read()
  imageJpegData["thumbData"] = thumbData
#  comm_s = "lynx -source %s >%s" % (img_url,"thumb_"+JPEGfilename) 
  print comm_s
#  os.system(comm_s)
  img_url = "http://"+daq_utils.imgsrv_host+":"+daq_utils.imgsrv_port+"/getHeader\?fileName="+ diffimageName+"\&userName=me\&sessionId=E"
  comm_s = "lynx -source " + img_url
  for outputline in os.popen(comm_s).readlines():    
    print outputline
    tokens = string.split(outputline)      
    if (tokens[0] == "OSC_START"):
      print "Omega start = " + tokens[1]
      imageJpegHeader["oscStart"] = float(tokens[1])
    elif (tokens[0] == "OSC_RANGE"):
      print "Omega range = " + tokens[1] 
      imageJpegHeader["oscRange"] = float(tokens[1])
    elif (tokens[0] == "EXPOSURE"):
      print "Exposure Time = " + tokens[2]
      imageJpegHeader["exptime"] = float(tokens[2])
    elif (tokens[0] == "DISTANCE"):
      print "Distance = " + str(float(tokens[1])/1000.0)
      imageJpegHeader["detDist"] = float(tokens[1])
    elif (tokens[0] == "WAVELENGTH"):
      print "Wavelength = " + tokens[1] 
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
  img_url = "http://"+daq_utils.imgsrv_host+":"+daq_utils.imgsrv_port+"/getImage" 
  r = requests.get(img_url,params=payload)
  data = r.content
  imageJpegData["data"] = data
  img_url = "http://"+daq_utils.imgsrv_host+":"+daq_utils.imgsrv_port+"/getThumbnail"
  r = requests.get(img_url,params=payload)
  thumbData = r.content
  imageJpegData["thumbData"] = thumbData
  payload = {"fileName":diffimageName,"userName":"me","sessionId":"E"}
  img_url = "http://"+daq_utils.imgsrv_host+":"+daq_utils.imgsrv_port+"/getHeader"
  r = requests.get(img_url,params=payload)
  imageJpegData["header"] = r
  headerData = r.text
  lines = headerData.split("\n")
  for i in range (0,len(lines)):
    line = lines[i]
    print line
    tokens = line.split()
    if (len(tokens) > 1):
      if (tokens[0] == "OSC_START"):
        print "Omega start = " + tokens[1]
        imageJpegHeader["oscStart"] = float(tokens[1])
      elif (tokens[0] == "OSC_RANGE"):
        print "Omega range = " + tokens[1] 
        imageJpegHeader["oscRange"] = float(tokens[1])
      elif (tokens[0] == "EXPOSURE"):
        print "Exposure Time = " + tokens[2]
        imageJpegHeader["exptime"] = float(tokens[2])
      elif (tokens[0] == "DISTANCE"):
        print "Distance = " + str(float(tokens[1])/1000.0)
        imageJpegHeader["detDist"] = float(tokens[1])
      elif (tokens[0] == "WAVELENGTH"):
        print "Wavelength = " + tokens[1] 
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


def set_vector_start():
  global x_vec_start, y_vec_start, z_vec_start
  x_vec_start = beamline_lib.get_epics_motor_pos("X")
  y_vec_start = beamline_lib.get_epics_motor_pos("Y")
  z_vec_start = beamline_lib.get_epics_motor_pos("Z")

def set_vector_end():
  global x_vec_end, y_vec_end, z_vec_end, x_vec, y_vec, z_vec, x_vec_start, y_vec_start, z_vec_start
  x_vec_end = beamline_lib.get_epics_motor_pos("X")
  y_vec_end = beamline_lib.get_epics_motor_pos("Y")
  z_vec_end = beamline_lib.get_epics_motor_pos("Z")
  x_vec = x_vec_end - x_vec_start
  y_vec = y_vec_end - y_vec_start
  z_vec = z_vec_end - z_vec_start
  trans_total = sqrt(x_vec**2 + y_vec**2 + z_vec**2)
  set_field("vector_translation",trans_total)  
  print "translation total =  " + str(trans_total)

  
def set_vector_fpp(fpp,numframes): #not used 7/22/15
  global x_vec, y_vec, z_vec

  set_field("vector_fpp",int(fpp))
  trans_total = 1000.0* sqrt(x_vec**2 + y_vec**2 + z_vec**2)
#  print "translation total =  " + str(trans_total)
  vec_step_microns = trans_total/(float(numframes)/float(fpp))
  print "trans step in microns = " + str(vec_step_microns)
  set_field("vector_step",vec_step_microns)


def vector_move(t_s,vecRequest): #I think t_s is a fraction of the total vector, so "1" would do the whole thing
  global x_vec_end, y_vec_end, z_vec_end, x_vec, y_vec, z_vec, x_vec_start, y_vec_start, z_vec_start

#  print "vec t = " + str(t_s)
  t = float(t_s)
  reqObj = vecRequest["request_obj"]
  trans_total = reqObj["vectorParams"]["trans_total"]
  trans_done = trans_total*t
  percent_done = t*100.0
  vec_s = "translation total = %f, translation done = %f, translation percent done = %f\n" % (trans_total,trans_done,percent_done)
  print vec_s
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
  beamline_lib.mva("X",new_x,"Y",new_y,"Z",new_z)
#  mva("Y",new_y)
#  mva("Z",new_z)


