import time
#import string
import os
from math import *
import requests
import xmltodict

#import metadatastore.commands as mdsc

#import beamline_support
import db_lib

#global det_radius
#det_radius = 0
global beamline
beamline = os.environ["BEAMLINE_ID"]
#beamline = "john"
global beamlineComm #this is the comm_ioc
beamlineComm = ""
#beamlineComm = "XF:17IDC-ES:FMX{Comm}"
global searchParams
global motor_dict,counter_dict,scan_list,soft_motor_list,pvLookupDict
global detector_id
detector_id = ""
pvLookupDict = {}
motor_dict = {}
counter_dict = {}
scan_list = []
soft_motor_list = []
global screenYCenterPixelsLowMagOffset
screenYCenterPixelsLowMagOffset = 58



def init_environment():
  global beamline,detector_id,mono_mot_code,has_beamline,has_xtalview,xtal_url,xtal_url_small,xtalview_user,xtalview_pass,det_type,has_dna,beamstop_x_pvname,beamstop_y_pvname,camera_offset,det_radius,lowMagFOVx,lowMagFOVy,highMagFOVx,highMagFOVy,lowMagPixX,lowMagPixY,highMagPixX,highMagPixY,screenPixX,screenPixY,screenPixCenterX,screenPixCenterY,screenProtocol,screenPhist,screenPhiend,screenWidth,screenDist,screenExptime,screenWave,screenReso,gonioPvPrefix,searchParams,screenEnergy,detectorOffline,imgsrv_host,imgsrv_port,beamlineComm,primaryDewarName,lowMagCamURL,highMagZoomCamURL,lowMagZoomCamURL,highMagCamURL,owner


  owner = db_lib.getBeamlineConfigParam(beamline,"user")
  primaryDewarName = db_lib.getBeamlineConfigParam(beamline,"primaryDewarName")
  db_lib.setPrimaryDewarName(primaryDewarName)
  lowMagCamURL = db_lib.getBeamlineConfigParam(beamline,"lowMagCamURL")
  highMagCamURL = db_lib.getBeamlineConfigParam(beamline,"highMagCamURL")
  highMagZoomCamURL = db_lib.getBeamlineConfigParam(beamline,"highMagZoomCamURL")
  lowMagZoomCamURL = db_lib.getBeamlineConfigParam(beamline,"lowMagZoomCamURL")
  lowMagFOVx = float(db_lib.getBeamlineConfigParam(beamline,"lowMagFOVx"))
  lowMagFOVy = float(db_lib.getBeamlineConfigParam(beamline,"lowMagFOVy"))
  highMagFOVx = float(db_lib.getBeamlineConfigParam(beamline,"highMagFOVx")) #digizoom will be this/2
  highMagFOVy = float(db_lib.getBeamlineConfigParam(beamline,"highMagFOVy"))
  lowMagPixX = float(db_lib.getBeamlineConfigParam(beamline,"lowMagPixX")) #for automated images
  lowMagPixY = float(db_lib.getBeamlineConfigParam(beamline,"lowMagPixY"))
  highMagPixX = float(db_lib.getBeamlineConfigParam(beamline,"highMagPixX")) #for automated images
  highMagPixY = float(db_lib.getBeamlineConfigParam(beamline,"highMagPixY"))
  screenPixX = float(db_lib.getBeamlineConfigParam(beamline,"screenPixX"))
  screenPixY = float(db_lib.getBeamlineConfigParam(beamline,"screenPixY"))
  beamlineComm = db_lib.getBeamlineConfigParam(beamline,"beamlineComm")
  screenPixCenterX = screenPixX/2.0
  screenPixCenterY = screenPixY/2.0
  gonioPvPrefix = db_lib.getBeamlineConfigParam(beamline,"gonioPvPrefix")
  detector_id = db_lib.getBeamlineConfigParam(beamline,"detector_id")
  det_radius = db_lib.getBeamlineConfigParam(beamline,"detRadius")
#  if (detector_id == "ADSC-Q315"):
#    det_radius = 157.5
#  elif (detector_id == "ADSC-Q210"):
#    det_radius = 105.0
#  elif (detector_id == "PILATUS-6"):
#    det_radius = 212.0
#  elif (detector_id == "EIGER-16"):
#    det_radius = 155.0
#  else: #default eiger 16
#    det_radius = 155.0
  det_type = db_lib.getBeamlineConfigParam(beamline,"detector_type")
  imgsrv_port = db_lib.getBeamlineConfigParam(beamline,"imgsrv_port")
  imgsrv_host = db_lib.getBeamlineConfigParam(beamline,"imgsrv_host")
  has_dna = int(db_lib.getBeamlineConfigParam(beamline,"has_edna"))
  has_beamline = int(db_lib.getBeamlineConfigParam(beamline,"has_beamline"))
  detectorOffline = int(db_lib.getBeamlineConfigParam(beamline,"detector_offline"))
  has_xtalview = int(db_lib.getBeamlineConfigParam(beamline,"has_xtalview"))
  camera_offset = float(db_lib.getBeamlineConfigParam(beamline,"camera_offset"))
  if (has_xtalview):
    xtal_url_small = db_lib.getBeamlineConfigParam(beamline,"xtal_url_small")
    xtal_url = db_lib.getBeamlineConfigParam(beamline,"xtal_url")
  mono_mot_code = db_lib.getBeamlineConfigParam(beamline,"mono_mot_code")
  screenProtocol = db_lib.getBeamlineConfigParam(beamline,"screen_default_protocol")
  screenPhist = float(db_lib.getBeamlineConfigParam(beamline,"screen_default_phist"))
  screenPhiend = float(db_lib.getBeamlineConfigParam(beamline,"screen_default_phi_end"))
  screenWidth = float(db_lib.getBeamlineConfigParam(beamline,"screen_default_width"))
  screenDist =  float(db_lib.getBeamlineConfigParam(beamline,"screen_default_dist"))
  screenExptime = float(db_lib.getBeamlineConfigParam(beamline,"screen_default_time"))
  screenReso = float(db_lib.getBeamlineConfigParam(beamline,"screen_default_reso"))
  screenWave = float(db_lib.getBeamlineConfigParam(beamline,"screen_default_wave"))
  screenEnergy = float(db_lib.getBeamlineConfigParam(beamline,"screen_default_energy"))
  screenbeamWidth = float(db_lib.getBeamlineConfigParam(beamline,"screen_default_beamWidth"))
  screenbeamHeight = float(db_lib.getBeamlineConfigParam(beamline,"screen_default_beamHeight"))
  screenTransmissionPercent = float(db_lib.getBeamlineConfigParam(beamline,"screen_transmission_percent"))
  beamstop_x_pvname = db_lib.getBeamlineConfigParam(beamline,"beamstop_x_pvname")
  beamstop_y_pvname = db_lib.getBeamlineConfigParam(beamline,"beamstop_y_pvname")

#  varname = "HAS_XTALVIEW"
#  if varname in os.environ:
#    has_xtalview = int(os.environ[varname])
  varname = "DETECTOR_OFFLINE"
  if varname in os.environ:
    detectorOffline = int(os.environ[varname])



#def broadcast_output(s):
#  time.sleep(0.01)
#  if (string.find(s,'|') == -1):
#    print s
#  beamline_support.pvPut(message_string_pv,s)


# beamlineconfig stuff moved to db_lib


def ObsoletegetCurrentFOVx(camera,zoom): #cam 0 = lowMag, 
  if (camera==0):
    return daq_utils.lowMagFOVx
  else:
    if (zoom==0):
      return daq_utils.highMagFOVx          
    else:
      return daq_utils.highMagFOVx/2          

def ObsoletegetCurrentFOVy(camera,zoom): #cam 0 = lowMag, 
  if (camera==0):
    return daq_utils.lowMagFOVy
  else:
    if (zoom==0):
      return daq_utils.highMagFOVy
    else:
      return daq_utils.highMagFOVy/2          


def calc_reso(det_radius,detDistance,wave,theta):

  if (detDistance == 0): #in case distance reads as 0
    distance = 100.0
  else:
    distance = detDistance
  dg2rd = 3.14159265 / 180.0
#  det_radius = float(diameter)/2
  theta_radians = float(theta) * dg2rd
  theta_t = (theta_radians + atan(det_radius/float(distance)))/2
  dmin_t = float(wave)/(2*(sin(theta_t)))
  return float("%.2f" % dmin_t)


def distance_from_reso(det_radius,reso,wave,theta):

  try:
    dg2rd = 3.14159265 / 180.0
    theta_radians = float(theta) * dg2rd
#  det_radius = float(diameter)/2
    dx = det_radius/(tan(2*(asin(float(wave)/(2*reso)))-theta_radians))
    return float("%.2f" % dx)
  except ValueError:  
    return 500.0 #a safe value for now


def energy2wave(e):
  if (float(e)==0.0):
    return 1.0
  else:
    return float("%.2f" % (12398.5/e))

def wave2energy(w):
  if (float(w)==0.0):
    return 12600.0
  else:
    return float("%.2f" % (12398.5/w))

def createDefaultRequest(sample_id):
    """
    Doesn't really create a request, just returns a dictionary
    with the default parameters that can be passed to addRequesttoSample().
    """


    screenPhist = float(db_lib.getBeamlineConfigParam(beamline,"screen_default_phist"))
    screenPhiend = float(db_lib.getBeamlineConfigParam(beamline,"screen_default_phi_end"))
    screenWidth = float(db_lib.getBeamlineConfigParam(beamline,"screen_default_width"))
    screenDist =  float(db_lib.getBeamlineConfigParam(beamline,"screen_default_dist"))
    screenExptime = float(db_lib.getBeamlineConfigParam(beamline,"screen_default_time"))
    screenReso = float(db_lib.getBeamlineConfigParam(beamline,"screen_default_reso"))
    screenWave = float(db_lib.getBeamlineConfigParam(beamline,"screen_default_wave"))
    screenEnergy = float(db_lib.getBeamlineConfigParam(beamline,"screen_default_energy"))
    screenbeamWidth = float(db_lib.getBeamlineConfigParam(beamline,"screen_default_beamWidth"))
    screenbeamHeight = float(db_lib.getBeamlineConfigParam(beamline,"screen_default_beamHeight"))
    screenTransmissionPercent = float(db_lib.getBeamlineConfigParam(beamline,"screen_transmission_percent"))
    sampleName = str(db_lib.getSampleNamebyID(sample_id))
    basePath = os.getcwd()
    runNum = db_lib.getSampleRequestCount(sample_id)
    request = {"sample": sample_id}
    requestObj = {
               "sample": sample_id,
               "sweep_start": screenPhist,  "sweep_end": screenPhiend,
               "img_width": screenWidth,
               "exposure_time": screenExptime,
               "protocol": "standard",
               "detDist": screenDist,
               "parentReqID": -1,
               "basePath": basePath,
               "file_prefix": sampleName,
               "directory": basePath+"/projID/"+sampleName+"/" + str(runNum) + "/",
               "file_number_start": 1,
               "energy":screenEnergy,
               "wavelength": energy2wave(screenEnergy),
               "resolution": screenReso,
               "slit_height": screenbeamHeight,  "slit_width": screenbeamWidth,
               "attenuation": screenTransmissionPercent,
               "pos_x": 0,  "pos_y": 0,  "pos_z": 0,  "pos_type": 'A', "gridStep": 30}
    request["request_obj"] = requestObj

    return request

def createResult(typeName,resultObj):
  result = {}
  result["type"] = typeName
  result["timestamp"] = time.time()
  result["resultObj"] = resultObj
  return result


def runDialsObsolete(imgPath,reqID=None):
  comm_s = "dials.find_spots_client " + imgPath
  print(comm_s)
  dialsResultObj = xmltodict.parse("<data>\n"+os.popen(comm_s).read()+"</data>\n")
  print("done parsing dials output")
  print(dialsResultObj)
  currentRequestID = db_lib.getBeamlineConfigParam(beamline,'currentRequestID')
  dialsResult = db_lib.addResultforRequest("dials",currentRequestID, owner=owner,result_obj=dialsResultObj)



def take_crystal_picture(filename=None,czoom=0,reqID=None,omega=-999):
  zoom = int(czoom)
  if not (has_xtalview):
    return
  if (1):
    if (zoom==0):
      r=requests.get(xtal_url)
    else:
      r=requests.get(xtal_url_small)
  else: #password, need to change to requests module if we need this
    comm_s = "curl -u %s:%s -o %s.jpg -s %s" % (xtalview_user,xtalview_pass,filename,xtal_url)
  data = r.content
  if (filename != None):
    fd = open(filename+".jpg","wb+")
    fd.write(data)
    fd.close()
  if (reqID != None):
    xtalpicJpegDataResult = {}
    imgRef = db_lib.addFile(data)
    xtalpicJpegDataResult["data"] = imgRef
    xtalpicJpegDataResult["omegaPos"] = omega 
    db_lib.addResultforRequest("xtalpicJpeg",reqID,owner=owner,result_obj=xtalpicJpegDataResult)


def diff2jpegLYNX(diffimageName,JPEGfilename=None,reqID=None):
  imageJpegData = {}
  imageJpegHeader = {}
  imageJpegData["dataFilePath"]=diffimageName
  img_url = "http://"+imgsrv_host+":"+imgsrv_port+"/getImage\?fileName="+ diffimageName+"\&sizeX=500\&sizeY=500\&gray=100\&zoom=1.0\&percentX=0.5\&percentY=0.5\&userName=me\&sessionId=E"
#  comm_s = "lynx -source %s >%s" % (img_url,JPEGfilename) 
  comm_s = "lynx -source %s" % (img_url) 
  print(comm_s)
  data = os.popen(comm_s).read()
  imageJpegData["data"] = data
#  os.system(comm_s)
  img_url = "http://"+imgsrv_host+":"+imgsrv_port+"/getThumbnail\?fileName="+ diffimageName+"\&sizeX=500\&sizeY=500\&gray=100\&zoom=1.0\&percentX=0.5\&percentY=0.5\&userName=me\&sessionId=E"
  comm_s = "lynx -source %s" % (img_url) 
  thumbData = os.popen(comm_s).read()
  imageJpegData["thumbData"] = thumbData
#  comm_s = "lynx -source %s >%s" % (img_url,"thumb_"+JPEGfilename) 
  print(comm_s)
#  os.system(comm_s)
  img_url = "http://"+imgsrv_host+":"+imgsrv_port+"/getHeader\?fileName="+ diffimageName+"\&userName=me\&sessionId=E"
  comm_s = "lynx -source " + img_url
  for outputline in os.popen(comm_s).readlines():    
    print(outputline)
    tokens = outputline.split()      
    if (tokens[0] == "OSC_START"):
      print("Omega start = " + tokens[1])
      imageJpegHeader["oscStart"] = float(tokens[1])
    elif (tokens[0] == "OSC_RANGE"):
      print("Omega range = " + tokens[1]) 
      imageJpegHeader["oscRange"] = float(tokens[1])
    elif (tokens[0] == "EXPOSURE"):
      print("Exposure Time = " + tokens[2])
      imageJpegHeader["exptime"] = float(tokens[2])
    elif (tokens[0] == "DISTANCE"):
      print("Distance = " + str(float(tokens[1])/1000.0))
      imageJpegHeader["detDist"] = float(tokens[1])
    elif (tokens[0] == "WAVELENGTH"):
      print("Wavelength = " + tokens[1]) 
      imageJpegHeader["wave"] = float(tokens[1])
  if (reqID != None):
    resultObj = {}
    imgRef = db_lib.addFile(data)
    resultObj["data"] = imgRef
    imgRef = db_lib.addFile(thumbData)
    resultObj["thumbData"] = imgRef
    resultObj["dataFilePath"] = diffimageName
    resultObj["header"] = imageJpegHeader
    db_lib.addResultforRequest("diffImageJpeg",reqID,owner=owner,result_obj=resultObj)
  return imageJpegData


def diff2jpeg(diffimageName,JPEGfilename=None,reqID=None):
  imageJpegData = {}
  imageJpegHeader = {}
  imageJpegData["dataFilePath"]=diffimageName
  payload = {"fileName":diffimageName,"sizeX":500,"sizeY":500,"gray":100,"percentX":0.5,"percentY":0.5,"userName":"me","sessionId":"E","zoom":1.0}
  img_url = "http://"+imgsrv_host+":"+imgsrv_port+"/getImage" 
  r = requests.get(img_url,params=payload)
  data = r.content
  imageJpegData["data"] = data
  img_url = "http://"+imgsrv_host+":"+imgsrv_port+"/getThumbnail"
  r = requests.get(img_url,params=payload)
  thumbData = r.content
  imageJpegData["thumbData"] = thumbData
  payload = {"fileName":diffimageName,"userName":"me","sessionId":"E"}
  img_url = "http://"+imgsrv_host+":"+imgsrv_port+"/getHeader"
  r = requests.get(img_url,params=payload)
  imageJpegData["header"] = r
  headerData = r.text
  lines = headerData.split("\n")
  for i in range (0,len(lines)):
    line = lines[i]
    print(line)
    tokens = line.split()
    if (len(tokens) > 1):
      if (tokens[0] == "OSC_START"):
        print("Omega start = " + tokens[1])
        imageJpegHeader["oscStart"] = float(tokens[1])
      elif (tokens[0] == "OSC_RANGE"):
        print("Omega range = " + tokens[1]) 
        imageJpegHeader["oscRange"] = float(tokens[1])
      elif (tokens[0] == "EXPOSURE"):
        print("Exposure Time = " + tokens[2])
        imageJpegHeader["exptime"] = float(tokens[2])
      elif (tokens[0] == "DISTANCE"):
        print("Distance = " + str(float(tokens[1])/1000.0))
        imageJpegHeader["detDist"] = float(tokens[1])
      elif (tokens[0] == "WAVELENGTH"):
        print("Wavelength = " + tokens[1]) 
        imageJpegHeader["wave"] = float(tokens[1])
  imageJpegData["header"] = imageJpegHeader
  if (reqID != None): #this means I'll dump into mongo as a result
    resultObj = {}
    imgRef = db_lib.addFile(data)
    resultObj["data"] = imgRef
    imgRef = db_lib.addFile(thumbData)
    resultObj["thumbData"] = imgRef
    resultObj["dataFilePath"] = diffimageName
    resultObj["header"] = imageJpegHeader
    db_lib.addResultforRequest("diffImageJpeg",reqID,owner=owner,result_obj=resultObj)
  return imageJpegData

def create_filename(prefix,number):
  if (detector_id == "EIGER-16"):  
#  if (0):
   tmp_filename = findH5Master(prefix)
  else:
    tmp_filename = "%s_%05d.cbf" % (prefix,int(number))
  if (prefix[0] != "/"):
    cwd = os.getcwd()
    filename = "%s/%s" % (cwd,tmp_filename)
  else:
    filename = tmp_filename
  return filename

def findH5Master(prefix):
  comm_s = "ls " + prefix + "*_master.h5"
  masterFilename = os.popen(comm_s).read()[0:-1]
  return masterFilename
  

def readPVDesc():
  global beamline_designation,motor_dict,soft_motor_list,scan_list,counter_dict
  
  envname = "EPICS_BEAMLINE_INFO"
  try:
    dbfilename = os.environ[envname]
  except KeyError:
    print(envname + " not defined. Defaulting to epx.db.")
    dbfilename = "epx.db"
  if (os.path.exists(dbfilename) == 0):
    error_msg = "EPICS BEAMLINE INFO %s does not exist.\n Program exiting." % dbfilename
    print(error_msg)
    sys.exit()
  else:
    dbfile = open(dbfilename,'r')
    line = dbfile.readline()
    line = dbfile.readline()
    beamline_designation = line[:-1]
    line = dbfile.readline()
    i = 0
    while(1):
      line = dbfile.readline()
      if (line == ""):
        break
      else:
        line = line[:-1]
        if (line == "#virtual motors"):
          break
        else:
          motor_inf = line.split()
          motor_dict[motor_inf[1]] = beamline_designation +  motor_inf[0]
    while(1):
      line = dbfile.readline()
      if (line == ""):
        break
      else:
        line = line[:-1]
        if (line == "#control PVs"):
          break
        else:
          motor_inf = line.split()
          soft_motor_list.append(beamline_designation + motor_inf[0])
          motor_dict[motor_inf[1]] = beamline_designation + motor_inf[0]          
    while(1):
      line = dbfile.readline()
      if (line == ""):
        break
      else:
        line = line[:-1]
        if (line == "#scanned motors"):
          break
        else:
          inf = line.split()
          pvLookupDict[inf[1]] = beamline_designation + inf[0]          
    while(1):
      line = dbfile.readline()
      if (line == ""):
        break
      else:
        line = line[:-1]
        if (line == "#counters"):
          break
        else:
          scan_list.append(beamline_designation + line + "scanParms")
    line = dbfile.readline()
    counter_inf = line.split()
    counter_dict[counter_inf[1]] = beamline_designation + counter_inf[0]    




#def calc_reso_edge(distance,wave,theta):
#  if (distance < 1.0):
#    distance = 1.0
#  theta_radians = float(theta) * dg2rd
#  theta_t = (theta_radians + atan(det_radius/float(distance)))/2
#  dmin_t = float(wave)/(2*(sin(theta_t)))
#  return dmin_t


#def distance_from_reso(reso,wave,theta):
#  theta_radians = float(theta) * dg2rd
#  dx = det_radius/(tan(2*(asin(float(wave)/(2*reso)))-theta_radians))
#  return dx

#def move_det_to_reso(reso):
#  new_distance = distance_from_reso(reso,12398.5/get_mono_energy(),0)
#  move_axis_absolute("dist",new_distance)
