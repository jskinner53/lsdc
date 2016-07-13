#!/opt/conda_envs/lsdc_dev/bin/ipython -i
import daq_utils
import time
import os
import string

newBeamlineConfig = {}
tmpConfigFile = open("./beamlineConfigMDS.txt","r")
for line in tmpConfigFile.readlines():
  print line
  (key,val) = string.split(line)
  newBeamlineConfig[key]=val
tmpConfigFile.close()
daq_utils.setBeamlineConfigParams(newBeamlineConfig)
#os.system("rm " + tmpFileName)


          
