#this will evolve for the staubli. Will need to know currently mounted sample. Will need to store this in the db.
#import staubliEpicsLib
#import stateModule

import RobotControlLib
import daq_utils
import db_lib
import daq_lib
import beamline_lib
import time
import daq_macros
import beamline_support


global method_pv,var_pv,pinsPerPuck
pinsPerPuck = 16

global retryMountCount
retryMountCount = 0

def finish():
  if (db_lib.getBeamlineConfigParam(daq_utils.beamline,'robot_online')):  
    try:
      RobotControlLib.runCmd("finish")
      return 1    
    except Exception as e:
      e_s = str(e)        
      daq_lib.gui_message("ROBOT Finish ERROR: " + e_s)        
      print(e)
#      daq_lib.gui_message(e)
      return 0

def recoverRobot():
  RobotControlLib.runCmd("recover")

def DewarAutoFillOn():
  RobotControlLib.runCmd("turnOnAutoFill")

def DewarAutoFillOff():
  RobotControlLib.runCmd("turnOffAutoFill")

def DewarHeaterOn():
  RobotControlLib.runCmd("dewarHeaterOn")
  
def DewarHeaterOff():
  RobotControlLib.runCmd("dewarHeaterOff")


def warmupGripper():
  RobotControlLib.runCmd("warmupGripper")


def enableDewarTscreen():
  RobotControlLib.runCmd("enableTScreen")
  
def openPort(portNo):
  RobotControlLib.openPort(int(portNo))

def closePorts():
  RobotControlLib.runCmd("closePorts")
  
def rebootEMBL():
  RobotControlLib.rebootEMBL()
  
def cooldownGripper():
  RobotControlLib.runCmd("cooldownGripper")

def parkGripper():
  RobotControlLib.runCmd("park")  
  
def mountRobotSample(puckPos,pinPos,sampID,init=0,warmup=0):
  global retryMountCount

#  absPos = (pinsPerPuck*puckPos)+pinPos+1
  absPos = (pinsPerPuck*(puckPos%3))+pinPos+1  
  if (db_lib.getBeamlineConfigParam(daq_utils.beamline,'robot_online')):
    if (not daq_lib.waitGovRobotSE()):
      daq_lib.setGovRobotSE()
    print("mounting " + str(puckPos) + " " + str(pinPos) + " " + str(sampID))
    print("absPos = " + str(absPos))
    platePos = int(puckPos/3)
    rotMotTarget = daq_utils.dewarPlateMap[platePos][0]
    rotCP = beamline_lib.motorPosFromDescriptor("dewarRot")
    print("dewar target,CP")
    print(rotMotTarget,rotCP)
    if (abs(rotMotTarget-rotCP)>1):
      print("rot dewar")
      try:
        if (init == 0):
          RobotControlLib.runCmd("park")
      except Exception as e:
        e_s = str(e)        
        daq_lib.gui_message("ROBOT Park ERROR: " + e_s)                  
        print(e)
        return 0
      beamline_lib.mvaDescriptor("dewarRot",rotMotTarget)
    try:
      if (init):
        beamline_support.setPvValFromDescriptor("boostSelect",0)
        if (beamline_support.getPvValFromDescriptor("sampleDetected") == 0): #reverse logic, 0 = true
          beamline_support.setPvValFromDescriptor("boostSelect",1)
        else:
#            if (beamline_support.getPvValFromDescriptor("gripTemp") > 20.0): #gripper warm
          robotStatus = beamline_support.get_any_epics_pv("SW:RobotState","VAL")
          if (robotStatus != "Ready"):
            if (daq_utils.beamline == "fmx"):
              daq_macros.homePins()
              time.sleep(3.0)
            if (not daq_lib.setGovRobotSE()):
              return
        RobotControlLib.mount(absPos)
      else:
        if (warmup):
          RobotControlLib._mount(absPos,warmup=True)
        else:
          RobotControlLib._mount(absPos)                    
      daq_lib.setGovRobotSA()
      return 1
    except Exception as e:
      print(e)
      e_s = str(e)
      if (e_s.find("Fatal") != -1):
        daq_macros.robotOff()
        daq_macros.disableMount()
        daq_lib.gui_message(e_s + ". FATAL ROBOT ERROR - CALL STAFF! robotOff() executed.")
        return 0                    
      if (e_s.find("tilted") != -1 or e_s.find("Load Sample Failed") != -1):
        if (db_lib.getBeamlineConfigParam(daq_utils.beamline,"queueCollect") == 0):          
          daq_lib.gui_message(e_s + ". Try mounting again")
          return 0            
        else:
          if (retryMountCount == 0):
            retryMountCount+=1
            mountStat = mountRobotSample(puckPos,pinPos,sampID,init)
            if (mountStat == 1):
              retryMountCount = 0
            return mountStat
          else:
            retryMountCount = 0
            daq_lib.gui_message("ROBOT: Could not recover from " + e_s)
            return 2
      daq_lib.gui_message("ROBOT mount ERROR: " + e_s)
      return 0
    return 1
  else:
    return 1

def unmountRobotSample(puckPos,pinPos,sampID): #will somehow know where it came from

#  absPos = (pinsPerPuck*puckPos)+pinPos+1
  absPos = (pinsPerPuck*(puckPos%3))+pinPos+1  
  robotOnline = db_lib.getBeamlineConfigParam(daq_utils.beamline,'robot_online')
  print("robot online = " + str(robotOnline))
  if (robotOnline):
    detDist = beamline_lib.motorPosFromDescriptor("detectorDist")    
    if (detDist<199.0):
      beamline_support.setPvValFromDescriptor("govRobotDetDistOut",200.0)
      beamline_support.setPvValFromDescriptor("govHumanDetDistOut",200.0)          
    daq_lib.setRobotGovState("SE")    
    print("unmounting " + str(puckPos) + " " + str(pinPos) + " " + str(sampID))
    print("absPos = " + str(absPos))
    platePos = int(puckPos/3)
    rotMotTarget = daq_utils.dewarPlateMap[platePos][0]
    rotCP = beamline_lib.motorPosFromDescriptor("dewarRot")
    print("dewar target,CP")
    print(rotMotTarget,rotCP)
    if (abs(rotMotTarget-rotCP)>1):
      print("rot dewar")
      try:
        RobotControlLib.runCmd("park")
      except Exception as e:
        e_s = str(e)        
        daq_lib.gui_message("ROBOT park ERROR: " + e_s)        
        print(e)
        return 0
      beamline_lib.mvaDescriptor("dewarRot",rotMotTarget)
    try:
      par_init=(beamline_support.get_any_epics_pv("SW:RobotState","VAL")!="Ready")
      par_cool=(beamline_support.getPvValFromDescriptor("gripTemp")>-170)
      if par_cool == False and daq_utils.beamline == "fmx": 
        time.sleep(3)
      RobotControlLib.unmount1(init=par_init,cooldown=par_cool)
    except Exception as e:
      e_s = str(e)        
      daq_lib.gui_message("ROBOT unmount ERROR: " + e_s)        
      print(e)
      return 0
    detDist = beamline_lib.motorPosFromDescriptor("detectorDist")
    if (detDist<200.0):
      beamline_lib.mvaDescriptor("detectorDist",200.0)
    if (beamline_lib.motorPosFromDescriptor("detectorDist") < 199.0):
      print("ERROR - Detector < 200.0!")
      return 0
    try:
      RobotControlLib.unmount2(absPos)
    except Exception as e:
      e_s = str(e)
      if (e_s.find("Fatal") != -1):
        daq_macros.robotOff()
        daq_macros.disableMount()          
        daq_lib.gui_message(e_s + ". FATAL ROBOT ERROR - CALL STAFF! robotOff() executed.")
        return 0
      daq_lib.gui_message("ROBOT unmount2 ERROR: " + e_s)        
      print(e)
      return 0
    if (not daq_lib.waitGovRobotSE()):
      daq_lib.clearMountedSample()
      print("could not go to SE")    
      return 0
  return 1



def initStaubliControl():
  global method_pv,var_pv
  method_pv = staubliEpicsLib.MethodPV("SW:startRobotTask")
  var_pv = staubliEpicsLib.MethodPV("SW:setRobotVariable")

def testRobotComm(numTurns=0):
  if (numTurns>0):
    var_pv.execute("nCamDelay",numTurns)
  method_pv.execute("Test",50000)
  print("executing robot task")
  staubliEpicsLib.waitReady()
  print("done executing robot task")

