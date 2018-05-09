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
      RobotControlLib.finish()
      return 1    
    except Exception as e:
      print(e)
#      daq_lib.gui_message(e)
      return 0

def warmupGripper():
  RobotControlLib.warmupGripper()


def enableDewarTscreen():
  RobotControlLib.enableDewarPad()
  
def openPort(portNo):
  RobotControlLib.openPort(int(portNo))

def closePorts():
  RobotControlLib.closePorts()
  
def rebootEMBL():
  RobotControlLib.rebootEMBL()
  
def cooldownGripper():
  RobotControlLib.cooldownGripper()

def parkGripper():
  RobotControlLib.park()  
  
def mountRobotSample(puckPos,pinPos,sampID,init=0):
  global retryMountCount

#  absPos = (pinsPerPuck*puckPos)+pinPos+1
  absPos = (pinsPerPuck*(puckPos%3))+pinPos+1  
  if (db_lib.getBeamlineConfigParam(daq_utils.beamline,'robot_online')):
    if (daq_lib.setGovRobotSE()):
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
          RobotControlLib.park()
        except Exception as e:
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
          RobotControlLib._mount(absPos)          
        daq_lib.setGovRobotSA()
        return 1
      except Exception as e:
        print(e)
        e_s = str(e)
        if (e_s.find("Fatal") != -1):
          daq_macros.robotOff()                    
          daq_lib.gui_message(e_s + ". FATAL ROBOT ERROR - CALL STAFF! robotOff() executed.")
          return 0                    
        if (e_s.find("tilted") != -1):
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
              daq_lib.gui_message("Could not recover from tilted sample.")
              return 2
        return 0
      return 1
    else:
      print("could not go to SE")
      return 0
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
        RobotControlLib.park()
      except Exception as e:
        print(e)
        return 0
      beamline_lib.mvaDescriptor("dewarRot",rotMotTarget)
    try:
      RobotControlLib.unmount1()
    except Exception as e:
      print(e)
      return 0
    detDist = beamline_lib.motorPosFromDescriptor("detectorDist")
    if (detDist<200.0):
      beamline_lib.mvaDescriptor("detectorDist",200.0)
    if (beamline_lib.motorPosFromDescriptor("detectorDist") < 199.0):
      print("ERROR - Detector < 200.0!")
      return 0
    try:
      time.sleep(1.0)
      RobotControlLib.goHome()
    except Exception as e:
      print(e)
      return 0
    if (daq_lib.waitGovRobotSE()):
      try:
        RobotControlLib.unmount2(absPos)
      except Exception as e:
        e_s = str(e)
        if (e_s.find("Fatal") != -1):
          daq_macros.robotOff()                    
          daq_lib.gui_message(e_s + ". FATAL ROBOT ERROR - CALL STAFF! robotOff() executed.")
          return 0                    
        print(e)
        return 0
    else:
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

