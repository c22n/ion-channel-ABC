### Digitised data from [Wang1993]
import numpy as np

# Steady State Activation

def Act_Wang():
    """
    Steady-State activation curve [Wang1993]
    cf Fig 2c
    """
    x = np.arange(-30, 60, 10).tolist()
    y = np.asarray([0.006968641114982743,
                    0.03310104529616731,
                    0.10801393728223019,
                    0.2857142857142858,
                    0.47560975609756106,
                    0.6829268292682928,
                    0.8222996515679444,
                    0.9216027874564461,
                    0.9965156794425089])
    yerr = np.asarray([0.020905923344947785,
                       0.04703832752613257,
                        0.1254355400696865,
                        0.3344947735191639,
                        0.5209059233449479,
                        0.7212543554006969,
                        0.848432055749129,
                        0.9390243902439026,
                        1.0139372822299653])
    sem = np.abs(y-yerr)
    N = 6
    sd = np.sqrt(N)*sem
    return x, y.tolist(), sd.tolist()


# Steady State Inactivation

def Inact_Wang():
    """
    Steady-State inactivation curve [Wang1993]
    cf Fig 2c
    """
    x = np.arange(-90, 40, 10).tolist()
    y = np.asarray([1.0000000000000002,
                    0.9773519163763068,
                    0.9808362369337981,
                    1.0034843205574915,
                    0.986062717770035,
                    0.8327526132404183,
                    0.34843205574912905,
                    0.0818815331010454,
                    0.03135888501742157,
                    0.005226480836237002,
                    -0.0017421602787455193,
                    0, 0])
    yerr = np.asarray([0.9808362369337981,
                        0.956445993031359,
                        0.9581881533101047,
                        0.9843205574912893,
                        0.9651567944250873,
                        0.7944250871080141,
                        0.29790940766550533,
                        0.10278745644599319,
                        0.010452961672474004,
                        -0.017421602787456303,
                        -0.020905923344947563,
                        -0.020905923344947563,
                        -0.019163763066202044])
    sem = np.abs(y-yerr)
    N = 10
    sd = np.sqrt(N)*sem
    return x, y.tolist(), sd.tolist()
