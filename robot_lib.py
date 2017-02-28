#this will evolve for the staubli. Will need to know currently mounted sample. Will need to store this in the db.
#import staubliEpicsLib
#import stateModule
import RobotControlLib
import daq_utils
import db_lib
import daq_lib
import time


global method_pv,var_pv,pinsPerPuck
pinsPerPuck = 16


def finish():
  if (db_lib.getBeamlineConfigParam(daq_utils.beamline,'robot_online')):  
    try:
      RobotControlLib.finish()
      return 1    
    except Exception as e:
      print(e)
      return 0

  
def mountRobotSample(puckPos,pinPos,sampID,init=0):

  absPos = (pinsPerPuck*puckPos)+pinPos+1
  if (db_lib.getBeamlineConfigParam(daq_utils.beamline,'robot_online')):
    if (daq_lib.setGovRobotSE()):
      print("mounting " + str(puckPos) + " " + str(pinPos) + " " + str(sampID))
      print("absPos = " + str(absPos))

      try:
        if (init):
          RobotControlLib.mount(absPos)
        else:
          RobotControlLib._mount(absPos)          
        daq_lib.setGovRobotSA()
        return 1
      except Exception as e:
        print(e)
        return 0
      else:
        time.sleep(5)
      return 1
    else:
      print("could not go to SE")
      return 0
  else:
    return 1

def unmountRobotSample(puckPos,pinPos,sampID): #will somehow know where it came from

  absPos = (pinsPerPuck*puckPos)+pinPos+1
  if (db_lib.getBeamlineConfigParam(daq_utils.beamline,'robot_online')):  
    if (daq_lib.setGovRobotSE()):
      print("unmounting " + str(puckPos) + " " + str(pinPos) + " " + str(sampID))
      print("absPos = " + str(absPos))

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
      print("could not go to SE")    
      return 0
  else:
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

