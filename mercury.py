from ophyd.mca import (EpicsMCA, EpicsDXP)
from ophyd import (Component as Cpt, Device, EpicsSignal, EpicsSignalRO,
                   EpicsSignalWithRBV, DeviceStatus)
from ophyd.device import (BlueskyInterface, Staged)

class Mercury(Device):
    dxp = Cpt(EpicsDXP, 'dxp1:')
    mca = Cpt(EpicsMCA, 'mca1')

    channel_advance = Cpt(EpicsSignal, 'ChannelAdvance')
    client_wait = Cpt(EpicsSignal, 'ClientWait')
    dwell = Cpt(EpicsSignal, 'Dwell')
    max_scas = Cpt(EpicsSignal, 'MaxSCAs')
    num_scas = Cpt(EpicsSignalWithRBV, 'NumSCAs')
    poll_time = Cpt(EpicsSignalWithRBV, 'PollTime')
    prescale = Cpt(EpicsSignal, 'Prescale')
    save_system = Cpt(EpicsSignalWithRBV, 'SaveSystem')
    save_system_file = Cpt(EpicsSignal, 'SaveSystemFile')
    set_client_wait = Cpt(EpicsSignal, 'SetClientWait')


class MercurySoftTrigger(BlueskyInterface):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._status = None
        self._acquisition_signal = self.mca.erase_start

        #self.stage_sigs[self.mca.stop_signal] = 1
        self.stage_sigs[self.dxp.preset_mode] = 'Real time'
        #self.stage_sigs[self.dxp.preset_mode] = 'Live time'

        self._count_signal = self.mca.preset_real_time
        self._count_time = None

    def stage(self):
        if self._count_time is not None:
            self.stage_sigs[self._count_signal] = self._count_time

        super().stage()

    def unstage(self):
        try:
            super().unstage()
        finally:
            if self._count_signal in self.stage_sigs:
                del self.stage_sigs[self._count_signal]
                self._count_time = None

    def trigger(self):
        "Trigger one acquisition."
        if self._staged != Staged.yes:
            raise RuntimeError("This detector is not ready to trigger."
                               "Call the stage() method before triggering.")

        self._status = DeviceStatus(self)
        self._acquisition_signal.put(1, callback=self._acquisition_done)
        return self._status

    def _acquisition_done(self, **kwargs):
        '''pyepics callback for when put completion finishes'''
        if self._status is not None:
            self._status._finished()
            self._status = None

    @property
    def count_time(self):
        '''Exposure time, as set by bluesky'''
        return self._count_time

    @count_time.setter
    def count_time(self, count_time):
        self._count_time = count_time


class FMXMercury(MercurySoftTrigger, Mercury):
    def __init__(self, prefix, *, read_attrs=None, configuration_attrs=None,
                 **kwargs):
        if read_attrs is None:
            read_attrs = ['mca.spectrum']

        if configuration_attrs is None:
            configuration_attrs = ['mca.preset_real_time',
                                   'mca.preset_live_time',
                                   'dxp.preset_mode',
                                   ]

        super().__init__(prefix, read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs, **kwargs)


mercury = FMXMercury('XF:17IDC-ES:FMX{Det:Mer}', name='mercury')
