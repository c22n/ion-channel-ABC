from .distance import IonChannelDistance
from .experiment import (Experiment,
                         setup)
from pyabc.visualization.kde import kde_1d
import numpy as np
import pandas as pd
import warnings
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Callable, List


def normalise(df, limits=None):
    result = df.copy()
    for feature_name in df.columns:
        if limits is None:
            max_value = df[feature_name].max()
            min_value = df[feature_name].min()
        else:
            max_value = limits[feature_name][1]
            min_value = limits[feature_name][0]
        result[feature_name] = ((df[feature_name] - min_value) /
                                (max_value - min_value))
    return result


def plot_sim_results(modelfile: str,
                     *experiments: Experiment,
                     pacevar: str='membrane.V',
                     tvar: str='phys.T',
                     prev_runs: List[str]=[],
                     df: pd.DataFrame=None,
                     w: np.ndarray=None,
                     n_samples: int=100) -> sns.FacetGrid:
    """Plot output of ABC against experimental and/or original output.

    Args:
        modelfile (str): Path to Myokit MMT file.
        *experiments (Experiment): Experiments to plot.
        df (pd.DataFrame): Dataframe of parameters (see pyabc.History).
            If `None` runs model with current parameter settings.
        w (np.ndarray): The corresponding weights (see pyabc.History).
        n_samples (int): Number of ABC posterior samples used to
            generate summary output.

    Returns
        sns.FacetGrid: Plots of measured output.
    """

    observations, model, summary_statistics = setup(modelfile,
                                                    *experiments,
                                                    pacevar=pacevar,
                                                    tvar=tvar,
                                                    prev_runs=prev_runs,
                                                    normalise=False)

    # Generate model samples from ABC approximate posterior or create default
    # samples if posterior was not provided as input.
    model_samples = pd.DataFrame({})
    if df is not None:
        posterior_samples = (df.sample(n=n_samples, weights=w, replace=True)
                               .to_dict(orient='records'))
    else:
        posterior_samples = [{}]

    for i, th in enumerate(posterior_samples):
        results = summary_statistics(model(th))
        output = pd.DataFrame({'x': observations.x,
                               'y': list(results.values()),
                               'exp_id': observations.exp_id})
        output['sample'] = i
        model_samples = model_samples.append(output, ignore_index=True)

    # Function for mapping observations onto plot later
    def measured_plot(**kwargs):
        measurements = kwargs.pop('measurements')
        data = kwargs.pop('data')
        exp = data['exp_id'].unique()[0]
        plt.errorbar(measurements.loc[measurements['exp_id']==exp]['x'],
                     measurements.loc[measurements['exp_id']==exp]['y'],
                     yerr=np.sqrt(measurements.loc[measurements['exp_id']==exp]['variance']),
                     #label='obs',
                     ls='None', marker='x', c='k')

    # Actually make the plot
    #with sns.color_palette("gray"):
    grid = sns.relplot(x='x', y='y',
                       col='exp_id', kind='line',
                       data=model_samples,
                       ci='sd',
                       facet_kws={'sharex': 'col',
                                  'sharey': 'col'})

    # Format lines in all plots
    for ax in grid.axes.flatten():
        for l in ax.lines:
            l.set_linestyle('-')

    grid = grid.map_dataframe(measured_plot, measurements=observations)
    #grid = grid.add_legend()

    return grid


def plot_distance_weights(
        observations: pd.DataFrame,
        distance_fn: IonChannelDistance,
        sum_stats_fn: Callable) -> sns.FacetGrid:
    """Plots weights of each sampling statistic in distance function.

    Args:
        observations (pd.DataFrame): Observation results.
        distance_fn (IonChannelDistance): ABC distance function.
        sum_stats_fn (Callable): ABC summary statistics calculator.

    Returns:
        sns.FacetGrid: Bar graph showing relative weights for each
            data point in distance function.
    """
    # Initialize weights
    _ = distance_fn(observations, observations, 0)

    w = distance_fn.w[0]
    exp = distance_fn.exp_map
    m = np.max(exp)

    df = pd.DataFrame({'data_point': list(w.keys()),
                       'weights': list(w.values())})

    pal = sns.cubehelix_palette(len(w), rot=-.25, light=.7)
    grid = (sns.catplot(x='data_point', y='weights',
                        data=df, aspect=m,
                        kind='bar',
                        palette=pal)
                        .set(xticklabels=[],
                             xticks=[]))
    for ax in grid.axes.flatten():
        ax.axhline(y=1, color='k', linestyle='--')
    return grid


def plot_parameters_kde(df, w, limits, aspect=None, height=None):
    """Plot grid of parameter KDE density estimates.

    EXPERIMENTAL: probably better off using functions from `pyabc`
    library to plot KDEs.
    """

    if aspect is None:
        aspect=5
    if height is None:
        height=.5
    sns.set(style="white", rc={"axes.facecolor": (0, 0, 0, 0)})
    pal = sns.cubehelix_palette(len(limits), rot=-.25, light=.7)

    df_melt = pd.melt(normalise(df, limits))
    g = sns.FacetGrid(df_melt, row="name", hue="name", aspect=aspect,
                      height=height, palette=pal, sharex=False)

    def custom_kde(x, shade=False, **kwargs):
        df = pd.concat((x,), axis=1)
        x_vals, pdf = kde_1d(df, w, x.name, xmin=0.0, xmax=1.0, numx=1000)
        pdf = (pdf-pdf.min())/(pdf.max()-pdf.min())
        facecolor = kwargs.pop("facecolor", None)
        ax = plt.gca()
        line, = ax.plot(x_vals, pdf, **kwargs)
        color = line.get_color()
        line.remove()
        kwargs.pop("color", None)
        facecolor = color if facecolor is None else facecolor
        ax.plot(x_vals, pdf, color=color, **kwargs)
        shade_kws = dict(
                facecolor=facecolor,
                alpha=kwargs.get("alpha", 0.25),
                clip_on=kwargs.get("clip_on", True),
                zorder=kwargs.get("zorder", 1)
                )
        if shade:
            ax.fill_between(x_vals, 0, pdf, **shade_kws)
        ax.set_ylim(0, auto=None)
        return ax

    g.map(custom_kde, "value", alpha=1, lw=1, shade=True)
    g.map(custom_kde, "value", color="w", lw=1)
    g.map(plt.axhline, y=0, lw=2, clip_on=False)

    def label(x, color, label):
        ax = plt.gca()
        ax.text(0, .2, label, fontweight="bold", color=color,
                ha="left", va="center", transform=ax.transAxes)
    g.map(label, "name")

    def xlims(x, color, label):
        ax = plt.gca()
        ax.set(xticks=[0, 1])
        ax.set(xticklabels=[limits[label][0], limits[label][1]])
    g.map(xlims, "name")

    # Set subplots to overlap
    g.fig.subplots_adjust(hspace=-.25)

    # Update axes details
    g.set_xlabels("posterior")
    g.set_titles("")
    g.set(yticks=[])
    g.despine(bottom=True, left=True)

    return g
