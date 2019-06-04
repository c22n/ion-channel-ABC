import numpy as np

### Digitised data for HL-1 i_CaT channel.


# I-V curves.

def IV_Deng():
    """Data points in IV curve for i_CaT.

    Data from figure 1B in Deng 2009. Reported as mean \pm SEM for 19 cells.
    """
    x = [-80, -70, -60, -50, -40, -30, -20, -10, 0, 10, 20, 30, 40]
    y = np.asarray([0.0951474785918176,
                    -0.2616555661274975,
                    -2.283539486203615,
                    -5.566127497621313,
                    -11.298763082778304,
                    -17.340627973358703,
                    -20.028544243577542,
                    -18.57754519505233,
                    -14.747859181731684,
                    -9.657469077069456,
                    -5.256898192197905,
                    -1.5223596574690768,
                    0.0237868696479544])
    N = 19
    sem = np.asarray([0.0713606089438632,
                      0.0237868696479544,
                      -1.6175071360608944,
                      -4.448144624167458,
                      -9.919124643196954,
                      -15.651760228353947,
                      -18.268315889628923,
                      -17.53092293054234,
                      -13.986679352997143,
                      -8.824928639391056,
                      -4.424357754519505,
                      -0.8325404376784014,
                      0.0951474785918176])
    sem = np.abs(y-sem)
    variances = np.sqrt(N) * sem
    variances = variances**2
    return x, y.tolist(), variances.tolist()


def IV_Nguyen():
    """Data points for IV curve in i_CaT.

    Extracted from figure 5B in Nguyen 2013. Reported as mean \pm SD
    for 9 cells.
    """
    x = [-75, -70, -65, -60, -55, -50, -45, -40, -35, -30, -25, -20,
         -15, -10, -5, 0, 5, 10, 15, 20, 25, 30, 35]
    y = np.asarray([0.23612750885478206,
                    0.18890200708382565,
                    0.3305785123966949,
                    0.2833530106257385,
                    -0.023612750885478206,
                    -0.8264462809917354,
                    -2.762691853600944,
                    -5.430932703659976,
                    -8.429752066115704,
                    -10.861865407319954,
                    -11.971664698937428,
                    -12.18417945690673,
                    -11.66469893742621,
                    -10.861865407319954,
                    -9.58677685950413,
                    -8.193624557260922,
                    -6.706021251475797,
                    -5.24203069657615,
                    -3.8488783943329397,
                    -2.6210153482880747,
                    -1.4167650531286888,
                    -0.6139315230224316,
                    -0.07083825265643462])
    N = 9
    sd = np.asarray([0.21251475796930386,
                      0.11806375442739103,
                      0.14167650531286924,
                      0.11806375442739103,
                      -0.330578512396694,
                      -1.558441558441558,
                      -4.037780401416765,
                      -6.942148760330578,
                      -9.940968122786305,
                      -12.373081463990555,
                      -13.506493506493506,
                      -13.648170011806375,
                      -12.987012987012989,
                      -12.278630460448642,
                      -10.838252656434474,
                      -9.279811097992916,
                      -7.697756788665878,
                      -6.162927981109799,
                      -4.580873671782762,
                      -3.3057851239669427,
                      -1.9598583234946867,
                      -1.109799291617473,
                      -0.6139315230224316])
    sd = np.abs(y-sd)
    variances = sd**2

    return x, y.tolist(), variances.tolist()


# Activation curves.

def Act_Deng():
    """Data points for normalised activation curve.

    Extracted from figure 3B in Deng 2009. Reported as mean \pm SEM for
    19 cells.
    """
    x = [-80, -70, -60, -50, -40, -30, -20, -10]
    y = np.asarray([0.0016477857878474111,
         0.026364572605561243,
         0.0016477857878474111,
         0.055200823892893824,
         0.2949536560247167,
         0.49845520082389283,
         0.8486096807415036,
         1.0018537590113286])
    N = 19
    sem = np.asarray([8.238928939237056E-4,
            0.017301750772399593,
            0.026364572605561243,
            0.06343975283213177,
            0.3559217301750772,
            0.5462409886714726,
            0.8634397528321318,
            1.0018537590113286])
    sem = np.abs(y-sem)
    variances = np.sqrt(N) * sem
    variances = variances**2

    return x, y.tolist(), variances.tolist()


def Act_Nguyen():
    """Data points for normalised activation curve for i_CaT.

    Data extracted from figure 5C in Nguyen 2013. Reported as mean \pm SD
    for 9 cells.
    """
    x = [-75, -70, -65, -60, -55, -50, -45, -40, -35, -30, -25, -20,
         -15, -10, -5, 0, 5]
    y = np.asarray([0.00592592592592589,
                    0.00592592592592589,
                    0.0,
                    0.004444444444444473,
                    0.014814814814814836,
                    0.04888888888888876,
                    0.13629629629629625,
                    0.2785185185185185,
                    0.4637037037037036,
                    0.6444444444444444,
                    0.7733333333333332,
                    0.8666666666666666,
                    0.9274074074074073,
                    0.9777777777777776,
                    0.994074074074074,
                    1.0044444444444443,
                    1.0029629629629628])
    N = 9
    sd = np.asarray([0.0251851851851852,
                      0.02370370370370356,
                      0.020740740740740726,
                      0.01185185185185178,
                      0.020740740740740726,
                      0.07703703703703701,
                      0.18074074074074065,
                      0.33333333333333326,
                      0.514074074074074,
                      0.6859259259259258,
                      0.8029629629629629,
                      0.8888888888888888,
                      0.9422222222222221,
                      0.9925925925925925,
                      1.0014814814814814,
                      1.0103703703703704,
                      1.0162962962962963])
    sd = np.abs(y-sd)
    variances = sd**2

    return x, y.tolist(), variances.tolist()


# Inactivation curves.

def Inact_Deng():
    """Data points for inactivation curve of i_CaT.

    Extracted from figure 3B in Deng 2009. Reported as mean \pm SEM
    for 19 cells.
    """
    x = [-100, -90, -80, -70, -60, -50, -40, -30, -20]
    y = np.asarray([1.000205973223481,
                    0.9868863714383797,
                    0.9883968417439065,
                    0.9767250257466529,
                    0.910676278750429,
                    0.5315482320631649,
                    0.1730175077239956,
                    6.875652927706977E-4,
                    5.492619292823964E-4])
    N = 19
    sem = np.asarray([0.9820803295571575,
                      0.9720562993477514,
                      0.9768623412289735,
                      0.9602471678681771,
                      0.8694816340542395,
                      0.4639890147614142,
                      0.23233779608650862,
                      0.01139817291377998,
                      0.013731548232063018])
    sem = np.abs(y-sem)
    variances = np.sqrt(N) * sem
    variances = variances**2

    return x, y.tolist(), variances.tolist()


def Inact_Nguyen():
    """Data points for inactivation curve for i_CaT.

    Extracted from figure 5E in Nguyen 2013. Data reported as mean \pm SEM
    for 7 cells.
    """
    x = [-80, -75, -70, -65, -60, -55, -50, -45, -40, -35, -30, -25]
    y = np.asarray([0.9985915492957746,
                    0.9900227169468424,
                    0.9800454338936847,
                    0.9658427987278511,
                    0.9178388611237317,
                    0.7853263668029684,
                    0.5359139784946236,
                    0.273824019385128,
                    0.10610177192185377,
                    0.04119491140390741,
                    0.02276843858852029,
                    0.02546721187339096])
    N = 7
    sd = np.asarray([0.9943646827199758,
                      0.9942465545963957,
                      0.9856792367105861,
                      0.9714766015447525,
                      0.9347402695744359,
                      0.8205376344086022,
                      0.6091519006512192,
                      0.3315704982583674,
                      0.13849462365591403,
                      0.05387096774193556,
                      0.029810692109647263,
                      0.012791155535362808])
    sd = np.abs(y-sd)
    variances = sd**2
    
    return x, y.tolist(), variances.tolist()


# Recovery curves.

def Rec_Deng():
    """Data points for recovery curve of i_CaT.

    Extracted from figure 4B in Deng 2009. Data reported as mean \pm SEM
    for 19 cells.
    """
    x = [32, 64, 96, 128, 160, 192, 224, 256, 288, 320]
    y = np.asarray([0.24120603015075381,
                    0.44472361809045224,
                    0.5787269681742044,
                    0.6582914572864322,
                    0.7738693467336684,
                    0.8165829145728644,
                    0.8961474036850922,
                    0.9338358458961474,
                    0.9706867671691792,
                    0.9807370184254607])
    N = 19
    sem = np.asarray([0.24036850921273034,
                      0.4061976549413736,
                      0.5326633165829147,
                      0.6072026800670017,
                      0.7286432160804021,
                      0.7654941373534339,
                      0.8634840871021776,
                      0.9053601340033501,
                      0.9405360134003351,
                      0.9514237855946399])
    sem = np.abs(y-sem)
    variances = np.sqrt(N) * sem
    variances = variances**2

    return x, y.tolist(), variances.tolist()

# Current trace

def CurrTrace_Deng():
    """Data points for current trace of i_CaT in HL-1.

    Trace from stimulation from HL=-80mV to -20mV (Fig 1A).
    """
    x = [-87.28295506275606, -86.08473694478766, -84.28497106067503,
         -82.43968264290822, -80.90004552253365, -78.81413799830915,
         -76.43883722442608, -73.34330493594328, -66.75554399427716,
         -57.87539832216948, -46.280158678545874, -32.618521167978145,
         -15.90524809780841, -2.809390648370936, 8.875268257787624,
         26.204721337061855, 43.745529036873265, 58.060740066332826,
         70.15347597060544]
    x0 = x[0]
    x = [xi - x0 for xi in x]
    y = [798.1053669530921, 542.7348922383435, 291.78405409212587,
         -20.302155233131316, -192.6679814058316, -286.378363149739,
         -227.21510071841112, -52.26088181433988, 306.4163966755882,
         564.8506831948164, 696.8763206085365, 761.3924496407947,
         789.0547964502044, 801.1163544161152, 813.054655585294,
         825.4859839414003, 824.834483730103, 823.9012536977041,
         829.3245527539092]
    y0 = y[0]
    y = [yi - y0 for yi in y]
    return x, y, None