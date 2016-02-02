import sys
import os
import time
import string
#from beamline_lib import *
import beamline_lib
import beamline_support
import dt_gon

global beamline

global command_active
command_active = 0

global still_osc
still_osc = 0

global head_alldone
#diffractometer routines

def lib_init_diffractometer():
  global beamline,head_alldone

#  beamline = beamline_support.beamline_designation
  head_alldone = beamline_support.pvCreate(beamline_support.beamline_designation+"gonioDone")
  beamline_support.initControlPVs()
  dt_gon.dt_init()


def lib_still_osc_mode(mode): #1=still,0=rotate(normal) - nsls2 - not sure how this changes
  global still_osc
  still_osc = mode


def lib_gon_center_xtal(x,y,angle_omega,angle_phi):
  beamline_lib.set_epics_pv_nowait("image_X_target","A",float(x))
  beamline_lib.set_epics_pv_nowait("image_Y_target","A",float(y))
  beamline_lib.set_epics_pv_nowait("OmegaPos","A",angle_omega)  
  beamline_lib.set_epics_pv_nowait("click_center","PROC",1)
  wait_for_goniohead()
  
def lib_open_shutter():
  dt_gon.dt_shutter(0)


def lib_close_shutter():
  dt_gon.dt_shutter(1)


def lib_open_shutter2():
  dt_gon.dt_shutter2(0)


def lib_close_shutter2():
  dt_gon.dt_shutter2(1)



def lib_home():
  dt_gon.dt_home_omega()


def lib_home_omega():
  dt_gon.dt_home_omega() 



def lib_home_dist():
  pass #for now
#  set_epics_pv("homedist","PROC",1)


def gon_stop():
  dt_gon.dt_stop()
    

def gon_osc(motname,angle_start,width,exptime):
#I think angle_start goes nowhere
  dt_gon.dt_set_osc_width(float(width))
  dt_gon.dt_set_osc_time(float(exptime))
  dt_gon.dt_osc() 
#  end_osc = get_epics_motor_pos("omega")
  end_osc = beamline_lib.get_epics_motor_pos("Omega")
  print "end_osc in gon_osc = " + str(end_osc) + "\n"
  return end_osc


def wait_for_goniohead(): #why can't I just call wait_motors????
  while (1):
    try:
      done_stat = beamline_support.pvGet(head_alldone)
      if (done_stat != 0):
        break
      else:
        time.sleep(.2)
        pass      
    except KeyboardInterrupt:
      pass
    except CaChannelException, status:
      print ca.message(status)
      print "\n\nHandled Epics Error in wait for motors-2\n\n"
      continue
  
  
