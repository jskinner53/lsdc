#!/usr/bin/python
from db_lib import *
import time
for i in range (1,25):
  containerName = "Puck" + str(i)
  for j in range (0,16):
    sampleName = "samp_"+str(i)+"_"+str(j)
#    time.sleep(1)
    sampID = createSample(sampleName)
    insertIntoContainer(containerName,j,sampID)


