#!/opt/conda_envs/lsdc_dev/bin/python
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
#looks like you could add new stuff like so for each new key:
#newBeamlineConfig["primaryDewarName"] = "primaryDewarAMX"
#newBeamlineConfig["lowMagCamURL"] = "http://xf17id2b-ioc2.cs.nsls2.local:8007/C2.MJPG.mjpg"
#newBeamlineConfig["lowMagZoomCamURL"] = "http://xf17id2b-ioc2.cs.nsls2.local:8007/C1.MJPG.mjpg"
#newBeamlineConfig["highMagZoomCamURL"] = "http://xf17id2b-ioc2.cs.nsls2.local:8007/C1.MJPG.mjpg"
#newBeamlineConfig["highMagCamURL"] = "http://xf17id2b-ioc2.cs.nsls2.local:8007/C2.MJPG.mjpg"
tmpConfigFile.close()
daq_utils.setBeamlineConfigParams(newBeamlineConfig)
#os.system("rm " + tmpFileName)



