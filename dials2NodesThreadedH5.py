#!/usr/bin/python
##!/opt/conda_envs/lsdc_dev/bin/ipython
import thread
import os
import xmltodict
import time

global dialsResultDict, rasterRowResultsList, processedRasterRowCount

dialsResultDict = {}
rasterRowResultsList = []



def runDialsThread(Hpattern,CBFpattern,rowIndex,rowCellCount):
  global rasterRowResultsList,processedRasterRowCount

  if (rowIndex%2 == 0):
    node = "cpu-004"
  else:
    node = "cpu-005"    
  hdfRowFilepattern = Hpattern + str(rowIndex) + "_master.h5"
  CBF_conversion_pattern = CBFpattern+str(rowIndex)+"_"
#normally use the cbf converter to get the frame count here, but we'll just harcode it for now, but we'll call it anyway
#  comm_s = "/usr/local/crys-local/bin/eiger2cbf-linux " + hdfRowFilepattern
#  os.system(comm_s)
  comm_s = "/usr/local/crys-local/bin/eiger2cbf-linux " + hdfRowFilepattern  + " 1:" + str(rowCellCount) + " " + CBF_conversion_pattern
#  os.system(comm_s)
  CBFpattern = CBF_conversion_pattern + "*.cbf"
  comm_s = "ls -rt " + CBFpattern + ">/dev/null"
  time.sleep(3.0)
  os.system(comm_s)  
   
#  comm_s = "ls -rt " + CBFpattern + "|/usr/local/crys-local/dials-v1-2-0/build/bin/dials.find_spots_client region_of_interest=1555,2585,1653,2718 host=" + node #center 1
#  comm_s = "ls -rt " + CBFpattern + "|/usr/local/crys-local/dials-v1-2-0/build/bin/dials.find_spots_client region_of_interest=1040,3110,1102,3369  host=" + node #center 4
  comm_s = "ls -rt " + CBFpattern + "|/usr/local/crys-local/dials-v1-2-0/build/bin/dials.find_spots_client host=" + node  
####  comm_s = "ssh -q cpu-004 \"ls -rt " + pattern + "|/usr/local/crys-local/dials-v1-1-4/build/bin/dials.find_spots_client\""  
#  print comm_s
#  print(os.popen(comm_s).read())
#  return
  localDialsResultDict = xmltodict.parse("<data>\n"+os.popen(comm_s).read()+"</data>\n")
  print "\n"
  print localDialsResultDict
  print "\n"  
  rasterRowResultsList[rowIndex-1] = xmltodict.parse("<data>\n"+os.popen(comm_s).read()+"</data>\n")
  processedRasterRowCount+=1
  


def doit():
  global dialsResultDict,rasterRowResultsList,processedRasterRowCount
  HfilePattern = "/GPFS/CENTRAL/XF17ID1/skinner/eiger16M/insu6_"
  CBFfilePattern = "/GPFS/CENTRAL/XF17ID1/skinner/eiger16M/cbf/insu6_"  
  rowCount = 9
  rowCellCount = 100
  rasterRowResultsList = [{} for i in xrange(rowCount)]  
  processedRasterRowCount = 0
  for i in range (1,rowCount+1):
    thread.start_new_thread(runDialsThread,(HfilePattern,CBFfilePattern,i,rowCellCount,))
#    time.sleep(5)
#  return #SHORT CIRCUIT
#need to wait for results and concatenate them.
  while (1):
    time.sleep(1)
    print processedRasterRowCount
    if (processedRasterRowCount == rowCount):
      break
  for i in range (0,len(rasterRowResultsList)):
#    dialsResultDict = dialsResultDict.items() + rasterRowResultsList[i].items()

    print rasterRowResultsList[i]
  for i in range (0,len(rasterRowResultsList)):
    print(str(i) + " " + str(len(rasterRowResultsList[i])))


doit()

