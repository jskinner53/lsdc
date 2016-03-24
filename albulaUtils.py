import dectris.albula
global albulaFrame, albulaSubFrame
albulaFrame = None
albulaSubframeFrame = None

def albulaClose(): #not used
  global albulaFrame,albulaSubFrame
  if (albulaSubFrame != None):
     albulaSubFrame.close()

  if (albulaFrame != None):
     albulaFrame.close()
  

def albulaDisp(filename):
  global albulaFrame,albulaSubFrame

  if (albulaFrame == None or albulaSubFrame == None):
     albulaFrame = dectris.albula.openMainFrame()
     albulaFrame.disableClose()
     albulaSubFrame = albulaFrame.openSubFrame()
  try:
    albulaSubFrame.loadFile(filename)
  except dectris.albula.DNoObject:
    albulaFrame = dectris.albula.openMainFrame()
    albulaSubFrame = albulaFrame.openSubFrame()
    albulaSubFrame.loadFile(filename)


