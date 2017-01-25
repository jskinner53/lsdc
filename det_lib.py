import sys
import os
import time
from string import *
import epics_det

#detector routines

#pixel array specific start

def detector_set_period(period):
  print("set detector period " + str(period))
  epics_det.det_set_image_period(period)

def detector_set_exposure_time(exptime):
  print("set detector exposure time " + str(exptime))
  epics_det.det_set_exptime(exptime)

def detector_get_seqnum():
  return epics_det.det_getSeqNum()


def detector_set_numimages(numimages):
  print("set detector number of images " + str(numimages))
  epics_det.det_set_numimages(numimages)

def detector_set_filepath(filepath):
  print("set detector file path " + filepath)
  epics_det.det_set_filepath(filepath)

def detector_set_fileprefix(fileprefix):
  print("set detector file prefix " + fileprefix)
  epics_det.det_set_fileprefix(fileprefix)

#def detector_set_fileNamePattern(fileNamePattern):
#  print "set detector file name pattern " + fileNamePattern
#  epics_det.det_set_fileprefix(fileprefix)

def detector_set_filenumber(filenumber): #I think this does nothing with the eiger
  print("set detector file number " + str(filenumber))
  epics_det.det_set_filenum(filenumber)

def detector_wait():
  epics_det.det_wait()

def detector_waitArmed():
  epics_det.det_waitArmed()
#pixel array specific end

def init_detector():
  print("init detector")
  epics_det.det_channels_init()
  epics_det.det_set_numexposures(1)

def detector_start():
  print("start detector")  
  epics_det.det_start()

def detector_trigger():
  print("trigger detector")  
  epics_det.det_trigger()

def get_trigger_mode():
  return epics_det.det_get_trigger_mode()

def detector_stop_acquire():
  epics_det.det_stop_acquire()
  
def detector_set_trigger_mode(mode):
  epics_det.det_set_trigger_mode(mode)
  
def detector_set_num_triggers(numTrigs):
  epics_det.det_set_num_triggers(numtrigs)
  
def detector_is_manual_trigger():
  return epics_det.det_is_manual_trigger()
  
def detector_stop():
  print("stop detector")  
  epics_det.det_stop()  
  
def detector_write(flag):
#  adsc_write(int(flag))
  pass

def detector_bin():
  epics_det.det_set_bin(2)

def detector_unbin():
  epics_det.det_set_bin(1)  

def detector_collect_darks(exptime):
  pass

def detector_set_filename(filename):
  print("detector filename")
  print(filename)
  last_slash = rfind(filename,"/")
  last_underscore = rfind(filename,"_")
  last_dot = rfind(filename,".")
  img_path = filename[0:last_slash]
  epics_det.det_set_filepath(img_path)
  img_prefix = filename[last_slash+1:last_underscore]
  epics_det.det_set_fileprefix(img_prefix)
  img_number = filename[last_underscore+1:last_dot]
  epics_det.det_set_filenum(int(img_number))

def detector_set_fileheader(phist,phiinc,dist,wave,theta,exptime,xbeam,ybeam,rot_ax,o,k,p):
#bogus rot axis,
  print("detector filehead")  
  epics_det.det_setheader(float(phist),float(phiinc),float(dist),float(wave),
                 float(theta),float(exptime),float(xbeam),float(ybeam),
                 0,float(o),float(k),float(p))


def detector_set_filekind(flag):
  pass

#  if (flag == 1):
#    adsc_setfilekind(4)
#  else:
#    adsc_setfilekind(5)


def detectorArmEigerObsolete(number_of_images,exposure_period,fileprefix,data_directory_name,wave,xbeam,ybeam,detDist): #will need some environ info to diff eiger/pilatus
  global image_started,allow_overwrite,abort_flag

  print("data directory = " + data_directory_name)

#  test_filename = "%s_%05d.cbf" % (fileprefix,int(file_number))
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
#  detector_dead_time = .0024 #pilatus

  detector_dead_time = .00001 #put this in config.
  exposure_time = exposure_period - detector_dead_time
  file_prefix_minus_directory = str(fileprefix)
  try:
    file_prefix_minus_directory = file_prefix_minus_directory[file_prefix_minus_directory.rindex("/")+1:len(file_prefix_minus_directory)]
  except ValueError: 
    pass
  detector_set_period(exposure_period)
  detector_set_exposure_time(exposure_time)
  detector_set_numimages(number_of_images)
  detector_set_filepath(data_directory_name)
  detector_set_fileprefix(file_prefix_minus_directory)
#  detector_set_filenumber(file_number)

  detector_set_fileheader(0.0,0.0,detDist,wave,0.0,0.0,xbeam,ybeam,"omega",0.0,0.0,0.0) #only a few for eiger
  
#  print "collect eiger %f degrees for %f seconds %d images exposure_period = %f exposure_time = %f" % (range_degrees,range_seconds,number_of_images,exposure_period,exposure_time)
  detector_start() #but you need wired or manual trigger
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



