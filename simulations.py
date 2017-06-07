'''
Author: Charles Houston
Date: 26/5/17

Default experimental simulations.
Originally taken from descriptions of how data was generated in Deng et al, 2009.
'''

import myokit
import protocols
import numpy as np

class AbstractSim(object):
    def run(s):
        raise NotImplementedError

class ActivationSim(AbstractSim):
    '''
    Runs the activation simulation protocol from Deng2009.
    '''
    def __init__(self, variable, vsteps, reversal_potential, vhold, tpre, tstep):
        self.variable           = variable
        self.vsteps             = np.array(vsteps)
        self.protocol           = protocols.steptrain(
            vsteps              = self.vsteps,
            vhold               = vhold,
            tpre                = tpre,
            tstep               = tstep,
        )
        self.period             = tpre + tstep
        self.pre                = tpre
        self.t                  = self.protocol.characteristic_time()
        self.reversal_potential = reversal_potential

    def run(self, s):
        s.reset()
        s.set_protocol(self.protocol)
        try:
            d = s.run(self.t, log=['environment.time', self.variable], log_interval=.1)
        except:
            return None

        # Split the log into chunks for each step
        ds = d.split_periodic(self.period, adjust=True)

        # Trim each new log to contain only the 100ms of peak current
        act_peaks = []
        for d in ds:
            d.trim_left(self.pre, adjust=True)
            d.trim_right(self.period - self.pre - 100)
            act_peaks.append(max(min(d[self.variable]), max(d[self.variable]), key=abs))
        act_peaks = np.array(act_peaks)

        # Calculate the activation (normalized condutance) from IV curve
        # - Divide the peak currents by (V-E)
        act_relative = act_peaks / (self.vsteps - self.reversal_potential)
        # - Normalise by dividing by the biggest value
        act_relative = act_relative / act_relative.max()

        res = np.hstack((act_peaks, act_relative))
        return res

class InactivationSim(AbstractSim):
    '''
    Runs the inactivation stimulation protocol from Deng 2009.
    '''
    def __init__(self, variable, prepulses, vhold, vpost, tpre, tstep, tbetween, tpost):
        self.protocol = protocols.steptrain_double(
            vsteps    = prepulses, # Use prepulse values from experimental data
            vhold     = vhold, # Holding potential
            vpost     = vpost, # Second step always
            tpre      = tpre, # Pre-conditioning
            tstep     = tstep, # Initial step
            tbetween  = tbetween, # Time between steps
            tpost     = tpost, # Final pulse
        )
        self.t        = self.protocol.characteristic_time()
        self.period   = tpre+tstep+tbetween+tpost
        # Variables for cutting output data
        self.pre      = tpre + tstep - 100
        self.post     = tbetween + tpost
        self.variable = variable

    def run(self, s, act_peaks):
        s.reset()
        s.set_protocol(self.protocol)

        # Run the simulation
        try:
            d = s.run(self.t, log=['environment.time', self.variable], log_interval=.1)
        except:
            return None

        # Trim each new log to contain only the 100ms of peak current
        ds = d.split_periodic(self.period, adjust=True)
        inact = []
        for d in ds:
            d.trim_left(self.pre, adjust=True)
            d.trim_right(self.post)
            d.npview()
            inact.append(max(np.abs(d[self.variable])))

        inact = np.array(inact)
        inact = inact / max(np.abs(act_peaks))
        return inact

class RecoverySim(AbstractSim):
    '''
    Runs the recovery simulation from Deng 2009.
    '''
    def __init__(self, variable, intervals, vstep, vhold, vpost, tpre, tstep, tpost):
        # Create intervaltrain protocol
        self.intervals    = intervals
        self.protocol     = protocols.intervaltrain(
            vstep         = vstep, # Voltage steps
            vhold         = vhold, # Holding potential
            vpost         = vpost, # Final pulse
            tpre          = tpre, # Pre-conditioning
            tstep         = tstep, # Initial step
            tintervals    = intervals, # Varying interval times
            tpost         = tpost, # Final pulse
        )
        self.t            = self.protocol.characteristic_time()
        self.period_const = tpre+tstep+tpost
        self.pre          = tpre+tstep-100
        self.variable     = variable

    def run(self, s):
        s.reset()
        s.set_protocol(self.protocol)

        # Run the simulation
        try:
            d = s.run(self.t, log=['environment.time', self.variable], log_interval=.1)
        except:
            return None

        # Trim each new log to contain only the 100ms of peak current
        ds = []
        d = d.npview()
        for interval in self.intervals:
            # Split each experiment
            d_split,d = d.split(interval+self.period_const)
            ds.append(d_split)

            # Adjust times of remaining data
            if len(d['environment.time']):
                d['environment.time'] -= d['environment.time'][0]

        rec = []

        for d in ds:
            d.trim_left(self.pre, adjust=True)
            rec.append(max(min(d[self.variable]), max(d[self.variable]), key=abs))

        rec = np.array(rec)
        rec = -1*rec / np.max(np.abs(rec))
        return rec
