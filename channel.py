### Class to build channel for ABCSolver.

import myokit
import distributions as dist
import matplotlib.pyplot as plt
import numpy as np
import dill as pickle


def add_subfig_letters(axes):
    """Add uppercase letters to sub figures in plot."""
    uppercase_letters = map(chr, range(65, 91))
    for i, ax in enumerate(axes.flatten()):
        ax.text(-0.07, 0.06,
                uppercase_letters[i], transform=ax.transAxes,
                fontsize=16, fontweight='bold', va='top', ha='right')
    return axes


class Channel():
    def __init__(self, modelfile, abc_params, vvar='membrane.V',
                 logvars=myokit.LOG_ALL):
        """Initialisation.

        Args:
            modelfile (str): Path to model for myokit to load.
            abc_params (Dict[str, Tuple[float]]): Dict mapping list of
                parameter name string to upper and lower limit of prior
                for ABC algorithm.
            vvar (str): String name of dependent variable in simulations,
                usually the voltage.
            logvars (Union[str, List[str]]): Model variables to log during
                simulation runs.
        """
        self.modelfile = modelfile
        self.vvar = vvar
        self.logvars = logvars

        self.param_names = []
        self.param_priors = []
        self.kernel = []
        for param, val in abc_params.iteritems():
            self.param_names.append(param)
            self.param_priors.append((val[0], val[1]))
            self.kernel.append(dist.Normal(0.0, 0.2 * (val[1]-val[0])))

        self.experiments = []
        self._sim = None

    def _generate_sim(self):
        """Creates class instance of Model and Simulation."""
        m, _, _ = myokit.load(self.modelfile)
        try:
            v = m.get(self.vvar)
        except:
            print('Model does not have vvar: ' + self.vvar)

        if v.is_state():
            v.demote()
        v.set_rhs(0)
        v.set_binding(None)

        # Check model has all parameters listed.
        for param_name in self.param_names:
            assert m.has_variable(param_name), (
                    'The parameter ' + param_name + ' does not exist.')

        self._sim = myokit.Simulation(m)

    def run_experiments(self, step_override=-1):
        """Run channel with defined experiments.

        Args:
            step_override (int): Steps between min and max of experiment,
                defaults to -1 which uses default steps from ExperimentData.

        Returns:
            Simulation output data points.
        """
        assert len(self.experiments) > 0, 'Need to add at least one experiment!'
        if self._sim is None:
            self._generate_sim()
        sim_results = []
        for exp in self.experiments:
            sim_results.append(exp.run(self._sim, self.vvar, self.logvars,
                                       step_override))
        return sim_results

    def eval_error(self, error_fn):
        """Evaluates error with experiment data over all experiments.

        Args:
            error_fn (Callable): Function to calculate error that accepts
                first argument as simulation results and second argument
                as ExperimentData object.

        Returns:
            Loss value as float.
        """
        if self._sim is None:
            self._generate_sim()
        tot_err = 0
        for exp in self.experiments:
            exp.run(self._sim, self.vvar, self.logvars)
            tot_err += exp.eval_err(error_fn)
        return tot_err

    def set_abc_params(self, new_params):
        """Set model ABC parameters to new values.

        Args:
            new_params (List[float]): List of new parameters corresponding
                to `param_names` attribute order.
        """
        # Need to reset all stored logs in experiments.
        for exp in self.experiments:
            exp.reset()
        if self._sim is None:
            self._generate_sim()
        else:
            self._sim.reset()
        for param_name, new_val in zip(self.param_names, new_params):
            try:
                self._sim.set_constant(param_name, new_val)
            except:
                print("Could not set parameter " + param_name
                      + " to value: " + str(new_val))

    def add_experiment(self, experiment):
        """Adds experiment to channel for ABC algorithm.

        Args:
            experiment (Experiment): Experiment class containing data and
                definition of stimulus protocol.
        """
        self.experiments.append(experiment)

    def reset(self):
        """Erases previously created simulations and experiment logs."""
        self._sim = None
        for exp in self.experiments:
            exp.reset()

    def plot_results(self, abc_distr, step=-1):
        """Plot results from ABC solver.

        Args:
            abc_distr (dist.Arbitrary): Posterior distribution estimate from
                ABC algorithm.

        Returns:
            Handle to figure with summary plots for each experiment.
        """
        pool = abc_distr.pool
        weights = abc_distr.weights

        # Original parameter values.
        self.reset()
        results_original = self.run_experiments(step)

        # Updated values for each ABC posterior particle.
        results_abc = []
        for i, params in enumerate(pool):
            self.set_abc_params(params)
            results_abc.append(self.run_experiments(step))
        results_abc = np.array(results_abc).swapaxes(0, 1)

        results_abc_mean = []
        results_abc_sd = []
        for exper in results_abc:
            d = dist.Arbitrary(exper[:, 1], weights)
            results_abc_mean.append(d.getmean())
            results_abc_sd.append(np.sqrt(d.getvar()))

        # Generate plots.
        plt.style.use('seaborn-colorblind')
        ncols = len(results_abc)
        x = [results_abc[i][0][0] for i in range(ncols)]
        fig, ax = plt.subplots(nrows=1, ncols=ncols, figsize=(3*ncols, 2.8))
        for i in range(ncols):
            if ncols > 1:
                axi = ax[i]
            else:
                axi = ax
            axi.plot(x[i], results_abc_mean[i], '-', label='ABC posterior')
            axi.fill_between(x[i], results_abc_mean[i]-results_abc_sd[i],
                             results_abc_mean[i]+results_abc_sd[i], alpha=0.25,
                             lw=0)
            if self.experiments[i].data.errs is not None:
                axi.errorbar(x=self.experiments[i].data.x,
                             y=self.experiments[i].data.y,
                             yerr=self.experiments[i].data.errs,
                             fmt='o')
            else:
                axi.plot(x=self.experiments[i].data.x,
                         y=self.experiments[i].data.y,
                         marker='o')

            if i == ncols-1:
                handles, labels = axi.get_legend_handles_labels()
                lgd = fig.legend(handles, labels, loc='lower center', ncol=3)
                bb = lgd.get_bbox_to_anchor().inverse_transformed(
                        fig.transFigure)
                bb.y0 -= 0.1
                lgd.set_bbox_to_anchor(bb, transform=fig.transFigure)

        # Mark letters on subfigures.
        if ncols > 1:
            ax = add_subfig_letters(ax)
        plt.tight_layout()
        return fig

    def save(self, filename):
        """Save channel and underlying experiments to disk."""
        self._sim = None
        pickle.dump(self, open(filename, 'wb'))

"""
class ikur(AbstractChannel):
    def __init__(self):
        self.name = 'ikur'
        self.model_name = 'Bondarenko2004_iKur.mmt'
        self.publication = 'Bondarenko et al., 2004'

        # Parameters involved in ABC process
        self.parameter_names = ['g_Kur',
                                'k_ass1',
                                'k_ass2',
                                'k_atau1',
                                'k_atau2',
                                'k_atau3',
                                'k_iss1',
                                'k_iss2',
                                'k_itau1',
                                'k_itau2']

        # Parameter specific prior intervals
        self.prior_intervals = [(0, 1),     # 0.0975
                                (0, 100),   # 22.5
                                (1, 10),    # 7.7
                                (0, 1),     # 0.493
                                (0, 10),    # 6.29
                                (0, 10),    # 2.058
                                (0, 100),   # 45.2
                                (1, 10),    # 5.7
                                (0, 10),    # 1.2
                                (0, 10)]    # 1.7

        # Edit which parameters to vary
        #use = [1,1,1,0,0,0,1,1,0,0]
        use = [1 for i in range(len(self.parameter_names))]
        self.parameter_names = [p for i,p in enumerate(self.parameter_names) if use[i] == 1]
        self.prior_intervals = [pr for i,pr in enumerate(self.prior_intervals) if use[i] == 1]

        # Loading experimental data
        vsteps, act_peaks_exp = data_ikur.IV_MaharaniFig2B()
        prepulses, inact_exp = data_ikur.Inact_BrouilleteFig6B()
        intervals, rec_exp = data_ikur.Recovery_BrouilleteFig6D()
        self.data_exp = [[vsteps, act_peaks_exp],
                         [prepulses, inact_exp],
                         [intervals, rec_exp]]

        # Define experimental setup for simulations
        setup_exp_act = {'sim_type': 'ActivationSim',
                         'variable': 'ikur.i_Kur', 'vhold': -60, 'thold': 6000,
                         'vsteps': vsteps, 'tstep': 300,
                         'xlabel': 'Membrane potential (mV)',
                         'ylabel': 'Current density (pA/pF)'}
        setup_exp_inact = {'sim_type': 'InactivationSim',
                           'variable': 'ikur.G_Kur', 'vhold': 30, 'thold': 2500,
                           'vsteps': prepulses, 'tstep': 5000,
                           'xlabel': 'Membrane potential (mV)',
                           'ylabel': 'Normalised conductance'}
        setup_exp_rec = {'sim_type': 'RecoverySim',
                         'variable': 'ikur.G_Kur', 'vhold': -80, 'thold': 2000,
                         'vstep': 30, 'tstep1': 1500, 'tstep2': 500,
                         'twaits': intervals,
                         'xlabel': 'Interval (ms)',
                         'ylabel': 'Relative recovery'}

        self.setup_exp = [setup_exp_act, setup_exp_inact, setup_exp_rec]

        super(ikur, self).__init__()


class ical(AbstractChannel):
    def __init__(self):
        self.name = 'ical'
        self.model_name = 'Houston2017_iCaL.mmt' # use full model
        self.publication = 'Korhonen et al., 2009'

        # Parameters involved in ABC process
        self.parameter_names = ['G_CaL',
                                'p1',
                                'p2',
                                'p3',
                                'p4',
                                'p5',
                                'p6',
                                'p7',
                                'p8',
                                'q1',
                                'q2',
                                'q3',
                                'q4',
                                'q5',
                                'q6',
                                'q7',
                                'q8',
                                'q9']

        # Parameter specific prior intervals
        # Original values given in comments
        self.prior_intervals = [(0, 0.001), # G_CaL
                                (-50, 50),  # p1
                                (0, 10),    # p2
                                (-100, 50),  # p3
                                (-50, 50),   # p4
                                (-50, 50),    # p5
                                (-50, 50),    # p6
                                (0, 200),   # p7
                                (0, 200),   # p8
                                (0, 100),   # q1
                                (0, 10),    # q2
                                (0, 10000), # q3
                                (0, 100),   # q4
                                (0, 1000),  # q5
                                (0, 1000),  # q6
                                (0, 100),   # q7
                                (0, 100),   # q8
                                (-500, 500)]  # q9

        # Loading experimental data
        # vsteps, act_exp = data_ical.IV_DiasFig7()
        vsteps, act_exp = data_ical.IV_RaoFig3B()
        act_exp = [17.1*a for a in act_exp] # maximum current reported by Dias et al (2014)
        prepulses, inact_exp = data_ical.Inact_RaoFig3C()
        self.data_exp = [[vsteps, act_exp],
                         [prepulses, inact_exp]]

        # Define experimental setup for simulations
        setup_exp_act = {'sim_type': 'ActivationSim',
                         'variable': 'ical.i_CaL', 'vhold': -80, 'thold': 2000,
                         'vsteps': vsteps, 'tstep': 250,
                         'normalise': False,
                         'xlabel': 'Membrane potential (mV)',
                         'ylabel': 'Current density (pA/pF)'}
        setup_exp_inact = {'sim_type': 'InactivationSim',
                           'variable': 'ical.i_CaL', 'vhold': -20, 'thold': 400,
                           'vsteps': prepulses, 'tstep': 1000,
                           'normalise': True,
                           'xlabel': 'Membrane potential (mV)',
                           'ylabel': 'Normalised conductance'}
        self.setup_exp = [setup_exp_act, setup_exp_inact]


        super(ical, self).__init__()


class ikr(AbstractChannel):
    def __init__(self):
        self.name = 'ikr'
        self.model_name = 'Korhonen2009_iKr.mmt'
        self.publication = 'Korhonen et al., 2009'

        # Parameters involved in ABC process
        self.parameter_names = ['g_Kr',
                                'p1',
                                'p2',
                                'p3',
                                'p4',
                                'p5',
                                'p6',
                                'q1',
                                'q2',
                                'q3',
                                'q4',
                                'q5',
                                'q6',
                                'k_f',
                                'k_b']

        # Parameter specific prior intervals
        self.prior_intervals = [(0, 1),     # 0.06
                                (0, 0.1),   # 0.022348
                                (0, 0.1),   # 0.01176
                                (0, 0.1),   # 0.013733
                                (0, 0.1),   # 0.038198
                                (0, 0.1),   # 0.090821
                                (0, 0.1),   # 0.023391
                                (0, 0.1),   # 0.047002
                                (-0.1, 0),  # -0.0631
                                (0, 0.0001),# 0.0000689
                                (-0.1, 0),  # -0.04178
                                (0, 0.01),  # 0.006497
                                (-0.1, 0),  # -0.03268
                                (0, 0.1),   # 0.023761
                                (0, 0.1)]   # 0.036778

        # Edit which parameters to vary
        use = [1 for i in range(len(self.parameter_names))]
        self.parameter_names = [p for i,p in enumerate(self.parameter_names) if use[i] == 1]
        self.prior_intervals = [pr for i,pr in enumerate(self.prior_intervals) if use[i] == 1]

        # Loading experimental data
        vsteps_IV, IV_exp, IV_errs, IV_N = data_ikr.IV_Toyoda()
        vsteps_act, act_exp, act_errs, act_N = data_ikr.Act_Toyoda()

        self.data_exp = [[vsteps_IV, IV_exp, IV_errs, IV_N],
                         [vsteps_act, act_exp, act_errs, act_N]]


        # Experimental setup
        setup_IV = {'sim_type': 'ActivationTailCurr',
                         'variable': 'ikr.i_Kr', 'vhold': -50, 'thold': 1000,
                         'vsteps': vsteps_IV, 'tstep': 1000,
                         'xlabel': 'Membrane potential (mV)',
                         'ylabel': 'Current density (pA/pF)'}
        setup_act = {'sim_type': 'InactivationSim',
                           'variable': 'ikr.i_Kr', 'vhold': -50, 'thold': 500,
                           'vsteps': vsteps_act, 'tstep': 1000,
                           'xlabel': 'Membrane potential (mV)',
                           'ylabel': 'Normalised tail current',
                           'normalise': True}
        self.setup_exp = [setup_IV, setup_act]

        super(ikr, self).__init__()


class iha(AbstractChannel):
    def __init__(self):
        self.name = 'iha'
        self.model_name = 'Majumder2016_iha.mmt'
        self.publication = 'Majumder et al., 2016'

        # Parameters involved in ABC process
        self.parameter_names = ['k_yss1',
                                'k_yss2',
                                'k_ytau1',
                                'k_ytau2',
                                'k_ytau3',
                                'k_ytau4',
                                'k_ytau5',
                                'k_ytau6',
                                'k_ytau7',
                                'k_i_haNa',
                                'g_ha']

        # Parameter specific prior intervals
        self.prior_intervals = [(0, 100),   # 78.65
                                (1, 10),    # 6.33
                                (0, 10),    # 1
                                (0, 1.0),   # 0.11885
                                (0, 100),   # 75
                                (1, 100),   # 28.37
                                (0, 1.0),   # 0.56236
                                (0, 100),   # 75
                                (0, 100),   # 14.19
                                (0, 1.0),   # 0.2
                                (0, 0.1)]   # 0.021

        # Edit which parameters to vary
        # use = [1,1,0,0,0,0,0,0,0,1,1]
        use = [1 for i in range(len(self.parameter_names))]
        self.parameter_names = [p for i,p in enumerate(self.parameter_names) if use[i] == 1]
        self.prior_intervals = [pr for i,pr in enumerate(self.prior_intervals) if use[i] == 1]

        # Loading experimental data
        vsteps, act_peaks_exp = data_iha.IV_Sartiana5B()
        prepulses, inact_exp = data_iha.Inact_Sartiana4B()
        vsteps2, time_consts = data_iha.Time_Sartiana4C()
        self.data_exp = [[vsteps, act_peaks_exp],
                         [prepulses, inact_exp],
                         [vsteps2, time_consts]]

        # Experimental setup
        setup_exp_act = {'sim_type': 'ActivationSim',
                         'variable': 'iha.i_ha', 'vhold': -120, 'thold': 1500,
                         'vsteps': vsteps, 'tstep': 1000,
                         'xlabel': 'Membrane potential (mV)',
                         'ylabel': 'Current density (pA/pF)'}
        setup_exp_inact = {'sim_type': 'InactivationSim',
                           'variable': 'iha.G_ha', 'vhold': 40, 'thold': 2000,
                           'vsteps': prepulses, 'tstep': 1500,
                           'xlabel': 'Membrane potential (mV)',
                           'ylabel': 'Normalised conductance'}
        setup_time_const = {'sim_type': 'TimeIndependentActivationSim',
                            'variable': 'iha.tau_y',
                            'vsteps': vsteps2,
                            'xlabel': 'Membrane potential (mV)',
                            'ylabel': 'Time constant (ms)'}


        self.setup_exp = [setup_exp_act, setup_exp_inact, setup_time_const]

        super(iha, self).__init__()


class ito(AbstractChannel):
    def __init__(self):
        self.name = 'ito'
        self.model_name = 'Takeuchi2013_ito.mmt'
        self.publication = 'Takeuchi et al., 2013'

        # Parameters involved in ABC process
        self.parameter_names = ['g_to',
                                'k_xss1',
                                'k_xss2',
                                'k_xtau1',
                                'k_xtau2',
                                'k_xtau3',
                                'k_yss1',
                                'k_yss2',
                                'k_ytau1',
                                'k_ytau2',
                                'k_ytau3',
                                'k_ytau4']

        # Parameter specific prior intervals
        self.prior_intervals = [(0, 1),     # 0.12375
                                (0, 10),    # 1
                                (0, 100),   # 11
                                (0, 10),    # 1.5
                                (0, 10),    # 3.5
                                (0, 100),   # 30
                                (0, 100),   # 40.5
                                (0, 100),   # 11.5
                                (0, 100),   # 21.21
                                (0, 100),   # 38.4525
                                (0, 100),   # 52.45
                                (0, 100)]   # 15.8827

        # Edit which parameters to vary
        use = [1,1,1,0,0,0,1,1,0,0,0,0]
        #use = [1 for i in range(len(self.parameter_names))]
        self.parameter_names = [p for i,p in enumerate(self.parameter_names) if use[i] == 1]
        self.prior_intervals = [pr for i,pr in enumerate(self.prior_intervals) if use[i] == 1]

        # Loading experimental data
        vsteps, act_peaks_exp = data_ito.IV_KaoFig6()
        prepulses, inact_exp = data_ito.Inact_XuFig9C()
        self.data_exp = [[vsteps, act_peaks_exp],
                         [prepulses, inact_exp]]

        # Define experimental setup for simulations
        setup_exp_act = {'sim_type': 'ActivationSim',
                         'variable': 'ito.i_to', 'vhold': -40, 'thold': 1000,
                         'vsteps': vsteps, 'tstep': 300,
                         'xlabel': 'Membrane potential (mV)',
                         'ylabel': 'Current density (pA/pF)'}
        setup_exp_inact = {'sim_type': 'InactivationSim',
                           'variable': 'ito.G_to', 'vhold': 50, 'thold': 500,
                           'vsteps': prepulses, 'tstep': 500,
                           'xlabel': 'Membrane potential (mV)',
                           'ylabel': 'Normalised conductance'}
        self.setup_exp = [setup_exp_act, setup_exp_inact]

        super(ito, self).__init__()


class ikach(AbstractChannel):
    def __init__(self):
        self.name = 'ikach'
        self.model_name = 'Majumder2016_iKAch.mmt'
        self.publication = 'Majumder et al., 2016'

        # Parameters involved in ABC process
        self.parameter_names = ['g_KAch',
                                'k_1',
                                'k_2',
                                'k_3',
                                'k_4',
                                'k_5',
                                'k_6',
                                'k_7',
                                'k_8']

        # Parameter specific prior intervals
        self.prior_intervals = [(0, 1),   # 0.37488
                                (0, 10),  # 3.5
                                (0, 10),   # 9.13652
                                (0, 1),    # 0.477811
                                (0, 0.1),  # 0.04
                                (0, 1),    # 0.23
                                (0, 1000), # 102
                                (0, 100),  # 10
                                (0, 100)]  # 10

        # Loading experimental data
        vsteps, act_peaks_exp = data_ikach.IV_KaoFig6()
        self.data_exp = [[vsteps, act_peaks_exp]]

        # Define experimental setup for simulations
        setup_exp_act = {'sim_type': 'TimeIndependentActivationSim',
                         'variable': 'ikach.i_KAch',
                         'vsteps': vsteps,
                         'xlabel': 'Membrane potential (mV)',
                         'ylabel': 'Current density (pA/pF)'}
        self.setup_exp = [setup_exp_act]

        super(ikach, self).__init__()


class ik1(AbstractChannel):
    def __init__(self):
        self.name = 'ik1'
        self.model_name = 'Korhonen2009_iK1.mmt'
        self.publication = 'Korhonen et al., 2009'

        self.parameter_names = ['g_K1',
                                #'k_1',
                                'k_2',
                                'k_3',
                                'k_4']

        self.prior_intervals = [(0, 0.2),   # 0.0515
                                #(-500, 500),  # 210
                                (0, 50),  # -6.1373
                                (0, 1),     # 0.1653
                                (0, 0.1)]   # 0.0319


        # Loading experimental data
        vsteps, act_peaks_exp = data_ik1.IV_GoldoniFig3D()
        # Convert to current densities using value reported for current
        #  density at -150mV in original paper (-42.2pA/pF)
        max_curr_density = -42.2
        act_peaks_exp = [p * max_curr_density / act_peaks_exp[0] for p in act_peaks_exp]
        self.data_exp = [[vsteps, act_peaks_exp]]

        # Define experimental setup for simulations
        setup_exp_act = {'sim_type': 'TimeIndependentActivationSim',
                         'variable': 'ik1.i_K1',
                         'vsteps': vsteps,
                         'xlabel': 'Membrane potential (mV)',
                         'ylabel': 'Current density (pA/pF)'}
        self.setup_exp = [setup_exp_act]

        super(ik1, self).__init__()

class full_sim(AbstractChannel):
    def __init__(self):
        self.name = 'fullsim'
        self.model_name = 'Houston2017.mmt'
        self.publication = 'na'

        self.parameter_names =['inak.i_NaK_max','incx.k_NCX','icab.g_Cab','inab.g_Nab','ryanodine_receptors.k_RyR','serca.V_max']

        self.prior_intervals = [(0, 10),    # 2.7
                                (0, 1e-15), # 2.268e-16
                                (0, 0.001), # 0.0008
                                (0, 0.01),  # 0.0026
                                (0, 0.1),   # 0.01
                                (0, 5)      # 0.9996
                                ]

        self.data_exp = [['v_rp',
                          'APD90'#,
                          #'APA',
                          #'ca_i_diastole',
                          #'ca_amplitude',
                          #'ca_time_to_peak',
                          #'ca_sr_diastole',
                          #'ca_i_systole',
                          #'ca_sr_systole',
                          #'CaT50'
                          #'CaT90'
                         ],
                         [-67.0,
                           42#,
                           #105,
                           # 0.6,
                           # #0.138,
                           # 59,
                           # # 1000,
                           # 0.7,
                           # # 500,
                           # 157,
                           # 397
                          ]
                          ]
        self.setup_exp = [{'sim_type': 'FullSimulation'}]

class ina(AbstractChannel):
    def __init__(self):
        self.name = 'ina'
        self.model_name = 'Korhonen2009_iNa.mmt'
        self.publication = 'Korhonen et al., 2009'

        # Parameters involved in ABC process
        self.parameter_names = ['g_Na',
                                'E_Na',
                                'p1',
                                'p2',
                                'p3',
                                'p4',
                                'p5',
                                'p6',
                                'p7',
                                'q1',
                                'q2']
        # Parameter specific prior intervals
        self.prior_intervals = [(0, 100),       # 35
                                (0, 100),       # 68.2
                                (0, 100),       # 45
                                (-10, 0),       # -6.5
                                (0, 1),         # 1.36 * 0.32
                                (0, 100),       # 47.13
                                (-1, 0),        # -0.1
                                (0, 1),         # 1.36 * 0.08
                                (0, 100),       # 11
                                (0, 100),       # 76.1
                                (0, 10)         # 6.07
                                ]

        # Loading experimental data
        vsteps_IV, IV_exp, IV_exp_sem, IV_exp_sd = data_ina.IV_Nakajima()
        vsteps_act, act_exp, act_exp_sem, act_exp_sd = data_ina.Act_Nakajima()
        vsteps_inact, inact_exp, inact_exp_sem, inact_exp_sd = data_ina.Inact_Nakajima()

        self.data_exp = [[vsteps_IV, IV_exp, IV_exp_sem, IV_exp_sd],
                         [vsteps_act, act_exp, act_exp_sem, act_exp_sd],
                         [vsteps_inact, inact_exp, inact_exp_sem, inact_exp_sd]]

        # Define experimental setup for simulations
        setup_exp_IV = {'sim_type': 'ActivationSim',
                        'variable': 'ina.i_Na', 'vhold': -120, 'thold': 500,
                        'vsteps': vsteps_IV, 'tstep': 20,
                        'xlabel': 'Membrane potential (mV)',
                        'ylabel': 'Current density (pA/pF)'}
        
        setup_exp_act = {'sim_type': 'ActivationSim',
                         'variable': 'ina.G_Na', 'vhold': -120, 'thold': 500,
                         'vsteps': vsteps_act, 'tstep': 20,
                         'xlabel': 'Membrane potential (mV)',
                         'ylabel': 'Normalised conductance',
                         'normalise': True}
        
        setup_exp_inact = {'sim_type': 'InactivationSim',
                           'variable': 'ina.G_Na', 'vhold': -20, 'thold': 20,
                           'vsteps': vsteps_inact, 'tstep': 500,
                           'xlabel': 'Membrane potential (mV)',
                           'ylabel': 'Normalised conductance'}
       
        self.setup_exp = [setup_exp_IV, setup_exp_act, setup_exp_inact]

        super(ina, self).__init__()

"""
