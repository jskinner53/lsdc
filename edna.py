
from XSDataMXv1 import XSDataCharacterisation
def dna_execute_collection3(dna_start,dna_range,dna_number_of_images,dna_exptime,dna_directory,prefix,start_image_number,overlap,dna_res,dna_run_num):
  global collect_and_characterize_success,dna_have_strategy_results,dna_have_index_results,picture_taken
  global dna_strategy_exptime,dna_strategy_start,dna_strategy_range,dna_strategy_end,dna_strat_dist
  global screeningoutputid
  

  dna_filename_list = []
  print "number of images " + str(dna_number_of_images) + " overlap = " + str(overlap) + " dna_start " + str(dna_start) + " dna_range " + str(dna_range) + " prefix " + prefix + " start number " + str(start_image_number) + "\n"
  collect_and_characterize_success = 0
  dna_have_strategy_results = 0
  dna_have_index_results = 0  
  dg2rd = 3.14159265 / 180.0  
  if (daq_utils.detector_id == "ADSC-Q315"):
    det_radius = 157.5
  elif (daq_utils.detector_id == "ADSC-Q210"):
    det_radius = 105.0
  else: #default Q4
    det_radius = 94.0
  theta_radians = daq_lib.get_field("theta") * dg2rd
  wave = daq_lib.get_field("wavelength0")
  dx = det_radius/(tan(2.0*(asin(wave/(2.0*dna_res)))-theta_radians))
  print "distance = ",dx
#skinner - could move distance and wave and scan axis here, leave wave alone for now
  print "skinner about to take reference images."
  for i in range(0,int(dna_number_of_images)):
    print "skinner prefix7 = " + prefix[0:7] + " startnum + " + str(start_image_number) + "\n"
    if (len(prefix)> 8):
      if ((prefix[0:7] == "postref") and (start_image_number == 1)):
        print "skinner postref bail\n"
        time.sleep(float(dna_number_of_images*float(dna_exptime)))        
        break
  #skinner roi - maybe I can measure and use that for dna_start so that first image is face on.
    if (daq_lib.need_auto_align_xtal_pic == 1):
      daq_lib.measure(1)
#      dna_start = daq_lib.var_list[daq_lib.var_list["scan_axis"]] + 75.0
    dna_start = daq_lib.get_field("datum_omega")
    colstart = float(dna_start) + (i*(abs(overlap)+float(dna_range)))
#    colstart = colstart + daq_lib.var_list["datum_omega"]    
#    daq_lib.move_axis_absolute(daq_lib.var_list["scan_axis"],colstart)
#    daq_lib.move_axis_absolute("dist",dx)
    dna_prefix = "ref-"+prefix+"_"+str(dna_run_num)
    image_number = start_image_number+i
    dna_prefix_long = dna_directory+"/"+dna_prefix
    filename = daq_lib.create_filename(dna_prefix_long,image_number)
    if (daq_lib.need_auto_align_xtal_pic == 1):
      daq_lib.need_auto_align_xtal_pic = 0
      camera_offset = float(os.environ["CAMERA_OFFSET"])
      beamline_lib.mvr("Omega",float(camera_offset))
#####      daq_lib.move_axis_relative("omega",camera_offset)
#####      daq_lib.take_crystal_picture_with_boxes(daq_lib.html_data_directory_name + "/xtal_align_" + str(daq_lib.sweep_seq_id))
#####      daq_lib.move_axis_relative("omega",0-camera_offset)
      beamline_lib.mvr("Omega",float(0-camera_offset))
    if (daq_lib.need_auto_align_xtal_pic == 2 and daq_lib.has_xtalview):
      daq_lib.need_auto_align_xtal_pic = 0
#####      daq_lib.take_crystal_picture_with_boxes(daq_lib.html_data_directory_name + "/xtal_postalign_" + str(daq_lib.sweep_seq_id))
      postalign_jpg = "xtal_postalign_" + str(daq_lib.sweep_seq_id)
#      postalign_jpg_th = "xtal_postalign_th_" + str(daq_lib.sweep_seq_id)    
    beamline_lib.mva("Omega",float(colstart))
#####    daq_lib.move_axis_absolute(daq_lib.get_field("scan_axis"),colstart)
    daq_lib.take_image(colstart,dna_range,dna_exptime,filename,daq_lib.get_field("scan_axis"),0,1)
    dna_filename_list.append(filename)
#####    daq_lib.take_crystal_picture_with_boxes(daq_lib.html_data_directory_name + "/xtal_" + str(daq_lib.sweep_seq_id) + "_" + str(i))
    picture_taken = 1
#                xml_from_file_list(flux,x_beamsize,y_beamsize,max_exptime_per_dc,aimed_completeness,file_list):
  edna_energy_ev = (12.3985/wave) * 1000.0
#####  xbeam_size = beamline_lib.get_motor_pos("slitHum")
#####  ybeam_size = beamline_lib.get_motor_pos("slitVum")
#  if (xbeam_size == 0.0 or ybeam_size == 0.0): #don't know where to get these from yet
  if (0): 
    xbeam_size = .1
    ybeam_size = .16
  else:
    xbeam_size = xbeam_size/1000
    ybeam_size = ybeam_size/1000    
  aimed_completness = daq_lib.get_field('edna_aimed_completeness')
  aimed_multiplicity = daq_lib.get_field('edna_aimed_multiplicity')
  aimed_resolution = daq_lib.get_field('edna_aimed_resolution')
  aimed_ISig = daq_lib.get_field('edna_aimed_ISig')
  timeout_check = 0;
  while(not os.path.exists(dna_filename_list[len(dna_filename_list)-1])): #this waits for edna images
    timeout_check = timeout_check + 1
    time.sleep(1.0)
    if (timeout_check > 10):
      break
  print "generating edna input\n"
#  edna_input_filename = edna_input_xml.xml_from_file_list(edna_energy_ev,xbeam_size,ybeam_size,1000000,aimed_completness,aimed_ISig,aimed_multiplicity,aimed_resolution,dna_filename_list)
  flux = 10000000000 * beamline_lib.get_epics_pv("flux","VAL")
  
  edna_input_filename = daq_lib.data_directory_name + "/adsc1_in.xml"
  edna_input_xml_command = "ssh swill \"/h/data/backed-up/pxsys/skinner/edna_header_code/makeAnEDNAXML-bnl.sh 1232 %s %s none %f %f 4000 0.01 0.01 0 xh1223_2_ %f %f %f\" > %s" % (daq_lib.data_directory_name,dna_prefix,3,aimed_ISig,flux,xbeam_size,ybeam_size,edna_input_filename)
  print edna_input_xml_command
  os.system(edna_input_xml_command)

  print "done generating edna input\n"
  command_string = "ssh swill \"cd %s; /h/crys/usr-local/fc3/crys_test/john_temp/edna/mxv1/bin/edna-mxv1-characterisation.py --verbose --data %s\"" % (daq_lib.data_directory_name,edna_input_filename)

#  command_string = "$EDNA_HOME/mxv1/bin/edna-mxv1-characterisation --data " + edna_input_filename
  print command_string
#  for i in range (0,len(dna_filename_list)):
#    command_string = command_string + " " + dna_filename_list[i]
  broadcast_output("\nProcessing with EDNA. Please stand by.\n")
  if ( os.path.exists( "edna.log" ) ) :
    os.remove( "edna.log" )
  if ( os.path.exists( "edna.err" ) ) :
    os.remove( "edna.err" )
  edna_execution_status = os.system( "%s > edna.log 2> edna.err" % command_string)
  fEdnaLogFile = open(daq_lib.get_misc_dir_name() + "/edna.log", "r" )
  ednaLogLines = fEdnaLogFile.readlines()
  fEdnaLogFile.close()
  for outline in ednaLogLines: 
 # for outline in os.popen(command_string,'r',0).readlines():
####skinner6/11 seg faults?    broadcast_output(outline)    
    if (string.find(outline,"EdnaDir")!= -1):
      (param,dirname) = string.split(outline,'=')
      strXMLFileName = dirname[0:len(dirname)-1]+"/ControlInterfacev1_2/Characterisation/ControlCharacterisationv1_1_dataOutput.xml"
    if (string.find(outline,"characterisation successful!")!= -1):
      collect_and_characterize_success = 1
  if (not collect_and_characterize_success):
    dna_comment =  "Indexing Failure"
    pxdb_lib.update_sweep(2,daq_lib.sweep_seq_id,dna_comment)  
    return 0
  xsDataCharacterisation = XSDataCharacterisation.parseFile( strXMLFileName )
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
      dna_strategy_exptime = dna_strategy_exptime-(dna_strategy_exptime%.1)
  program = "edna-1.0" # for now
#####  screeningoutputid = pxdb_lib.insert_dna_index_results(daq_lib.sweep_seq_id,daq_lib.get_field("xtal_id"),program,statusDescription,rejectedReflections,resolutionObtained,spotDeviationR,spotDeviationTheta,beamShiftX,beamShiftY,numSpotsFound,numSpotsUsed,numSpotsRejected,mosaicity,diffractionRings,spacegroup_name,pointGroup,bravaisLattice,rawOrientationMatrix_a_x,rawOrientationMatrix_a_y,rawOrientationMatrix_a_z,rawOrientationMatrix_b_x,rawOrientationMatrix_b_y,rawOrientationMatrix_b_z,rawOrientationMatrix_c_x,rawOrientationMatrix_c_y,rawOrientationMatrix_c_z,unitCell_a,unitCell_b,unitCell_c,unitCell_alpha,unitCell_beta,unitCell_gamma)
  dna_comment =  "spacegroup = " + str(spacegroup_name) + " mosaicity = " + str(mosaicity) + " resolutionHigh = " + str(resolutionObtained) + " cell_a = " + str(unitCell_a) + " cell_b = " + str(unitCell_b) + " cell_c = " + str(unitCell_c) + " cell_alpha = " + str(unitCell_alpha) + " cell_beta = " + str(unitCell_beta) + " cell_gamma = " + str(unitCell_gamma) + " status = " + str(statusDescription)
  print "\n\n skinner " + dna_comment + "\n" +str(daq_lib.sweep_seq_id) + "\n"
#####  pxdb_lib.update_sweep(2,daq_lib.sweep_seq_id,dna_comment)
  if (dna_have_strategy_results):
#####    pxdb_lib.insert_to_screening_strategy_table(screeningoutputid,dna_strategy_start,dna_strategy_end,dna_strategy_range,dna_strategy_exptime,resolutionObtained,program)
    dna_strat_comment = "\ndna Strategy results: Start=" + str(dna_strategy_start) + " End=" + str(dna_strategy_end) + " Width=" + str(dna_strategy_range) + " Time=" + str(dna_strategy_exptime) + " Dist=" + str(dna_strat_dist)
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
      print  str(maxResolution_bin) + " " + str(i_over_sigma_bin)
      isig_plot_file.write(str(maxResolution_bin) + " " + str(i_over_sigma_bin)+"\n")
    isig_plot_file.close()
    comm_s = "isig_res_plot.pl -i " + edna_isig_plot_filename + " -o " + daq_lib.html_data_directory_name + "/edna_isig_res_plot" + str(int(now))
    os.system(comm_s)
#####  broadcast_output(dna_comment)
  if (dna_have_strategy_results):
    broadcast_output(dna_strat_comment)  
  
  return 1

