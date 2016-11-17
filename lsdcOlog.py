#!/usr/bin/python
from pyOlog import OlogClient 
from pyOlog.OlogDataTypes import * 
import requests 
import os

#requests.packages.urllib3.disable_warnings() 

global client
client = None
 
url = "https://xf17id2-ca1.cs.nsls2.local:9191/Olog"
logbook = "Operations"
username = os.environ["OLOG_USER"]
password = os.environ["OLOG_PASS"]
default_owner="olog_logs"
owner = default_owner
 

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


def toOlogComment(comment,omega_pv=None):
  global client

  if (client==None):
    client = OlogClient(url, username, password) 
  if (omega_pv==None):
    propOmega = Property(name='motorPosition', attributes={'id':'XF:AMXFMX{MC-Goni}Omega.RBV', 'name':'Omega', 'value':'offline', 'unit':'deg'}) 
  else:
    propOmega = Property(name='motorPosition', attributes={'id':'XF:AMXFMX{MC-Goni}Omega.RBV', 'name':'Omega', 'value':str(omega_pv.get()), 'unit':'deg'}) 
  client.createProperty(propOmega) 
  entry = LogEntry(text=comment, owner=owner, logbooks=[Logbook(logbook)], properties=[propOmega]) 
  client.log(entry) 
