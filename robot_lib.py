#this will evolve for the staubli. Will need to know currently mounted sample. Will need to store this in the db.
import staubliEpicsLib
import stateModule


global method_pv,var_pv

def mountRobotSample(puckPos,pinPos,sampID):
  if (stateModule.gotoState("SampleExchange")):
    print "mounting " + str(puckPos) + " " + str(pinPos) + " " + str(sampID)
    return 1
  else:
    return 0

def unmountRobotSample(puckPos,pinPos,sampID): #will somehow know where it came from
  if (stateModule.gotoState("SampleExchange")):
    print "unmounting " + str(puckPos) + " " + str(pinPos) + " " + str(sampID)
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
  print "executing robot task"
  staubliEpicsLib.waitReady()
  print "done executing robot task"

