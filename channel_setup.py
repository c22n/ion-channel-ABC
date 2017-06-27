'''
Author: Charles Houston

Specific channel settings for use with approximate Bayesian computation procedure.
'''
import numpy as np

import myokit
import distributions as Dist

# Data imports
import data.ical.data_ical as data_ical
import data.icat.data_icat as data_icat
import data.ina.data_ina as data_ina
import data.ikur.data_ikur as data_ikur

# Experimental simulations import
import simulations as sim

class AbstractChannel(object):
    def __init__(self):
        self.parameters = []
        self.simulations = []

    def reset_params(self, new_params):
        '''
        Set parameters of channel to new values in prior draw.
        '''
        if len(self.simulations) is 0:
            print "Need to add simulations to channel first!"
        else:
            for sim in self.simulations:
                sim.set_parameters(self.parameters, new_params)

    def simulate(self):
        '''
        Run the simulations necessary to generate values to compare with
        experimental results.
        '''
        if len(self.simulations) is 0:
            print "Need to add simulations to channel first!"
            return None

        sim_output = []

        for simulation in self.simulations:
            out = simulation.run(self.model_name)
            if out is None:
                return None
            sim_output.append(out)

        return sim_output

class TTypeCalcium(AbstractChannel):
    def __init__(self):
        self.name = 'icat'
        self.model_name = 'Takeuchi2013_iCaT.mmt'

        # Parameters involved in ABC process
        self.parameters = ['icat.dssk1',
                           'icat.dssk2',
                           'icat.dtauk1',
                           'icat.dtauk2',
                           'icat.dtauk3',
                           'icat.dtauk4',
                           'icat.dtauk5',
                           'icat.dtauk6',
                           'icat.fssk1',
                           'icat.fssk2',
                           'icat.ftauk1',
                           'icat.ftauk2',
                           'icat.ftauk3',
                           'icat.ftauk4',
                           'icat.ftauk5',
                           'icat.ftauk6']

        # Parameter specific prior intervals
        # Original values given in comments
        self.prior_intervals = [(0,100), # 30
                                (1,10),  # 6.0
                                (0,10),  # 1.068
                                (0,100), # 26.3
                                (1,100), # 30
                                (0,10),  # 1.068
                                (0,100), # 26.3
                                (1,100), # 30
                                (0,100), # 48
                                (1,10),  # 7.0
                                (0,0.1), # 0.0153
                                (0,100), # 61.7
                                (1,100), # 83.3
                                (0,0.1), # 0.015
                                (0,100), # 61.7
                                (1,100)] # 30

        # Specifying pertubation kernel
        # - Uniform random walk with width 10% of prior range
        self.kernel = []
        for pr in self.prior_intervals:
            param_range = pr[1]-pr[0]
            self.kernel.append(Dist.Uniform(-1*param_range/20, param_range/20))

        # Loading T-type channel experimental data
        vsteps, act_exp = data_icat.IV_DengFig1B()
        prepulses, inact_exp = data_icat.Inact_DengFig3B()
        intervals, rec_exp = data_icat.Recovery_DengFig4B()

        # Concatenate experimental data
        self.data_exp = [[vsteps, act_exp],
                         [prepulses, inact_exp],
                         [intervals, rec_exp]]

        # Setup simulations
        sim_act = sim.ActivationSim('icat.i_CaT', vhold=-80, thold=5000,
                                    vmin=min(vsteps), vmax=max(vsteps),
                                    dv=vsteps[1]-vsteps[0], tstep=300)
        sim_inact = sim.InactivationSim('icat.G_CaT', vhold=-20, thold=300,
                                        vmin=min(prepulses), vmax=max(prepulses),
                                        dv=prepulses[1]-prepulses[0], tstep=1000)
        sim_rec = sim.RecoverySim('icat.G_CaT', vhold=-80, thold=5000,
                                  vstep=-20, tstep1=300, tstep2=300,
                                  twaits=intervals)
        self.simulations = [sim_act, sim_inact, sim_rec]


class FastSodium(AbstractChannel):
    def __init__(self):
        self.name = 'ina'
        self.model_name = 'Bondarenko2004_iNa.mmt'

        # Parameters involved in ABC process
        self.parameters = ['ina.k_alpha1',
                           'ina.k_alpha2',
                           'ina.k_alpha3',
                           'ina.k_alpha4',
                           'ina.k_alpha5_11',
                           'ina.k_alpha5_12',
                           'ina.k_alpha5_13',
                           'ina.k_alpha6_11',
                           'ina.k_alpha6_12',
                           'ina.k_alpha6_13',
                           'ina.k_alpha7',
                           'ina.k_alpha8',
                           'ina.k_alpha9',
                           'ina.k_alpha10',
                           'ina.k_alpha11',
                           'ina.k_alpha12',
                           'ina.k_beta1',
                           'ina.k_beta2_11',
                           'ina.k_beta2_12',
                           'ina.k_beta2_13',
                           'ina.k_beta3',
                           'ina.k_beta4',
                           'ina.k_beta5',
                           'ina.k_beta6',
                           'ina.k_beta7',
                           'ina.k_beta8']
        # Parameter specific prior intervals
        self.prior_intervals = [(0,10),  # 0
                                (0,1.0), # 1
                                (0,10),  # 2
                                (1,1000),# 3
                                (1,100), # 4
                                (1,100), # 5
                                (1,100), # 6
                                (0,1.0), # 7
                                (0,1.0), # 8
                                (0,1.0), # 9
                                (0,1.0), # 10
                                (0,10),  # 11
                                (1,100), # 12
                                (0,1.0), # 13
                                (0,1e-6),# 14
                                (1,10),  # 15
                                (0,1.0), # 16
                                (-50,50),# 17
                                (-50,50),# 18
                                (-50,50),# 19
                                (1,100), # 20
                                (0,1.0), # 21
                                (0,1.0), # 22
                                (0,1e-2),# 23
                                (0,1e-4),# 24
                                (0,10)]  # 25

        # Specifying pertubation kernel
        # - Uniform random walk with width 10% of prior range
        self.kernel = []
        for pr in self.prior_intervals:
            param_range = pr[1]-pr[0]
            self.kernel.append(Dist.Uniform(-1*param_range/20, param_range/20))

        # Loading fast Na channel experimental data
        vsteps, act_exp = data_ina.IV_DiasFig6()
        prepulses, inact_exp = data_ina.Inact_FukudaFig5C()
        intervals, rec_exp = data_ina.Recovery_ZhangFig4B()

        # Concatenate experimental data
        self.data_exp = [[vsteps, act_exp],
                         [prepulses, inact_exp],
                         [intervals, rec_exp]]

        # Setup simulations
        sim_act = sim.ActivationSim('ina.i_Na', vhold=-80, thold=3000,
                                    vmin=min(vsteps), vmax=max(vsteps),
                                    dv=vsteps[1]-vsteps[0], tstep=100)
        sim_inact = sim.InactivationSim('ina.G_Na', vhold=-20, thold=20,
                                        vmin=min(prepulses), vmax=max(prepulses),
                                        dv=prepulses[1]-prepulses[0], tstep=500)
        sim_rec = sim.RecoverySim('ina.G_Na', vhold=-120, thold=3000,
                                  vstep=-30, tstep1=20, tstep2=20,
                                  twaits=intervals)
        self.simulations = [sim_act, sim_inact, sim_rec]


class UltraRapidlyActivatingDelayedPotassium(AbstractChannel):
    def __init__(self):
        self.name = 'ikur'
        self.model_name = 'Bondarenko2004_iKur.mmt'

        # Parameters involved in ABC process
        self.parameters = ['ikur.g_Kur',
                           'ikur.assk1',
                           'ikur.assk2',
                           'ikur.atauk1',
                           'ikur.atauk2',
                           'ikur.atauk3',
                           'ikur.issk1',
                           'ikur.issk2',
                           'ikur.itauk1',
                           'ikur.itauk2',
                           'ikur.itauk3',
                           'ikur.itauk4']

        # Parameter specific prior intervals
        self.prior_intervals = [(0, 1),     # 0.0975
                                (0, 100),   # 22.5
                                (1, 10),    # 7.5
                                (0, 1),     # 0.493
                                (0, 0.1),   # 0.0629
                                (0, 10),    # 2.058
                                (0, 100),   # 45.2
                                (1, 10),    # 5.7
                                (0, 10000), # 1200
                                (0, 1000),  # 170
                                (0, 100),   # 45.2
                                (1, 10)]    # 5.7

        # Specifying pertubation kernel
        # - Uniform random walk with width 10% of prior range
        self.kernel = []
        for pr in self.prior_intervals:
            param_range = pr[1]-pr[0]
            self.kernel.append(Dist.Uniform(-1*param_range/20, param_range/20))

        # Loading i_Kur channel experimental data
        vsteps, act_peaks_exp = data_ikur.IV_MuharaniFig2B()
        prepulses, inact_exp = data_ikur.Inact_XuFig9C()
        intervals, rec_exp = data_ikur.Recovery_XuFig10C()

        self.data_exp = [[vsteps, act_peaks_exp],
                         [prepulses, inact_exp],
                         [intervals, rec_exp]]

        # Setup simulations
        sim_act = sim.ActivationSim('ikur.i_Kur', vhold=-60, thold=5000,
                                    vmin=min(vsteps), vmax=max(vsteps),
                                    dv=vsteps[1]-vsteps[0], tstep=300)
        sim_inact = sim.InactivationSim('ikur.G_Kur', vhold=50, thold=5000,
                                        vmin=min(prepulses), vmax=max(prepulses),
                                        dv=prepulses[1]-prepulses[0], tstep=5000)
        sim_rec = sim.RecoverySim('ikur.G_Kur', vhold=-70, thold=5000,
                                  vstep=50, tstep1=9500, tstep2=9500,
                                  twaits=intervals)
        self.simulations = [sim_act, sim_inact, sim_rec]


class LTypeCalcium(AbstractChannel):
    def __init__(self):
        self.name = 'ical'
        self.model_name = 'Houston2017.mmt'

        # Parameters involved in ABC process
        self.parameters = ['ical.g_CaL',
                           'ical.E_CaL',
                           'ical.kalpha1',
                           'ical.kalpha2',
                           'ical.kalpha3',
                           'ical.kalpha4',
                           'ical.kalpha5',
                           'ical.kalpha6',
                           'ical.kalpha7',
                           'ical.kalpha1',
                           'ical.kalpha9',
                           'ical.kalpha10',
                           'ical.kalpha11',
                           'ical.kalpha12',
                           'ical.kbeta1',
                           'ical.kbeta2',
                           'ical.kbeta3',
                           'ical.kKpcf1',
                           'ical.kKpcf2',
                           'ical.kKpcf3']

        # Parameter specific prior intervals
        # Original values given in comments
        self.prior_intervals = [(0,1),   # 0.1729
                                (0,100), # 63.0
                                (0,1),   # 0.4
                                (0,100), # 12
                                (1,100), # 10
                                (0,10),  # 1.068
                                (0,1),   # 0.7
                                (0,100), # 40
                                (1,100), # 10
                                (0,1),   # 0.75
                                (0,100), # 20
                                (1,1000),# 400
                                (0,1),   # 0.12
                                (0,100), # 12
                                (1,100), # 10
                                (0,0.1), # 0.05
                                (0,100), # 12
                                (1,100), # 13
                                (0,100), # 13
                                (0,100), # 14.5
                                (1,1000)]# 100

        # Specifying pertubation kernel
        # - Uniform random walk with width 10% of prior range
        self.kernel = []
        for pr in self.prior_intervals:
            param_range = pr[1]-pr[0]
            self.kernel.append(Dist.Uniform(-1*param_range/20, param_range/20))

        # Loading T-type channel experimental data
        vsteps, act_exp = data_ical.IV_DiasFig7()
        prepulses, inact_exp = data_ical.Inact_RaoFig3C()
        intervals, rec_exp = data_ical.Recovery_RaoFig3D()

        # Concatenate experimental data
        self.data_exp = [[vsteps, act_exp],
                         [prepulses, inact_exp],
                         [intervals, rec_exp]]

        # Setup simulations
        sim_act = sim.ActivationSim('ical.i_CaL', vhold=-40, thold=200,
                                    vmin=min(vsteps), vmax=max(vsteps),
                                    dv=vsteps[1]-vsteps[0], tstep=250)
        sim_inact = sim.InactivationSim('ical.G_CaL', vhold=-20, thold=400,
                                        vmin=min(prepulses), vmax=max(prepulses),
                                        dv=prepulses[1]-prepulses[0], tstep=1000)
        sim_rec = sim.RecoverySim('ical.G_CaL', vhold=-40, thold=5000,
                                  vstep=20, tstep1=250, tstep2=250,
                                  twaits=intervals)
        self.simulations = [sim_act, sim_inact, sim_rec]

