"""
Experiments from [Nygren1998]
Charles Houston 2019-10-18
"""
from ionchannelABC.experiment import Experiment
from ionchannelABC.protocol import recovery
import data.ito.Nygren1998.data_Nygren1998 as data
import numpy as np
import myokit

import warnings
from scipy.optimize import OptimizeWarning
import scipy.optimize as so


Q10_tau = 2.2 # [Wang1993]


fit_threshold = 0.9


#
# Inactivation kinetics [Nygren1998]
#
nygren_inact_kin_desc = """
    Inactivation kinetics for ito in human
    atrial myocytes [Nygren1998] cf Fig 4c.

    It is not clear where these data are from. We assume
    the same inactivation curve fitting protocol as described
    in [Firek1995] (same lab and Nygren et al refer to
    `our data`).

    Current traces are recorded in response to selected
    voltage steps from a holding potential of -80 mV. Analysis
    of the kinetics of inactivation of these records showed that
    a double exponential function provides the best fit in most
    cases.

    The double exponential fit was to include time constants
    for Isus as well as Ito. We assume a single exponential fit
    for the isolated Ito.
    """
vsteps_taui, tau_i, _ = data.Inact_Kin_Nygren()
variances_taui = [0.]*len(vsteps_taui)
nygren_inact_kin_dataset = np.asarray([vsteps_taui, tau_i, variances_taui])

nygren_inact_kin_protocol = myokit.pacing.steptrain(
    vsteps_taui, -80, 20000, 400)

# assume same as Firek conditions
firek_conditions = {'phys.T': 306.15,  # K
                    'k_conc.K_i': 140, # mM
                    'k_conc.K_o': 5.4
                   }

def nygren_inact_kin_sum_stats(data):
    def single_exp(t, tau, A, A0):
        return A0 + A*np.exp(-t/tau)
    output = []
    for d in data.split_periodic(20400, adjust=True, closed_intervals=False):
        d = d.trim_left(20000, adjust=True)

        current = d['ito.i_to']
        time = d['engine.time']
        index = np.argmax(np.abs(current))

        # Set time zero to peak current
        current = current[index:]
        time = time[index:]
        t0 = time[0]
        time = [t-t0 for t in time]

        with warnings.catch_warnings():
            warnings.simplefilter('error', OptimizeWarning)
            warnings.simplefilter('error', RuntimeWarning)
            try:
                norm = current[0]
                current = [c/norm for c in current]
                if len(time)<=1 or len(current)<=1:
                    raise Exception('Failed simulation')
                popt, _ = so.curve_fit(single_exp,
                                       time,
                                       current,
                                       p0=[10,0.5,0.],
                                       bounds=(0.,
                                               [np.inf, 1.0, 1.0]),
                                       max_nfev=1000)
                fit = [single_exp(t,popt[0],popt[1],popt[2]) for t in time]

                # Calculate r2
                ss_res = np.sum((np.array(current)-np.array(fit))**2)
                ss_tot = np.sum((np.array(current)-np.mean(np.array(current)))**2)
                r2 = 1 - (ss_res / ss_tot)

                tau = popt[0]

                if r2 > fit_threshold:
                    output = output+[tau]
                else:
                    raise RuntimeWarning('scipy.optimize.curve_fit found a poor fit')
            except:
                output = output+[float('inf')]
    return output

nygren_inact_kin = Experiment(
    dataset=nygren_inact_kin_dataset,
    protocol=nygren_inact_kin_protocol,
    conditions=firek_conditions,
    sum_stats=nygren_inact_kin_sum_stats,
    description=nygren_inact_kin_desc,
    Q10=Q10_tau,
    Q10_factor=-1)


#
# Recovery kinetics [Nygren1998]
#
nygren_rec_desc = """
    Recovery kinetics for ito in human
    atrial myocytes [Nygren1998] cf Fig 4c.

    It is not clear where these data are from. We assume
    the same recovery protocol as described
    in [Shibata1989] (same lab and Nygren et al refer to
    `our data`), and using the temperature of the Nygren
    cell model: 33C,

    Two idential depolarizing voltage-clamp pulses from the holding
    potential were applied to a potential (+20 mV) that activated
    a large outward current, and the interval between the two
    pulses was varied.
    """
prepulses, tau_r, _ = data.Rec_Nygren()
variances_taur = [0.]*len(prepulses)
nygren_rec_dataset = np.asarray([prepulses, tau_r, variances_taur])

twaits = [2**i for i in range(1,8)]
tmp_protocols = []
for v in prepulses:
    tmp_protocols.append(
        recovery(twaits,v,20,20,20000,100,100)
    )
nygren_rec_protocol = tmp_protocols[0]
tsplit_rec = tmp_protocols[0].characteristic_time()
for p in tmp_protocols[1:]:
    for e in p.events():
        nygren_rec_protocol.add_step(e.level(), e.duration())

tsplits_rec = [t+100+100+20000 for t in twaits]
for i in range(len(tsplits_rec)-1):
    tsplits_rec[i+1] += tsplits_rec[i]

def nygren_rec_sum_stats(data):
    def single_exp(t, tau, A, A0):
        return A0 - A*np.exp(-t/tau)
    output = []
    timename = 'engine.time'
    for i, d in enumerate(data.split_periodic(tsplit_rec, adjust=True, closed_intervals=False)):
        recov = []
        for t in tsplits_rec:
            d_, d = d.split(t)
            step1 = d_.trim(d_[timename][0]+20000,
                            d_[timename][0]+20000+100,
                            adjust=True)
            step2 = d_.trim_left(t-100, adjust=True)
            try:
                max1 = max(step1['ito.i_to'], key=abs)
                max2 = max(step2['ito.i_to'], key=abs)
                recov = recov + [max2/max1]
            except:
                recov = recov + [float('inf')]

        # now fit to exponential curve
        with warnings.catch_warnings():
            warnings.simplefilter('error', OptimizeWarning)
            warnings.simplefilter('error', RuntimeWarning)
            try:
                popt, _ = so.curve_fit(single_exp,
                                       twaits,
                                       recov,
                                       p0=[50,0.5,0.],
                                       bounds=(0.,
                                               [np.inf, 1.0, 1.0]),
                                       max_nfev=1000)
                fit = [single_exp(t,popt[0],popt[1],popt[2]) for t in twaits]
                # Calculate r2
                ss_res = np.sum((np.array(recov)-np.array(fit))**2)
                ss_tot = np.sum((np.array(recov)-np.mean(np.array(recov)))**2)
                r2 = 1 - (ss_res / ss_tot)

                tau = popt[0]

                if r2 > fit_threshold:
                    output = output+[tau]
                else:
                    raise RuntimeWarning('scipy.optimize.curve_fit found a poor fit')
            except:
                output = output+[float('inf')]
    return output

nygren_rec = Experiment(
    dataset=nygren_rec_dataset,
    protocol=nygren_rec_protocol,
    conditions=firek_conditions,
    sum_stats=nygren_rec_sum_stats,
    description=nygren_rec_desc,
    Q10=Q10_tau,
    Q10_factor=-1)
