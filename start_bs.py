#!/opt/conda_envs/lsdc_dev3/bin/ipython -i
import matplotlib.pyplot as plt
plt.ion()
import ophyd
ophyd.utils.startup.setup()

import bluesky
from ophyd import *
from ophyd.commands import *
from ophyd import EpicsMotor

import asyncio
from functools import partial
from bluesky.standard_config import *
from bluesky.plans import *
from bluesky.callbacks import *
from bluesky.broker_callbacks import *
from bluesky.callbacks.olog import logbook_cb_factory
from bluesky.hardware_checklist import *
from bluesky.qt_kicker import install_qt_kicker


# The following line allows bluesky and pyqt4 GUIs to play nicely together:
install_qt_kicker()


RE = gs.RE
abort = RE.abort
resume = RE.resume
stop = RE.stop

RE.md['group'] = 'amx'
RE.md['beamline_id'] = 'AMX'
RE.ignore_callback_exceptions = False

loop = asyncio.get_event_loop()
loop.set_debug(False)



from ophyd import (SingleTrigger, TIFFPlugin, ProsilicaDetector,
                   ImagePlugin, StatsPlugin, ROIPlugin, DetectorBase, HDF5Plugin,
                   AreaDetector)

import ophyd.areadetector.cam as cam

from ophyd.areadetector.filestore_mixins import (FileStoreTIFFIterativeWrite,
                                                 FileStoreHDF5IterativeWrite)

from ophyd import Component as Cpt

class StandardProsilica(SingleTrigger, ProsilicaDetector):
    #tiff = Cpt(TIFFPluginWithFileStore,
    #           suffix='TIFF1:',
    #           write_path_template='/XF16ID/data/')
    image = Cpt(ImagePlugin, 'image1:')
    roi1 = Cpt(ROIPlugin, 'ROI1:')
#    roi2 = Cpt(ROIPlugin, 'ROI2:')
#    roi3 = Cpt(ROIPlugin, 'ROI3:')
#    roi4 = Cpt(ROIPlugin, 'ROI4:')
    stats1 = Cpt(StatsPlugin, 'Stats1:')
#    stats2 = Cpt(StatsPlugin, 'Stats2:')
#    stats3 = Cpt(StatsPlugin, 'Stats3:')
#    stats4 = Cpt(StatsPlugin, 'Stats4:')
    stats5 = Cpt(StatsPlugin, 'Stats5:')

def filter_camera_data(camera):
    camera.read_attrs = ['stats1', 'stats5']
    #camera.tiff.read_attrs = []  # leaving just the 'image'
    camera.stats1.read_attrs = ['total', 'centroid']
    #camera.stats2.read_attrs = ['total', 'centroid']
    #camera.stats3.read_attrs = ['total', 'centroid']
    #camera.stats4.read_attrs = ['total', 'centroid']
    camera.stats5.read_attrs = ['total', 'centroid']


cam_7 = StandardProsilica('XF:17IDC-ES:FMX{Cam:7}', name='cam_7')
filter_camera_data(cam_7)

omega = EpicsMotor("XF:17IDC-ES:FMX{Gon:1-Ax:O}Mtr",name="omega")
gs.DETS=[cam_7]
gs.PLOT_Y=cam_7.stats1.total.name
