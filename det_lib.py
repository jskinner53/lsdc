#!/usr/bin/python
import sys
import os
import time
from string import *
import epics_det

#detector routines

#pixel array specific start

def detector_set_period(period):
  print "set detector period " + str(period)
  epics_det.det_set_image_period(period)

def detector_set_exposure_time(exptime):
  print "set detector exposure time " + str(exptime)
  epics_det.det_set_exptime(exptime)

def detector_set_numimages(numimages):
  print "set detector number of images " + str(numimages)
  epics_det.det_set_numimages(numimages)

def detector_set_filepath(filepath):
  print "set detector file path " + filepath
  epics_det.det_set_filepath(filepath)

def detector_set_fileprefix(fileprefix):
  print "set detector file prefix " + fileprefix
  epics_det.det_set_fileprefix(fileprefix)

def detector_set_filenumber(filenumber):
  print "set detector file number " + str(filenumber)
  epics_det.det_set_filenum(filenumber)

def detector_wait():
  epics_det.det_wait()
  
#pixel array specific end

def init_detector():
  print "init detector"
  epics_det.det_channels_init()
  epics_det.det_set_numexposures(1)

def detector_start():
  print "start detector"  
  epics_det.det_start()

def detector_stop():
  print "stop detector"  
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
  print "detector filename"
  print filename
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
  print "detector filehead"  
  epics_det.det_setheader(float(phist),float(phiinc),float(dist),float(wave),
                 float(theta),float(exptime),float(xbeam),float(ybeam),
                 0,float(o),float(k),float(p))


def detector_set_filekind(flag):
  pass

#  if (flag == 1):
#    adsc_setfilekind(4)
#  else:
#    adsc_setfilekind(5)

