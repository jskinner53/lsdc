#!/usr/bin/python
import time
import string
import os
import _thread
from epics import PV
#import beamline_support
#from beamline_support import *


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
global beamlineStateChannel
beamlineStateChannel = None
#beamline = "john"
#global beamlineComm #this is the comm_ioc
#beamlineComm = "XF:17IDC-ES:FMX{Comm}"

global command_list,is_first
command_list = []

is_first = 1

def getCurrentState():
  global beamlineStateChannel

  for i in range(1,len(stateDefinitions)): #skipping maintenance for now
    stateTest = 1
    for key in list(stateDefinitions[i]["stateDef"].keys()):
      high = stateDefinitions[i]["stateDef"][key]["low"]
      low = stateDefinitions[i]["stateDef"][key]["hi"]
      if (stateVars[key] <= high and stateVars[key] >= low):
        pass
      else:
        stateTest = 0
        break
    if (stateTest == 1):
      beamlineStateChannel.put(i)
      return stateDefinitions[i]   # if I made it here, then I passed all of the tests for a state
  beamlineStateChannel.put(0)
  return stateDefinitions[0] # if I made it here, then none of the states passed all tests, so it must be maintenance
    

def gotoState(stateName):
  machineState = getCurrentState()
  machineStateName = machineState["stateName"]
  if (machineStateName == stateName):
    return 1
  print("trying to go to " + stateName + " from " + machineStateName)
  for i in range(len(machineState["safeTransitions"])):
    if (machineState["safeTransitions"][i]["stateName"] == stateName):
      print("OK to transition")
#      print(machineState["safeTransitions"][i]['transitionProc'])
      exec(machineState["safeTransitions"][i]['transitionProc']+"()")  
      return 1
  return 1


def transProcM2SE():
  print("transition Maintenance to Sample Exchange")
  var_channel_list["beamStop"].put(11)  
  var_channel_list["aperature"].put(0)


def transProcSE2SA():
  print("transition Sample Exchange to Sample Alignment")
  var_channel_list["beamStop"].put(0)
  var_channel_list["aperature"].put(20)

def transProcSA2SE():
  print("transition Sample Alignment to Sample Exchange")
  var_channel_list["beamStop"].put(11)
  var_channel_list["aperature"].put(0)

def transProcSA2DC():
  print("transition Sample Alignment to Data Collection")
  var_channel_list["beamStop"].put(10)
  var_channel_list["aperature"].put(0)


def transProcDC2SA():
  print("transition Data Collection to Sample Alignment")
  var_channel_list["beamStop"].put(0)
  var_channel_list["aperature"].put(20)


def transProcDC2SE():
  print("transition Data Collection to Sample Exchange")
  var_channel_list["beamStop"].put(11)
  var_channel_list["aperature"].put(0)


def transProcBL2SE():
  print("transition Beam Location to Sample Exchange")
  var_channel_list["beamStop"].put(11)


def init_var_channels(beamlineComm):
  global var_channel_list,beamlineStateChannel

  beamlineStateChannel = PV(beamlineComm + "beamlineState")
  beamlineStateChannel.put(0)
  for varname in list(stateVars.keys()):
    var_channel_list[varname] = PV(beamlineComm  + varname)
#    beamline_support.pvPut(var_channel_list[varname],stateVars[varname])
    var_channel_list[varname].add_callback(var_list_item_changeCb,varname=varname)    


def var_list_item_changeCb(value=None, char_value=None, **kw):
##  print("in callback " + char_value + " " + kw["varname"])

  #  if (ca.dbf_text(epics_args['type']) == "DBF_CHAR"):
#    stateVars[user_args[0]] = beamline_support.waveform_to_string(epics_args['pv_value'])
#  else:

  stateVars[kw["varname"]] = value
##  print(stateVars)

        
def stateEvalThread(frequency):
  while (1):
    time.sleep(frequency)
    getCurrentState()    


def initStateControl(beamlineComm):
  init_var_channels(beamlineComm)
  _thread.start_new_thread(stateEvalThread,(.5,))     

