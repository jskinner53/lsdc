#!/usr/bin/python
import time
import string
import os
import beamline_support
from beamline_support import *


#the following is a list of things the machine is interested in, and their default vals at startup. PVs channels are created for these
#and stored in stateChannelDict, indexed by these var names.
stateVars = {"collimator":0.0,"aperature":0.0,"lamp":0,"beamStop":0.0}

stateDefinitions = [{"stateName":"Maintenance","stateDef":{},"safeTransitions":[{"stateName":"SampleExchange","transitionProc":"transProcM2SE"}]}, \
{"stateName":"BeamLocation","stateDef":{"collimator":{"hi":0.0,"low":0.0},"aperature":{"hi":0.0,"low":0.0},"lamp":{"hi":0.0,"low":0.0},"beamStop":{"hi":0.0,"low":0.0}}, "safeTransitions":[{"stateName":"SampleExchange","transitionProc":"transProcBL2SE"},{"stateName":"Maintenance","transitionProc":"transProcBL2M"}]}, \
{"stateName":"DataCollection","stateDef":{"collimator":{"hi":0.0,"low":0.0},"aperature":{"hi":0.0,"low":0.0},"lamp":{"hi":0.0,"low":0.0},"beamStop":{"hi":10.0,"low":10.0}},"safeTransitions":[{"stateName":"SampleAlignment","transitionProc":"transProcDC2SA"},{"stateName":"Maintenance","transitionProc":"transProcDC2SM"}]}, \
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

  for i in range (1,len(stateDefinitions)): #skipping maintenance for now
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
  print "trying to go to " + stateName
  machineState = getCurrentState()
  for i in range (0,len(machineState["safeTransitions"])):
    if (machineState["safeTransitions"][i]["stateName"] == stateName):
      print "OK to transition"
      print machineState["safeTransitions"][i]['transitionProc']
      exec machineState["safeTransitions"][i]['transitionProc']+"()"  
      return
  print "no transition for you"


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

        

def comm_cb(epics_args, user_args):
  global command_list,is_first
  
#  print waveform_to_string(epics_args['pv_value'])
  if (is_first == 0):
    command_list.append(waveform_to_string(epics_args['pv_value']))
  else:
    is_first = 0
  

def  process_input(s):
  input_tokens = string.split(s)
  if (len(input_tokens)>0):
    first_token = input_tokens[0]
    if (first_token == "q"): 
      sys.exit()
    else:
      if (len(input_tokens)>0):
        command_string = "%s(" % input_tokens[0]
        for i in range(1,len(input_tokens)):
          command_string = command_string + "\"" + input_tokens[i] + "\""
          if (i != (len(input_tokens)-1)):
            command_string = command_string + ","
        command_string = command_string + ")"
      try:
        print command_string
#        from my_macros import *
        exec command_string
      except NameError:
        error_string = "Unknown command: " + command_string
        print error_string
      except SyntaxError:
        print "Syntax error"
      except KeyError:
        print "Key error"
      except TypeError:
        print "Type error"



def main():

  init_var_channels()
  comm_pv = pvCreate(beamline + "_comm:stateCommand_s")
  add_callback(comm_pv,comm_cb,0)
  while 1:
    if (len(command_list) > 0):
      print "command list len " + str(len(command_list))
      process_input(command_list.pop(0))
      print "Command> "
    time.sleep(.1)
    getCurrentState()

main()



if __name__ == '__main__':
  main()








