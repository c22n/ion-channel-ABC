import numpy as np
import pandas as pd
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('channel', type=str)
parser.add_argument('--exp_num', type=int, nargs='?', default=None,
                    const=None)
parser.add_argument('--logvars', type=str, nargs='*', default=None,
                    const=None)
parser.add_argument('--vdep', type=str, nargs='*', default=None,
                    const=None)
args = parser.parse_known_args()

# Import correct channel.
ch = None
if args[0].channel == 'icat':
    import channels.icat
    ch = channels.icat.icat
elif args[0].channel == 'ikur':
    import channels.ikur
    ch = channels.ikur.ikur
elif args[0].channel == 'ikr':
    import channels.ikr
    ch = channels.ikr.ikr
elif args[0].channel == 'iha':
    import channels.iha
    ch = channels.iha.iha
elif args[0].channel == 'ina':
    import channels.ina
    ch = channels.ina.ina
elif args[0].channel == 'ina_nrvm':
    import channels.ina_nrvm
    ch = channels.ina_nrvm.ina
elif args[0].channel == 'ito':
    import channels.ito
    ch = channels.ito.ito
elif args[0].channel == 'ik1':
    import channels.ik1
    ch = channels.ik1.ik1
elif args[0].channel == 'ical':
    import channels.ical
    ch = channels.ical.ical
elif args[0].channel == 'hl1':
    import channels.hl1
    ch = channels.hl1.hl1
else:
    raise ValueError("Unrecognised channel.")

exp_num = args[0].exp_num
logvars = args[0].logvars
vdep = args[0].vdep

# Collect parameters from input arguments.
for p in ch.pars:
    parser.add_argument("-" + p, type=float)
parser.add_argument('--n_x', type=int, nargs='?', default=None,
                    const=None)
args = parser.parse_args()

# Make dictionary of args to pass to simulation
args_d = vars(args)

# Resolution of independent variable
n_x = args_d['n_x'] 

# Delete all non-parameter arguments
del args_d['channel']
del args_d['exp_num']
del args_d['logvars']
del args_d['vdep']

sim = None
if vdep is not None:
    sim = ch.get_V_dependence(variables=vdep,
                              vvals=np.arange(-150, 60, 10),
                              pars=args_d)
else:
    sim = ch(args_d, exp_num=exp_num, logvars=logvars,
             n_x=n_x)
with pd.option_context('display.max_rows', -1, 'display.max_columns', -1):
    print sim.to_string(index=False)
