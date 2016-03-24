#!/usr/bin/python
from pyOlog import OlogClient 
from pyOlog.OlogDataTypes import * 
import requests 
 
#requests.packages.urllib3.disable_warnings() 

global client
client = None
 
url = "https://lsbr-dev.nsls2.bnl.gov:8181/Olog" 
username = password = "olog" 
 

def toOlog(imagePath,comment,omega_pv=None):
  global client

  if (client==None):
    client = OlogClient(url, username, password) 
  att = Attachment(open(imagePath,"rb")) 
  if (omega_pv==None):
    propOmega = Property(name='motorPosition', attributes={'id':'XF:AMXFMX{MC-Goni}Omega.RBV', 'name':'Omega', 'value':'offline', 'unit':'deg'}) 
  else:
    propOmega = Property(name='motorPosition', attributes={'id':'XF:AMXFMX{MC-Goni}Omega.RBV', 'name':'Omega', 'value':str(omega_pv.get()), 'unit':'deg'}) 
  client.createProperty(propOmega) 
  entry = LogEntry(text=comment, owner="HHS", logbooks=[Logbook("raster")], properties=[propOmega], attachments=[att]) 
  client.log(entry) 
