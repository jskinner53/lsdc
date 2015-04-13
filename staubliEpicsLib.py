from beamline_support import *
import time


################################################
#Acessing regular PVs (getter/setters)
################################################

################################################
#Calling Method PVs 
################################################
NO_PARAMETERS = "__EMPTY__"

class MethodPV():

    def __init__(self, pvName):
      self.robotTaskPV = pvCreate(pvName)

    def execute(self,*args):        
        if len(args)==0:
            pars = [NO_PARAMETERS,]
        else:
            pars=[]
            for arg in args:
                pars.append(str(arg))
        
        #Python implementation does not support writing a an array if return is a single value
        if (len(pars)>1):
            pvPut(self.robotTaskPV,pars) 
            ret = pvGet(self.robotTaskPV)[0]
        else:
            pvPut(self.robotTaskPV,pars[0]) 
            ret = pvGet(self.robotTaskPV)
#        if self.severity!=0:
#            raise Exception(ret)
        return ret




################################################
#Sincronizing Activities
################################################

def waitReady(timeout=-1):    
    state = pvCreate("SW:State")
    start=time.clock()
    while True:
        if pvGet(state) not in ("Running","Moving","Busy","Initialize"):
            break
        if (timeout>=0) and ((time.clock() - start) > timeout):
            raise Exception("Timeout waiting ready")
        time.sleep(0.01)

def isTaskRunning(id):    
    pv = MethodPV("SW:isTaskRunning")
    return pv.execute(id)
   

#method_pv=MethodPV("SW:startRobotTask")
#task_id = method_pv.execute("Test",50000)


#print "Task ID = " + str(task_id)
#print "Task Status = " + str(epics.PV("SW:LastTaskInfo").get())
#print "Task Running = " + isTaskRunning(task_id)

#waitReady()

#print "Task Status = " + str(epics.PV("SW:LastTaskInfo").get())
#print "Task Running = " + isTaskRunning(task_id)


