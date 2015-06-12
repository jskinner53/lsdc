#!/usr/bin/python

import time
import mongoengine

from db_lib import *


for i in range (1,25):
  containerName = "Puck" + str(i)
  for j in range (0,16):
    sampleName = "samp_"+str(i)+"_"+str(j)

    try:
      sampID = createSample(sampleName)
    except mongoengine.NotUniqueError:
      raise mongoengine.NotUniqueError('{0}'.format(sampleName))

    insertIntoContainer(containerName, j, sampID)
