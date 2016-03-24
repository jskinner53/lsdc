#!/usr/bin/python -Wignore
#11/23/115 - WARNING. This is pretty shitty code that descends from X25 logger. It basically monitors areaDetector and logs stuff when data collections start. 
import beamline_support
import epics_det
import time
import string
import os
import db_lib
import daq_utils
import beamline_lib

global jpeg_needed
jpeg_needed = 0

def getDetPv(pvcode): 
  return  beamline_support.pvGet(epics_det.channel_list[pvcode])


def acquire_cb(epics_args, user_args):
  global jpeg_needed

  print 'my callback ' + str(epics_args['pv_value'])
  if (epics_args['pv_value'] == 1):
##    jpeg_needed = -99 #abort any current display loops
##    time.sleep(0.5)
    jpeg_needed = 1

  

def display_images():

  currentRequestID = db_lib.beamlineInfo('john', 'currentRequestID')["requestID"]
  print "display images for req " + str(currentRequestID)
  data_directory_name = getDetPv("data_filepath_rbv")
  numimages = getDetPv("numimages")
  prefix = getDetPv("data_filename_rbv")
  image_period = getDetPv("image_period")
  numstart = getDetPv("file_number_rbv")
  numstart = numstart - 1
  if (numimages>10 and image_period<10):
    sample = 10
  else:
    sample = 1
  filelist = []
  for i in range (numstart,numstart+numimages,sample):
    filename = "%s/%s_%05d.cbf" % (data_directory_name,prefix,i)
    filelist.append(filename)
  filename = "%s/%s_%05d.cbf" % (data_directory_name,prefix,numimages+numstart-1) # last image
  if (len(filelist) > 0):
    if (filename != filelist[len(filelist)-1]):
      filelist.append(filename)  
  for j in range (0,len(filelist)):
    filename = filelist[j]
    last_dot = string.rfind(filename,".")
    i = int(filename[last_dot-5:last_dot])
    print "looking for " + filename
    while not (os.path.exists(filename)):
      os.system("ls " + data_directory_name + " >/dev/null")
      time.sleep(0.03)
      if (jpeg_needed == -99):
        return
#    time.sleep(0.1) 
    print "found for " + filename
    time.sleep(.05) #got a corrupted file error in albula w/0 this, might not happen in real collection
##    daq_utils.albulaDisp(filename) #why have the logger kicking off albula? Because that's what it does for now, don't bother with eiger, use monitor
    daq_utils.diff2jpeg(filename,JPEGfilename=None,reqID=currentRequestID)
##huh? I think the filelist takes care of this    if (j%10 == 0):
    now = time.time()
    print "take xtal picture"
    daq_utils.runDials(filename)
    daq_utils.take_crystal_picture(filename=None,czoom=0,reqID=currentRequestID,omega=beamline_lib.motorPosFromDescriptor("omega")) #but this is unlikely to be synchronized with diff image




epics_det.read_db()
epics_det.det_init_pvs()
beamline_lib.read_db()
beamline_lib.init_mots()
daq_utils.init_environment()
keyname = "start"
beamline_support.add_callback(epics_det.channel_list[keyname],acquire_cb,"")
while 1:
  time.sleep(0.03)
  if (jpeg_needed):
    display_images()
#    if (jpeg_needed != -99): #abort of a run
    jpeg_needed = 0

    


