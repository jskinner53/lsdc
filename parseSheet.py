import pandas
import db_lib


def parseSpreadsheet(infilename):
#  file_extension  = infilename[string.rfind(infilename,"."):len(infilename)]
#  file_prefix = infilename[0:string.rfind(infilename,".")]
#  csvfilename = file_prefix + ".csv"

  excel_data = pandas.read_excel(infilename,header=1)

#  for line in excel_data.iterrows():
#    print(line)
  DataFrame = pandas.read_excel(infilename, sheetname=0)
#  print(DataFrame)
  d = DataFrame.to_dict()
  print(d)
  return d

def insertSpreadsheetDict(d,owner):
  for i in range (0,len(d["puckName"])): #number of rows in sheet
#    print(d["container_name"][i])
#    print(d["position"][i])
#    print(d["item_name"][i])
    container_name = str(d["puckName"][i]).replace(" ","")
    position = d["position"][i]
    propNum = None
    try:
      propNum = int(d["proposalNum"][i])
    except KeyError:
      pass
    except ValueError:
      propNum = None      
    if (propNum == ''):
      propNum = None
    print(propNum)
    item_name1 = str(d["sampleName"][i]).replace(".","-")
    item_name = item_name1.replace(" ","-")    
    modelFilename = str(d["model"][i])
    sequenceFilename = str(d["sequence"][i])
    containerUID = db_lib.getContainerIDbyName(container_name,owner)
    if (containerUID == ''):
      print("create container " + str(container_name))
      containerUID = db_lib.createContainer(container_name,16,owner,"16_pin_puck")
    sampleUID = db_lib.getSampleIDbyName(item_name,owner)
    if (1):
#    if (sampleUID == ''):      
      print("create sample " + str(item_name))
      sampleUID = db_lib.createSample(item_name,owner,"pin",model=modelFilename,sequence=sequenceFilename,proposalID=propNum)
    else:
      print("WARNING - DUPLICATE SAMPLE NAME " + str(item_name))      
    print("insertIntoContainer " + str(container_name) + "," + owner + "," + str(position) + "," + sampleUID)
    db_lib.insertIntoContainer(container_name, owner, position, sampleUID)


def importSpreadsheet(infilename,owner):
  d = parseSpreadsheet(infilename)
  insertSpreadsheetDict(d,owner)


  

    
