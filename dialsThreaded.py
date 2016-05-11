#!/opt/conda_envs/lsdc_dev/bin/ipython
import thread
import os
import xmltodict
import time

global dialsResultDict, rasterRowResultsList, processedRasterRowCount

dialsResultDict = {}
rasterRowResultsList = []



def runDialsThread(pattern,rowIndex):
  global rasterRowResultsList,processedRasterRowCount
#  comm_s = ssh -q xf17id1-srv1 "ls -rt /nfs/skinner/testdata/Eiger1M/tryp2s_01deg_01sec_1_1*.cbf|/usr/local/crys/dials-installer-dev-316-intel-linux-2.6-x86_64-centos5/build/bin/dials.find_spots_client"
  comm_s = "ssh -q cpu-004 \"ls -rt " + pattern + "|/usr/local/crys-local/dials-v1-1-4/build/bin/dials.find_spots_client\""
#  comm_s = "ssh -q xf17id1-srv1 \"ls -rt " + pattern + "|/usr/local/crys/dials-installer-dev-316-intel-linux-2.6-x86_64-centos5/build/bin/dials.find_spots_client\""  
#  print comm_s
  localDialsResultDict = xmltodict.parse("<data>\n"+os.popen(comm_s).read()+"</data>\n")
  print "\n"
  print localDialsResultDict
  print "\n"  
  rasterRowResultsList[rowIndex] = xmltodict.parse("<data>\n"+os.popen(comm_s).read()+"</data>\n")
  processedRasterRowCount+=1
#  rasterRowResultsList.append(xmltodict.parse("<data>\n"+os.popen(comm_s).read()+"</data>\n"))
  


def doit():
  global dialsResultDict,rasterRowResultsList,processedRasterRowCount
  rowCount = 5
  rasterRowResultsList = [{} for i in xrange(rowCount)]
  processedRasterRowCount = 0
  for i in range (0,rowCount):
    pattern = "/nfs/skinner/testdata/Eiger1M/tryp2s_01deg_01sec_1_0"+str(i)+"*.cbf"
#  pattern = "/nfs/skinner/testdata/Eiger1M/tryp2s_01deg_01sec_1_"+str(i)+"*.cbf"  
    thread.start_new_thread(runDialsThread,(pattern,i,))
#need to wait for results and concatenate them.
  while (1):
    time.sleep(1)
    print processedRasterRowCount
    if (processedRasterRowCount == rowCount):
      break
  for i in range (0,len(rasterRowResultsList)):
#    dialsResultDict = dialsResultDict.items() + rasterRowResultsList[i].items()
#    print rasterRowResultsList[i]

    print rasterRowResultsList[i]


doit()

