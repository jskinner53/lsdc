#!/usr/bin/python
import time
import os
import sys
import db_lib
#import xmltodict
from XSDataMXv1 import XSDataResultCharacterisation
#import daq_utils



dna_directory = sys.argv[1]
dna_prefix = sys.argv[2]
aimed_ISig = float(sys.argv[3])
flux = float(sys.argv[4])
xbeam_size = float(sys.argv[5])
ybeam_size = float(sys.argv[6])
edna_input_filename = sys.argv[7]
request_id = int(sys.argv[8])


print("generating edna input\n")
#edna_input_xml_command = "ssh -q xf17id1-srv1 \"/nfs/skinner/edna_header_code/makeAnEDNAXML-bnl.sh 1232 %s %s none %f %f 4000 0.01 0.01 0 xh1223_2_ %f %f %f > %s\"" % (dna_directory,dna_prefix,3,aimed_ISig,flux,xbeam_size,ybeam_size,edna_input_filename)
edna_input_xml_command = "/nfs/skinner/edna_header_code/makeAnEDNAXML-bnl.sh 1232 %s %s none %f %f 4000 0.01 0.01 0 xh1223_2_ %f %f %f > %s" % (dna_directory,dna_prefix,3.0,aimed_ISig,flux,xbeam_size,ybeam_size,edna_input_filename)  
print(edna_input_xml_command)
comm_sss = "echo " + edna_input_xml_command + "> edna_comm.txt"
os.system(comm_sss)
os.system(edna_input_xml_command)

print("done generating edna input\n")
#command_string = "ssh -q xf17id1-srv1 \"/usr/local/crys/edna-mx/mxv1/bin/edna-mxv1-characterisation.py --verbose --data %s\"" % (edna_input_filename)
command_string = "/usr/local/crys/edna-mx/mxv1/bin/edna-mxv1-characterisation.py --verbose --data %s" % (edna_input_filename)  
print(command_string)
#  for i in range (0,len(dna_filename_list)):
#    command_string = command_string + " " + dna_filename_list[i]
#broadcast_output("\nProcessing with EDNA. Please stand by.\n")
if ( os.path.exists( "edna.log" ) ) :
  os.remove( "edna.log" )
if ( os.path.exists( "edna.err" ) ) :
  os.remove( "edna.err" )
edna_execution_status = os.system( "%s > edna.log 2> edna.err" % command_string)
#####  fEdnaLogFile = open(daq_lib.get_misc_dir_name() + "/edna.log", "r" )
fEdnaLogFile = open("./edna.log", "r" )
ednaLogLines = fEdnaLogFile.readlines()
fEdnaLogFile.close()
collect_and_characterize_success = 0
for outline in ednaLogLines: 
  if (outline.find("EdnaDir")!= -1):
    (param,dirname) = outline.split('=')
    strXMLFileName = dirname[0:len(dirname)-1]+"/ControlInterfacev1_2/Characterisation/ControlCharacterisationv1_3_dataOutput.xml"
#####    strXMLFileName = dirname[0:len(dirname)-1]+"/ControlInterfacev1_2/Characterisation/ControlCharacterisationv1_1_dataOutput.xml"
  if (outline.find("characterisation successful!")!= -1):
    collect_and_characterize_success = 1
if (not collect_and_characterize_success):
  dna_comment =  "Indexing Failure"
#####  pxdb_lib.update_sweep(2,daq_lib.sweep_seq_id,dna_comment)  
  exit(0)
else:
  xsDataCharacterisation = XSDataResultCharacterisation.parseFile( strXMLFileName )
  xsDataIndexingResult = xsDataCharacterisation.getIndexingResult()
  xsDataIndexingSolutionSelected = xsDataIndexingResult.getSelectedSolution()
  xsDataStatisticsIndexing = xsDataIndexingSolutionSelected.getStatistics()
  numSpotsFound  = xsDataStatisticsIndexing.getSpotsTotal().getValue()
  numSpotsUsed  = xsDataStatisticsIndexing.getSpotsUsed().getValue()
  numSpotsRejected = numSpotsFound-numSpotsUsed
  beamShiftX = xsDataStatisticsIndexing.getBeamPositionShiftX().getValue()
  beamShiftY = xsDataStatisticsIndexing.getBeamPositionShiftY().getValue()
  spotDeviationR = xsDataStatisticsIndexing.getSpotDeviationPositional().getValue()
  try:
    spotDeviationTheta = xsDataStatisticsIndexing.getSpotDeviationAngular().getValue()
  except AttributeError:
    spotDeviationTheta = 0.0
  diffractionRings = 0 #for now, don't see this in xml except message string        
  reflections_used = 0 #for now
  reflections_used_in_indexing = 0 #for now
  rejectedReflections = 0 #for now
  xsDataOrientation = xsDataIndexingSolutionSelected.getOrientation()
  xsDataMatrixA = xsDataOrientation.getMatrixA()
  rawOrientationMatrix_a_x = xsDataMatrixA.getM11()
  rawOrientationMatrix_a_y = xsDataMatrixA.getM12()
  rawOrientationMatrix_a_z = xsDataMatrixA.getM13()
  rawOrientationMatrix_b_x = xsDataMatrixA.getM21()
  rawOrientationMatrix_b_y = xsDataMatrixA.getM22()
  rawOrientationMatrix_b_z = xsDataMatrixA.getM23()
  rawOrientationMatrix_c_x = xsDataMatrixA.getM31()
  rawOrientationMatrix_c_y = xsDataMatrixA.getM32()
  rawOrientationMatrix_c_z = xsDataMatrixA.getM33()
  xsDataCrystal = xsDataIndexingSolutionSelected.getCrystal()
  xsDataCell = xsDataCrystal.getCell()
  unitCell_alpha = xsDataCell.getAngle_alpha().getValue()
  unitCell_beta = xsDataCell.getAngle_beta().getValue()
  unitCell_gamma = xsDataCell.getAngle_gamma().getValue()
  unitCell_a = xsDataCell.getLength_a().getValue()
  unitCell_b = xsDataCell.getLength_b().getValue()
  unitCell_c = xsDataCell.getLength_c().getValue()
  mosaicity = xsDataCrystal.getMosaicity().getValue()
  xsSpaceGroup = xsDataCrystal.getSpaceGroup()
  spacegroup_name = xsSpaceGroup.getName().getValue()
  pointGroup = spacegroup_name #for now
  bravaisLattice = pointGroup #for now
  statusDescription = "ok" #for now
  try:
    spacegroup_number = xsSpaceGroup.getITNumber().getValue()
  except AttributeError:
    spacegroup_number = 0
  xsStrategyResult = xsDataCharacterisation.getStrategyResult()
  resolutionObtained = -999
  if (xsStrategyResult != None):
    dna_have_strategy_results = 1
    xsCollectionPlan = xsStrategyResult.getCollectionPlan()
    xsStrategySummary = xsCollectionPlan[0].getStrategySummary()
    resolutionObtained = xsStrategySummary.getRankingResolution().getValue()
    xsCollectionStrategy = xsCollectionPlan[0].getCollectionStrategy()
    xsSubWedge = xsCollectionStrategy.getSubWedge()
    for i in range (0,len(xsSubWedge)):
      xsExperimentalCondition = xsSubWedge[i].getExperimentalCondition()
      xsGoniostat = xsExperimentalCondition.getGoniostat()
      xsDetector = xsExperimentalCondition.getDetector()
      xsBeam = xsExperimentalCondition.getBeam()
      dna_strategy_start = xsGoniostat.getRotationAxisStart().getValue()
      dna_strategy_start = dna_strategy_start-(dna_strategy_start%.1)
      dna_strategy_range = xsGoniostat.getOscillationWidth().getValue()
      dna_strategy_range = dna_strategy_range-(dna_strategy_range%.1)
      dna_strategy_end = xsGoniostat.getRotationAxisEnd().getValue()
      dna_strategy_end = (dna_strategy_end-(dna_strategy_end%.1)) + dna_strategy_range
      dna_strat_dist = xsDetector.getDistance().getValue()
      dna_strat_dist = dna_strat_dist-(dna_strat_dist%1)
      dna_strategy_exptime = xsBeam.getExposureTime().getValue()
#wtf?      dna_strategy_exptime = dna_strategy_exptime-(dna_strategy_exptime%.2)
  program = "edna-1.0" # for now
#####  screeningoutputid = pxdb_lib.insert_dna_index_results(daq_lib.sweep_seq_id,daq_lib.get_field("xtal_id"),program,statusDescription,rejectedReflections,resolutionObtained,spotDeviationR,spotDeviationTheta,beamShiftX,beamShiftY,numSpotsFound,numSpotsUsed,numSpotsRejected,mosaicity,diffractionRings,spacegroup_name,pointGroup,bravaisLattice,rawOrientationMatrix_a_x,rawOrientationMatrix_a_y,rawOrientationMatrix_a_z,rawOrientationMatrix_b_x,rawOrientationMatrix_b_y,rawOrientationMatrix_b_z,rawOrientationMatrix_c_x,rawOrientationMatrix_c_y,rawOrientationMatrix_c_z,unitCell_a,unitCell_b,unitCell_c,unitCell_alpha,unitCell_beta,unitCell_gamma)
  dna_comment =  "spacegroup = " + str(spacegroup_name) + " mosaicity = " + str(mosaicity) + " resolutionHigh = " + str(resolutionObtained) + " cell_a = " + str(unitCell_a) + " cell_b = " + str(unitCell_b) + " cell_c = " + str(unitCell_c) + " cell_alpha = " + str(unitCell_alpha) + " cell_beta = " + str(unitCell_beta) + " cell_gamma = " + str(unitCell_gamma) + " status = " + str(statusDescription)
#####  print "\n\n skinner " + dna_comment + "\n" +str(daq_lib.sweep_seq_id) + "\n"
  print("\n\n skinner " + dna_comment + "\n") 
#####  pxdb_lib.update_sweep(2,daq_lib.sweep_seq_id,dna_comment)
  if (dna_have_strategy_results):
#####    pxdb_lib.insert_to_screening_strategy_table(screeningoutputid,dna_strategy_start,dna_strategy_end,dna_strategy_range,dna_strategy_exptime,resolutionObtained,program)
    dna_strat_comment = "\ndna Strategy results: Start=" + str(dna_strategy_start) + " End=" + str(dna_strategy_end) + " Width=" + str(dna_strategy_range) + " Time=" + str(dna_strategy_exptime) + " Dist=" + str(dna_strat_dist)
#    characterizationResult = {}
    characterizationResultObj = {}
#    characterizationResult["type"] = "characterizationStrategy"
 #   characterizationResult["timestamp"] = time.time()
    characterizationResultObj = {"strategy":{"start":dna_strategy_start,"end":dna_strategy_end,"width":dna_strategy_range,"exptime":dna_strategy_exptime,"detDist":dna_strat_dist}}
#    characterizationResult["resultObj"] = characterizationResultObj
    db_lib.addResultforRequest("characterizationStrategy",request_id, characterizationResultObj)
#####    pxdb_lib.update_sweep(2,daq_lib.sweep_seq_id,dna_strat_comment)
    xsStrategyStatistics = xsCollectionPlan[0].getStatistics()
    xsStrategyResolutionBins = xsStrategyStatistics.getResolutionBin()
    now = time.time()
#  edna_isig_plot_filename = dirname[0:len(dirname)-1] + "/edna_isig_res_" + str(now) + ".txt"
    edna_isig_plot_filename = dirname[0:len(dirname)-1] + "/edna_isig_res.txt"
    isig_plot_file = open(edna_isig_plot_filename,"w")
    for i in range (0,len(xsStrategyResolutionBins)-1):
      i_over_sigma_bin = xsStrategyResolutionBins[i].getIOverSigma().getValue()
      maxResolution_bin = xsStrategyResolutionBins[i].getMaxResolution().getValue()
      print(str(maxResolution_bin) + " " + str(i_over_sigma_bin))
      isig_plot_file.write(str(maxResolution_bin) + " " + str(i_over_sigma_bin)+"\n")
    isig_plot_file.close()
  if (dna_have_strategy_results):
#    broadcast_output(dna_strat_comment)
    print(dna_strat_comment)      





