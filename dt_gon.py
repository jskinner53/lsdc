from beamline_support import *
import daq_utils
import time
import os

global dt_input,dt_output,gon_offline


def set_gon_pv(comm_s):
  print(comm_s)
  if (gon_offline):
    return
  pvPut(dt_input,comm_s)
  time.sleep(.1) #doubt this is necessary, but saw .5-sec sleeps for the shutter. something to watch


def dt_init():
    global dt_input, dt_output, gon_offline

    gon_offline = int(os.environ["GON_OFFLINE"])
    beamline = os.environ["BEAMLINE_ID"]
    if not (gon_offline):
#      dt_input = pvCreate(beamline+":-Asyn.AOUT")
#      dt_output = pvCreate(beamline+":-Asyn.TINP")
#      dt_input = pvCreate(daq_utils.gonioPvPrefix+"OmegaAsyn.AOUT")
#      dt_output = pvCreate(daq_utils.gonioPvPrefix+"OmegaAsyn.TINP")
#NOTE HARDCODING FOR NOW 1/16
      dt_input = pvCreate("XF:17IDC-CT:FMX{MC:13}Asyn.AOUT")
      dt_output = pvCreate("XF:17IDC-CT:FMX{MC:13}Asyn.TINP")


def dt_set_osc_width(w_degrees):
    comm_s = "p1="+str(w_degrees)
    set_gon_pv(comm_s)


def dt_set_osc_time(t_seconds): #output in milliseconds (t*1000)
#    comm_s = "p2="+str(t_seconds*1000)
    comm_s = "p2="+str(t_seconds)
    set_gon_pv(comm_s)


def dt_osc():
    comm_s = "&1 B1 R"
    set_gon_pv(comm_s)
    dt_done()

def dt_shutter(state): #0 = open, 1 = close
    comm_s = "m112="+repr(state)+" m111=1"
    set_gon_pv(comm_s)

def dt_shutter2(state): #0 = open, 1 = close
    comm_s = "m212="+repr(state)+" m211=1"
    set_gon_pv(comm_s)


def dt_home_omega():
    comm_s = "#1hm"
    set_gon_pv(comm_s)
    dt_done()

def dt_done():
    global dt_input, dt_output
    if (gon_offline):
      return
    pvPut(dt_input, "p99")
    time.sleep(.1)
    while(1):
        answer = pvGet(dt_output)
        print(answer)
        if (answer=='0\\r'):
          break
        time.sleep(.1)
        pvPut(dt_input, "p99")
    print("dt_done")

def dt_stop():
#    pvPut(dt_input, "!S")
    comm_s = "a"
    set_gon_pv(comm_s)
    comm_s = "p99=0"
    set_gon_pv(comm_s)


