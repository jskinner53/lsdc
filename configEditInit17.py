#!/opt/conda_envs/lsdc_dev/bin/python
import db_lib

#searchParams = {'info_name': 'config_params', 'beamline_id': beamline}


#def beamlineInfo(beamline_id, info_name, info_dict=None):
#    to write info:  beamlineInfo('x25', 'det', info_dict={'vendor':'adsc','model':'q315r'})
#    to fetch info:  info = beamlineInfo('x25', 'det')

db_lib.db_connect()
beamline_id = "fmx"
tmpConfigFile = open("/nfs/skinner/projects/bnlpx_config/BLConfigsTemp/configJohnFmx16shut.txt","r")
for line in tmpConfigFile.readlines():
  print(line)
  (key,val) = line.split()
  db_lib.beamlineInfo(beamline_id,key,{"val":val})
tmpConfigFile.close()
#daq_utils.setBeamlineConfigParams(newBeamlineConfig)



          
