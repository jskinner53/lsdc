#!/opt/conda_envs/lsdc_dev/bin/python
import db_lib
import time
import os
import string
import sys

beamline_id = sys.argv[1]
beamlineConfigList = db_lib.getAllBeamlineConfigParams(beamline_id)
tmpFileName = "/tmp/blConfig"+str(time.time())
tmpConfigFile = open(tmpFileName,"w+")
for i in range (0,len(beamlineConfigList)):
  infoName = beamlineConfigList[i]['info_name']
  info = beamlineConfigList[i]['info']
  if ("val" in info.keys()):
    tmpConfigFile.write(infoName + " " + str(info["val"]) + "\n")
tmpConfigFile.close()
#exit(0)
comm_s = "emacs -nw " + tmpFileName
os.system(comm_s)
tmpConfigFile = open(tmpFileName,"r")
for line in tmpConfigFile.readlines():
  print line
  (key,val) = line.split()
#  (key,val) = string.split(line)  
  db_lib.setBeamlineConfigParam(beamline_id, key, val)
tmpConfigFile.close()
#os.system("rm " + tmpFileName)



