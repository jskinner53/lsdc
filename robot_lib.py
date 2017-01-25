#this will evolve for the staubli. Will need to know currently mounted sample. Will need to store this in the db.
#import staubliEpicsLib
#import stateModule
import RobotControlLib
import daq_utils
import db_lib
import time


global method_pv,var_pv,pinsPerPuck
pinsPerPuck = 16


def mountRobotSample(puckPos,pinPos,sampID):

  absPos = (pinsPerPuck*puckPos)+pinPos+1
#  if (stateModule.gotoState("SampleExchange")):  
  if (1):    
    print("mounting " + str(puckPos) + " " + str(pinPos) + " " + str(sampID))
    print("absPos = " + str(absPos))
    if (db_lib.getBeamlineConfigParam(daq_utils.beamline,'robot_online')):
      try:
        RobotControlLib.mount(absPos)
        return 1
      except Exception as e:
        print(e)
        return 0
    else:
      time.sleep(5)
    return 1
  else:
    return 0

def unmountRobotSample(puckPos,pinPos,sampID): #will somehow know where it came from

  absPos = (pinsPerPuck*puckPos)+pinPos+1
#  if (stateModule.gotoState("SampleExchange")):  
  if (1):    
    print("unmounting " + str(puckPos) + " " + str(pinPos) + " " + str(sampID))
    print("absPos = " + str(absPos))
    if (db_lib.getBeamlineConfigParam(daq_utils.beamline,'robot_online')):
      try:
        RobotControlLib.unmount(absPos)
        return 1
      except Exception as e:
        print(e)
        return 0        
    else:
      time.sleep(5)
    return 1
  else:
    return 0


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

