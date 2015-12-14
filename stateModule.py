#!/usr/bin/python
import time
import string
import os
import thread
import beamline_support
from beamline_support import *


#the following is a list of things the machine is interested in, and their default vals at startup. PVs channels are created for these
#and stored in stateChannelDict, indexed by these var names.
stateVars = {"collimator":0.0,"aperature":0.0,"lamp":0,"beamStop":0.0}

stateDefinitions = [{"stateName":"Maintenance","stateDef":{},"safeTransitions":[{"stateName":"SampleExchange","transitionProc":"transProcM2SE"}]}, \
{"stateName":"BeamLocation","stateDef":{"collimator":{"hi":0.0,"low":0.0},"aperature":{"hi":0.0,"low":0.0},"lamp":{"hi":0.0,"low":0.0},"beamStop":{"hi":0.0,"low":0.0}}, "safeTransitions":[{"stateName":"SampleExchange","transitionProc":"transProcBL2SE"},{"stateName":"Maintenance","transitionProc":"transProcBL2M"}]}, \
{"stateName":"DataCollection","stateDef":{"collimator":{"hi":0.0,"low":0.0},"aperature":{"hi":0.0,"low":0.0},"lamp":{"hi":0.0,"low":0.0},"beamStop":{"hi":10.0,"low":10.0}},"safeTransitions":[{"stateName":"SampleAlignment","transitionProc":"transProcDC2SA"},{"stateName":"Maintenance","transitionProc":"transProcDC2SM"},{"stateName":"SampleExchange","transitionProc":"transProcDC2SE"}]}, \
{"stateName":"SampleAlignment","stateDef":{"collimator":{"hi":0.0,"low":0.0},"aperature":{"hi":20.0,"low":20.0},"lamp":{"hi":0.0,"low":0.0},"beamStop":{"hi":0.0,"low":0.0}},"safeTransitions":[{"stateName":"SampleExchange","transitionProc":"transProcSA2SE"},{"stateName":"DataCollection","transitionProc":"transProcSA2DC"},{"stateName":"Maintenance","transitionProc":"transProcSA2SM"}]}, \
{"stateName":"SampleExchange","stateDef":{"collimator":{"hi":0.0,"low":0.0},"aperature":{"hi":0.0,"low":0.0},"lamp":{"hi":0.0,"low":0.0},"beamStop":{"hi":11.0,"low":20.0}},"safeTransitions":[{"stateName":"SampleAlignment","transitionProc":"transProcSE2SA"},{"stateName":"BeamLocation","transitionProc":"transProcSE2BL"},{"stateName":"Maintenance","transitionProc":"transProcSE2M"}]}]


global var_channel_list
var_channel_list = {}
global beamline, beamlineStateChannel
beamlineStateChannel = None
beamline = "john"

global command_list,is_first
command_list = []

is_first = 1

def getCurrentState():
  global beamlineStateChannel

  for i in xrange(1,len(stateDefinitions)): #skipping maintenance for now
    stateTest = 1
    for key in stateDefinitions[i]["stateDef"].keys():
      high = stateDefinitions[i]["stateDef"][key]["low"]
      low = stateDefinitions[i]["stateDef"][key]["hi"]
      if (stateVars[key] <= high and stateVars[key] >= low):
        pass
      else:
        stateTest = 0
        break
    if (stateTest == 1):
      beamline_support.pvPut(beamlineStateChannel,i)
      return stateDefinitions[i]   # if I made it here, then I passed all of the tests for a state
  beamline_support.pvPut(beamlineStateChannel,0)
  return stateDefinitions[0] # if I made it here, then none of the states passed all tests, so it must be maintenance
    

def gotoState(stateName):
  machineState = getCurrentState()
  machineStateName = machineState["stateName"]
  if (machineStateName == stateName):
    return 1
  print "trying to go to " + stateName + " from " + machineStateName
  for i in xrange(len(machineState["safeTransitions"])):
    if (machineState["safeTransitions"][i]["stateName"] == stateName):
      print "OK to transition"
      print machineState["safeTransitions"][i]['transitionProc']
      exec machineState["safeTransitions"][i]['transitionProc']+"()"  
      return 1
  return 0


def transProcM2SE():
  print "transition Maintenance to Sample Exchange"


def transProcSE2SA():
  print "transition Sample Exchange to Sample Alignment"
  pvPut(var_channel_list["beamStop"],0)
  pvPut(var_channel_list["aperature"],20)

def transProcSA2SE():
  print "transition Sample Alignment to Sample Exchange"
  pvPut(var_channel_list["beamStop"],11)
  pvPut(var_channel_list["aperature"],0)

def transProcSA2DC():
  print "transition Sample Alignment to Data Collection"
  pvPut(var_channel_list["beamStop"],10)
  pvPut(var_channel_list["aperature"],0)


def transProcDC2SA():
  print "transition Data Collection to Sample Alignment"
  pvPut(var_channel_list["beamStop"],0)
  pvPut(var_channel_list["aperature"],20)


def transProcDC2SE():
  print "transition Data Collection to Sample Exchange"
  pvPut(var_channel_list["beamStop"],11)
  pvPut(var_channel_list["aperature"],0)




def transProcBL2SE():
  print "transition Beam Location to Sample Exchange"
  pvPut(var_channel_list["beamStop"],11)


def init_var_channels():
  global var_channel_list,beamlineStateChannel

  beamlineStateChannel = beamline_support.pvCreate(beamline + "_comm:beamlineState")
  beamline_support.pvPut(beamlineStateChannel,0)
  for varname in stateVars.keys():
    var_channel_list[varname] = beamline_support.pvCreate(beamline + "_comm:" + varname)
#    beamline_support.pvPut(var_channel_list[varname],stateVars[varname])
    add_callback(var_channel_list[varname],var_list_item_changeCb,varname)    


def var_list_item_changeCb(epics_args, user_args):
  print "in callback " + str(epics_args['pv_value']) + " " + user_args[0]
  if (ca.dbf_text(epics_args['type']) == "DBF_CHAR"):
    stateVars[user_args[0]] = beamline_support.waveform_to_string(epics_args['pv_value'])
  else:
    stateVars[user_args[0]] = epics_args['pv_value']
  print stateVars

        
def stateEvalThread(frequency):
  while (1):
    time.sleep(frequency)
    getCurrentState()    


def initStateControl():
  init_var_channels()
  thread.start_new_thread(stateEvalThread,(.5,))     

