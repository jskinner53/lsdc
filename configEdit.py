#!/usr/bin/python
import daq_utils
import time
import os
import string

beamlineConfig = daq_utils.getAllBeamlineConfigParams()
tmpFileName = "/tmp/blConfig"+str(time.time())
tmpConfigFile = open(tmpFileName,"w+")
for key in beamlineConfig.keys():
  tmpConfigFile.write(key + " " + str(beamlineConfig[key]) + "\n")
tmpConfigFile.close()
comm_s = "emacs -nw " + tmpFileName
os.system(comm_s)
newBeamlineConfig = {}
tmpConfigFile = open(tmpFileName,"r")
for line in tmpConfigFile.readlines():
#  print line
  (key,val) = string.split(line)
  newBeamlineConfig[key]=val
tmpConfigFile.close()
daq_utils.setBeamlineConfigParams(newBeamlineConfig)
os.system("rm " + tmpFileName)



