####!/opt/conda_envs/lsdc_dev/bin/python
import daq_utils
import time
import os
import string

newBeamlineConfig = {}
tmpConfigFile = open("/nfs/skinner/projects/bnlpx_config/BLConfigsTemp/configJohnFmx.txt","r")
for line in tmpConfigFile.readlines():
  print(line)
  (key,val) = line.split()
#  (key,val) = string.split(line)  
  newBeamlineConfig[key]=val
tmpConfigFile.close()
daq_utils.setBeamlineConfigParams(newBeamlineConfig)
#os.system("rm " + tmpFileName)


          
