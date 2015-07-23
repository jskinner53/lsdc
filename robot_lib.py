#this will evolve for the staubli. Will need to know currently mounted sample. Will need to store this in the db.
import staubliEpicsLib


global method_pv,var_pv

def mountRobotSample(puckPos,pinPos,sampID):
  print "mounting " + str(puckPos) + " " + str(pinPos) + " " + str(sampID)

def unmountRobotSample(puckPos,pinPos,sampID): #will somehow know where it came from
  print "unmounting " + str(puckPos) + " " + str(pinPos) + " " + str(sampID)


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

