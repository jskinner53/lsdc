#!/usr/bin/python
import time
import os
import sys
#import db_lib
#import xmltodict
#from XSDataMXv1 import XSDataResultCharacterisation
#import daq_utils



#dna_directory = sys.argv[1]
#dna_prefix = sys.argv[2]
dataFile1 = sys.argv[1]
dataFile2 = sys.argv[2]
aimed_ISig = float(sys.argv[3])
flux = float(sys.argv[4])
xbeam_size = float(sys.argv[5])
ybeam_size = float(sys.argv[6])
request_id = sys.argv[7]

#dataFile1=dna_directory+"/"+dna_prefix+"_0001.h5"
#dataFile2=dna_directory+"/"+dna_prefix+"_0002.h5"
#/usr/local/MX-Soft/edna-mx/mxv1/bin/nsls-characterisation.py --image test1_0_0001.h5 test1_0_0002.h5 --flux 100000000 --beamSize .01
#command_string = "/usr/local/MX-Soft/edna-mx/mxv1/bin/nsls-characterisation.py --verbose --image " + dataFile1 + " " + dataFile2 + " --flux " + str(flux) + " --strategyOption \"-w 0.05 -DIS_MAX 500 -DIS_MIN 180\" --minExposureTimePerImage .005  --beamSize " + str(xbeam_size)
command_string = "/usr/local/MX-Soft/edna-mx/mxv1/bin/nsls-characterisation.py --verbose --image " + dataFile1 + " " + dataFile2 + " --flux " + str(flux) + " --minExposureTimePerImage .005  --beamSize " + str(xbeam_size)
#command_string = "/usr/local/MX-Soft/edna-mx/mxv1/bin/nsls-characterisation.py --verbose --image " + dataFile1 + " " + dataFile2 + " --flux " + str(flux) + " --beamSize " + str(xbeam_size)
print(command_string)
if ( os.path.exists( "edna.log" ) ) :
  os.remove( "edna.log" )
if ( os.path.exists( "edna.err" ) ) :
  os.remove( "edna.err" )
edna_execution_status = os.system( "%s > edna.log 2> edna.err" % command_string)






