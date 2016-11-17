#!/opt/conda_envs/lsdc_dev3/bin/python
##!/usr/bin/python
import time
import os
import sys
import db_lib
import xmltodict
import daq_utils


def generateSpotsFileFromXMLObsolete(fastdpXmlFilename="fast_dp.xml"): #no idea what this is - 6/16

  tree = ET.parse(fastdpXmlFilename)
  root = tree.getroot()
  for i in range (0,len(root)):
    dataFileName = root[i].find("image").text
    spots = int(root[i].find("spot_count").text)
    grid_spots_file.write("%d %s\n" % (spots,dataFileName))
  grid_spots_file.close()  


directory = sys.argv[1]
runningDir = directory+"/fastDPOutput"
comm_s = "mkdir -p " + runningDir
os.system(comm_s)
os.chdir(runningDir)
filePrefix = sys.argv[2]
numstart = int(sys.argv[3])
numimages = int(sys.argv[4])
request_id = int(sys.argv[5])
runFastEP = int(sys.argv[6])
expectedFilenameList = []
timeoutLimit = 600 #for now
prefix_long = directory+"/"+filePrefix
for i in range (numstart,numstart+numimages):
  filename = daq_utils.create_filename(prefix_long,i)
  expectedFilenameList.append(filename)
#for i in range (0,len(expectedFilenameList)):
#  print expectedFilenameList[i]
timeout_check = 0
while(not os.path.exists(expectedFilenameList[len(expectedFilenameList)-1])): #this waits for images
  timeout_check = timeout_check + 1
  time.sleep(1.0)
  if (timeout_check > timeoutLimit):
    break
node = "cpu-004"
comm_s = "ssh  -q " + node + " \"cd " + runningDir +";source /nfs/skinner/wrappers/fastDPWrap;fast_dp -1 3 " + expectedFilenameList[0] + "\""  
#comm_s = "fast_dp " + expectedFilenameList[0] #note this the first image
print(comm_s)
os.system(comm_s)
fd = open("fast_dp.xml")
#nresult = {}
#result["timestamp"] = time.time()
#result["type"] = "fastDP"
resultObj = xmltodict.parse(fd.read())
#result["resultObj"] = resultObj
db_lib.addResultforRequest("fastDP",request_id,resultObj)
print("finished fast_dp")
if (runFastEP):
  comm_s = "ssh  -q " + node + " \"cd " + runningDir +";source /nfs/skinner/wrappers/fastDPWrap;fast_ep"
  print("running fast_ep")
  os.system(comm_s)




