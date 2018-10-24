from pyabc.distance_functions import PNormDistance
from pyabc.acceptor import SimpleAcceptor, accept_use_complete_history
from pyabc.model import Model
from pyabc.transition.multivariatenormal import MultivariateNormalTransition

from .experiment import Experiment
import myokit

import scipy.stats as stats
import numpy as np
import warnings
import pandas as pd
import subprocess
import io
from typing import List, Dict, Union
import logging
import signal # for function timeouts
from contextlib import contextmanager # for function timeouts

abclogger = logging.getLogger('ABC')


class TimeoutException(Exception): pass


@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


def ion_channel_sum_stats_calculator(model_output: pd.DataFrame) -> dict:
    """
    Converts myokit simulation wrapper output into ABC-readable output.
    """
    if not model_output.empty:
        keys = range(len(model_output))
        return dict(zip(keys, model_output.y))
    else:
        return {}


class EfficientMultivariateNormalTransition(MultivariateNormalTransition):
    """
    Efficient implementation of multivariate normal for multiple samples.

    Only overrides the default `rvs` method.
    """
    def rvs(self, size=None):
        if size is None:
            return self.rvs_single()
        else:
            sample = (self.X.sample(n=size, replace=True, weights=self.w)
                      .iloc[:])
            perturbed = (sample +
                         np.random.multivariate_normal(
                             np.zeros(self.cov.shape[0]),
                             self.cov,
                             size=size))
            return pd.DataFrame(perturbed)


class IonChannelModel(Model):
    """
    Pyabc model to run myokit simulations for ion channel.

    Parameters
    ----------

    channel: str
        Shortcode name of channel to simulate.

    modelfile: str
        Location myokit mmt file defining model formulation.

    vvar: str
        Name of voltage variable in `modelfile`.

    logvars: List[str]
        Variables to log during simulation runs.

    external_par_samples: List[Dict[str, float]]
        List of dictionaries of parameters to randomly choose external to the
        ABC fitting process. These are set randomly prior to running each
        simulation.
    """

    def __init__(self,
                 channel: str,
                 modelfile: str,
                 vvar: str,
                 logvars: List[str]=myokit.LOG_ALL,
                 external_par_samples: List[Dict[str, float]]=None):

        self.channel = channel
        self.external_par_samples = external_par_samples
        self.modelfile = modelfile

        self.vvar = vvar
        self.logvars = logvars

        self._sim = None
        self.experiments = []

        super().__init__(name = channel+"_model")

    def sample(self,
               pars: Dict[str, float],
               n_x: int=None,
               exp_num: int=None,
               logvars: List[str]=None) -> pd.DataFrame:

        if self.external_par_samples is not None:
            full_pars = dict(np.random.choice(self.external_par_samples),
                             **pars)
        else:
            full_pars = pars

        # Run myokit simulation and return empty dataframe if failure.
        try:
            results = self._simulate(n_x, exp_num, logvars, **full_pars)
        except:
            results = pd.DataFrame({})
        return results

    def add_external_par_samples(self,
                                 samples: List[Dict[str, float]]=None):
        self.external_par_samples = samples

    def _simulate(self,
                  n_x: int=None,
                  exp_num: int=None,
                  logvars: List[str]=None,
                  **pars) -> pd.DataFrame:
        """
        Simulate model in myokit.

        Parameters
        ----------

        n_x: int
            Resolution of independent variable to simulate. If `None` uses the
            default resolution of the observed data defined by the experiment.

        exp_num: int
            Number of specific experiment to run on its own.

        logvars: List[str]
            List of variables to log from simulation.

        pars: Dict[str, float]
            Model parameters as separate kwargs.

        Returns
        -------

        Pandas dataframe with simulated output.

        Errors
        ------

        Throws a RuntimeError if the simulation fails.
        Throws a ValueError if exp_num is outside range of experiments.
        """

        if logvars is None:
            logvars = self.logvars

        # Sanity check for experiment number
        if (exp_num is not None and
                (exp_num < 0 or exp_num > len(self.experiments)-1)):
            raise ValueError("Experiment number is outside range.")
       

        # Get original parameter values to reset later
        original_vals = self.get_parameter_vals(list(pars.keys()))

        self.set_parameters(**pars)
        all_results = pd.DataFrame({})

        for i, e in enumerate(self.experiments):
            if exp_num is not None and i is not exp_num:
                continue

            try:
                with time_limit(5):
                    results = e.run(sim=self._sim,
                                    vvar=self.vvar,
                                    logvars=logvars,
                                    n_x=n_x)
            except:
                self.set_parameters(**original_vals)
                raise RuntimeError("Failed simulation.")

            results['exp'] = i

            if i is 0:
                all_results = results
            else:
                all_results = all_results.append(results)
    
        # Reset to original values
        self.set_parameters(**original_vals)

        return all_results

    def set_parameters(self, **pars):
        """
        Set parameters of simulation model.
        """

        # Make sure a myokit simulation exists
        if self._sim is None:
            self._build_simulation()
        else:
            self._sim.reset()

        # Set parameters
        for name, value in pars.items():
            try:
                if value is not None:
                    if '.' not in name:
                        self._sim.set_constant(
                                self.channel+'.'+name, value)
                    else:
                        self._sim.set_constant(name, value)
            except:
                raise ValueError('Could not set parameter {0} to {1}'
                                 .format(name, value))

    def get_parameter_vals(self, parameters: List[str]) -> Dict[str, float]:
        """
        Return dict with value of variables or nan if variable does not exist.
        """
        m, _, _ = myokit.load(self.modelfile)
        parameter_values = {} 
        for p in parameters:
            if m.has_variable(p):
                parameter_values[p] = m.get(p).value()
            else:
                parameter_values[p] = np.nan
        return parameter_values

    def _build_simulation(self):
        """
        Creates a class instance of myokit.Model and myokit.Simulation.
        """
        m, _, _ = myokit.load(self.modelfile)
        try:
            v = m.get(self.vvar)
        except:
            raise ValueError('Model does not have vvar: {}'
                             .format(self.vvar))
        if v.is_state():
            v.demote()
        v.set_rhs(0)
        v.set_binding(None)
        self._sim = myokit.Simulation(m)

    def add_experiments(self,
                        experiments: Union[Experiment, List[Experiment]]):
        """
        Add Experiment object to be run when model is sampled.
        """
        self.experiments.extend(experiments)

    def get_experiment_data(self) -> pd.DataFrame:
        """
        Returns experimental data from Experiments.
        """
        measurements = pd.DataFrame(columns=['exp', 'x', 'y', 'errs'])
        for i, exp in enumerate(self.experiments):
            data = exp.data.df
            data['exp'] = i
            measurements = measurements.append(data, ignore_index=True,
                                               sort=True)
        return measurements


class IonChannelAcceptor(SimpleAcceptor):
    """
    Identical to SimpleAcceptor other than uses complete history.
    """
    def __init__(self):
        fun = accept_use_complete_history
        super().__init__(fun)


class IonChannelDistance(PNormDistance):
    """
    Distance function to automatically set weights for a given ion channel.

    Reduces weighting between separate experimental data sets according
    to number of data points, scale of experiment y-axis, and error bars
    in reported values.

    Calling is identical to pyabc.distance_functions.PNormDistance, other than
    it checks whether the simulated input is empty, in which case it returns
    np.inf.

    Parameters
    ----------

    obs: Dict[int, float]
        Mapping from data point index to value.

    exp_map: Dict[int, int]
        Mapping from data point index to separate experiments.

    err_bars: Dict[int, float]
        Mapping from data point index to absolute error bars.

    err_th: float
        Upper threshold of errors as percentage of experiment IQR to include 
        in down-weighting, avoids overweighting of points with very low 
        uncertainty. Defaults to 0.0, i.e. no threshold for the errors.
    """

    def __init__(self,
                 obs: Dict[int, float],
                 exp_map: Dict[int, int],
                 err_bars: Dict[int, float]=None,
                 err_th: float=0.0):

        self.exp_map = exp_map
        data_by_exp = self._group_data_by_exp(obs)

        N_by_exp = {k: len(l) for k, l in data_by_exp.items()}
        IQR_by_exp = self._calculate_experiment_IQR(data_by_exp)

        # Optionally include error bars
        if err_bars is None:
            err_by_pt = [1.0] * len(obs)
        else:
            err_by_pt = self._calculate_err_by_pt(
                    err_bars, err_th, IQR_by_exp)

        # Create dictionary of weights
        w = {} 
        for ss, exp_num in self.exp_map.items():
            w[ss] = 1. / (err_by_pt[ss] * np.sqrt(N_by_exp[exp_num] *
                                                  IQR_by_exp[exp_num]))

        mean_weight = np.mean(list(w.values()))
        for key in w.keys():
            w[key] /= mean_weight

        abclogger.debug('ion channel weights: {}'.format(w))

        # now initialize PNormDistance
        super().__init__(p=2, w={0: w})

    def __call__(self,
                 t: int,
                 x: dict,
                 y: dict) -> float:
        # x is the simulated output
        if (len(x) is 0 or
            any(np.isinf(xi) for xi in x.values())):
            return np.inf

        # Catch possible runtime overflow warnings
        warnings.simplefilter('error', RuntimeWarning)
        try:
            distance = super().__call__(t, x, y)
            warnings.resetwarnings()
            return distance
        except RuntimeWarning:
            warnings.resetwarnings()
            return np.inf

    def _group_data_by_exp(
            self,
            obs: Dict[int, float]) -> Dict[int, List[float]]:
        """
        Computes a dictionary mapping experiment number to data points.
        """
        data_by_exp = {}
        for index, value in obs.items():
            exp_num = self.exp_map[index]
            if exp_num not in data_by_exp:
                data_by_exp[exp_num] = []
            data_by_exp[exp_num].append(value)
        return data_by_exp

    def _calculate_experiment_IQR(
            self,
            data_by_exp: Dict[int, List[float]]) -> Dict[int, float]:
        """
        Calculate the interquartile range of each experimental dataset.
        """
        IQR_by_exp = {}
        for exp_num, l_obs in data_by_exp.items():
            if len(l_obs) > 1:
                weight = stats.iqr(l_obs)
                if weight == 0:
                    # each value is the same
                    weight = 1.0 # TODO: better way to handle this edge case?
            else:
                weight = abs(l_obs[0])
            IQR_by_exp[exp_num] = weight
        return IQR_by_exp

    def _calculate_err_by_pt(
            self,
            err_bars: Dict[int, float],
            err_th: float, 
            IQR_by_exp: Dict[int, float]) -> Dict[int, float]:
        """
        Calculates weighting due to error bars for each observed data point.
        """

        err_by_pt = {}
        err_by_exp = {}
        for index, err in err_bars.items():
            exp_num = self.exp_map[index]

            if exp_num not in err_by_exp:
                err_by_exp[exp_num] = []

            if np.isnan(err):
                # If no error bar value supplied
                weight = 1.0
            else:
                weight = err
                if err_th > 0.0:
                    iqr = IQR_by_exp[exp_num]
                    # Error threshold given as % of experiment IQR
                    th = err_th * iqr
                    weight /= th
                    # If weight is below the threshold, no downweighting
                    if weight < 1.0:
                        weight = 1.0
            err_by_pt[index] = weight
            err_by_exp[exp_num].append(weight)

        # Normalise between all points in a given experiment
        for index, weight in err_by_pt.items():
            exp_num = self.exp_map[index]
            if len(err_by_exp[exp_num]) > 1:
                err_by_pt[index] = (err_by_pt[index] / sum(err_by_exp[exp_num]) *
                                    len(err_by_exp[exp_num]))
        return err_by_pt
