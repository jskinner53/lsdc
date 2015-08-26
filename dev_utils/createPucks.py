#!/usr/bin/python

from db_lib import *
import time

for i in range (1,25):
  containerName = "Puck" + str(i)
  createContainer(containerName,"puck",16)
