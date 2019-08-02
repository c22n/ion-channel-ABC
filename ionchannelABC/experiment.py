from functools import wraps, reduce
import numpy as np
import myokit
import pandas as pd
from typing import List, Callable, Dict, Union, Tuple
import warnings


def log_transform(f):
    @wraps(f)
    def log_transformed(**log_kwargs):
        kwargs = dict([(key[4:], 10**value) if key.startswith("log")
                       else (key, value)
                       for key, value in log_kwargs.items()])
        return f(**kwargs)
    return log_transformed


def combine_sum_stats(*functions):
    def sum_stats_fn(x):
        sum_stats = []
        for i, flist in enumerate(functions):
            for f in flist:
                sum_stats = sum_stats+f(x[i])
        return sum_stats
    return lambda x: sum_stats_fn(x)


class Experiment:
    """Contains related information from patch clamp experiment."""
    def __init__(self,
                 dataset: Union[np.ndarray, List[np.ndarray]],
                 protocol: myokit.Protocol,
                 conditions: Dict[str, float],
                 sum_stats: Union[Callable, List[Callable]],
                 tvar: str='membrane.T',
                 Q10: float=None,
                 Q10_factor: int=0,
                 description: str=""):
        """Initialisation.

        Args:
            dataset (Union[np.ndarray, List[np.ndarray]]):
                Experimental data in format (x, y, variance). More than one
                dataset can be supplied in a list and will be assigned
                separate exp_id. Care must be taken in this case that sum stats
                function produces appropriate output.
            protocol (myokit.Protocol): Voltage step protocol from experiment.
            conditions (Dict[str, float]): Reported experimental conditions.
            sum_stats (Union[Callable, List[Callable]]): Summary statistics
                function(s) which may be list of functions as more than one
                measurement could be made from one protocol.
            tvar: Name of temperature condition variable in `conditions`.
            Q10 (float): Optional Q10 value to be used to adjust any
                values to temperature of model.
            Q10_factor (int): Optional factor for Q10 temperature
                conversion. The factor is used when adjusting values
                using the Q10 equation to differentiate between
                different types of data.
                Defaults to zero which will give no adjustment.
                Set to 1 for IV datasets, 0 for steady-state datasets and
                -1 for rate constant datasets.
            description (str): Optional descriptor.
        """
        if isinstance(dataset, list):
            self._dataset = dataset
        else:
            self._dataset = [dataset]

        self._protocol = protocol

        if isinstance(sum_stats, list):
            self._sum_stats = sum_stats
        else:
            self._sum_stats = [sum_stats]

        conditions_exp = conditions.copy() # in case conditions used by other experiments
        self._temperature = conditions_exp.pop(tvar, None)
        self._conditions = conditions_exp
        self._Q10 = Q10
        self._Q10_factor = Q10_factor
        self._description = description

    def __call__(self) -> None:
        """Print descriptor"""
        print(self._description)

    @property
    def dataset(self) -> np.ndarray:
        return self._dataset

    @property
    def protocol(self) -> myokit.Protocol:
        return self._protocol

    @property
    def conditions(self) -> Dict:
        return self._conditions

    @property
    def sum_stats(self) -> Callable:
        return self._sum_stats

    @property
    def temperature(self) -> float:
        return self._temperature

    @property
    def Q10(self) -> float:
        return self._Q10

    @property
    def Q10_factor(self) -> int:
        return self._Q10_factor


def setup(modelfile: str,
          *experiments: Experiment,
          vvar: str='membrane.V',
          tvar: str='membrane.T',
          logvars: List[str]=myokit.LOG_ALL,
          normalise: bool=True,
          ) -> Tuple[pd.DataFrame, Callable, Callable]:
    """Combine chosen experiments into inputs for ABC.

    Args:
        modelfile (str): Path to Myokit MMT file.
        *experiments (Experiment): Any number of experiments to run in ABC.
        vvar (str): Optionally specify name of membrane voltage in modelfile.
        tvar (str): Optionally specify name of temperature in modelfile.
        logvars (str): Optionally specify variables to log in simulations.

    Returns:
        Tuple[pd.DataFrame, Callable, Callable]:
            Observations combined from experiments.
            Model function to run combined protocols from experiments.
            Summary statistics function to convert 'raw' simulation output.
    """

    # Create Myokit model instance
    m = myokit.load_model(modelfile)
    v = m.get(vvar)
    v.demote()
    v.set_rhs(0)
    v.set_binding('pace')
    model_temperature = m.get(tvar).value()

    # Initialise combined variables
    observations = get_observations_df(list(experiments),
                                       normalise=normalise,
                                       temp_adjust=True,
                                       model_temperature=model_temperature)

    # Combine protocols into Myokit simulations
    simulations, times = [], []
    for exp in list(experiments):
        s = myokit.Simulation(m, exp.protocol)
        for ci, vi in exp.conditions.items():
            s.set_constant(ci, vi)
        simulations.append(s)
        times.append(exp.protocol.characteristic_time())

    # Create model function
    def simulate_model(**pars):
        sim_output = []
        for sim, time in zip(simulations, times):
            for p, v in pars.items():
                try:
                    sim.set_constant(p, v)
                except:
                    warnings.warn("Could not set value of {}"
                                  .format(p))
                    return None
            sim.reset()
            try:
                sim_output.append(sim.run(time, log=logvars))
            except:
                del(sim_output)
                return None
        return sim_output
    def model(x):
        return log_transform(simulate_model)(**x)

    # Combine summary statistic functions
    normalise_factor = {}
    for i, f in enumerate(observations.normalise_factor):
        normalise_factor[i] = f
    sum_stats_combined = combine_sum_stats(
        *[e.sum_stats for e in list(experiments)]
    )
    def summary_statistics(data):
        if data is None:
            return {}
        ss = {str(i): val/normalise_factor[i]
              for i, val in enumerate(sum_stats_combined(data))}
        return ss

    return observations, model, summary_statistics


def get_observations_df(experiments: List[Experiment],
                        normalise: bool=True,
                        temp_adjust: bool=False,
                        model_temperature: float=None) -> pd.DataFrame:
    """Returns observations dataframe with combined datasets.

    Args:
        *experiments (Experiment): Any number of experiments to run in ABC.
        normalise (bool): Whether to normalise dependent variable and
            variance in output dataframe. Defaults to True.
        temp_adjust (bool): Whether to adjust to temperature in
            modelfile. Defaults to False.
        model_temperature (float): Temperature to adjust values to. Must
            be supplied if `temp_adjust=True`.

    Returns:
        pd.DataFrame: Combined datasets in dataframe with columns
            `x`, `y`, `variance` and `exp_id`.
    """
    cols = ['x', 'y', 'variance', 'exp_id', 'normalise_factor']
    observations = pd.DataFrame(columns=cols)

    exp_id = 0
    for exp in experiments:
        if exp.temperature is None and temp_adjust:
            warnings.warn('No experimental temperature provided so data not adjusted')

        # Combine datasets
        for d in exp.dataset:
            dataset = np.copy(d)

            if (temp_adjust and
                exp.temperature is not None and
                model_temperature is not None and
                model_temperature != exp.temperature and
                exp.Q10 is not None and
                exp.Q10_factor is not None):
                dataset = adjust_for_temperature(dataset,
                                                 exp.temperature,
                                                 model_temperature,
                                                 exp.Q10,
                                                 exp.Q10_factor)

            if normalise:
                normalise_factor, dataset = normalise_dataset(dataset)
            else:
                normalise_factor = 1.

            dataset = dataset.T.tolist()
            dataset = [d_+[str(exp_id), normalise_factor] for d_ in dataset]
            observations = observations.append(
                pd.DataFrame(dataset, columns=cols),
                ignore_index=True
            )
            exp_id += 1
    return observations


def normalise_dataset(dataset: np.ndarray) -> Tuple[float, np.ndarray]:
    """Normalise the dependent variable and variance.

    Returns both the normalising factor and normalised dataset.
    """
    # Dependent variable
    y = dataset[1]
    max_y = np.max(np.abs(y))
    y = [y_/max_y for y_ in y]

    # Variance (convert back to SD to normalise)
    variance = dataset[2]
    variance = (np.sqrt(variance)/max_y)**2

    return max_y, np.array([dataset[0], y, variance])


def adjust_for_temperature(dataset: List[float],
                           exp_temperature: float,
                           model_temperature: float,
                           Q10: float,
                           Q10_factor: int) -> List[float]:
    """Adjusts dependent variable and variance for temperature."""
    A = Q10**(Q10_factor*(model_temperature-exp_temperature)/10)

    # Dependent variable
    y = A*dataset[1]

    # Variance (convert back to SD to adjust)
    variance = (A*np.sqrt(dataset[2]))**2

    return np.array([dataset[0], y, variance])
